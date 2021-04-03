import socket
import ssl
from dataclasses import dataclass
from typing import Optional, Tuple, List
import base64


@dataclass
class SenderException(Exception):
    message: str


class SMTPSender:
    _host: str
    _user_name: str
    _password: str
    _from_to: str
    _rcpt_to: str
    _port: int
    _sock: socket.socket

    def __init__(self, host: str, user_name: str,
                 password: str, from_to: str, rcpt_to: str, port):
        self._host, self._port = host, port
        self._user_name, self._password = user_name, password
        self._from_to, self._rcpt_to = from_to, rcpt_to

    def _accept_message(self) -> Optional[bytes]:
        buffer = []
        try:
            while 1:
                message = self._sock.recv(1024)
                if not message:
                    break
                buffer.append(message)
        except socket.timeout:
            pass
        return b''.join(buffer)

    @staticmethod
    def _get_message_from_file(file_name: str) -> Optional[bytes]:
        with open(file_name) as file:
            return file.read().encode()

    @staticmethod
    def _ensure_code_correct(accept: bytes, accept_code: bytes) -> None:
        accept = accept.strip(b'\r\n').split(b'\r\n')[-1]
        if not accept.startswith(accept_code):
            raise SenderException(accept.decode())

    def _sender(self, commands: List[Tuple[bytes, bytes]]) -> None:
        for command, code in commands:
            self._sock.sendall(command)
            self._ensure_code_correct(self._accept_message(), code)

    def send_message(self, message: str) -> Optional[str]:
        self._sock = ssl.wrap_socket(socket.socket())
        self._sock.settimeout(1)
        try:
            self._sock.connect((self._host, self._port))
            self._ensure_code_correct(self._accept_message(), b'220 ')
            self._sender([
                (f'EHLO {self._host}\r\n'.encode(), b'250 '),
                (b'AUTH LOGIN\r\n', b'334 '),
                (base64.b64encode(self._user_name.encode()) + b'\r\n', b'334 '),
                (base64.b64encode(self._password.encode()) + b'\r\n', b'235 '),
                (f'MAIL FROM: {self._from_to}\r\n'.encode(), b'250 '),
                (f'rcpt TO: {self._rcpt_to}\r\n'.encode(), b'250 '),
                (b'DATA\r\n', b'354 ')
            ])
            self._sock.sendall(self._get_message_from_file(message))
            self._sender([
                (b'\n.\r\n', b'250 '),
                (b'QUIT\r\n', b'221 ')
            ])
            return 'Email sent successfully!'
        finally:
            self._sock.close()


if __name__ == '__main__':
    print('Write all in utf-8!')
    sender = SMTPSender(
        input('SMTP host -> '),
        input('User name -> '),
        input('Password -> '),
        input('From -> '),
        input('Rcpt to -> '),
        int(input('Server port -> ') or 465)
    )
    try:
        print(sender.send_message(input('Path to file with message -> ')))
    except SenderException as exc:
        print(exc.message.strip('\r\n'))
