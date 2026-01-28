"""
Transform for Village of Waterford Muni-Link transform (Dec 2019).

Started with unknow number of meters, services etc.
"""

import csv
from transforms.client_transforms.ancillaries import waterford_records


def transform_data(csv_writer, source_text):
    """Assumes a csv source that is written unchanged to output file."""
    csv_reader = csv.reader(source_text)
    record = waterford_records.Record()
    csv_writer.writerow(record.headings())
    count = 0
    for row in csv_reader:
        if row and row[0] != 'HDR':  # bypass empty line and header
            if (row[0] == 'BILL' and record.len() > 99) or row[0] == 'TLR':
                csv_writer.writerow(record.get())
                count += 1
                record.reset()
            if row[0] != 'TLR':
                record.build(row)
    return count
