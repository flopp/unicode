import re
from typing import Dict, List, Optional, Tuple
from www import app
from www.block import Block, BlockInfo, Subblock
from www.codepoint import Codepoint, CodepointInfo, code_link, hex2id


def sanitize_name(name: str) -> str:
    non_alphanum = re.compile(r"([^a-z0-9])")
    return non_alphanum.sub(r"\\\1", name.strip().lower())


def all_in(needles: List[str], haystack: str) -> bool:
    for needle in needles:
        if needle not in haystack:
            return False
    return True


class UInfo:
    def __init__(self):
        self._blocks: Dict[int, Block] = {}
        self._chars: List[Optional[Codepoint]] = []
        self._subblocks: Dict[int, Subblock] = []

    def get_char(self, code: int) -> Optional[Codepoint]:
        if 0 <= code < len(self._chars):
            return self._chars[code]
        return None

    def get_block(self, block_id) -> Optional[Block]:
        if block_id not in self._blocks:
            return None
        block = self._blocks[block_id]
        block.fetch_wikipedia()
        return block

    def get_char_info(self, code: Optional[int]) -> Optional[CodepointInfo]:
        if code is None or code < 0 or code >= len(self._chars):
            return None
        codepoint = self._chars[code]
        if not codepoint:
            return None
        return codepoint.info

    def get_random_char_infos(self, count: int) -> List[CodepointInfo]:
        import random

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
        chars = []
        for code in random.sample(candidates, count):
            codepoint_info = self.get_char_info(code)
            if codepoint_info is not None:
                chars.append(codepoint_info)
        return chars

    def get_block_id(self, code_id: int) -> Optional[int]:
        for block_id, block in self._blocks.items():
            if block.contains(code_id):
                return block_id
        return None

    def get_block_id_by_name(self, name: str) -> Optional[int]:
        re_non_alpha = re.compile("[^a-z]+")
        name = re_non_alpha.sub("", name.lower())

        for block_id, block in self._blocks.items():
            if re_non_alpha.sub("", block.name().lower()) == name:
                return block_id
        return None

    def get_block_info(self, block_id: int) -> Optional[BlockInfo]:
        if block_id not in self._blocks:
            return None
        block = self._blocks[block_id]
        return block.info

    def get_block_infos(self) -> List[BlockInfo]:
        infos = []
        last_block_id = -1
        for codepoint in self._chars:
            if not codepoint:
                continue
            if codepoint.block != last_block_id:
                assert codepoint.block is not None
                last_block_id = codepoint.block
                block_info = self.get_block_info(last_block_id)
                assert block_info
                infos.append(block_info)
        return infos

    def get_subblock_id(self, code: int) -> Optional[int]:
        for subblock_id, subblock in self._subblocks.items():
            if subblock.contains(code):
                return subblock_id
        return None

    def get_subblock(self, subblock_id: int) -> Optional[Subblock]:
        if subblock_id not in self._subblocks:
            return None
        return self._subblocks[subblock_id]

    def load(self):
        import time

        start_time = time.time()
        self._load_blocks(app.root_path + "/data/Blocks.txt")
        self._load_nameslist(app.root_path + "/data/NamesList.txt")
        self._load_confusables(app.root_path + "/data/confusables.txt")
        self._load_casefolding(app.root_path + "/data/CaseFolding.txt")
        self._load_unihan(app.root_path + "/data/Unihan_Readings.txt")
        self._load_hangul(app.root_path + "/data/hangul.txt")
        self._load_wikipedia(app.root_path + "/data/wikipedia.html")
        self._determine_prev_next_chars()
        self._determine_prev_next_blocks()
        elapsed_time = time.time() - start_time
        print("-- loading time: {}s".format(elapsed_time))

    def _load_blocks(self, file_name: str):
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
                range_to = hex2id(match[1])
                name = match[2]
                self._blocks[range_from] = Block(range_from, range_to, name)

    def _load_nameslist(self, file_name: str):
        if self._chars:
            return
        if not self._blocks:
            raise RuntimeError("cannot load nameslist. blocks not initialized, yet!")
        self._chars = [None] * (0x10FFFF + 1)
        for block_id, block in self._blocks.items():
            for codepoint_id in block.codepoints_iter():
                self._chars[codepoint_id] = Codepoint(
                    codepoint_id, "<unassigned>", block_id=block_id
                )

        self._subblocks = {}
        with open(file_name, encoding="utf-8") as nameslist_file:
            codepoint_id = -1
            codepoint = None
            subblock = None
            blockend = None

            re_x_name_hex = re.compile(r"^\tx \(.* - ([0-9A-F]{4,6})\)$")
            re_x_hex = re.compile(r"^\tx ([0-9A-F]{4,6})$")
            re_block_header = re.compile(
                r"^@@\t([0-9A-F]{4,6})\t(.*)\t([0-9A-F]{4,6})$"
            )

            for line in nameslist_file:
                if re.match(r"^[0-9A-F]{4,6}\t", line):
                    hex_name = line.split("\t")
                    codepoint_id = hex2id(hex_name[0])
                    if codepoint_id > 0x10FFFF:
                        raise ValueError("invalid code in line: {}".format(line))
                    codepoint = self.get_char(codepoint_id)
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
                        if codepoint_id2 > 0x10FFFF:
                            raise ValueError("invalid code in line: {}".format(line))
                        assert codepoint
                        codepoint.related.append(codepoint_id2)
                        continue
                    match = re_x_hex.match(line)
                    if match:
                        codepoint_id2 = hex2id(match.group(1))
                        if codepoint_id2 > 0x10FFFF:
                            raise ValueError("invalid code in line: {}".format(line))
                        assert codepoint
                        codepoint.related.append(codepoint_id2)
                        continue
                    app.logger.info("strange related: {}".format(line))
                elif line.startswith("@@\t"):
                    if subblock is not None:
                        self._subblocks[subblock].set_to_codepoint(blockend)
                    subblock = None
                    match = re_block_header.match(line)
                    if match is None:
                        app.logger.info("bad block header: {}".format(line))
                        continue
                    block_id = hex2id(match.group(1))
                    codepoint_id = block_id - 1
                    if block_id in self._blocks:
                        blockend = self._blocks[block_id].to_codepoint()
                    else:
                        range_from = block_id
                        range_to = hex2id(match.group(3))
                        blockend = range_to
                        print(
                            "unknown block: {}-{}: {}".format(
                                match.group(1), match.group(3), match.group(2)
                            )
                        )
                        self._blocks[block_id] = Block(
                            range_from, range_to, match.group(2)
                        )

                        for codepoint_id2 in range(range_from, range_to + 1):
                            self._chars[codepoint_id2] = Codepoint(
                                codepoint_id2, "<unassigned>", block_id=block_id
                            )
                elif line.startswith("@\t\t"):
                    if subblock is not None:
                        self._subblocks[subblock].set_to_codepoint(codepoint_id)
                    subblock = codepoint_id + 1
                    self._subblocks[subblock] = Subblock(
                        subblock, None, line[3:].strip()
                    )
            if subblock is not None:
                self._subblocks[subblock].set_to_codepoint(blockend)
            for subblock_id, subblock in self._subblocks.items():
                for codepoint_id in subblock.codepoints_iter():
                    codepoint = self.get_char(codepoint_id)
                    assert codepoint
                    codepoint.subblock = subblock_id
        self._detect_codes_in_comments()

    def _detect_codes_in_comments(self):
        re_hex = re.compile(r"\b[0-9A-F]{4,6}\b")
        for codepoint in self._chars:
            if codepoint is None:
                continue
            new_comments = []
            for comment in codepoint.comments:
                replacements = []
                for hex_id in re_hex.findall(comment):
                    if self.get_char_info(hex2id(hex_id.lower())) is not None:
                        replacements.append((hex_id, code_link(hex_id.lower())))
                for replacement in replacements:
                    comment = comment.replace(replacement[0], replacement[1])
                new_comments.append(comment)
            codepoint.comments = new_comments

    def _load_confusables(self, file_name: str):
        if not self._chars:
            raise RuntimeError("cannot load confusables. chars not initialized, yet!")
        with open(file_name, encoding="utf-8") as confusables_file:
            re_confusable_pair = re.compile(
                r"^\s*([0-9A-Fa-f]{4,6})\s*;\s*([0-9A-Fa-f]{4,6})\s*;\s*MA"
            )
            re_confusable_list2 = re.compile(
                r"^\s*([0-9A-Fa-f]{4,6})\s*;\s*([0-9A-Fa-f]{4,6})\s+([0-9A-Fa-f]{4,6})\s*;\s*MA"
            )
            re_confusable_list3 = re.compile(
                r"^\s*([0-9A-Fa-f]{4,6})\s*;\s*([0-9A-Fa-f]{4,6})\s+([0-9A-Fa-f]{4,6})\s+([0-9A-Fa-f]{4,6})\s*;\s*MA"
            )
            re_confusable_list4 = re.compile(
                r"^\s*([0-9A-Fa-f]{4,6})\s*;\s*([0-9A-Fa-f]{4,6})\s+([0-9A-Fa-f]{4,6})\s+([0-9A-Fa-f]{4,6})\s+([0-9A-Fa-f]{4,6})\s*;\s*MA"
            )
            sets: Dict[int, List[int]] = {}
            for line in confusables_file:
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue
                match = re_confusable_pair.match(line)
                if match:
                    codepoint_id1 = hex2id(match.group(1))
                    codepoint_id2 = hex2id(match.group(2))
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
                        codepoint = self.get_char(hex2id(match.group(1)))
                        assert codepoint
                        codepoint_ids = [
                            hex2id(group) for group in (match.groups()[1:])
                        ]
                        codepoint.combinables.append(codepoint_ids)
                        break
            for _, confusable_set in sets.items():
                for codepoint_id1 in confusable_set:
                    confusables = []
                    for codepoint_id2 in confusable_set:
                        if codepoint_id2 != codepoint_id1:
                            confusables.append(codepoint_id2)
                    codepoint = self.get_char(codepoint_id1)
                    assert codepoint
                    codepoint.confusables = confusables

    def _load_casefolding(self, file_name: str):
        if not self._chars:
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

                    codepoint1 = self.get_char(codepoint_id1)
                    assert codepoint1
                    codepoint1.case = codepoint_id2

                    codepoint2 = self.get_char(codepoint_id2)
                    assert codepoint2
                    codepoint2.case = codepoint_id1

    def _load_unihan(self, file_name: str):
        if not self._chars:
            raise RuntimeError("cannot load unihan. chars not initialized, yet!")
        with open(file_name, "r", encoding="utf-8") as unihan_file:
            re_definition = re.compile(r"^U\+([0-9A-Fa-f]{4,6})\tkDefinition\t(.*)$")
            for line in unihan_file:
                line = line.strip()
                match = re_definition.match(line)
                if match:
                    codepoint_id = hex2id(match.group(1))
                    if codepoint_id >= len(self._chars):
                        continue
                    codepoint = self.get_char(codepoint_id)
                    assert codepoint
                    codepoint.set_name(match.group(2))

    def _load_wikipedia(self, file_name: str):
        if not self._chars:
            raise RuntimeError("cannot load wikipedia. chars not initialized, yet!")
        with open(file_name, encoding="utf-8") as wikipedia_file:
            rx1 = re.compile(
                r'^<td data-sort-value=".*">U\+([0-9A-Fa-f]{4,6})\.\.U\+([0-9A-Fa-f]{4,6})</td>'
            )
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
                            block.wikipedia = "https://en.wikipedia.org{}".format(url)
                            block.wikipedia_summary = None
                    range_from = None

    def _load_hangul(self, file_name: str):
        if not self._chars:
            raise RuntimeError("cannot load hangul. chars not initialized, yet!")
        with open(file_name, "r", encoding="utf-8") as hangul_file:
            #   423	0xAE28	긨 (HANGUL SYLLABLE GYISS)
            re_definition = re.compile(
                r"^\s*[0-9]+\s*0x([0-9A-Fa-f]{4,6})\s+.*\((.+)\)\s*$"
            )
            for line in hangul_file:
                line = line.strip()
                match = re_definition.match(line)
                if match is None:
                    continue
                codepoint_id = hex2id(match.group(1))
                if codepoint_id >= len(self._chars):
                    continue
                name = match.group(2)
                codepoint = self.get_char(codepoint_id)
                assert codepoint
                if codepoint.name() == "<unassigned>":
                    codepoint.set_name(name)

    def _determine_prev_next_chars(self):
        last = None
        for i, codepoint in enumerate(self._chars):
            if codepoint is None:
                continue
            if last is not None:
                self._chars[last].next = i
                codepoint.prev = last
            else:
                codepoint.prev = None
            codepoint.next = None
            last = i

    def _determine_prev_next_blocks(self):
        last_block_id = None
        for codepoint in self._chars:
            if codepoint is None:
                continue
            block_id = codepoint.block
            if block_id != last_block_id:
                if last_block_id is not None:
                    self._blocks[last_block_id].next = block_id
                self._blocks[block_id].prev = last_block_id
                self._blocks[block_id].next = None
                last_block_id = block_id

    def search_by_name(
        self, keyword: str, limit: int
    ) -> Tuple[List[CodepointInfo], Optional[str]]:
        # check keyword 'as is' (single char)
        if len(keyword) == 1:
            result = self.get_char_info(ord(keyword))
            assert result
            return [result], "Direct character match."
        keyword = keyword.strip()
        if not keyword:
            return [], "Empty query :("
        if len(keyword) == 1:
            result = self.get_char_info(ord(keyword))
            assert result
            return [result], "Direct character match."
        keywords = []
        for word in keyword.upper().split():
            word = word.strip()
            if word != "":
                keywords.append(word)
        if len(keywords) == 1:
            match = re.match(r"^U?\+?([0-9A-F]{1,6})$", keywords[0], re.IGNORECASE)
            if match:
                codepoint_info = self.get_char_info(hex2id(match.group(1)))
                if codepoint_info:
                    return [codepoint_info], "Direct codepoint match."

        matches_prio: List[Tuple[CodepointInfo, int]] = []
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
        # search in non-deprioritized blocks first
        for codepoint in self._chars:
            if codepoint is None:
                continue
            if codepoint.block in deprioritized_blocks:
                continue
            if all_in(keywords, codepoint.name().upper()):
                if len(matches_prio) >= limit:
                    limit_reached = True
                    break
                matches_prio.append((codepoint.info, len(codepoint.name())))
                continue
        # search in deprioritized blocks
        for codepoint in self._chars:
            if codepoint is None:
                continue
            if codepoint.block not in deprioritized_blocks:
                continue
            if all_in(keywords, codepoint.name().upper()):
                if len(matches_prio) >= limit:
                    limit_reached = True
                    break
                matches_prio.append((codepoint.info, 10 * len(codepoint.name())))
                continue
        matches = list(map(lambda x: x[0], sorted(matches_prio, key=lambda x: x[1])))
        if limit_reached:
            return matches, "Search aborted after {} matches".format(limit)
        return matches, None
