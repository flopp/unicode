import logging
import re
import typing

import wikipedia  # type: ignore

from unicode.codepoint import code_link


class BlockInfo:
    def __init__(self, codepoint_from: int, name: str):
        self.codepoint_from = codepoint_from
        self._name = name

    def block_id(self) -> int:
        return self.codepoint_from

    def name(self) -> str:
        return self._name

    def url(self) -> str:
        return f"/b/{self.block_id():04X}"

    def u_plus(self) -> str:
        return f"U+{self.block_id():04X}"


class Block:
    def __init__(self, codepoint_from: int, codepoint_to: int, name: str) -> None:
        self.info = BlockInfo(codepoint_from, name)
        self.codepoint_to = codepoint_to
        self.wikipedia: typing.Optional[str] = None
        self.wikipedia_summary: typing.Optional[str] = None
        self.prev: typing.Optional[int] = None
        self.next: typing.Optional[int] = None

    def block_id(self) -> int:
        return self.info.block_id()

    def name(self) -> str:
        return self.info.name()

    def url(self) -> str:
        return self.info.url()

    def u_plus(self) -> str:
        return self.info.u_plus()

    def from_codepoint(self) -> int:
        return self.info.codepoint_from

    def to_codepoint(self) -> int:
        return self.codepoint_to

    def contains(self, codepoint: int) -> bool:
        return self.info.codepoint_from <= codepoint <= self.codepoint_to

    def codepoints_iter(self) -> typing.Iterable[int]:
        return range(self.info.codepoint_from, self.codepoint_to + 1)

    def fetch_wikipedia(self) -> None:
        if self.wikipedia_summary is not None:
            return
        if self.wikipedia is None:
            self.wikipedia_summary = ""
            return
        try:
            topic = self.wikipedia.split("/")[-1].replace("_", " ")
            self.wikipedia_summary = Block._format_wikipedia(wikipedia.summary(topic, sentences=3))
        except Exception:  # pylint: disable=broad-except
            logging.warning("Failed to fetch wikipedia infos for topic %s", topic)
            self.wikipedia_summary = ""

    @staticmethod
    def _format_wikipedia(wikipedia_text: str) -> str:
        lines = []
        last_empty = True

        re_h2 = re.compile(r"^== (.*) ==$")
        re_h3 = re.compile(r"^=== (.*) ===$")

        for line in wikipedia_text.split("\n"):
            line = line.strip()
            if not line:
                if not last_empty:
                    lines.append("")
                last_empty = True
                continue

            last_empty = False
            match = re_h2.match(line)
            if match:
                lines.append(f"<b>{match.group(1)}</b>")
                continue
            match = re_h3.match(line)
            if match:
                lines.append(f"<b>{match.group(1)}</b>")
                continue

            lines.append(Block._replace_codepoints_with_links(line))
        return "<br />\n".join(lines)

    @staticmethod
    def _replace_codepoints_with_links(s: str) -> str:
        re_single_code = re.compile(r"U\+([0-9A-Fa-f]{4,6})\b")
        re_code_range = re.compile(r"\b([0-9A-Fa-f]{4,6})[-–—]([0-9A-Fa-f]{4,6})\b")

        replacements = []
        for match in re_single_code.finditer(s):
            original = match.group(0)
            code = match.group(1).upper()
            replacements.append((original, code_link(code)))
        for match in re_code_range.finditer(s):
            from_original = match.group(1)
            to_original = match.group(2)
            from_code = from_original.upper()
            to_code = from_original.upper()
            replacements.append((from_original, code_link(from_code)))
            replacements.append((to_original, code_link(to_code)))
        for replacement in replacements:
            s = s.replace(replacement[0], replacement[1])

        return s


class Subblock:
    def __init__(self, codepoint_from: int, codepoint_to: typing.Optional[int], name: str) -> None:
        self.codepoint_from = codepoint_from
        self.codepoint_to = codepoint_to
        self._name = name

    def block_id(self) -> int:
        return self.codepoint_from

    def name(self) -> str:
        return self._name

    def from_codepoint(self) -> int:
        return self.codepoint_from

    def to_codepoint(self) -> typing.Optional[int]:
        return self.codepoint_to

    def set_to_codepoint(self, codepoint: typing.Optional[int]) -> None:
        self.codepoint_to = codepoint

    def contains(self, codepoint: int) -> bool:
        assert self.codepoint_to is not None
        return self.codepoint_from <= codepoint <= self.codepoint_to

    def codepoints_iter(self) -> typing.Iterable[int]:
        assert self.codepoint_to is not None
        return range(self.codepoint_from, self.codepoint_to + 1)
