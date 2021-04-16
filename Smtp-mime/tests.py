import unittest
from unittest import TestCase

from message import ContentMessage, Message


class MessageTests(TestCase):
    _content_message: ContentMessage

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls._content_message = ContentMessage(
            {
                'Content-type': 'type: image/jpeg',
                'Content-transfer-encoding': ' base64'
            },
            b'test')

    def test_content(self):
        """
        Content - type: image / jpeg;
        Content - transfer - encoding: base64
        Content - disposition: attachment;
        filename: "test.jpg"
        Content - Id: photo
        """
        self.assertEqual(b'\n'.join([
            b'Content-type: type: image/jpeg;',
            b'Content-transfer-encoding:  base64;',
            b'',
            b'test'
        ]), self._content_message.__bytes__())

    def test_message(self):
        message = Message(
            {
                'From': 'from mail',
                'To': 'to mail'
            },
            [self._content_message, self._content_message],
            'part'
        )
        result = b'\n'.join([
            b'\n'.join([b'From: from mail', b'To: to mail']),
            b'\n--part',
            b'--part\n'.join(self._content_message.__bytes__() + b'\n' for _ in range(2)),
            b'--part--\n'
        ])
        self.assertEqual(result, message.__bytes__())


if __name__ == '__main__':
    unittest.main()
