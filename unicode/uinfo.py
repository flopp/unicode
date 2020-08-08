import logging
import os
import random
import re
import time
import typing

from unicode.block import Block, BlockInfo, Subblock
from unicode.codepoint import Codepoint, CodepointInfo, code_link, hex2id


def all_in(needles: typing.List[str], haystack: str) -> bool:
    for needle in needles:
        if needle not in haystack:
            return False
    return True


class UInfo:
    def __init__(self) -> None:
        self._blocks: typing.Dict[int, Block] = {}
        self._codepoints: typing.List[typing.Optional[Codepoint]] = []
        self._subblocks: typing.Dict[int, Subblock] = {}

    def get_codepoint(self, code: typing.Optional[int]) -> typing.Optional[Codepoint]:
        if code is None or code < 0 or code >= len(self._codepoints):
            return None
        return self._codepoints[code]

    def get_block(self, block_id: typing.Optional[int]) -> typing.Optional[Block]:
        if block_id is None or block_id not in self._blocks:
            return None
        block = self._blocks[block_id]
        block.fetch_wikipedia()
        return block

    def get_codepoint_info(self, code: typing.Optional[int]) -> typing.Optional[CodepointInfo]:
        if code is None or code < 0 or code >= len(self._codepoints):
            return None
        codepoint = self._codepoints[code]
        return codepoint.info if codepoint else None

    def get_random_char_infos(self, count: int) -> typing.List[CodepointInfo]:
        blocks = [
            0x0180,
            0x0250,
            0x1F600,
            0x1F0A0,
            0x1F680,
            0x0370,
            0x0900,
            0x0700,
            0x0400,
            0x2200,
            0x2190,
        ]
        candidates = []
        for block_id in blocks:
            block = self.get_block(block_id)
            if block is not None:
                for i in block.codepoints_iter():
                    candidates.append(i)
        return list(filter(None, [self.get_codepoint_info(code) for code in random.sample(candidates, count)]))

    def get_block_id_by_name(self, name: str) -> typing.Optional[int]:
        re_non_alpha = re.compile("[^a-z]+")
        name = re_non_alpha.sub("", name.lower())

        for block_id, block in self._blocks.items():
            if re_non_alpha.sub("", block.name().lower()) == name:
                return block_id
        return None

    def get_block_info(self, block_id: typing.Optional[int]) -> typing.Optional[BlockInfo]:
        if block_id is None or block_id not in self._blocks:
            return None
        return self._blocks[block_id].info

    def get_block_infos(self) -> typing.List[BlockInfo]:
        infos = []
        last_block_id = -1
        for codepoint in self._codepoints:
            if not codepoint:
                continue
            if codepoint.block != last_block_id:
                assert codepoint.block is not None
                last_block_id = codepoint.block
                block_info = self.get_block_info(last_block_id)
                assert block_info
                infos.append(block_info)
        return infos

    def get_subblock(self, subblock_id: typing.Optional[int]) -> typing.Optional[Subblock]:
        if subblock_id is None or subblock_id not in self._subblocks:
            return None
        return self._subblocks[subblock_id]

    def load(self, cache_dir: str) -> None:
        start_time = time.time()
        self._load_blocks(os.path.join(cache_dir, "Blocks.txt"))
        self._load_nameslist(os.path.join(cache_dir, "NamesList.txt"))
        self._load_confusables(os.path.join(cache_dir, "confusables.txt"))
        self._load_casefolding(os.path.join(cache_dir, "CaseFolding.txt"))
        self._load_unihan(os.path.join(cache_dir, "Unihan_Readings.txt"))
        self._load_hangul(os.path.join(cache_dir, "hangul.txt"))
        self._load_wikipedia(os.path.join(cache_dir, "wikipedia.html"))
        self._determine_prev_next_codepoints()
        self._determine_prev_next_blocks()
        elapsed_time = time.time() - start_time
        logging.info("loading time: %ds", elapsed_time)

    def _load_blocks(self, file_name: str) -> None:
        if self._blocks:
            return
        self._blocks = {}
        with open(file_name, "r", encoding="utf-8") as blocks_file:
            for line in blocks_file:
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue
                match = re.split(r"\.\.|;\s+", line)
                if len(match) != 3:
                    continue
                range_from = hex2id(match[0])
                assert range_from is not None
                range_to = hex2id(match[1])
                assert range_to is not None
                name = match[2]
                self._blocks[range_from] = Block(range_from, range_to, name)

    def _load_nameslist(self, file_name: str) -> None:
        if self._codepoints:
            return
        self._initialize_codepoints()

        self._subblocks = {}
        with open(file_name, encoding="utf-8") as nameslist_file:
            codepoint_id: typing.Optional[int] = None
            codepoint = None
            subblock = None
            blockend = None

            re_x_name_hex = re.compile(r"^\tx \(.* - ([0-9A-F]{4,6})\)$")
            re_x_hex = re.compile(r"^\tx ([0-9A-F]{4,6})$")
            re_block_header = re.compile(r"^@@\t([0-9A-F]{4,6})\t(.*)\t([0-9A-F]{4,6})$")

            for line in nameslist_file:
                if re.match(r"^[0-9A-F]{4,6}\t", line):
                    hex_name = line.split("\t")
                    codepoint_id = hex2id(hex_name[0])
                    if codepoint_id is None or codepoint_id > 0x10FFFF:
                        raise ValueError(f"invalid code in line: {line}")
                    codepoint = self.get_codepoint(codepoint_id)
                    assert codepoint
                    codepoint.set_name(hex_name[1].strip())
                elif line.startswith("\t="):
                    assert codepoint
                    codepoint.alternate.append(line[2:].strip())
                elif line.startswith("\t*"):
                    assert codepoint
                    codepoint.comments.append(line[2:].strip())
                elif line.startswith("\tx"):
                    match = re_x_name_hex.match(line)
                    if match:
                        codepoint_id2 = hex2id(match.group(1))
                        if codepoint_id2 is None or codepoint_id2 > 0x10FFFF:
                            raise ValueError(f"invalid code in line: {line}")
                        assert codepoint
                        codepoint.related.append(codepoint_id2)
                        continue
                    match = re_x_hex.match(line)
                    if match:
                        codepoint_id2 = hex2id(match.group(1))
                        if codepoint_id2 is None or codepoint_id2 > 0x10FFFF:
                            raise ValueError(f"invalid code in line: {line}")
                        assert codepoint
                        codepoint.related.append(codepoint_id2)
                        continue
                    logging.info("strange related: %s", line)
                elif line.startswith("@@\t"):
                    if subblock is not None:
                        self._subblocks[subblock].set_to_codepoint(blockend)
                    subblock = None
                    match = re_block_header.match(line)
                    if match is None:
                        logging.info("bad block header: %s", line)
                        continue
                    block_id = hex2id(match.group(1))
                    assert block_id is not None
                    codepoint_id = block_id - 1
                    if block_id in self._blocks:
                        blockend = self._blocks[block_id].to_codepoint()
                    else:
                        range_from = block_id
                        range_to = hex2id(match.group(3))
                        assert range_to is not None
                        blockend = range_to
                        logging.info("unknown block: %s-%s: %s", match.group(1), match.group(3), match.group(2))
                        self._blocks[block_id] = Block(range_from, range_to, match.group(2))

                        for codepoint_id2 in range(range_from, range_to + 1):
                            self._codepoints[codepoint_id2] = Codepoint(
                                codepoint_id2, "<unassigned>", block_id=block_id
                            )
                elif line.startswith("@\t\t"):
                    assert codepoint_id is not None
                    if subblock is not None:
                        self._subblocks[subblock].set_to_codepoint(codepoint_id)
                    subblock = codepoint_id + 1
                    self._subblocks[subblock] = Subblock(subblock, None, line[3:].strip())
            if subblock is not None:
                self._subblocks[subblock].set_to_codepoint(blockend)
        self._assign_subblocks()
        self._detect_codes_in_comments()

    def _initialize_codepoints(self) -> None:
        if not self._blocks:
            raise RuntimeError("blocks not initialized, yet!")
        self._codepoints = [None] * (0x10FFFF + 1)
        for block_id, block in self._blocks.items():
            for codepoint_id in block.codepoints_iter():
                self._codepoints[codepoint_id] = Codepoint(codepoint_id, "<unassigned>", block_id=block_id)

    def _assign_subblocks(self) -> None:
        for subblock_id, subblock in self._subblocks.items():
            for codepoint_id in subblock.codepoints_iter():
                codepoint = self.get_codepoint(codepoint_id)
                assert codepoint
                codepoint.subblock = subblock_id

    def _detect_codes_in_comments(self) -> None:
        re_hex = re.compile(r"\b[0-9A-F]{4,6}\b")
        for codepoint in self._codepoints:
            if codepoint is None:
                continue
            new_comments = []
            for comment in codepoint.comments:
                replacements = []
                for hex_id in re_hex.findall(comment):
                    if self.get_codepoint_info(hex2id(hex_id.lower())) is not None:
                        replacements.append((hex_id, code_link(hex_id.lower())))
                for replacement in replacements:
                    comment = comment.replace(replacement[0], replacement[1])
                new_comments.append(comment)
            codepoint.comments = new_comments

    def _load_confusables(self, file_name: str) -> None:
        if not self._codepoints:
            raise RuntimeError("cannot load confusables. chars not initialized, yet!")
        with open(file_name, encoding="utf-8") as confusables_file:
            hx = r"([0-9A-Fa-f]{4,6})"
            re_confusable_pair = re.compile(r"^\s*" + hx + r"\s*;\s*" + hx + r"\s*;\s*MA")
            re_confusable_list2 = re.compile(r"^\s*" + hx + r"\s*;\s*" + hx + r"\s+" + hx + r"\s*;\s*MA")
            re_confusable_list3 = re.compile(r"^\s*" + hx + r"\s*;\s*" + hx + r"\s+" + hx + r"\s+" + hx + r"\s*;\s*MA")
            re_confusable_list4 = re.compile(
                r"^\s*" + hx + r"\s*;\s*" + hx + r"\s+" + hx + r"\s+" + hx + r"\s+" + hx + r"\s*;\s*MA"
            )
            sets: typing.Dict[int, typing.List[int]] = {}
            for line in confusables_file:
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue
                match = re_confusable_pair.match(line)
                if match:
                    codepoint_id1 = hex2id(match.group(1))
                    codepoint_id2 = hex2id(match.group(2))
                    assert codepoint_id1 is not None
                    assert codepoint_id2 is not None
                    if codepoint_id1 > codepoint_id2:
                        codepoint_id1, codepoint_id2 = codepoint_id2, codepoint_id1
                    if codepoint_id1 not in sets:
                        sets[codepoint_id1] = []
                        sets[codepoint_id1].append(codepoint_id1)
                    sets[codepoint_id1].append(codepoint_id2)
                    continue
                for re_list in [
                    re_confusable_list2,
                    re_confusable_list3,
                    re_confusable_list4,
                ]:
                    match = re_list.match(line)
                    if match:
                        codepoint = self.get_codepoint(hex2id(match.group(1)))
                        assert codepoint
                        codepoint.combinables.append(
                            list(filter(None, [hex2id(group) for group in match.groups()[1:]]))
                        )
                        break
            for _, confusable_set in sets.items():
                for codepoint_id1 in confusable_set:
                    confusables = []
                    for codepoint_id2 in confusable_set:
                        if codepoint_id2 != codepoint_id1:
                            confusables.append(codepoint_id2)
                    codepoint = self.get_codepoint(codepoint_id1)
                    assert codepoint
                    codepoint.confusables = confusables

    def _load_casefolding(self, file_name: str) -> None:
        if not self._codepoints:
            raise RuntimeError("cannot load case folding. chars not initialized, yet!")
        with open(file_name, encoding="utf-8") as casefolding_file:
            re_case = re.compile(r"^\s*([0-9A-Fa-f]{4,6}); C; ([0-9A-Fa-f]{4,6}); #")
            for line in casefolding_file:
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue
                match = re_case.match(line)
                if match:
                    codepoint_id1 = hex2id(match.group(1))
                    codepoint_id2 = hex2id(match.group(2))

                    codepoint1 = self.get_codepoint(codepoint_id1)
                    assert codepoint1
                    codepoint1.case = codepoint_id2

                    codepoint2 = self.get_codepoint(codepoint_id2)
                    assert codepoint2
                    codepoint2.case = codepoint_id1

    def _load_unihan(self, file_name: str) -> None:
        if not self._codepoints:
            raise RuntimeError("cannot load unihan. chars not initialized, yet!")
        with open(file_name, "r", encoding="utf-8") as unihan_file:
            re_definition = re.compile(r"^U\+([0-9A-Fa-f]{4,6})\tkDefinition\t(.*)$")
            for line in unihan_file:
                line = line.strip()
                match = re_definition.match(line)
                if match:
                    codepoint_id = hex2id(match.group(1))
                    assert codepoint_id is not None
                    if codepoint_id >= len(self._codepoints):
                        continue
                    codepoint = self.get_codepoint(codepoint_id)
                    assert codepoint is not None
                    codepoint.set_name(match.group(2))

    def _load_wikipedia(self, file_name: str) -> None:
        if not self._codepoints:
            raise RuntimeError("cannot load wikipedia. chars not initialized, yet!")
        with open(file_name, encoding="utf-8") as wikipedia_file:
            rx1 = re.compile(r'^<td data-sort-value=".*">U\+([0-9A-Fa-f]{4,6})\.\.U\+([0-9A-Fa-f]{4,6})</td>')
            rx2 = re.compile(r'^<td><a href="([^"]*)".*title="([^"]*)">')
            range_from = None
            for line in wikipedia_file:
                line = line.strip()
                if range_from is None:
                    match = rx1.match(line)
                    if match:
                        range_from = hex2id(match.group(1))
                else:
                    match = rx2.match(line)
                    if match:
                        url = match.group(1)
                        block = self.get_block(range_from)
                        if block:
                            block.wikipedia = f"https://en.wikipedia.org{url}"
                            block.wikipedia_summary = None
                    range_from = None

    def _load_hangul(self, file_name: str) -> None:
        if not self._codepoints:
            raise RuntimeError("cannot load hangul. chars not initialized, yet!")
        with open(file_name, "r", encoding="utf-8") as hangul_file:
            #   423	0xAE28	긨 (HANGUL SYLLABLE GYISS)
            re_definition = re.compile(r"^\s*[0-9]+\s*0x([0-9A-Fa-f]{4,6})\s+.*\((.+)\)\s*$")
            for line in hangul_file:
                line = line.strip()
                match = re_definition.match(line)
                if match is None:
                    continue
                codepoint_id = hex2id(match.group(1))
                assert codepoint_id is not None
                if codepoint_id >= len(self._codepoints):
                    continue
                name = match.group(2)
                codepoint = self.get_codepoint(codepoint_id)
                assert codepoint is not None
                if codepoint.name() == "<unassigned>":
                    codepoint.set_name(name)

    def _determine_prev_next_codepoints(self) -> None:
        last: typing.Optional[Codepoint] = None
        for i, codepoint in enumerate(self._codepoints):
            if codepoint is None:
                continue
            if last is not None:
                last.next = i
                codepoint.prev = last.codepoint_id()
            else:
                codepoint.prev = None
            codepoint.next = None
            last = codepoint

    def _determine_prev_next_blocks(self) -> None:
        last_block_id = None
        for codepoint in self._codepoints:
            if codepoint is None:
                continue
            block_id = codepoint.block
            assert block_id is not None
            if block_id != last_block_id:
                if last_block_id is not None:
                    self._blocks[last_block_id].next = block_id
                self._blocks[block_id].prev = last_block_id
                self._blocks[block_id].next = None
                last_block_id = block_id

    def search_by_name(
        self, keyword: str, limit: int
    ) -> typing.Tuple[typing.List[CodepointInfo], typing.Optional[str]]:
        matches, message = self.search_direct(keyword)
        if len(matches) > 0:
            return matches, message

        matches_prio: typing.List[typing.Tuple[CodepointInfo, int]] = []
        # CJK blocks are deprioritized, since their characters have very long descriptive names
        deprioritized_blocks = [
            0x2E80,
            0x2F00,
            0x31C0,
            0x3300,
            0x3400,
            0x4E00,
            0xF900,
            0x20000,
            0x2A700,
            0x2B740,
            0x2B820,
            0x2F800,
        ]
        limit_reached = False

        keywords: typing.List[str] = []
        for word in keyword.upper().split():
            word = word.strip()
            if word != "":
                keywords.append(word)

        # search in non-deprioritized blocks first
        for codepoint in self._codepoints:
            if codepoint is None or codepoint.block in deprioritized_blocks:
                continue
            if all_in(keywords, codepoint.name().upper()):
                if len(matches_prio) >= limit:
                    limit_reached = True
                    break
                matches_prio.append((codepoint.info, len(codepoint.name())))
                continue

        # search in deprioritized blocks
        for codepoint in self._codepoints:
            if codepoint is None or codepoint.block not in deprioritized_blocks:
                continue
            if all_in(keywords, codepoint.name().upper()):
                if len(matches_prio) >= limit:
                    limit_reached = True
                    break
                matches_prio.append((codepoint.info, 10 * len(codepoint.name())))
                continue

        return (
            list(map(lambda x: x[0], sorted(matches_prio, key=lambda x: x[1]))),
            f"Search aborted after {limit} matches" if limit_reached else None,
        )

    def search_direct(self, keyword: str) -> typing.Tuple[typing.List[CodepointInfo], typing.Optional[str]]:
        if len(keyword) == 1:
            result = self.get_codepoint_info(ord(keyword))
            assert result
            return [result], "Direct character match."
        keyword = keyword.strip()
        if not keyword:
            return [], "Empty query :("
        if len(keyword) == 1:
            result = self.get_codepoint_info(ord(keyword))
            assert result
            return [result], "Direct character match."
        match = re.match(r"^U?\+?([0-9A-F]{1,6})$", keyword, re.IGNORECASE)
        if match:
            codepoint_info = self.get_codepoint_info(hex2id(match.group(1)))
            if codepoint_info:
                return [codepoint_info], "Direct codepoint match."
        return [], "No direct match"
