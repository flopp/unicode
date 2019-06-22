from typing import List, Optional


def code_link(code: str) -> str:
    return '<a href="/c/{code}">U+{code}</a>'.format(code=code.upper())

def hex2id(hex_string: str) -> int:
    return int(hex_string, 16)

class CodepointInfo:
    def __init__(self, codepoint: int, name: str):
        self.codepoint = codepoint
        self._name = name

    def codepoint_id(self) -> int:
        return self.codepoint

    def url(self) -> str:
        return "/c/{:04X}".format(self.codepoint_id())

    def u_plus(self) -> str:
        return "U+{:04X}".format(self.codepoint_id())

    def get_string(self) -> Optional[str]:
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

    def set_name(self, name: str):
        self._name = name


class Codepoint:
    def __init__(self, codepoint: int, name: str, block_id: int = None):
        self.info = CodepointInfo(codepoint, name)
        self.block: Optional[int] = block_id
        self.subblock: Optional[int] = None
        self.case: Optional[int] = None
        self.alternate: List[str] = []
        self.comments: List[str] = []
        self.related: List[int] = []
        self.confusables: List[int] = []
        self.combinables: List[List[int]] = []
        self.prev: Optional[int] = None
        self.next: Optional[int] = None

    def codepoint_id(self) -> int:
        return self.info.codepoint_id()

    def url(self) -> str:
        return self.info.url()

    def u_plus(self) -> str:
        return self.info.u_plus()

    def get_string(self) -> Optional[str]:
        return self.info.get_string()

    def name(self) -> str:
        return self.info.name()

    def set_name(self, name: str):
        self.info.set_name(name)
