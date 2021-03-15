import socket
from threading import Thread, Lock
from typing import Set, Optional, Dict


def ident_iter():
    i = 1
    while True:
        yield i
        i += 1


class Connection:
    _ident_iter = iter(ident_iter())
    _connection: socket.socket = None
    _lock: Lock = None
    _id: int = None
    _stop: bool = None
    _close_hook: set.remove = None
    _conn_thread: Thread = None
    response_template: Dict[str, str] = {
        'Hello': 'Hello, glad to see you on our server!',
        'PING': 'PONG'
    }

    def __init__(self, conn: socket.socket, close_hook: set.remove):
        self._connection: socket.socket = conn
        self._connection.settimeout(3)
        self._lock = Lock()
        self._stop = False
        self._close_hook = close_hook

    def start(self):
        self._conn_thread = Thread(target=self._run)
        self._conn_thread.start()

    def _run(self) -> None:
        try:
            self._connection.sendall(
                self.response_template.get('Hello').encode()
            )
            while not self._stop:
                message = self._get_message()
                if message in self.response_template.keys():
                    self._connection.sendall(
                        self.response_template.get(message).encode()
                    )
        except socket.error:
            pass
        finally:
            self._close_connection()

    def _get_message(self) -> Optional[str]:
        buf = []
        try:
            while not self._stop:
                data = self._connection.recv(1024)
                if not data:
                    break
                buf.append(data.decode())
        except socket.timeout:
            if not len(buf):
                raise
        return ''.join(buf)

    def _close_connection(self) -> None:
        with self._lock:
            print('Close connection', flush=True)
        if self._connection:
            self._connection.close()
        self._close_hook(self)

    def close(self) -> None:
        self._stop = True
        self._conn_thread.join()

    @property
    def id(self):
        with self._lock:
            if not self._id:
                self._id = next(self._ident_iter)
        return self._id

    def __hash__(self):
        return self.id


class Server:
    _host: str
    _port: int
    _count: int
    _stop: bool = False
    _server: socket = None

    def __init__(self, host: str = '', port: int = 0, count: int = 0):
        self._host, self._port, self._count = host, port, count
        self._connections: Set[Connection] = set()
        self._stop = False

    def create_server(self):
        self._server: socket = socket.create_server(
            (self._host, self._port), backlog=self._count
        )

    def start(self):
        try:
            while not self._stop:
                conn, adr = self._server.accept()
                connection = Connection(conn, self._connections.remove)
                connection.start()
                self._connections.add(connection)
                print(f'Connections count - {len(self._connections)}')
        except (OSError, socket.error):
            pass

    @property
    def port(self):
        if self._server:
            return self._server.getsockname()[1]

    @property
    def host(self):
        if self._server:
            return self._server.getsockname()[0]

    def close(self):
        self._stop = True
        if self._server:
            self._server.close()
        for conn in list(self._connections):
            conn.close()


def main():
    server = Server(port=8080)
    try:
        server.create_server()
        print(f'Server run on {server.host}:{server.port}')
        server.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()


if __name__ == '__main__':
    main()
