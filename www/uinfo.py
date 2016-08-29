from www import app
import unicodedata
import re


def init():
    _load_blocks()
    _load_nameslist()
    _load_confusables()


def get_name(codepoint):
    if codepoint < 0 or codepoint > 0x10FFFF:
        return None
    _load_nameslist()
    extended = _get_extended(codepoint)
    if extended:
        (e_code, e_name, e_alternate, e_comments, e_related) = extended
        return e_name
    else:
        try:
            return unicodedata.name(chr(codepoint))
        except ValueError as e:
            return None
    return None

def get_info(codepoint):
    if codepoint < 0 or codepoint > 0x10FFFF:
        return None
    
    _load_blocks()
    _load_nameslist()
    
    res = {}
    res['name'] = None
    res['block'] = _get_block(codepoint)
    res['subblock'] = _get_subblock(codepoint)
    res['alternate'] = []
    res['comments'] = []
    res['related'] = []
    
    extended = _get_extended(codepoint)
    if extended:
        (e_code, e_name, e_alternate, e_comments, e_related) = extended
        res['name'] = e_name
        res['alternate'] = e_alternate
        res['comments'] = e_comments
        res['related'] = e_related
    else:
        try:
            res['name'] = unicodedata.name(chr(codepoint))
        except ValueError as e:
            res['name'] = None
    
    return res    

_blocks = []
def _load_blocks():
    if len(_blocks) != 0:
        return
    fname = app.root_path + '/data/Blocks.txt'
    app.logger.info("loading: {}".format(fname))
    with open(fname, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or line == '':
                continue
            m = re.split('\.\.|;\s+', line)
            if len(m) != 3:
                continue
            b = (m[2].lower().replace(' ', '-'), m[2], int(m[0], 16), int(m[1], 16))
            _blocks.append(b)

def _get_block(codepoint):
    _load_blocks()
    _load_nameslist()
    for (block, name, range_from, range_to) in _blocks:
        if range_from <= codepoint and codepoint <= range_to:
            return {"block": block, "name": name, "from": range_from, "to": range_to}
    return {}

_extended = {}
_subblocks = []
def _load_nameslist():
    if len(_extended) > 0:
        return
    _load_blocks()
    for (_, _, range_from, range_to) in _blocks:
        for code in range(range_from, range_to + 1):
            _extended[code] = (code, '<unassigned>', [], [], [])
    fname = app.root_path + '/data/NamesList.txt'
    app.logger.info("loading: {}".format(fname))
    
    loaded_chars = 0
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            code = -1
            name = None
            alternate = []
            related = []
            comments = []
            subblock_from = None
            subblock_name = None
            subblock_comments = []
            for line in f:
                if re.match('^[0-9A-F]{4,5}\t', line):
                    loaded_chars += 1
                    if code >= 0:
                        _extended[code] = (code, name, alternate, comments, related)
                    a = line.split('\t')
                    code = int(a[0], 16)
                    name = a[1]
                    alternate = []
                    related = []
                    comments = []
                elif line.startswith('\t='):
                    alternate.append(line[2:].strip())
                elif line.startswith('\t*'):
                    comments.append(line[2:].strip())
                elif line.startswith('\tx'):
                    line = line[2:].strip()
                    m = line.split(' - ')
                    if len(m) == 2:
                        m = m[1].strip()
                        m = re.match('^([0-9A-F]{4,6})\)$', m)
                        if m:
                            related.append(int(m.group(1), 16))
                    elif re.match('^[0-9A-F]{4,6}$', line):
                        related.append(int(line, 16))
                    else:
                        app.logger.info('strange related: {}'.format(line))
                elif line.startswith('@\t\t'):
                    if subblock_from != None:
                        _subblocks.append((subblock_from, subblock_name))
                    subblock_from = code+1
                    subblock_name = line[3:].strip()
                    subblock_comments = []
                elif line.startswith('@+\t\t'):
                    subblock_comments.append(line[4:].strip())
                #else:
                #    print('strange line: {}'.format(line))
            if code >= 0:
                _extended[code] = (code, name, alternate, comments, related)
            if subblock_from != None:
                _subblocks.append((subblock_from, subblock_name))
    except IOError as e:
        app.logger.error("IOError: {}".format(e))
    except Exception as e:
        app.logger.error("Exception: {}".format(e))
    except:
        e = sys.exc_info()[0]
        app.logger.error("unknown exception: {}".format(e))
    app.logger.info("loaded chars: {}".format(loaded_chars))
    
    _update_related()

def _get_extended(codepoint):
    _load_nameslist()
    if codepoint in _extended:
        return _extended[codepoint]
    return None

def _get_subblock(codepoint):
    subblock_from = None
    subblock_name = None
    for (range_from, name) in _subblocks:
        if range_from > codepoint:
            return {"name": subblock_name, "from": subblock_from}
        subblock_name = name
        subblock_from = range_from
    if subblock_name:
        return {"name": subblock_name, "from": subblock_from}
    return None
    
    
def _update_related():
    app.logger.info('updating related chars')
    keys = _extended.keys()
    for code in keys:
        rel = _extended[code][4]
        for r in rel:
            if r not in _extended:
                app.logger.info('{}: bad related {}'.format("%0.4X" % code, "%0.4X" % r))
            (e_code, e_name, e_alternate, e_comments, e_related) = _extended[r]
            new = e_related
            new.append(code)
            new = sorted(list(set(new)))
            _extended[r] = (e_code, e_name, e_alternate, e_comments, new)

_confusables = {}
def _load_confusables():
    if len(_confusables) != 0:
        return
    fname = app.root_path + '/data/confusables.txt'
    app.logger.info("loading: {}".format(fname))
    with open(fname, 'r', encoding='utf-8') as f:
        sets = {}
        for line in f:
            line = line.strip()
            if line.startswith('#') or line == '':
                continue
            m = re.match('^\s*([0-9A-Fa-f]{4,6})\s*;\s*([0-9A-Fa-f]{4,6})\s*;\s*MA', line)
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
            _confusables[key] = value
            for v in value:
                values2 = []
                values2.append(key)
                for vv in value:
                    if vv != v:
                        values2.append(vv)
                _confusables[v] = values2

def get_confusables(codepoint):
    if codepoint in _confusables:
        return _confusables[codepoint]
    return []

def get_block(name):
    _load_blocks()
    _load_nameslist()
    
    name = name.lower()
    prev_block = None
    the_block = None
    next_block = None
    for (block, block_name, range_from, range_to) in _blocks:
        if name == block:
            the_block = {"block": block, "name": block_name, "range_from": range_from, "range_to": range_to}
        elif the_block is not None:
            next_block = {"block": block, "name": block_name}
            break
        else:
            prev_block = {"block": block, "name": block_name}
        
    if the_block is not None:
        the_block["prev"] = prev_block
        the_block["next"] = next_block
        return the_block
    return None


def get_blocks():
    _load_blocks()
    blocks = []
    for (block, block_name, range_from, range_to) in _blocks:
        blocks.append({"block": block, "name": block_name})
    return blocks
