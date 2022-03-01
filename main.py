
from gui.app import App

if __name__ == '__main__':
    timer_height = 25
    width = 550
    height = 550 + 2 * timer_height

    app = App(width, height)
    app.start()
