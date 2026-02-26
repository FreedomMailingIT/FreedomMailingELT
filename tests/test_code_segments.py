"""Test miscellaneous code segments."""


import decimal as dec  # noqa
import csv
from pathlib import Path
from app_modules import utilities as utils


def test_amt_to_string():
    """Format decimal amount as output string (old vs new)."""
    neg_char = '-'
    for amount in (12.99, 13.0, -4.99, 0.0):
        neg_sign = neg_char if amount < 0 else ' ' * len(neg_char)
        old = '{:0.2f}{}'.format(abs(dec.Decimal(amount)), neg_sign)  # pylint: disable=c0209:consider-using-f-string
        new = f'{abs(dec.Decimal(amount)):0.2f}{neg_sign}'
        assert new == old


def test_remove_leading_zeros():
    """Remove leading zeros from non dollar value (old vs new)."""
    for number in ('000254', '-100', '0', '100'):
        number = f'-{number[:-1]}' if number[-1] == '-' else number
        old = '{:0f}'.format(dec.Decimal(number))  # pylint: disable=c0209:consider-using-f-string
        new = f'{dec.Decimal(number):0f}'
        assert new == old


def test_col_letter_to_number():
    """Ensure speadsheet column letter translated to number correctly."""
    assert utils.convert_col_letter_to_number('ED') == 133
    assert utils.convert_col_letter_to_number('EE') == 134
    assert utils.convert_col_letter_to_number('EF') == 135
    assert utils.convert_col_letter_to_number('EG') == 136
    assert utils.convert_col_letter_to_number('EH') == 137


def test_row_col_read():
    """Test the right column is being extracted."""
    test_file = Path(utils.TEST_DATA) / "archive" / "many_columns.txt"
    with open(test_file, encoding="utf8") as test_data:
        csv_reader = csv.reader(test_data, delimiter="\t")
        for row in csv_reader:
            assert row[utils.convert_col_letter_to_number('ED')] == ''
            assert row[utils.convert_col_letter_to_number('EE')] == 'PO BOX 1478'
            assert row[utils.convert_col_letter_to_number('EF')] == 'HAYDEN ID 83835-1478'
            assert row[utils.convert_col_letter_to_number('EG')] == 'ID'
            assert row[utils.convert_col_letter_to_number('EH')] == '83835-1478'
