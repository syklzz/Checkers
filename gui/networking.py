import socket
import threading
import queue
from typing import List
from pygame.constants import USEREVENT
import pygame.event

HOST = '83.4.53.166'
PORT = 5000


class ThreadEvent:
    def __init__(self, request_name: str, args: List[str], is_response_only: bool = False):
        self.request_name = request_name
        self.args = args
        self.is_response_only = is_response_only

    def should_send_request(self):
        return not self.is_response_only

    def get_request_string(self):
        request_string = '\n'.join([self.request_name, *self.args])
        request_string += '\n\n'
        return request_string


class NetworkThread:
    def __init__(self):
        self.thread = threading.Thread(target=self.thread_routine)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.requests_queue: queue.Queue[ThreadEvent] = queue.Queue()
        self.event_queue = threading.Event()

    def disconnect(self):
        self.requests_queue.queue.clear()
        self.socket.close()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.event_queue.clear()
        self.socket.connect((HOST, PORT))
        if not self.thread.is_alive():
            self.thread.start()

    def thread_routine(self):
        while True:
            self.event_queue.wait()
            while not self.requests_queue.empty():
                try:
                    request = self.requests_queue.get()
                    if request.should_send_request():
                        request_string = request.get_request_string()
                        self.socket.sendall(request_string.encode('utf-8'))
                    else:
                        print("waiting for", request.request_name)
                    response = self.socket.recv(2048).decode()
                    print("server resposnded: ", response)
                    pygame.event.post(pygame.event.Event(USEREVENT, name=request.request_name, data=response))
                except ConnectionAbortedError:
                    pass
            self.event_queue.clear()

    def send_request(self, request_name: str, args: List[str]):
        self.requests_queue.put(ThreadEvent(request_name, args))
        self.event_queue.set()

    def wait_for_response(self, event_name: str):
        self.requests_queue.put(ThreadEvent(event_name, [], True))
        self.event_queue.set()
