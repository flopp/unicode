from www import app, cache
from flask import render_template, url_for, request, redirect
import copy
import re


@app.before_first_request
def init():
    app.uinfo.load()


@app.route('/')
def welcome():
    blocks = app.uinfo.get_block_infos()
    b1 = blocks[:int(len(blocks)/2)]
    b2 = blocks[int(len(blocks)/2):]
    data = {
        'chars': app.uinfo.get_random_char_infos(32),
        'blocks1': b1,
        'blocks2': b2
    }
    return render_template('welcome.html', data=data)


@app.route('/sitemap.txt')
@cache.memoize(120)
def sitemap():
    return render_template('sitemap.txt', blocks=app.uinfo.get_block_infos())


@app.route('/robots.txt')
@cache.memoize(120)
def robots():
    return render_template('robots.txt')


@app.route('/c/<code>')
@cache.memoize(120)
def show_code(code):
    if not re.match(r'^[0-9A-Fa-f]{1,6}$', code):
        return render_template('404.html')
    code = int(code.lower(), 16)
    info = app.uinfo.get_char(code)
    if info is None:
        return render_template('404.html')
    info = copy.deepcopy(info)

    related = []
    for r in info['related']:
        related.append(app.uinfo.get_char_info(r))
    info['related'] = related

    confusables = []
    for r in info['confusables']:
        confusables.append(app.uinfo.get_char_info(r))
    info['confusables'] = confusables

    info['case'] = app.uinfo.get_char_info(info['case'])
    info['prev'] = app.uinfo.get_char_info(info['prev'])
    info['next'] = app.uinfo.get_char_info(info['next'])
    info['block'] = app.uinfo.get_block_info(info['block'])
    info['subblock'] = app.uinfo.get_subblock_info(info['subblock'])

    return render_template('code.html', data=info)


@app.route('/code/<code>')
def show_code_old(code):
    return redirect(url_for('show_code', code=code))


@app.route('/b/<code>')
@cache.memoize(120)
def show_block(code):
    if not re.match(r'^[0-9A-Fa-f]{1,6}$', code):
        return render_template('404.html')

    code = int(code.lower(), 16)
    info = copy.deepcopy(app.uinfo.get_block(code))
    if not info:
        return render_template('404.html')

    chars = []
    for c in range(info['range_from'], info['range_to']+1):
        chars.append(app.uinfo.get_char_info(c))
    info['chars'] = chars

    info['prev'] = app.uinfo.get_block_info(info['prev'])
    info['next'] = app.uinfo.get_block_info(info['next'])

    return render_template('block.html', data=info)


@app.route('/block/<name>')
def show_block_old(name):
    i = app.uinfo.get_block_id_by_name(name)
    if i >= 0:
        return redirect(url_for('show_block', code='{:04X}'.format(i)))
    return render_template('404.html')


@app.route('/search', methods=['POST'])
def search():
    query = request.form['q']
    app.logger.info('get /search/{}'.format(query))
    matches, msg = app.uinfo.search_by_name(query, 100)
    return render_template('search_results.html',
                           query=query, msg=msg, matches=matches)


@app.route('/search', methods=['GET'])
def search_bad_method():
    return redirect('/')
