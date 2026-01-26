"""
Convert Heber Light & Power billing text file into tsv file for FreedomMailing.

There are two options.  Convert only printable bills (used for paper print run)
or print all bills (used for PDF print run to produce utility customer viewable
statements see hlp_pdf_idx).  Both options used each job run.
"""


import csv
import os
from src.transforms.client_transforms.ancillaries.hlap_account import Account
import src.app_modules.utilities as utils


DEBUG = False
BUDGET_BILLING = True
EOR_REQUIRED = True


def transform_data(dest_file, src_file, print_all):
    """Extract data from individual lines of input file."""
    total_bills = printed_bills = deleted_bills = 0
    with open(src_file, encoding='utf8') as hpl_file:
        line = hpl_file.readline()
        account = Account(line, BUDGET_BILLING, EOR_REQUIRED)
        if line.startswith('CYCCTL'):
            account.unpack_cycle(line)

        with open(
                dest_file
                .replace('TXT', 'csv')
                .replace('txt', 'csv'),
                'w', encoding='utf8') as out_file:
            csv_file = csv.writer(
                out_file, delimiter='\t', lineterminator='\n')
            csv_file.writerow(account.get_headings())
            xmethod = {
                'MSTR': account.unpack_mstr,
                'HIST': account.unpack_hist,
                'MTR':  account.unpack_meter,
                'CHGS': account.unpack_charges,
                'INFM': account.unpack_msg,
                'ACTT': account.unpack_acc_totals,
                '': account.noop
                }

            while line:
                line = hpl_file.readline()
                line_type = line[:4].strip()
                xmethod[line_type](line)
                if line_type == 'ACTT':  # last line of account XML record
                    account.pack_output()
                    total_bills += 1
                    if account.print_bill or print_all:
                        printed_bills += 1
                        if DEBUG:
                            print(account.account, end='\n\n')
                        else:
                            csv_file.writerow(account.account)
                    else:
                        deleted_bills += 1
                    account.reset()

        utils.logger.info('Created "%s"', dest_file.split('/')[-1])
        utils.logger.info('Total bills: %d', total_bills)
        utils.logger.info('Printed: %d', printed_bills)
        utils.logger.info('Not printed: %d', deleted_bills)


if __name__ == '__main__':
    CITY_NAME, FILE_NAME, FILE_TYPE, NEW_FNAME, FILE_PATH = utils.parse_user_input()
    # print(f'{CITY_NAME=}, {FILE_NAME=}, {FILE_TYPE=}, {NEW_FNAME=}, {FILE_PATH=}'); exit()

    IN_FILE_NAME = f'{FILE_PATH}{NEW_FNAME}'
    OUT_FILE_NAME = f'{FILE_PATH}{utils.TRANS_PREFIX}{NEW_FNAME}'
    # print(f'{IN_FILE_NAME=}, {OUT_FILE_NAME=}'); exit()

    if os.path.exists(IN_FILE_NAME):
        # convert to paper print file then PDF print file
        transform_data(
            OUT_FILE_NAME.replace('.', '_PRN.'), IN_FILE_NAME, False)
        transform_data(
            OUT_FILE_NAME.replace('.', '_PDF.'), IN_FILE_NAME, True)
    else:
        utils.logger.info('Could not find file "%s"', IN_FILE_NAME)
