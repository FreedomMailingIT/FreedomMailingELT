"""
Read specified input file and sort records.

Sort based upon the parameters given in sort_parameters.py and outputs
sorted records to renamed file.
"""

import csv
import datetime
import operator
import os
import sys

from sort_parameters import ORGS
import app_modules.utilities as utils

REGISTERS = {}
INC = 10000
LIMIT = 1.0


def check_due_date(due_date, filename):
    """Make sure the due date in file is later than today's date.

    (avoids accidental processing old file, due_date format 'mm/dd/yyyy')
    """
    if 'tests' in filename:
        # don't bother with date check when testing
        return True
    due_date = due_date.split()[0]  # handle timestamp, eg Jerome ID
    dformat = '%m/%d/%Y' if len(due_date) > 8 else '%m/%d/%y'
    due_date = datetime.datetime.strptime(due_date, dformat)
    return (due_date - datetime.datetime.now()).days >= 0


def check_file_sizes(ofn, sfn):
    """Confirm sorted file size is resonable, compared to original file."""
    ofs = os.path.getsize(ofn)
    sfs = os.path.getsize(sfn)
    try:
        size_ok = (abs(sfs - ofs) / ofs) * 100 <= LIMIT
    except ZeroDivisionError:
        size_ok = False
    return (ofn, sfn, size_ok)


def get_key_value(idx):
    """Keep track of the sorted goup header."""
    if idx in REGISTERS:
        REGISTERS[idx] += 1
    else:
        REGISTERS[idx] = (idx * INC) + 1
    return REGISTERS[idx]


def get_parameters(city_name):
    """Find field parameters for city in auxilary program file."""
    try:
        org_details = ORGS[city_name]
    except KeyError:
        # program found city name not found in parameters
        print_register_help(city_name or 'A blank city name')
        sys.exit(1)

    if len(org_details) == 3:
        # add possible missing date column
        org_details.append('')
    for idx, item in enumerate(org_details):
        if isinstance(item, str):
            org_details[idx] = utils.convert_col_letter_to_number(item)
        else:
            org_details[idx] = item
    return org_details


def prepare_input(abs_fn, city_params):
    """Read whole file into memory to be sorted.

    Should not be an issue, most, if not all files less than 2 MB.
    """
    try:
        col1, col2, col3, _ = city_params  # last param in due date if given
    except ValueError:
        col1, col2, col3 = city_params

    utils.logger.info('Sorting %s using %s parameters', abs_fn, city_params)
    with open(abs_fn, 'r', encoding=utils.get_file_encode(abs_fn)) as ifile:
        delim = get_delimeter(ifile)
        lines = csv.reader(ifile, delimiter=delim)
        new_lines = [massage_line(line) for line in lines]
        sorted_file = sorted(
            new_lines, key=operator.itemgetter(col1, col2, col3))
        return (sorted_file, delim)


def massage_line(line):
    """Add end of record marker and trim column data."""
    new_line = [item.strip() for item in line]
    new_line.append('*')
    return new_line


def get_delimeter(ifile):
    """Find delimeter being used."""
    delim = '\t' if '\t' in ifile.readline() else ','
    ifile.seek(0)
    return delim


def print_missing_file_help(city_name):
    """Print user message about missing input file."""
    utils.logger.info('Could not find a recent %s file.', city_name)
    utils.logger.info('Have you placed unsorted file in work area?')
    utils.logger.info('Perhaps you gave wrong city name.')


def print_register_help(city):
    """Print user message about unregistered city."""
    utils.logger.info('City "%s" is not registered.', city)
    utils.logger.info('Registration or valid city name required to sort.')
    utils.logger.info('Contact gregory.j.baker@gmail.com to register city.')


def print_success_msg(data):
    """Print user message indicating success."""
    filename, due_date_col, due_date, first_banner, blank_lines, records, sorted_fn = data
    date_msg = (str(due_date_col) if due_date_col is not None else '??')
    if due_date_col >= 0:
        date_col = (
            f' {utils.LETTERS}'[(due_date_col) // 26] +
            utils.LETTERS[(due_date_col) % 26]
        )
    else:
        date_col = 'Unknown'

    ofn, _, size_ok = check_file_sizes(filename, sorted_fn)
    size_msg = 'less' if size_ok else 'more'
    blank_lim = 500
    problems = {
        'file size': size_ok,
        'first banner': first_banner <= 16,
        'due date': not due_date or check_due_date(due_date, filename),
        'record count': records > 100,
        'blank lines': blank_lines < blank_lim,
        }
    problems = [key for key, val in problems.items() if not val]

    utils.logger.debug('*' * 80)  # used in testing
    utils.logger.info('Sorted "%s"', ofn.split('/')[-1])
    utils.logger.info(
        'Due date is in column %s (%s) and has value of %s',
        date_msg,
        date_col.replace(' ', ''),
        due_date)
    utils.logger.info(
        'File size diff is %s than %d percent', size_msg, int(LIMIT))
    if blank_lines:
        utils.logger.info('but input file had %s blank lines', blank_lines)
    utils.logger.info('File has %s lines', records)
    utils.logger.info('First banner appears on line %s', first_banner)
    if records:
        utils.logger.info(
            'Conversion of "%s" is %s %s',
            ofn.split('/')[-1],
            ('possibly' if problems else 'probably'),
            ('**suspect** because of:' if problems else 'OK'))
        if problems:
            utils.logger.info('%s', ', '.join(key for key in problems if key))
    else:
        utils.logger.info('There is a problem; ***file is empty***')


def sort_and_output(groups, filename, due_date_col, delim, blank_lines):
    """Sort the input file and output sorted result."""
    fn_parts = filename.split('/')
    sorted_fn = f'{'/'.join(fn_parts[:-1])}/sorted {fn_parts[-1]}'
    with open(sorted_fn, 'w', encoding='utf8') as outfile:
        out_file = csv.writer(
            outfile, delimiter=delim,
            quoting={',': csv.QUOTE_ALL, '\t': csv.QUOTE_MINIMAL}[delim],
            lineterminator='\n')
        prev_key = 2 * INC
        record_no = first_banner = line_no = 0
        due_date = None
        for i in sorted(groups.keys()):
            record_no += 1
            if i > prev_key:
                first_banner, prev_key = new_section(
                    out_file, record_no, i, prev_key, first_banner)
            for line in groups[i]:
                line_no, due_date = write_record(
                    due_date_col, out_file, line, line_no)
    print_success_msg(
        (filename, due_date_col, due_date, first_banner, blank_lines, line_no, sorted_fn)
        )


def write_record(due_date_col, out_file, line, line_no):
    """Print record to file."""
    line_no += 1
    out_file.writerow(line)
    due_date = line[due_date_col] if due_date_col >= 0 else None
    return (line_no, due_date)


def new_section(out_file, record_no, i, prev_key, first_banner):
    """Write banner for new sort section."""
    banner = int(i / INC)
    first_banner = record_no if banner == 2 else first_banner
    out_file.writerow([f'{str(banner) * 10} banner'])
    prev_key = (banner + 1) * INC
    return (first_banner, prev_key)


def main(file2sort, city_name):
    """Process file."""
    groups = {}
    group = []
    prev_key = None
    count = 0
    blank_lines = 0

    city_params = get_parameters(city_name)
    sorted_file, delim = prepare_input(file2sort, city_params)
    for line in sorted_file:
        if line[0]:
            # only write non blank lines
            curr_key = ''.join([
                line[city_params[0]],
                line[city_params[1]] or line[city_params[2]]
                ])
            if curr_key == prev_key:
                count += 1
            else:
                if group:
                    groups[get_key_value(count)] = group
                    group = []
                prev_key = curr_key
                count = 1
            line[-1] = line[-1].rstrip('^')  # extra char in rawlins file
            group.append(line)
        else:
            blank_lines += 1
    groups[get_key_value(count)] = group
    sort_and_output(groups, file2sort, city_params[3], delim, blank_lines)
    return 1


if __name__ == '__main__':
    CITY_NAME, FILE_NAME, FILE_TYPE, NEW_FNAME, FILE_PATH = utils.parse_user_input()
    # print(f'{CITY_NAME=}, {FILE_NAME=}, {FILE_TYPE=}, {NEW_FNAME=}, {FILE_PATH=}'); exit()

    ABS_FILENAME = FILE_NAME if FILE_NAME[0] == '/' else f'{utils.FILE_PATH}{FILE_NAME}'

    RESULT = 1
    if CITY_NAME not in ORGS:
        print_register_help(CITY_NAME)
    elif not os.path.exists(ABS_FILENAME):
        utils.logger.info('File "%s" not found.', ABS_FILENAME)
    else:
        RESULT = main(ABS_FILENAME, CITY_NAME)
    utils.logger.info('*' * 80)
    sys.exit(RESULT)
