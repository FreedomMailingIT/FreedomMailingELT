"""Transform TylerTech XML.

Beware! Changes here may effect multiple clients.
"""


from datetime import datetime
from app_modules import csv_io
import transforms.client_transforms.tyler_tech_xml as ttx
import transforms.client_transforms.ancillaries.discovery_bay_fields as dbf


def blank_unneeded_usages(bill):
    """Blank usage for services that do not require them."""
    try:
        for idx, service in enumerate(bill['service_?']):
            if service in dbf.blank_usage_services:
                bill['usage?'][idx] = ''
    except (AttributeError, KeyError):
        pass  # blank_usage not setup OR no services attached to account
    return bill

def build_consumption_history(bill):
    """Build consumption columns from extracted data."""
    start_per = 12 - int(bill['Cons_prd'].split('/')[0])
    for idx, usage in enumerate(bill[ttx.CONS_KEY][start_per - 36:-14]):
        field_name = f'usagepri{idx}' if idx else 'currusage'
        bill[field_name] = usage.lstrip('0') or '0'  # leave at least one 0
    return bill


def calc_period_days(bill, start_date, end_date):
    """Calculate the number of days in the building period."""
    d1 = datetime.strptime(start_date, "%m/%d/%Y").date()
    d2 = datetime.strptime(end_date, "%m/%d/%Y").date()
    bill['numb_days'] = (d2 - d1).days
    return bill


def format_currency(bill, name, value):
    """Format extracted data into suitable currency field."""
    value = value.replace('-', 'CR').lstrip('0')
    value = ('0.00' if value == '.00'
             else (f'0{value}' if value[0] == '.' else value))
    bill[name] = value


def set_contract_pay(bill):
    """Set Contract Pay message (if ever needed)."""
    return bill


def set_direct_pay(bill, direct_pay):
    """Set Direct Pay CSV column."""
    msg = direct_pay['message'].replace(
        '{draft_date}', bill[direct_pay['pay_date']])
    bill[direct_pay['msg_col']] = msg
    return bill


def strip_leading_numbers(value):
    """Strip non-alpha characters at beginning of service name."""
    return value[value.find('-')+1:].strip()


def strip_leading_zeros(name, value, currency_fields):
    """Strip zeros, except on account number (needed for bills & notices)."""
    return value.lstrip('0') if name in currency_fields else value


def unpack_list_values(bill, name, values):
    """Unpack returned list into appropriate CSV columns."""
    for idx, item in enumerate(values):
        new_key = name.replace('?', str(idx+1))
        new_key = f'curr{new_key}' if new_key == 'usage1' else new_key
        bill[new_key] = (
            strip_leading_numbers(item)
            if (new_key.startswith('service_') or
                (new_key.startswith('meter') and len(new_key) < 8))
            else item.lstrip('0')
            )
    return bill


##########
def add_global_messages(bill, source):
    """Add maximum of four BillComments from XML file to all records."""
    for idx in range(min(4, len(source.comments))):
        bill[f'message{idx + 1}'] = source.comments[idx]
    return bill


def correct_meter_types(bill):
    """Erase meter type value if not metered service.

    (no meter_id for service).
    """
    for idx in range(1, 11):
        meter_type = f'meter{idx}'
        if bill.get(meter_type, False) and not bill.get(f'meter_id{idx}'):
            bill[meter_type] = ''
    return bill


def format_data(bill):
    """Format extracted XML data for output."""
    new_bill = bill
    return new_bill


def post_processing(bill):
    """Calculate and record Past Due amount."""
    bill = (build_consumption_history(bill)
            if bill.get(ttx.CONS_KEY, False)
            else bill)
    bill = (set_direct_pay(bill, dbf.direct_pay)
            if dbf.DIR_PAY_MSG and bill.get('directpay', False) == 'Y'
            else bill)
    bill = set_contract_pay(bill) if bill.get('contrctamt', False) else bill
    bill = blank_unneeded_usages(bill)
    new_bill = calc_period_days(bill, bill.get('curbegdate'), bill.get('curenddate'))
    new_bill = {k: v for (k, v) in bill.items() if not k.endswith('?')}
    new_bill |= dbf.bill_literals
    new_bill['baraccnum'] = new_bill['accnumber'].replace('-', '')
    for name, value in bill.items():
        if name in dbf.currency_fields:
            format_currency(new_bill, name, value)
        elif isinstance(value, list):
            unpack_list_values(new_bill, name, value)
        else:
            strip_leading_zeros(name, value, dbf.currency_fields)
    return new_bill


############## main function ################

def transform_data(csv_w, source_text):
    """Convert Roosevelt source XML into required format."""
    count = 0
    # if 'bill' in csv_w.name or 'usbx' in csv_w.name:
    if 'BillExtract' in source_text[1]:
        # bills extraction
        source = ttx.SourceXML(
            source_text, dbf.bill_extract, active_only=dbf.ACTIVE_ONLY,
            zero_balance=dbf.ZERO_BALANCE)
        csv_out = csv_io.CSVhandler(csv_w, dbf.bill_headings)
        for bill in source.traverse_xml():
            new_bill = post_processing(bill)
            new_bill = format_data(new_bill)
            # correct meter types must be done after everything loaded
            new_bill = correct_meter_types(new_bill)
            new_bill = add_global_messages(new_bill, source)
            csv_out.write_record(new_bill)
            count += 1
    else:
        # late pay extractiom
        source = ttx.SourceXML(
            source_text, dbf.late_pay_extract, root='Account')
        csv_out = csv_io.CSVhandler(csv_w, dbf.late_pay_headings)
        for notice in source.traverse_xml():
            csv_out.write_record(notice)
            count += 1
    return count
