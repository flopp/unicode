from www import app
import unicodedata
import re

def sanitize_name(s):
    non_alphanum = re.compile('([^a-z0-9])')
    return non_alphanum.sub(r'\\\1', s.strip().lower())

def to_utf8(i):
    try:
        c = chr(i).encode('utf8')
        return chr(i)
    except UnicodeEncodeError as e:
        return ''

class UInfo:
    def __init__(self):
        self._blocks = None
        self._chars = None
        self._subblocks = None
    
    def get_char(self, code):
        if code > len(self._chars):
            return None
        return self._chars[code]        
    
    def get_block(self, bid):
        if bid not in self._blocks:
            return None
        return self._blocks[bid]
    
    def get_char_info(self, code):
        if code is None or code >= len(self._chars) or self._chars[code] is None:
            return None
        return {
            "id": code,
            "char": to_utf8(code),
            "name": self._chars[code]["name"]
        }
    
    def get_random_char_infos(self, count):
        import random
        blocks = [0x0180, 0x0250, 0x1F600, 0x1F0A0, 0x1F680, 0x0370, 0x0900, 0x0700, 0x0400, 0x2200, 0x2190]
        candidates = []
        for b in blocks:
            block = self.get_block(b)
            if block is not None:
                for i in range(block["range_from"], block["range_to"] + 1):
                    candidates.append(i)
        chars = []
        for code in random.sample(candidates, count):
            c = self.get_char_info(code)
            if c is not None:
                chars.append(c)
        return chars
    
    def get_block_id(self, code):
        for block_id, block in self._blocks.items():
            if block["range_from"] <= code and code <= block["range_to"]:
                return block_id
        return None
        
    def get_block_info(self, bid):
        if bid not in self._blocks:
            return None
        return {
            "id": bid,
            "name": self._blocks[bid]["name"]
        }
    
    def get_block_infos(self):
        blocks = []
        last = -1
        for c in self._chars:
            if c is not None and c["block"] != last:
                last = c["block"]
                blocks.append(self.get_block_info(last))
        return blocks
    
    
    def get_subblock_id(self, code):
        for block_id, block in self._subblocks.items():
            if block["range_from"] <= code and code <= block["range_to"]:
                return block_id
        return None
    
    def get_subblock_info(self, bid):
        if bid not in self._subblocks:
            return None
        return {
            "id": bid,
            "name": self._subblocks[bid]["name"]
        }
        
    def load(self):
        import time
        start_time = time.time()
        self._load_blocks(app.root_path + '/data/Blocks.txt')
        self._load_nameslist(app.root_path + '/data/NamesList.txt')
        self._load_confusables(app.root_path + '/data/confusables.txt')
        self._load_casefolding(app.root_path + '/data/CaseFolding.txt')
        self._load_unihan(app.root_path + '/data/Unihan_Readings.txt')
        self._determine_prev_next_chars()
        self._determine_prev_next_blocks()
        elapsed_time = time.time() - start_time
        print('-- loading time: {}s'.format(elapsed_time))
    
    def _load_blocks(self, file_name):
        if self._blocks is not None:
            return
        self._blocks = {}
        with open(file_name, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or line == '':
                    continue
                m = re.split('\.\.|;\s+', line)
                if len(m) != 3:
                    continue
                range_from = int(m[0], 16)
                range_to = int(m[1], 16)
                name = m[2]
                self._blocks[range_from] = {
                    "id": range_from,
                    "range_from": range_from,
                    "range_to": range_to,
                    "name": name,
                    "prev": None,
                    "next": None
                }
        
    def _load_nameslist(self, file_name):
        if self._chars is not None:
            return
        if self._blocks is None:
            raise RuntimeError("cannot load nameslist. blocks not initialized, yet!")
        self._chars = [None] * (0x10FFFF + 1)
        for block_id, block in self._blocks.items():
            for code in range(block["range_from"], block["range_to"] + 1):
                self._chars[code] = {
                    "name": "<unassigned>",
                    "id": code,
                    "char": to_utf8(code),
                    "block": block_id,
                    "subblock": None,
                    "case": None,
                    "alternate": [],
                    "comments": [],
                    "related": [],
                    "confusables": [],
                    "prev": None,
                    "next": None
                }
        
        self._subblocks = {}
        with open(file_name, 'r', encoding='utf-8') as f:
            code = -1
            data = None
            block = None
            subblock = None
            blockend = None
            for line in f:
                if re.match('^[0-9A-F]{4,6}\t', line):
                    a = line.split('\t')
                    code = int(a[0], 16)
                    if code > 0x10FFFF:
                        raise ValueError("invalid code in line: {}".format(line))
                    self._chars[code]["name"] = a[1].strip()
                elif line.startswith('\t='):
                    self._chars[code]["alternate"].append(line[2:].strip())
                elif line.startswith('\t*'):
                    self._chars[code]["comments"].append(line[2:].strip())
                elif line.startswith('\tx'):
                    a = line[2:].strip()
                    m = a.split(' - ')
                    if len(m) == 2:
                        m = m[1].strip()
                        m = re.match('^([0-9A-F]{4,6})\)$', m)
                        if m:
                            code2 = int(m.group(1), 16)
                            if code2 > 0x10FFFF:
                                raise ValueError("invalid code in line: {}".format(line))
                            self._chars[code]["related"].append(code2)
                    elif re.match('^[0-9A-F]{4,6}$', a):
                        self._chars[code]["related"].append(int(a, 16))
                        code2 = int(a, 16)
                        if code2 > 0x10FFFF:
                            raise ValueError("invalid code in line: {}".format(line))
                        self._chars[code]["related"].append(code2)
                    else:
                        app.logger.info('strange related: {}'.format(line))
                elif line.startswith('@@\t'):
                    if subblock != None:
                        self._subblocks[subblock]["range_to"] = blockend
                    subblock = None
                    m = re.match('^@@\t([0-9A-F]{4,6})\t(.*)\t([0-9A-F]{4,6})$', line)
                    block = int(m.group(1), 16)
                    code = block-1
                    if block in self._blocks:
                        blockend = self._blocks[block]["range_to"]
                    else:
                        range_from = block
                        range_to = int(m.group(3), 16)
                        blockend = range_to
                        print('unknown block: {}-{}: {}'.format(m.group(1), m.group(3), m.group(2)))
                        self._blocks[block] = {
                            "id": range_from,
                            "range_from": range_from,
                            "range_to": range_to,
                            "name": m.group(2),
                            "prev": None,
                            "next": None
                        }
                        for code2 in range(range_from, range_to + 1):
                            self._chars[code2] = {
                                "name": "<unassigned>",
                                "id": code,
                                "char": to_utf8(code),
                                "block": block,
                                "subblock": None,
                                "case": None,
                                "alternate": [],
                                "comments": [],
                                "related": [],
                                "confusables": [],
                                "prev": None,
                                "next": None
                            }
                elif line.startswith('@\t\t'):
                    if subblock != None:
                        self._subblocks[subblock]["range_to"] = code
                    subblock = code + 1
                    self._subblocks[subblock] = {
                        "name": line[3:].strip(),
                        "range_from": subblock,
                        "range_to": None
                    }
            if subblock != None:
                self._subblocks[subblock]["range_to"] = blockend
            for block_id, block in self._subblocks.items():
                for code in range(block["range_from"], block["range_to"] + 1):
                    self._chars[code]["subblock"] = block_id
    
    def _load_confusables(self, file_name):
        if self._chars is None:
            raise RuntimeError("cannot load confusables. chars not initialized, yet!")
        with open(file_name, 'r', encoding='utf-8') as f:
            rx = re.compile('^\s*([0-9A-Fa-f]{4,6})\s*;\s*([0-9A-Fa-f]{4,6})\s*;\s*MA')
            sets = {}
            for line in f:
                line = line.strip()
                if line.startswith('#') or line == '':
                    continue
                m = rx.match(line)
                if m:
                    i1 = int(m.group(1), 16)
                    i2 = int(m.group(2), 16)
                    if (i1 > i2):
                        i1, i2 = i2, i1
                    if i1 not in sets:
                        sets[i1] = []
                        sets[i1].append(i1)
                    sets[i1].append(i2)
            for key, value in sets.items():
                for v in value:
                    confusables = []
                    for vv in value:
                        if vv != v:
                            confusables.append(vv)
                    self._chars[v]["confusables"] = confusables
    
    def _load_casefolding(self, file_name):
        if self._chars is None:
            raise RuntimeError("cannot load case folding. chars not initialized, yet!")
        with open(file_name, 'r', encoding='utf-8') as f:
            rx = re.compile('^\s*([0-9A-Fa-f]{4,6}); C; ([0-9A-Fa-f]{4,6}); #')
            sets = {}
            for line in f:
                line = line.strip()
                if line.startswith('#') or line == '':
                    continue
                m = rx.match(line)
                if m:
                    i1 = int(m.group(1), 16)
                    i2 = int(m.group(2), 16)
                    self._chars[i1]["case"] = i2 
                    self._chars[i2]["case"] = i1
    
    def _load_unihan(self, file_name):
        if self._chars is None:
            raise RuntimeError("cannot load unihan. chars not initialized, yet!")
        with open(file_name, 'r', encoding='utf-8') as f:
            rx = re.compile('^U\+([0-9A-Fa-f]{4,6})\tkDefinition\t(.*)$')
            for line in f:
                line = line.strip()
                m = rx.match(line)
                if m:
                    i = int(m.group(1), 16)
                    if (i >= len(self._chars)):
                        continue
                    self._chars[i]["name"] = m.group(2)
            
    def _determine_prev_next_chars(self):
        last = None
        for i, c in enumerate(self._chars):
            if c is None:
                continue
            
            if last is not None:
                self._chars[last]["next"] = i
                c["prev"] = last
            else:
                c["prev"] = None
            c["next"] = None
            last = i
    
    def _determine_prev_next_blocks(self):
        last = None
        for c in self._chars:
            if c is None:
                continue
            b = c["block"]
            if b != last:
                if last is not None:
                    self._blocks[last]["next"] = b
                self._blocks[b]["prev"] = last
                self._blocks[b]["next"] = None
                last = b
    
    def search_by_name(self, keyword, limit):
        keyword = keyword.upper()
        matches = []
        deprioritized_blocks = [0x2E80, 0x2F00, 0x31C0, 0x3300, 0x3400, 0x4E00, 0xF900, 0x20000, 0x2A700, 0x2B740, 0x2B820, 0x2F800]
        limit_reached = False
        for i, c in enumerate(self._chars):
            if c is None:
                continue
            if c["block"] in deprioritized_blocks:
                continue
            s = c["name"].upper()
            if keyword in s:
                if len(matches) >= limit:
                    limit_reached = True
                    break
                matches.append(self.get_char_info(i))
                continue
        for i, c in enumerate(self._chars):
            if c is None:
                continue
            if c["block"] not in deprioritized_blocks:
                continue
            s = c["name"].upper()
            if keyword in s:
                if len(matches) >= limit:
                    limit_reached = True
                    break
                matches.append(self.get_char_info(i))
                continue
        if limit_reached:
            return matches, "Search aborted after {} matches".format(limit)
        else:
            return matches, None
                    
