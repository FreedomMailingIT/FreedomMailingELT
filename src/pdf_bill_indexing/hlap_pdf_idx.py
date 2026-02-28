"""
Produce index of PDF bill file.

Extracts account & page numbers from PDF file into file with name structure:
B47001_02_201702_47001.spdfi (company_billcycle_yearmonth_company).

Switched to PyMuPDF (import as fitz) because os independent Python package
that is ~20 faster that PyPDF4.
"""

import subprocess
import sys
from pathlib import Path

import pymupdf as pdf_reader
import hlap_sftp_host as c
from pdf_bill_indexing.hlap_idx_check import check_idx_file
import app_modules.utilities as utils


def parse_pdf_page(page, raw_page_no, status):
    """Update status based on a single PDF page.
    Returns (acc_no, idx_no) or None if alignment page.
    """
    text = page.get_text()
    if 'ALIGNMENT' in text:
        status['align'] += 1
        return None
    lines = text.split('\n')
    acc_no = lines[8]
    idx_no = raw_page_no + status['align']
    if status['first'] is None:
        status['first'] = acc_no
    status['last'] = acc_no
    return acc_no, idx_no


def create_index(new_abs_fn_prefix):
    """Create index with account number, start page, and end page on each line."""
    tmp_file = f'{new_abs_fn_prefix}.tmp'
    spdfi_file = f'{new_abs_fn_prefix}.spdfi'
    pdf_file = f'{new_abs_fn_prefix}.pdf'

    utils.logger.info('Scaning %s.', pdf_file.rsplit('/', maxsplit=1)[-1])

    pdf_doc = pdf_reader.open(pdf_file)
    out_line = '{0:0>10},{sp},{ep}\n'
    status = {'align': 0, 'first': None, 'last': None}
    with open(tmp_file, 'w', encoding='utf8') as idxf:
        for raw_page_no, page in enumerate(pdf_doc, start=1):
            result = parse_pdf_page(page, raw_page_no, status)
            if result is None:
                continue
            acc_no, idx_no = result
            idxf.write(out_line.format(acc_no, sp=idx_no, ep=idx_no))
    idx_path = Path(spdfi_file)
    Path(tmp_file).replace(idx_path)
    utils.logger.info('Created index file %s', idx_path.name)
    checkout_idx(spdfi_file, len(pdf_doc), status['first'], status['last'])


def checkout_idx(spdfi_file, page_no, first_acc, acc_no):
    """Verify index file makes sense and report results."""
    results = check_idx_file(spdfi_file, first_acc, acc_no, page_no)
    checkout = all(results.values())
    if checkout:
        msg = 'correctly.'
    else:
        probs = {key: value for key, value in results.items() if not value}
        msg = f'with problems {probs}'
    utils.logger.info('%s bills indexed %s', page_no, msg)


def put_files_to_sftp(fn_prefix):
    """Copy required files to SFTP server."""
    cmd = [
        'sshpass', '-p', c.pswd,
        'scp', fn_prefix+'*',
        c.user+'@'+c.host+':~'
    ]
    err = subprocess.run(cmd, check=False)
    if err:
        utils.logger.info('Problems coping B47001* files to SFTP server.')
    else:
        utils.logger.info('Copied B47001* files to SFTP server.', )


def main(input_fp, input_fn=None):
    """
    Extract account & page numbers.

    Read though PDF text file and extracts account & page numbers which are
    output to index file as single line CSV. Account number must be 10 digits
    with leading zeros, both beginning and ending page numbers
    (always the same) also output
    eg 0123456789,10,10
    """
    file_path = Path(input_fp)
    filename = utils.compose_hlap_filename()
    new_abs_fn_prefix = file_path / filename
    if input_fn != filename:
        old_fn = file_path / input_fn
        new_fn = new_abs_fn_prefix.with_suffix(".pdf")
        utils.logger.info('Renaming "%s" to "%s"', old_fn.name, new_fn.name)
        old_fn.replace(new_fn)
    create_index(new_abs_fn_prefix)
    if 'test' not in input_fp:
        # no FTP if testing
        put_files_to_sftp(new_abs_fn_prefix)
    utils.logger.info('Process completed.')


if __name__ == '__main__':
    CITY_NAME, FILE_NAME, FILE_TYPE, NEW_FNAME, FILE_PATH = utils.parse_user_input()
    # must have source filename, fsmonitor usually supplies this
    if FILE_NAME:
        main(FILE_PATH, NEW_FNAME)
        # put_files_to_sftp(FILE_NAME)
    else:
        sys.exit(1)
