import logging
import os
import typing

import appdirs  # type: ignore
from flask import Flask, render_template, url_for, request, redirect
from flask_caching import Cache  # type: ignore
from werkzeug.wrappers import Response

from unicode.codepoint import hex2id
from unicode.download import fetch_data_files
from unicode.uinfo import UInfo


flask_app = Flask(__name__)
cache = Cache(flask_app, config={"CACHE_TYPE": "simple"})
unicode_info = UInfo()

StrIntT = typing.Tuple[str, int]


def configure(config_file_name: str, reset_cache: bool) -> None:
    flask_app.config.from_pyfile(os.path.abspath(config_file_name))

    if "CACHE_DIR" in flask_app.config:
        cache_dir = flask_app.config["CACHE_DIR"]
    else:
        cache_dir = os.path.join(appdirs.user_cache_dir("flopp.unicode"))
    fetch_data_files(cache_dir, reset_cache)
    unicode_info.load(cache_dir)


@flask_app.errorhandler(404)
def page_not_found(error: str) -> StrIntT:
    logging.error("Pag %s not found: %s", request.path, error)
    return render_template("404.html"), 404


@flask_app.errorhandler(500)
def internal_server_error(error: str) -> StrIntT:
    logging.error("Server Error: %s", error)
    return render_template("500.html"), 500


# @app.errorhandler(Exception)
def unhandled_exception(error: str) -> StrIntT:
    logging.error("Unhandled Exception: %s", error)
    return render_template("500.html"), 500


@flask_app.route("/")
def welcome() -> StrIntT:
    blocks = unicode_info.get_block_infos()
    half = int(len(blocks) / 2)
    data = {
        "chars": unicode_info.get_random_char_infos(32),
        "blocks1": blocks[:half],
        "blocks2": blocks[half:],
    }
    return render_template("welcome.html", data=data), 200


@flask_app.route("/sitemap.txt")
@cache.memoize(120)
def sitemap() -> StrIntT:
    return render_template("sitemap.txt", blocks=unicode_info.get_block_infos()), 200


@flask_app.route("/robots.txt")
@cache.memoize(120)
def robots() -> StrIntT:
    return render_template("robots.txt"), 200


@flask_app.route("/c/<char_code>")
@cache.memoize(120)
def show_code(char_code: str) -> StrIntT:
    codepoint = unicode_info.get_codepoint(hex2id(char_code.lower()))
    if codepoint is None:
        return render_template("404.html"), 404

    combinables = []
    for combinable in codepoint.combinables:
        combinables.append([unicode_info.get_codepoint_info(codepoint_id) for codepoint_id in combinable])

    info = {
        "codepoint": codepoint,
        "related": list(
            filter(None, [unicode_info.get_codepoint_info(code_related) for code_related in codepoint.related])
        ),
        "confusables": list(
            filter(
                None, [unicode_info.get_codepoint_info(code_confusable) for code_confusable in codepoint.confusables]
            )
        ),
        "combinables": combinables,
        "case": unicode_info.get_codepoint_info(codepoint.case),
        "prev": unicode_info.get_codepoint_info(codepoint.prev),
        "next": unicode_info.get_codepoint_info(codepoint.next),
        "block": unicode_info.get_block_info(codepoint.block),
        "subblock": unicode_info.get_subblock(codepoint.subblock),
    }

    return render_template("code.html", data=info), 200


@flask_app.route("/code/<code>")
def show_code_old(code: str) -> Response:
    return redirect(url_for("show_code", char_code=code))


@flask_app.route("/b/<block_code>")
@cache.memoize(120)
def show_block(block_code: str) -> StrIntT:
    block = unicode_info.get_block(hex2id(block_code.lower()))
    if not block:
        return render_template("404.html"), 404

    info = {
        "block": block,
        "chars": list(
            filter(None, [unicode_info.get_codepoint_info(codepoint) for codepoint in block.codepoints_iter()])
        ),
        "prev": unicode_info.get_block_info(block.prev),
        "next": unicode_info.get_block_info(block.next),
    }

    return render_template("block.html", data=info), 200


@flask_app.route("/block/<name>")
def show_block_old(name: str) -> typing.Union[StrIntT, Response]:
    block_id = unicode_info.get_block_id_by_name(name)
    if block_id is not None:
        return redirect(url_for("show_block", code=f"{block_id:04X}"))
    return render_template("404.html"), 404


@flask_app.route("/search", methods=["POST"])
def search() -> StrIntT:
    query = request.form["q"]
    logging.info("get /search/%s", query)
    matches, msg = unicode_info.search_by_name(query, 100)
    return render_template("search_results.html", query=query, msg=msg, matches=matches), 200


@flask_app.route("/search", methods=["GET"])
def search_bad_method() -> Response:
    return redirect("/")
