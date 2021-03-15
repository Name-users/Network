import socket
from threading import Thread
from time import sleep


class Client(Thread):
    def __init__(self, host: str, port: int, id: int):
        super().__init__()
        self.host, self.port = host, port
        self.client: socket.socket = socket.socket()
        self.id = id

    def run(self) -> None:
        try:
            self.client.connect((self.host, self.port))
            print(self.client.recv(1024).decode(), f'Thread - {self.id}', flush=True)
            self.client.sendall(b'PING')
            print(self.client.recv(1024).decode(), f'Thread - {self.id}', flush=True)
            sleep(5)
        except socket.error as exc:
            print(exc)
        finally:
            self.client.close()


def main(host: str, port: int):
    clients = [Client(host, port, _) for _ in range(10)]
    for client in clients:
        client.start()


if __name__ == '__main__':
    main('localhost', 8080)
