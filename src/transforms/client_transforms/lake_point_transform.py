"""
Transfor Lake Point from multi line account CSV file to single line TSV.

Receives csv file handle (for transformed data) and source text to transform
"""

import csv

import app_modules.utilities as utils

import transforms.client_transforms.ancillaries.lake_point_fields as lpf

coln = utils.convert_col_letter_to_number
MAX_TRANSACTIONS = 10
SERV_COLS = len(lpf.BODY)


def transform_data(csv_w, source_text):
    """Assumes a csv source that is written unchanged to output file."""
    count = 0
    try:
        csv_r = csv.reader(source_text)
        write_headers(csv_w)
        for row in csv_r:
            if row:  # skip empty row
                match row[coln('A')]:
                    case 'HEADER':
                        header_fields = extract_header(csv_r)
                    case 'BODY':
                        body_fields, msg, acc_id = extract_body(csv_r)
                    case 'FOOTER':
                        footer_fields = extract_footer(csv_r)

                        # end of account, write adjusted results to csv file
                        header_fields[0] = acc_id if acc_id else header_fields[0]
                        output_record(
                            csv_w, header_fields, body_fields, footer_fields, msg)
                        count += 1
    except Exception as err:
        raise err
    return count


def write_headers(csv_w):
    """Write headers to output file."""
    transactions = []
    for i in range(1, MAX_TRANSACTIONS+1):
        transactions += [x.format(i) for x in lpf.BODY]
    csv_w.writerow(
        list(lpf.HEADER.keys()) +
        list(lpf.FOOTER.keys()) +
        transactions +
        ['MESSAGE', 'EOR']
        )


def extract_header(csv_r):
    """Extract data from HEADER section of account details."""
    row = next(csv_r)
    return [row[coln(col)] for col in lpf.HEADER.values()]


def extract_body(csv_r):
    """Extract data from BODY section of account details."""
    msg = None
    acc_id = None
    body_fields = []
    while row := next(csv_r):
        desc_parts = row[1].replace('comID#', 'com ID#').split()
        if desc_parts and desc_parts[-1].isnumeric():  # must be message ending in ID
            msg = ' '.join(desc_parts)
            acc_id = desc_parts[-1]
            continue

        body_fields += [
            format_currency(row[coln(col)]) if col == 'D' else row[coln(col)]
            for col in lpf.BODY.values()
        ]
        if row[coln('C')] == 'Balance Due:':
            break  # have reached the end of "body" transactions
    return (body_fields, msg, acc_id)


def extract_footer(csv_r):
    """Extract data from FOOTER section of account."""
    row = next(csv_r)
    row = next(csv_r)
    return [format_currency(row[coln(col)]) for col in lpf.FOOTER.values()]


def output_record(csv_w, header_fields, body_fields, footer_fields, msg):
    """Write extracted data to CSV file."""
    no_serv = int(len(body_fields) / SERV_COLS)
    output = header_fields + \
        footer_fields + \
        body_fields + \
        (['']*SERV_COLS)*(MAX_TRANSACTIONS-no_serv) + \
        [msg] + ['*']
    csv_w.writerow(output)


def format_currency(value: str):
    """Change currency value to format $0.00."""
    if value:
        if '.' not in value:
            value = f'{value[:-2]}.{value[-2:]}'
        if value.startswith('$.'):
            value = f'$0{value[-3:]}'
        if not value.startswith('$'):
            value = f'${value}'
    return value
