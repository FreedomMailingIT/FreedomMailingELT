"""Testing of sort program using multiple source files.

Need to:
1 - set environment variable FM_FILES=tests (run FMT.bat) to run tests.
2 - enter environment with command 'wo fm'
3 - start tests with 'py -m pytest test_sort_multiples.py'
"""

from pathlib import Path
import subprocess
import pytest
import app_modules.utilities as utils
import app_modules.file_locations as loctns


# Prepare for testing
TEST_DATA = Path(loctns.TEST_DATA) / 'multiples_data'
utils.initialize_log_file(path=utils.FILE_PATH)

sort_tests = [
    ('lehi dupes.csv', 'is probably OK', 2),
    ('baca dupes.txt', 'is probably OK', 2),
    ('ivins dupes ascii.txt', 'is probably OK', 2),
    ('ivins dupes size.txt', 'File size diff is more than 1 percent', 6),
    ('lehi dupes.txt', 'is probably OK', 2),
    ('parowan dupes.txt', 'is probably OK', 2),
    ('jerome dupes.txt', 'Due date is in column 4 (E) and has value of 12/15/2020 12:0', 6),
    ('clearfield dupes.txt', 'First banner appears on line 5', 3),
    ('lehi dupes blanks.txt', 'but input file had 61 blank lines', 6),
    ('nodate test.csv', 'Due date is in column -1 (Unknown) and has value of None', 7),
]

missing_tests = [
    ('burley dupes missing.txt', 'not found', 2),
    ('not_registered.csv', 'to register city', 2),
]


@pytest.mark.parametrize('fname, msg, line', sort_tests)
def test_sorting(fname, msg, line, subtests):
    """Test sorts."""
    with subtests.test(fname):
        subprocess.run(
            ['py', 'src/dupes_sorting/sort_multiples.py', '-f', str(TEST_DATA / fname)],
            check=False
        )
    _, seg_lines = utils.trim_log_seg(utils.get_last_log_segment())
    with subtests.test():
        assert msg in seg_lines[-line]


@pytest.mark.parametrize('fname, msg, line', missing_tests)
def test_missing_data(fname, msg, line, subtests):
    """Test sorts with missing data."""
    with subtests.test(fname):
        subprocess.run(
            ['py', 'src/dupes_sorting/sort_multiples.py', '-f', str(TEST_DATA / fname)],
            check=False)

    _, seg_lines = utils.trim_log_seg(utils.get_last_log_segment())
    with subtests.test():
        assert msg in seg_lines[-line]


def test_cleanup():
    """Archive results to keep test data directory clean."""
    old_files = [
        x.name for x in TEST_DATA.iterdir()
        if x.name.startswith('sorted') and not x.name.endswith('.zip')
    ]
    if old_files:
        utils.logger.debug('*' * 80)
        utils.logger.debug('Files to be archived: %s', old_files)
        utils.archive_files(
            files=old_files,
            path_to_archive=utils.FILE_PATH,
            path_to_files=str(TEST_DATA) + '/',
            arch_name='sorted_files'
        )


if __name__ == '__main__':
    subprocess.run(
        ['py', 'dupes_sorting/sort_multiples.py', '-f', str(TEST_DATA / 'lehi dupes.csv')],
        check=True)
    seg_len, lines = utils.trim_log_seg(utils.get_last_log_segment())
    print(f'{seg_len=}\n{lines=}')
    test_cleanup()
