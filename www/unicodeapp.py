from www import app
from www import uinfo
from flask import render_template
import re
import unicodedata


def to_utf8(i):
    try:
        c = chr(i).encode('utf8')
        return chr(i)
    except UnicodeEncodeError as e:
        return ''


@app.before_first_request
def init():
    uinfo.init()


@app.route('/')
def welcome():
    chars = []
    for i in range(0, 300, 1):
        c = 33 + i * 23
        chars.append(dict(
            code=c,
            char=to_utf8(c),
            name=uinfo.get_name(c)
        ))
    return render_template("welcome.html", chars=chars, blocks=uinfo.get_blocks())


@app.route('/code/<codepoint>')
def show_codepoint(codepoint):
    app.logger.info('get /code/{}'.format(codepoint))
    if not re.match('^[0-9A-Fa-f]{1,6}$', codepoint):
        return render_template("404.html")
    
    codepoint = int(codepoint.lower(), 16)
    info = uinfo.get_info(codepoint)
    related = []
    for r in info['related']:
        related.append(dict(
            code=r,
            char=to_utf8(r),
            name=uinfo.get_name(r)
        ))
    
    prev_code = None
    if codepoint > 0:
        prev_code = codepoint - 1
    next_code = None
    if codepoint < 0x10FFFF:
        next_code = codepoint + 1
    return render_template("code.html", 
        code=codepoint,
        char=to_utf8(codepoint),
        name=info['name'],
        block=info['block'],
        subblock=info['subblock'],
        alternate=info['alternate'],
        comments=info['comments'],
        related=related,
        prev_code=prev_code,
        next_code=next_code)
    
    
@app.route('/block/<blockname>')
def show_block(blockname):
    app.logger.info('get /block/{}'.format(blockname))
    block = uinfo.get_block(blockname)
    if block:
        chars = []
        for c in range(block["range_from"], block["range_to"]+1):
            chars.append(dict(
                code=c,
                char=to_utf8(c),
                name=uinfo.get_name(c)
            ))
        return render_template("block.html", block=block, chars=chars)
    return render_template("404.html")
