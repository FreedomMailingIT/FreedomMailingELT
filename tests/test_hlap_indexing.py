"""Test Heber Light & Power's indexing programs."""


import os
from shutil import copyfile
import app_modules.utilities as utils


DATA = utils.FILE_PATH


# Prepare for testing
DATA = utils.FILE_PATH
FNAME = '_hlap Aug 2023 cycle 2.pdf'
NEW_FILE = FNAME[1:]
copyfile(f'{DATA}/archive/{FNAME}', f'{DATA}{NEW_FILE}')


def test_hlap_idx(fname=NEW_FILE):
    """Test PDF indexing program."""
    command = f'py src/pdf_bill_indexing/hlap_pdf_idx.py -f "{fname}"'
    utils.logger.info('About to execute: %s', command)
    assert os.system(command) == 0


def test_hlap_idx_log():
    """Intergate log to see if indexing was successful."""
    lines = utils.get_last_log_segment()
    assert '250 bills indexed' in lines[-2]


def test_cleanup():
    """Remove results to keep test data directory clean."""
    if test_files := [
            x for x in os.listdir(DATA)
            if x.startswith('B47001')]:
        for test_file in test_files:
            os.remove(f'{DATA}{test_file}')


if __name__ == '__main__':
    test_hlap_idx()
