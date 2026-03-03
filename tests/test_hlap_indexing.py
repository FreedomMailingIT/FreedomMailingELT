"""Test Heber Light & Power's indexing programs."""


from pathlib import Path
import subprocess
from shutil import copyfile
import app_modules.utilities as utils


# Prepare for testing
TEST_DATA = Path(utils.FILE_PATH)
FNAME = 'hlap Aug 2023 cycle 2.pdf'
copyfile(TEST_DATA / 'archive' / FNAME, TEST_DATA / FNAME)
utils.initialize_log_file(path=utils.FILE_PATH)  # FILE_PATH needed because utilities uses it


def test_hlap_idx(fname=FNAME):
    """Test PDF indexing program."""
    command = ['py', 'src/pdf_bill_indexing/hlap_pdf_idx.py', '-f', fname]
    subprocess.run(command, check=True)


def test_hlap_idx_log():
    """Intergate log to see if indexing was successful."""
    lines = utils.get_last_log_segment()
    assert '250 bills indexed' in lines[-2]


def test_cleanup():
    """Archive results to keep test data directory clean."""
    old_files = [x.name for x in TEST_DATA.iterdir() if x.name.startswith('B47001')]
    if old_files:
        utils.logger.debug('*' * 80)
        utils.logger.debug('Files to be archived: %s', old_files)
        utils.archive_files(
            files=old_files,
            path_to_archive=utils.FILE_PATH,
            path_to_files=str(TEST_DATA) + '/',
            arch_name='hlap_files'
        )


if __name__ == '__main__':
    test_hlap_idx()
