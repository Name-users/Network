from typing import Dict, List


class ContentMessage:
    _headers: Dict[str, str]
    _body: bytes

    def __init__(self, headers: Dict[str, str], body: bytes):
        self._headers = headers
        self._body = body

    def __bytes__(self):
        return b'\n'.join([
            *(f'{key}: {value};'.encode() for key, value in self._headers.items()),
            b'',
            self._body
        ])


class Message:
    _headers: Dict[str, str]
    _body: List[ContentMessage]
    _boundary: str

    def __init__(self, headers: Dict[str, str], body: List[ContentMessage], boundary: str):
        self._headers = headers
        self._body = body
        self._boundary = boundary

    def __bytes__(self):
        head = '\n'.join([
            *(f'{key}: {value}' for key, value in self._headers.items()),
            '', ''
        ])
        body = f'--{self._boundary}\n'.encode().join([
            b'',
            *(content.__bytes__() + b'\n' for content in self._body)
        ]) + f'\n--{self._boundary}--\n'.encode()
        return head.encode() + body

