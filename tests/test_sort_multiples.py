"""Testing of sort program using multiple source files.

Need to:
1 - set enviroment variable FM_FILES=tests (run FMT.bat) to run tests.
2 - enter environment with command 'wo fm'
3 - start tests with 'py -m pytest test_sort_multiples.py'
"""


import os
import pytest
import app_modules.utilities as utils
import app_modules.file_locations as loctns


# Prepare for testing
TEST_DATA = f'{loctns.TEST_DATA}multiples_data/'
utils.initialize_log_file(path=utils.FILE_PATH)

sort_tests = [
    ('lehi dupes.csv', 'is probably OK', 1),  # comma separated file with alpha sort
    ('baca dupes.txt', 'is probably OK', 1),  # tab separated file
    ('ivins dupes ascii.txt', 'is probably OK', 1),  # UTF8 file with extended characters
    ('ivins dupes size.txt', 'File size diff is more than 1 percent', 5),
    ('lehi dupes.txt', 'is probably OK', 1),  # ASCII file with extended characters in first line
    ('parowan dupes.txt', 'is probably OK', 1),  # needs extra column FS with *
    ('jerome dupes.txt', 'Due date is in column 4 (E) and has value of 12/15/2020 12:0', 5),
    ('clearfield dupes.txt', 'First banner appears on line 5', 2),  # many single records
    ('lehi dupes blanks.txt', 'but input file had 61 blank lines', 5),  # empty lines, tabs only
    ('nodate test.csv', 'Due date is in column -1 (Unknown) and has value of None', 6),
    ]
missing_tests = [
    ('burley dupes missing.txt', 'not found', 1),  # registered city with missing file
    ('not_registered.csv', 'to register city', 1),
    ]


@pytest.mark.parametrize('fname, msg, line', sort_tests)
def test_sorting(fname, msg, line, subtests):
    """Test sorts."""
    with subtests.test(fname):
        assert os.system(f'py src/dupes_sorting/sort_multiples.py -f "{TEST_DATA}{fname}"') == 0

    _, seg_lines = utils.trim_log_seg(utils.get_last_log_segment())

    with subtests.test():
        assert msg in seg_lines[-line]


@pytest.mark.parametrize('fname, msg, line', missing_tests)
def test_missing_data(fname, msg, line, subtests):
    """Test sorts."""
    with subtests.test(fname):
        assert os.system(f'py src/dupes_sorting/sort_multiples.py -f "{TEST_DATA}{fname}"') != 0

    _, seg_lines = utils.trim_log_seg(utils.get_last_log_segment())

    with subtests.test():
        assert msg in seg_lines[-line]


def test_cleanup():
    """Archive results to keep test data directory clean."""
    if old_files := [
            x for x in os.listdir(TEST_DATA)
            if x.startswith('sorted') and not x.endswith('.zip')]:
        utils.logger.debug('*' * 80)
        utils.logger.debug('Files to be archived: %s', old_files)
        utils.archive_files(
            files=old_files,
            path_to_archive=utils.FILE_PATH,
            path_to_files=TEST_DATA,
            arch_name='sorted_files')


if __name__ == '__main__':
    _ = os.system(f'py dupes_sorting/sort_multiples.py -f "{TEST_DATA}lehi dupes.csv') == 0
    seg_len, lines = utils.trim_log_seg(utils.get_last_log_segment())
    print(f'{seg_len=}\n{lines=}')
    test_cleanup()
