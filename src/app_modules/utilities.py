"""Utility functions used by multiple programs."""


import argparse
import fnmatch as fnm
import os
import sys
import zipfile
from datetime import date as dt
from datetime import timedelta as td
from pathlib import Path

import chardet
import app_modules.file_locations as loctns
from app_modules.app_logger import logger  #noqa F401, pylint: disable=W0611:unused-import

DATA_ROOT = loctns.DATA_ROOT
FILE_PATH = loctns.FILE_PATH
ARCHIVE_PATH = loctns.ARCHIVE_PATH
ORIGINAL_DATA = loctns.ORIGINAL_DATA
TEST_DATA = loctns.TEST_DATA

LOG_FILE = loctns.LOG_FILE
PROJECT = loctns.PROJECT
ROOT = loctns.ROOT

TRANSFORM_MODULES = 'transforms.client_transforms.'
TRANS_PREFIX = 'fxd '
LETTERN = '01234567890123456789012345'
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
LEN_LETTERS = len(LETTERS)
TRANSLATE = {
    'halp': 'hlap', 'hlp': 'hlap', 'eagle': 'eagle_mtn', 'usbxmlf': 'frederick',
    'lake': 'lake_point', 'kemmer': 'kemmerer', 'discovery': 'discovery_bay',
    }

#file prefixes to ignore in watchme directory
IGNORE = ['sorted', 'fxd', '.~lock', '.log', 'B47001', 'Zone.Identifier', '_.pdf']


def archive_files(
        files, path_to_archive=TEST_DATA, path_to_files=TEST_DATA, arch_name=None, mode='w'
        ):
    """
    Compress files to archive directory.

    Using name of first file in list as archive name.
    """
    arch_name = arch_name or files[0].split('.')[0]
    arch_name = f'{path_to_archive}archive/{arch_name}.zip'
    with zipfile.ZipFile(arch_name, mode) as zip_file:
        for filename in files:
            target_file = f'{path_to_files}{filename}'
            zip_file.write(
                target_file, filename,
                compress_type=zipfile.ZIP_DEFLATED)
            os.remove(target_file)


def compose_hlap_filename(day=None):
    """
    Calc year/month and cycle for use in filename.

    CUT_OFF days subtracted from today's date to build filename allowing
    program to run in first week of new month for cycle 2.
    """
    cut_off = 8
    in_file = 'B47001_{cycle:02}_{yr_mth}_47001'
    dt_parts = str(dt.today() - td(days=cut_off)).split('-')
    day = day or dt.today().day
    cycle = 1 if (0 + cut_off) <= day <= (31 - cut_off) else 2
    return in_file.format(cycle=cycle, yr_mth=''.join(dt_parts[:2]))


def convert_col_letter_to_number(ltrs):
    """Convert column letter in spreadsheet to zero based index number."""
    return sum(
        (LETTERS.find(ltr) + 1) * LEN_LETTERS**pwr
        for pwr, ltr in enumerate(ltrs[::-1])
        ) - 1


def find_all_files(part_name, file_type, file_path):
    """Find all files."""
    return [
        x for x in os.listdir(file_path)
        if not (
            [xcld for xcld in IGNORE if fnm.fnmatch(x, f'{xcld}*')]
            )  # eliminate excluded files
        and
        x[x.rfind('.') + 1:].lower() in file_type.lower()  # check file type
        and
        (not part_name or  # check partial filename match
            (part_name and part_name.lower() in x.lower()))
        ]


def get_absolute_filenames(filename):
    """Name of function says it all."""
    prefix = FILE_PATH
    infile = prefix + filename
    outfile = filename.split('.')[0] + '.csv'
    outfile = prefix + TRANS_PREFIX + outfile
    return (infile, outfile)


def get_file_encode(abs_filename):
    """Open file (using absolute name) to determining encoding.

    Needed because default encoding does not handle all ASCII
    extending characters (bug found using City Of Ivins files).

    chardet module is most reliable method to detect encoding. Only using
    first line of file to inprove performance.

    Change ASCII encoding to UTF8 for better coverage.
    """
    with open(abs_filename, 'rb') as tfile:
        result = chardet.detect(tfile.readline())
    return result['encoding'].replace('ascii', 'utf8')


def get_filename(part_name=None, file_type=None, file_path=FILE_PATH):
    """
    Get required file based upon supplied partial name and/or file type.

    Or get newest file of specified type if no partial name is given.
    """
    file_path = file_path.replace('//', '/')
    file_type = file_type or 'csv,txt,zip,xml'
    filename = None
    if all_files := find_all_files(part_name, file_type, file_path):
        found_files = [  # get file time stamps
            (os.stat(file_path + x).st_mtime, x) for x in all_files
            ]
        # find most recent file
        filename = sorted(found_files, reverse=True)[0][1]
    else:
        filename = ' '.join([
                'nothing using',
                'partname',
                f'"{part_name}"',
                'and filetype',
                f'"{file_type}"',
            ])
    return filename


def get_last_log_segment(lines=100):
    """Get last n records of log file."""
    with open(f'{FILE_PATH}{LOG_FILE}', 'r', encoding='utf8') as log_file_data:
        return log_file_data.readlines()[-lines:]


def initialize_log_file(path=FILE_PATH):
    """Initialize log file so it doesn't get too large."""
    with open(f'{path}{LOG_FILE}', 'w', encoding='utf8') as log:
        log.writelines([])


def nomalize_user_input(u_cname=None, u_fname=None, u_ftype=None, u_fpath=FILE_PATH):
    """Turn user imput into normalized data for processing."""
    u_fname = u_fname.replace('../', ROOT) if u_fname.startswith('../') else u_fname
    if not u_fname or not Path(u_fname).exists():
        if '.' in u_fname:
            u_fname, u_ftype = u_fname.rsplit('.', 1)
        u_fname = get_filename(u_fname, u_ftype, u_fpath)
    cname, fname, ftype, fnew, fpath = parse_filename_new(f'{u_fpath}{u_fname}')
    fnew = fnew if '.' in fnew else ''  # f'{fnew}.{u_ftype or ftype}'
    return (u_cname or cname, u_fname or fname, ftype or u_ftype, fnew, fpath)


def parse_filename_new(abs_fname):
    """
    Use pathlib.Path (easier and more flexible) to parse file name.

    fnew = new filename but input filename should remain unchanged unless really bad.
    Ext = always the first given ".xml (2).txt" -> ".xml" (if multiple types given)
          New filename may be used as output name or for file rename to simplify later code
    cname = City name (part of filename prior to blank) made lower case to simplify later code
    fpath = path to file, if given overrides default path (flip between testing & normal)
    """
    fparts = Path(abs_fname)
    ftype = fparts.suffixes[-1] if fparts.suffixes else '.'
    ftype = ftype.split(' ', maxsplit=1)[0]
    fname = fparts.name
    cname = xtract_city_name(fparts.stem)
    fnew = f'{fparts.stem.replace('.', '_')}{ftype if len(ftype) > 1 else ""}'
    fpath = fparts.parent.as_posix().rsplit(':', maxsplit=1)[-1]
    fpath = f'{FILE_PATH if fpath == '.' else fpath}/'
    return (TRANSLATE.get(cname, cname), fname, ftype[1:], fnew, fpath.replace('//', '/'))


def trim_log_seg(lines):
    """Extract log segment that applies to testing."""

    # extract message to make testing easier
    lines = [line.split(']')[1].strip() for line in lines]

    seg_len, idx = len(lines), 0
    for idx, line in reversed(list(enumerate(lines))):
        if not line.strip('*'):
            break
    lines = lines[idx-seg_len+1:]
    seg_len = len(lines)
    return (seg_len, lines)


def xtract_city_name(fname):
    """Get city name (lower case) from beg of filename to 1st space."""
    fname = fname.lower()
    if 'diamondville' in fname:
        # kemmerer diamondville needs special attention because
        # two entity files start with kemmerer in filename
        return 'kemmerer_diamondville'
    return fname.split()[0].split('.')[0].split('_')[0].split('-')[0]


def parse_user_input(desc='Specify file to be processed'):
    """
    Parse user input for files to processed.

    If full file name given the other parts are extracted.
    User input option overrides extracted option (except for file type).
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '-n', action='store', dest='city_name', default='',
        help='city name to search for (default=most recent of type)')
    parser.add_argument(
        '-f', action='store', dest='file_name', default='',
        help='name of file to be processed (mandatory)')
    parser.add_argument(
        '-t', action='store', dest='file_type', default='zip',
        help='file type to search for')
    parser.add_argument(
        '-p', action='store', dest='file_path', default=FILE_PATH,
        help='path to file location')
    return nomalize_user_input(
        u_cname = parser.parse_args().city_name,
        u_fname = parser.parse_args().file_name,
        u_ftype = parser.parse_args().file_type,
        u_fpath = parser.parse_args().file_path,
    )


if __name__ == "__main__":
    CITY_NAME, FILE_NAME, FILE_TYPE, NEW_FNAME, FILE_PATH = parse_user_input()
    print(f'Input: {sys.argv[1:]=}')
    print(f'Result: {CITY_NAME=}, {FILE_NAME=}, {FILE_TYPE=}, {NEW_FNAME=}, {FILE_PATH=}')
    print()

    # # Mock sys.argv for testing
    # sys.argv = ["script.py", "--name", "Alice"]
    # args = parse_args()

    # print(f"Hello, {args.name}!")  # Output: Hello, Alice!
