#!/usr/bin/env python
import sys
from functools import partial
from pathlib import Path

import click
from streamlit.web import cli as stcli

from anl import DEFAULT_TOURNAMENT_PATH

click.option = partial(click.option, show_default=True)


@click.group()
def main():
    pass


@main.command(help="Opens the visualizer")
@click.option(
    "-f",
    "--folder",
    type=click.Path(file_okay=False, dir_okay=True),
    default=None,
    help=f"Folder containing logs of a tournament to open. If not given, All runs at {DEFAULT_TOURNAMENT_PATH} will be used",
)
def show(folder: Path):
    # folder = Path(folder) if folder is not None else None
    if folder:
        sys.argv = [
            "streamlit",
            "run",
            str(Path(__file__).parent / "app.py"),
            str(folder),
        ]
    else:
        sys.argv = ["streamlit", "run", str(Path(__file__).parent / "app.py")]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
