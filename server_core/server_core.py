import socket
import select
import traceback
from typing import List, Dict, Callable, Set, Optional

# type hint
RequestHandler = Callable[[List[str], 'Server.Response'], None]
ConnectionCloseCallback = Callable[[int], None]


class Server:
    def __init__(self, host: str = '127.0.0.1', port: int = 3000):
        self._HOST = host
        self._PORT = port
        self._MESSAGE_TERMINAITON_SEQUENCES: List[bytes] = [b'\n\n', b'\n\r\n']
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._epoll = select.epoll()
        self._client_sockets: Dict[int, socket.socket] = {}
        self._closing_sockets: Set[int] = set()
        self._requests: Dict[int, bytes] = {}
        self._responses: Dict[int, bytes] = {}
        self._request_handlers: Dict[str, RequestHandler] = {}
        self._on_connection_close: Optional[ConnectionCloseCallback] = None
        self._responses_connections: Dict[int, int] = {}

    def register_handler(self, request_name: str, handler: RequestHandler) -> None:
        self._request_handlers[request_name] = handler

    def set_connection_close_callback(self, callback: ConnectionCloseCallback) -> None:
        self._on_connection_close = callback

    def start(self) -> None:
        """Runs the server """
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self._HOST, self._PORT))
        self._server_socket.listen()
        self._server_socket.setblocking(False)
        self._epoll.register(self._server_socket.fileno(), select.EPOLLIN)
        try:
            self._start_event_loop()
        except:
            traceback.print_exc()
            # quit on exceptions and after keyboard interrupt (CTRL + c)
            self._epoll.unregister(self._server_socket.fileno())
            self._epoll.close()
            self._server_socket.close()

    def _start_event_loop(self) -> None:
        """Starts server infinite event loop in which it accepts new conections or reads client data.
            This is done using `epoll` linux system call. I/O operations are performed only when there
            is data ready to read and therefore all socket reads should be non-blocking. 
            Only blocking operation is epoll call. This allows one thread to handle all client connections.
        """
        while True:
            events = self._epoll.poll(None, -1)
            for file_descriptor, event in events:
                try:
                    if file_descriptor == self._server_socket.fileno():
                        self._accept_new_connection()
                    elif event & select.EPOLLIN:
                        self._read_client_socket(file_descriptor)
                    elif event & select.EPOLLOUT:
                        self._write_to_client_socket(file_descriptor)
                    elif event & select.EPOLLHUP:
                        self._handle_connection_shutdown(file_descriptor)
                except ConnectionResetError:
                    self._handle_connection_shutdown(file_descriptor)

    def _accept_new_connection(self) -> None:
        client_socket, _ = self._server_socket.accept()
        client_socket.setblocking(False)
        file_descriptor = client_socket.fileno()
        self._client_sockets[file_descriptor] = client_socket
        self._requests[file_descriptor] = b''
        self._responses[file_descriptor] = b''
        self._epoll.register(file_descriptor, select.EPOLLIN)
        print(f'client with file descriptor {file_descriptor} connected')

    def _read_client_socket(self, file_descriptor: int) -> None:
        client_socket = self._client_sockets[file_descriptor]
        buffer: bytes = client_socket.recv(1024)
        if len(buffer) == 0:
            # after client sudden shutdown of socket EOF is reached and buffer is empty
            # if not handled epoll will keep reading empty bytes from this socket
            self._handle_connection_shutdown(file_descriptor)
            return
        else:
            self._requests[file_descriptor] += buffer
        print(f'received message from socket with file descriptor: {client_socket.fileno()}: ')
        print(buffer)
        if any(seq in buffer for seq in self._MESSAGE_TERMINAITON_SEQUENCES):
            self._handle_completed_request(file_descriptor)

    def _write_to_client_socket(self, file_descriptor: int) -> None:
        response = self._responses[file_descriptor]
        if len(response) < 2 or response[-1] != b'\n' or response[-2] != b'\n':
            response += b'\n\n'
        sent_bytes_count = self._client_sockets[file_descriptor].send(response)
        self._responses[file_descriptor] = response[sent_bytes_count:]
        if len(response) == sent_bytes_count:
            if file_descriptor in self._closing_sockets:
                self._closing_sockets.remove(file_descriptor)
                self._handle_connection_shutdown(file_descriptor)
                return
            self._requests[file_descriptor] = b''
            self._responses[file_descriptor] = b''
            self._epoll.modify(file_descriptor, select.EPOLLIN)

    def _handle_completed_request(self, file_descriptor: int) -> None:
        request: bytes = self._requests[file_descriptor]
        lines: List[str] = request.decode('utf-8').splitlines()
        if not len(lines) > 0:
            self._handle_invalid_request(file_descriptor)
            return
        request_name = lines.pop(0).strip()
        handler = self._request_handlers.get(request_name)
        if handler is None:
            self._handle_invalid_request(file_descriptor)
            return
        paired_response: Optional[Server.Response] = None
        if file_descriptor in self._responses_connections:
            paired_response = Server.Response(self._responses_connections[file_descriptor], self, None)
        response = Server.Response(file_descriptor, self, paired_response)
        handler(lines, response)

    def _handle_invalid_request(self, file_descriptor: int, message: str = "Invalid Request") -> None:
        self._responses[file_descriptor] = message.encode('utf-8')
        self._epoll.modify(file_descriptor, select.EPOLLOUT)

    def _handle_connection_shutdown(self, file_descriptor: int) -> None:
        print(f'connection {file_descriptor} closed')
        if self._on_connection_close is not None:
            self._on_connection_close(file_descriptor)
        self._epoll.unregister(file_descriptor)
        self._client_sockets[file_descriptor].close()
        del self._client_sockets[file_descriptor]
        del self._requests[file_descriptor]
        del self._responses[file_descriptor]

    def _create_responses_connection(self, first_file_descriptor: int, second_file_descriptor: int) -> None:
        self._responses_connections[first_file_descriptor] = second_file_descriptor
        self._responses_connections[second_file_descriptor] = first_file_descriptor

    class Response:
        def __init__(self, file_descriptor: int, server: 'Server', pair: Optional['Server.Response']):
            self._server = server
            self._file_descriptor = file_descriptor
            self._is_already_sent = False
            self._pair = pair

        def close(self) -> None:
            assert not self._is_already_sent, 'response already sent'
            self._server._handle_connection_shutdown(self._file_descriptor)
            self._is_already_sent = True

        def send(self, message: str) -> None:
            assert not self._is_already_sent, 'response already sent'
            self._server._responses[self._file_descriptor] = message.encode('utf-8')
            self._server._epoll.modify(self._file_descriptor, select.EPOLLOUT)
            self._is_already_sent = True

        def send_and_close(self, message: str) -> None:
            assert not self._is_already_sent, 'response already sent'
            self._server._responses[self._file_descriptor] = message.encode('utf-8')
            self._server._epoll.modify(self._file_descriptor, select.EPOLLOUT)
            self._server._closing_sockets.add(self._file_descriptor)
            self._is_already_sent = True

        def reject_request(self) -> None:
            assert not self._is_already_sent, 'response already sent'
            self._server._handle_invalid_request(self._file_descriptor)
            self._is_already_sent = True

        def pair_with(self, file_descriptor: int) -> 'Server.Response':
            self._server._create_responses_connection(self._file_descriptor, file_descriptor)
            return Server.Response(file_descriptor, self._server, None)

        def get_paired_response(self) -> Optional['Server.Response']:
            return self._pair

        def get_file_descriptor(self) -> int:
            return self._file_descriptor
