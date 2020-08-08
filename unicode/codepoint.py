import re
import typing


def code_link(code: str) -> str:
    code_upper = code.upper()
    return f'<a href="/c/{code_upper}">U+{code_upper}</a>'


def hex2id(hex_string: str) -> typing.Optional[int]:
    if not re.match(r"^[0-9A-Fa-f]{1,6}$", hex_string):
        return None
    return int(hex_string, 16)


class CodepointInfo:
    def __init__(self, codepoint: int, name: str):
        self.codepoint = codepoint
        self._name = name

    def codepoint_id(self) -> int:
        return self.codepoint

    def url(self) -> str:
        return f"/c/{self.codepoint_id():04X}"

    def u_plus(self) -> str:
        return f"U+{self.codepoint_id():04X}"

    def get_string(self) -> typing.Optional[str]:
        try:
            string = chr(self.codepoint)
        except ValueError:
            return None
        try:
            # try to encode the string as utf-8 (this fails e.g. for surrogates)
            string.encode("utf-8")
            return string
        except UnicodeEncodeError:
            return None

    def name(self) -> str:
        return self._name

    def set_name(self, name: str) -> None:
        self._name = name

    def title(self) -> str:
        return f"U+{self.codepoint_id():04X}: {self._name}"


class Codepoint:
    def __init__(self, codepoint: int, name: str, block_id: int = None):
        self.info = CodepointInfo(codepoint, name)
        self.block: typing.Optional[int] = block_id
        self.subblock: typing.Optional[int] = None
        self.case: typing.Optional[int] = None
        self.alternate: typing.List[str] = []
        self.comments: typing.List[str] = []
        self.related: typing.List[int] = []
        self.confusables: typing.List[int] = []
        self.combinables: typing.List[typing.List[int]] = []
        self.prev: typing.Optional[int] = None
        self.next: typing.Optional[int] = None

    def codepoint_id(self) -> int:
        return self.info.codepoint_id()

    def url(self) -> str:
        return self.info.url()

    def u_plus(self) -> str:
        return self.info.u_plus()

    def get_string(self) -> typing.Optional[str]:
        return self.info.get_string()

    def name(self) -> str:
        return self.info.name()

    def set_name(self, name: str) -> None:
        self.info.set_name(name)

    def title(self) -> str:
        return self.info.title()
