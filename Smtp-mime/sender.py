import argparse
import os
import socket
import ssl
from dataclasses import dataclass
from typing import Optional, Tuple, List
import base64

from message import ContentMessage, Message


@dataclass
class SenderException(Exception):
    message: str


class SMTPSender:
    _host: str
    _mess_from: str
    _mess_to: str
    _port: int
    _sock: socket.socket
    _directory: str
    _boundary: str = 'part'
    _subject: str

    def __init__(self, host: str, mess_from: str, mess_to: str, port: int, directory: str, subject: str):
        self._host, self._port = host, port
        self._mess_from, self._mess_to = mess_from, mess_to
        self._directory = directory or os.getcwd()
        self._subject = subject
        self._sock = socket.socket()

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
        for name in os.listdir(self._directory):
            ext = name.rsplit('.', maxsplit=1)[1]
            with open(os.path.join(self._directory, name), 'rb') as file:
                result.append(ContentMessage(
                    {'Content-type': f'image/{ext}; name={name}',
                     'Content-transfer-encoding': 'base64',
                     'Content-disposition': f'attachment;filename:"{name}"'},
                    base64.b64encode(file.read()),
                ))
        if not len(result):
            raise SenderException('Dir is empty!')
        return result

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

    def _sender(self, commands: List[Tuple[bytes, bytes]], verbose: bool) -> None:
        for command, code in commands:
            self._sock.sendall(command)
            answer = self._accept_message()
            self._ensure_code_correct(answer, code)
            if verbose:
                print('Client:')
                print(b'\n'.join(command.split(b'\r\n')).decode())
                print('Server:')
                print(b'\n'.join(answer.split(b'\r\n')).decode())

    def send_message(self, verbose: bool, auth: bool, tls: bool) -> Optional[str]:
        self._sock = socket.socket()
        self._sock.settimeout(1)
        if self._port == 465:
            self._sock, tls = ssl.wrap_socket(self._sock), False
        try:
            self._sock.connect((self._host, self._port))
            self._ensure_code_correct(self._accept_message(), b'220 ')
            if tls:
                self._sender([(f'EHLO {self._host}\r\n'.encode(), b'250 ')], verbose)   # ESMTP
                self._sender([(b'STARTTLS\r\n', b'220 ')], verbose)     # ESMTP
                self._sock = ssl.wrap_socket(self._sock)
            self._sender([(f'EHLO {self._host}\r\n'.encode(), b'250 ')], verbose)
            if auth:
                self._sender([
                    (b'AUTH LOGIN\r\n', b'334 '),
                    (base64.b64encode(self._mess_from.encode()) + b'\r\n', b'334 '),
                    (base64.b64encode(input('Password --> ').encode()) + b'\r\n', b'235 ')], verbose)
            self._sender([
                (f'MAIL FROM: <{self._mess_from}>\r\n'.encode(), b'250 '),
                (f'rcpt TO: <{self._mess_to}>\r\n'.encode(), b'250 '),
                (b'DATA\r\n', b'354 ')
            ], verbose)
            self._sock.sendall(self._create_message().__bytes__())
            self._sender([
                (b'\n.\r\n', b'250 '),
                (b'QUIT\r\n', b'221 ')
            ], verbose)
            return 'Email sent successfully!'
        finally:
            self._sock.close()


def main():
    parser = argparse.ArgumentParser(prog='Smtp-mime', description='Smtp-mime with arguments')
    parser.add_argument('--ssh', action='store_true', help='Start with ssh')
    parser.add_argument('--auth', action='store_true', help='Authentication')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    parser.add_argument('-s', '--server', help='Server[:port]. Default 25 port.')
    parser.add_argument('-d', '--directory', help='Directory')
    parser.add_argument('-t', '--to', help='Email of recipient')
    parser.add_argument('-f', '--from', dest='user_name', default='', help='Email of sender')
    parser.add_argument('--subject', default='Happy Pictures', help='Sabject of mail.')
    args = parser.parse_args()
    for method in ['server', 'directory', 'to']:
        if getattr(args, method) is None:
            return print(f'Empty field {method}')
    try:
        host, port = args.server.strip(':').split(':')
    except ValueError:
        host, port = args.server, 25
    sender = SMTPSender(host, args.user_name, args.to, int(port), args.directory, args.subject)
    try:
        print(sender.send_message(args.verbose, args.auth, args.ssh))
    except SenderException as exc:
        print(exc.message.strip('\r\n') or 'Unknown error!')
        exit(1)


if __name__ == '__main__':
    main()
