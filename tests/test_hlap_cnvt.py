"""Test Heber Light & Power's convert of their RAW text to FM TSV."""


import os
from shutil import copyfile
import app_modules.utilities as utils


# Prepare for testing
DATA = utils.FILE_PATH
FNAME = '_hlap Jan 25 CYCLE 2.TXT'
NEW_FILE = FNAME[1:]
copyfile(f'{DATA}/archive/{FNAME}', f'{DATA}{NEW_FILE}')
utils.initialize_log_file(path=utils.FILE_PATH)  # FILE_PATH needed because utilities uses it


def test_hlap_cnvt(fname=NEW_FILE):
    """Test conversion program."""
    command = f'py src/transforms/hlap_cnvrt.py -f "{fname}"'
    assert os.system(command) == 0


def test_hlap_cnvt_log():
    """Intergate log to see if conversion was successful."""
    lines = utils.get_last_log_segment()
    assert 'Printed: 250' in lines[-2]


def test_cleanup():
    """Remove results to keep test data directory clean."""
    if test_files := [
            x for x in os.listdir(DATA)
            if x.startswith('fxd') and not x.endswith('.zip')]:
        for test_file in test_files:
            os.remove(f'{DATA}{test_file}')
    os.remove(f'{DATA}{NEW_FILE}')


if __name__ == '__main__':
    test_hlap_cnvt()
