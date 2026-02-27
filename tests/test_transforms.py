"""Test transform programs.

Should test all transforms because they are all unique.

Each transform ZIP file is copied into the test directory, processed,
and validated through log inspection. Cleanup removes temporary files
and archives fixed output files.
"""

from pathlib import Path
from shutil import copyfile
import subprocess

import pytest

import app_modules.utilities as utils
import app_modules.file_locations as loctns

# Prepare for testing
TEST_DATA = Path(loctns.TEST_DATA)
utils.initialize_log_file(path=utils.FILE_PATH)

transforms = [
    'Charlevoix csv_EOR.zip',
    'Charlevoix tsv_EOR.zip',
    'Charlevoix fixed_length.zip',
    'draper non water.zip',
    'draper water.zip',
    'eagle_mtn.zip',
    'effingham bills.zip',
    'effingham delinquents.zip',
    'elko.zip',
    'frederick water.zip',
    'frederick non water.zip',
    'frederick shutoffs.zip',
    'lake_point.zip',
    'roosevelt.zip',
    'waterford.zip',
    'discovery_bay.zip'
]

@pytest.mark.parametrize('fname', transforms)
def test_transform(fname, subtests):
    """Run a transform and validate its log output.

    Steps:
    - Copy the ZIP file into the test directory
    - Execute the transform logic
    - Inspect the last log segment
    - Validate conversion, CSV creation, non-empty output, and compression
    """
    with subtests.test(msg=f'{fname} failed to execute!'):
        src = TEST_DATA / "transform_data" / fname
        dst = TEST_DATA / fname
        copyfile(src, dst)

        result = subprocess.run(
            ["py", "src/transforms/transform_file.py", "-f", fname],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.returncode == 0

    seg_len, lines = utils.trim_log_seg(utils.get_last_log_segment())

    with subtests.test(msg=f'{fname} not converted!'):
        assert seg_len == 4 and 'Converted ' in lines[1]

    with subtests.test(msg=f'{fname} failed to create CSV file!'):
        assert seg_len == 4 and 'Created ' in lines[2]

    with subtests.test(msg=f'{fname} has empty conversion file!'):
        assert seg_len == 4 and int(lines[2].split()[1]) > 0

    with subtests.test(msg=f'{fname} results not compressed!'):
        assert 'Compressed results to "fxd' in lines[-1]


def test_cleanup():
    """Keep test TEST_DATA directory clean.

    Delete temporary files and archiving fixed files for examination of results,
    if needed.
    """
    old_files = [x for x in TEST_DATA.iterdir() if x.name.startswith('fxd ')]
    if old_files:
        utils.logger.debug('*' * 80)
        utils.logger.debug('Files to be archived: %s', old_files)
        utils.archive_files(
            files=[f.name for f in old_files],
            path_to_archive=utils.FILE_PATH,
            path_to_files=str(TEST_DATA) + '/',
            arch_name='transformed_files'
        )

    # remove copied source files
    deletions = []
    for file in transforms:
        path = TEST_DATA / file
        if path.exists():
            path.unlink()
            deletions.append(file)

    utils.logger.info('Deleted test files: %s', deletions)


if __name__ == '__main__':
    subprocess.run(["py", "src/transforms/transform_file.py", "-f", "waterford.zip"], check=True)
    test_cleanup()
