#!/usr/bin/env python3
import os
import re
import setuptools


def _read_version(rel_path):
    abs_path = os.path.join(os.path.dirname(__file__), rel_path)
    with open(abs_path) as f:
        content = f.read()
    r = r"^__version__ = ['\"]([^'\"]*)['\"]$"
    m = re.search(r, content, re.M)
    if not m:
        raise RuntimeError(f"Unable to find version string in {rel_path}.")
    return m.group(1)


def _read_descr(rel_path):
    abs_path = os.path.join(os.path.dirname(__file__), rel_path)
    with open(abs_path) as f:
        return f.read()


def _read_reqs(relpath):
    abspath = os.path.join(os.path.dirname(__file__), relpath)
    with open(abspath) as f:
        return [
            s.strip()
            for s in f.readlines()
            if s.strip() and not s.strip().startswith("#")
        ]


setuptools.setup(
    name="airports",
    version=_read_version("unicode/version.py"),
    description='A web-app showing satellite images of random airports',
    long_description=_read_descr("README.md"),
    install_requires=_read_reqs("requirements.txt"),
    extras_require={"dev": _read_reqs("requirements-dev.txt"),},
    entry_points={"console_scripts": ["unicode = unicode.cli:main",],},
    packages=setuptools.find_packages(),
    include_package_data=True,
)
