"""Test PyMuPDF which promises fast, cross platform PDF text extract."""


import os
from pathlib import Path
from shutil import copyfile
import pymupdf


# Prepare for testing
DATA = 'tests/data/'
FNAME = 'hlap Aug 2023 cycle 2'
copyfile(f'{DATA}archive/{FNAME}.pdf', FNAME)


def test_page_count():
    """Checks number of pages in PDF document."""
    #delete files that may interfere with testing
    for file in Path(DATA).iterdir():
        if file.match('B47001*.*'):
            os.remove(file)

    with pymupdf.open(FNAME) as pdf:
        num = 0
        for num, page in enumerate(pdf):
            text = page.get_text()
            lines = text.split('\n')
            lines[2].isalpha()
        assert num == 249


if __name__ == "__main__":
    test_page_count()
