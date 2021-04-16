import os
import socket
import ssl
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
import base64

from message import ContentMessage, Message


@dataclass
class SenderException(Exception):
    message: str


class SMTPSender:
    _format: Dict[str, str] = {'jpg': 'jpeg'}
    _host: str
    _user_name: str
    _password: str
    _mess_from: str
    _mess_to: str
    _port: int
    _sock: socket.socket
    _dir: str
    _boundary: str = 'part'
    _subject: str

    def __init__(self, host: str, user_name: str,
                 password: str, mess_from: str, mess_to: str, port, dir: str, subject: str):
        self._host, self._port = host, port
        self._user_name, self._password = user_name, password
        self._mess_from, self._mess_to = mess_from, mess_to
        self._dir = dir or os.getcwd()
        self._subject = subject

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

    def _open_content(self) -> List[ContentMessage]:
        result: List[ContentMessage] = []
        for name in os.listdir(self._dir):
            ext = name.rsplit('.', maxsplit=1)[1]
            if ext not in self._format.keys():
                continue
            with open(os.path.join(self._dir, name), 'rb') as file:
                result.append(ContentMessage(
                    {'Content-type': f'image/{self._format[ext]}',
                     'Content-transfer-encoding': 'base64',
                     'Content-disposition': f'attachment; filename: "{name}"'},
                    base64.b64encode(file.read()),
                ))
        if not len(result):
            raise SenderException('Dir is empty!')
        return result

    # @staticmethod
    # def _get_message_from_file(file_name: str) -> Optional[bytes]:
    #     with open(file_name) as file:
    #         return file.read().encode(encoding="windows-1251")

    def _create_message(self) -> Message:
        return Message(
            {
                'From': f'<{self._mess_from}>',
                'To': f'<{self._mess_to}>',
                'Subject': f'{self._subject}',
                'Content-type': f'multipart/mixed; boundary={self._boundary}'
            },
            self._open_content(),
            self._boundary
        )

    @staticmethod
    def _ensure_code_correct(accept: bytes, accept_code: bytes) -> None:
        accept = accept.strip(b'\r\n').split(b'\r\n')[-1]
        if not accept.startswith(accept_code):
            raise SenderException(accept.decode())

    def _sender(self, commands: List[Tuple[bytes, bytes]]) -> None:
        for command, code in commands:
            self._sock.sendall(command)
            self._ensure_code_correct(self._accept_message(), code)

    def send_message(self) -> Optional[str]:
        self._sock = ssl.wrap_socket(socket.socket())
        self._sock.settimeout(1)
        # if (auth) do 103-105
        try:
            self._sock.connect((self._host, self._port))
            self._ensure_code_correct(self._accept_message(), b'220 ')
            self._sender([
                (f'EHLO {self._host}\r\n'.encode(), b'250 '),
                (b'AUTH LOGIN\r\n', b'334 '),
                (base64.b64encode(self._user_name.encode()) + b'\r\n', b'334 '),
                (base64.b64encode(self._password.encode()) + b'\r\n', b'235 '),
                (f'MAIL FROM: {self._mess_from}\r\n'.encode(), b'250 '),
                (f'rcpt TO: {self._mess_to}\r\n'.encode(), b'250 '),
                (b'DATA\r\n', b'354 ')
            ])
            self._sock.sendall(self._create_message().__bytes__())
            self._sender([
                (b'\n.\r\n', b'250 '),
                (b'QUIT\r\n', b'221 ')
            ])
            return 'Email sent successfully!'
        finally:
            self._sock.close()



