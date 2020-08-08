#!/usr/bin/env python3

import logging

import click

from unicode.app import flask_app, configure


@click.command()
@click.option("-c", "--config", default="config.py", type=click.Path(exists=True))
@click.option("-r", "--reset", is_flag=True)
@click.option("-v", "--verbose", is_flag=True)
def main(config: str, reset: bool, verbose: bool,) -> None:
    if verbose:
        logging.basicConfig(level=logging.INFO)
    configure(config, reset)
    flask_app.run()


if __name__ == "__main__":
    main()
