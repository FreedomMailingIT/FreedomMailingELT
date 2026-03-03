"""Heber Light and Power account object defined."""

import transforms.client_transforms.ancillaries.hlap_fields as record_defs
from app_modules.freedom_utils import DotDict


class Account():
    """Object to represent individual account details extracted from file."""

    def __init__(self, ctrl_text, budget_billing, eor_required):
        """
        Use 'list' for ease of addition and output.

        Assumes output in same order as input.
        If output order changes this may need to change.
        """
        self.budget_billing = budget_billing
        self.eor_required = eor_required
        self.rec_defs = record_defs.DEFINITIONS
        self.cnvt_methods = {
            'format_acc_no': self.format_acc_no,
            'convert_date': self.convert_date,
            'convert_to_integer': self.convert_to_integer,
            'convert_multipler': self.convert_multipler,
            'convert_acct_multipler': self.convert_acct_multipler,
            'convert_to_demand': self.convert_to_demand,
            'convert_to_usage': self.convert_to_usage,
            'convert_to_currency': self.convert_to_currency,
            'delete_bill': self.delete_bill,
            'noop': self.noop,
            }

        # Initialize object attributes
        if self.budget_billing:
            appdx = self.rec_defs.with_budget
        else:
            appdx = self.rec_defs.without_budget
        self.acc_line_def = self.rec_defs.acct_totals + appdx

        self.on_peak_use = ''
        self.on_peak_chg = ''
        self.on_peak_dmd = ''
        self.off_peak_use = ''
        self.off_peak_chg = ''
        self.off_peak_dmd = ''
        self.total_banked_usage = ''

        self.print_bill = True
        self.bdgt_flg = self.bdgt_msg = ''
        self.meters = []
        self.valid_pers = []
        self.all_accts = DotDict({
            'b_date': '',
            'p_date': '',
            })
        self.counters = DotDict({
            'charge_count': 0,
            'meter_count': 0,
            })
        self.unpack_control(ctrl_text)
        self.cycle_number = ''
        self.get_valid_periods()
        self.reset()

    def __str__(self):
        """Return string representation."""
        return '|'.join(self.account)

    def get_valid_periods(self):
        """Get valid periods because source data has old history sometimes."""
        mths_nml = ('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec')
        mths_rev = list(reversed(mths_nml))
        curr_year = int(self.all_accts.b_date[-4:])
        prior_year = curr_year - 1

        curr_mth = mths_nml[int(self.all_accts.b_date[:2]) - 1]
        mth_ptr = mths_rev.index(curr_mth)
        mth_lbl = mths_rev[mth_ptr:] + mths_rev[:mth_ptr+1]

        yr, py, valid_pers = str(curr_year), str(prior_year), []
        yr_chg_ptr = len(mth_lbl)-mth_ptr-1
        for ptr, month in enumerate(mth_lbl):
            yr = py if ptr >= yr_chg_ptr else yr
            valid_pers.append(f'{yr}{mths_nml.index(month)+1:02}')
        self.valid_pers = valid_pers

    def add_eor(self):
        """Add end fo record marker."""
        if self.eor_required:
            self.account.append('*')

    def convert_multipler(self, mult):
        """Convert to multiplier format which has four decimal places."""
        return self.convert_number(mult, 4)

    def convert_acct_multipler(self, mult):
        """Convert account multiplier first 3 digits & prepended decimal."""
        return f'.{mult[:4]}'

    def convert_to_currency(self, amt):
        """Convert input amount to currency with 'CR' for negative amount."""
        amt = self.convert_number(amt, 2)
        return f'{amt[1:]}CR' if amt[0] == '-' else amt

    def convert_to_demand(self, num):
        """Convert input to number without leading zeros and three decimals."""
        return self.convert_number(num, 3)

    def convert_to_integer(self, num):
        """Convert input reading/usage to number without leading zeros."""
        return self.convert_number(num, 0)

    def convert_to_usage(self, num):
        """Convert input to number without leading zeros and two decimals."""
        return self.convert_number(num, 2)

    def delete_bill(self, flag):
        """
        Bill does not need to be printed.

        A 'Y' in the field indicates and
        electronic bill, which means the bill should not be printed.  Other
        possible values are 'N' for not electronic and 'B' for both types.
        In short: 'Y' means do not print and anything else means print bill.
        """
        self.print_bill = flag != 'Y'
        return flag

    def get_headings(self):
        """Get headings for output."""
        headings = (
            ['BILL_DATE'] +
            ['PEN_DATE'] +
            [x[0] for x in self.rec_defs.master]
            )
        for i in range(1, self.rec_defs.months_of_history+1):
            headings += [x[0].format(i) for x in self.rec_defs.history]
        for i in range(1, self.rec_defs.max_num_charges+1):
            headings += [x[0].format(i) for x in self.rec_defs.charges]
        for i in range(1, self.rec_defs.num_message_lines+1):
            headings += [x[0].format(i) for x in self.rec_defs.messages]
        headings += [x[0] for x in self.acc_line_def]  # rec_defs.acct_totals]

        if self.budget_billing:
            # shift bdgt_msg to end of output if exists
            #  & add column for requested BUDGET BILLING flag
            bdgt_msg = [headings.pop(-2), 'BUDGET BILLING FLAG']
        else:
            bdgt_msg = None

        for i in range(1, self.rec_defs.max_num_meters+1):
            headings += [x[0].format(i) for x in self.rec_defs.meters]

        headings = headings+bdgt_msg if self.budget_billing else headings

        headings = headings + self.rec_defs.custom_headings

        return headings+['EOR'] if self.eor_required else headings

    def reset(self):
        """Reset class data for new record."""
        self.account = [self.all_accts.b_date, self.all_accts.p_date]
        self.meters = []
        self.counters.charge_count = 0
        self.counters.meter_count = 0
        self.bdgt_msg = ''
        self.bdgt_flg = ''
        self.on_peak_use = ''
        self.on_peak_chg = ''
        self.on_peak_dmd = ''
        self.off_peak_use = ''
        self.off_peak_chg = ''
        self.off_peak_dmd = ''
        self.total_banked_usage = ''

    # ------------ unpacking methods ------------

    def append_custom_cols(self):
        """Add custom fields to end of record."""
        self.account.append(self.cycle_number)
        # append on_peak data
        use = int(self.on_peak_use) if self.on_peak_use else ''
        self.account.append(use)
        self.account.append(self.on_peak_chg)
        # append off-peak data
        use = int(self.off_peak_use) if self.off_peak_use else ''
        self.account.append(use)
        self.account.append(self.off_peak_chg)
        total_use = self.add_uses(self.off_peak_use, self.on_peak_use)
        self.account.append(total_use or '')
        total_demand = self.add_dmds(self.off_peak_dmd, self.on_peak_dmd)
        self.account.append(f'{total_demand/1000:.3f}' if total_use else '')
        # append banked usage
        self.account.append(self.total_banked_usage or '')

    def pack_output(self):
        """Add meter & custom fields to end of account output record."""
        # add meter details to end of record
        for meter in self.meters:
            self.account.append(meter)
        # pack columns for missing meters
        for _ in range(
                self.counters.meter_count, self.rec_defs.max_num_meters):
            # pack columns for missing meters
            self.account.extend([''] * len(self.rec_defs.meters))
        self.counters.meter_count = 99
        self.account.append(self.bdgt_msg)  # add bdgt_msg to end of output
        self.account.append(self.bdgt_flg)  # add new accnt budget billing flag
        self.append_custom_cols()
        self.add_eor()  # end of record marker

    def unpack_acc_totals(self, raw_text):
        """Extract file account total details."""
        self.unpack_record(raw_text, self.acc_line_def)

    def unpack_charges(self, raw_text):
        """
        Extract file charges are given one charge per line.

        Except on/off peak charges placed in custom field at end of record.
        """
        if '-PEAK CHARGES' in raw_text:
            chg_specs = self.rec_defs.charges
            chg_name, chg_amt = self.unpack_chg_name_amt(raw_text, chg_specs)
            if chg_name.startswith('ON-'):
                self.on_peak_chg = chg_amt
            else:
                self.off_peak_chg = chg_amt
        else:
            self.unpack_record(raw_text, self.rec_defs.charges)
            self.counters.charge_count += 1

    def unpack_chg_name_amt(self, text, specs):
        """Unpack and return the charge name and amount."""
        return (
            text[specs[0][1]:specs[0][2]].strip(),
            self.cnvt_methods[specs[1][3]](text[specs[1][1]:specs[1][2]])
        )

    def unpack_control(self, raw_text):
        """Extract first line of file that has some details for all records."""
        field = self.rec_defs.cycctl[0]
        self.all_accts.b_date = self.convert_date(raw_text[field[1]:field[2]])
        field = self.rec_defs.cycctl[1]
        self.all_accts.p_date = self.convert_date(raw_text[field[1]:field[2]])

    def unpack_cycle(self, raw_text):
        """Extract the cycle number from last 2 digits of line 1 in file."""
        self.cycle_number = raw_text[-3:].strip()

    def unpack_hist(self, raw_text):
        """Extract file account history which is given one period per line."""
        if raw_text[21:27] not in self.valid_pers or len(set(raw_text[28:37])) == 1:
            # no valid period history info, or no use, set year and month to blank
            self.account.extend([''] * len(self.rec_defs.history))
        else:
            field = self.rec_defs.history[0]
            self.account.append(raw_text[field[1]:field[2]])
            field = self.rec_defs.history[1]
            self.account.append(
                self.rec_defs.months[raw_text[field[1]:field[2]]]
                )
            self.unpack_record(raw_text, self.rec_defs.history[2:])

    def unpack_meter(self, raw_text):
        """Extract file account meter details given one meter per line.

        Except on/off peak useage placed in custom field at end of record.
        """
        # get start and end idices of meter rate field
        meter_def = self.rec_defs.meters
        _ = (meter_def[1][1], meter_def[1][2])
        rate_name = raw_text[_[0]:_[1]].strip()
        use = raw_text[meter_def[6][1]:meter_def[6][2]]
        dmd = raw_text[meter_def[7][1]:meter_def[7][2]]
        b_use = raw_text[meter_def[20][1]:meter_def[20][2]]
        # unpack all meters, test for max when adding meter in unpack_record
        self.unpack_record(raw_text, meter_def, 'meters')
        self.counters.meter_count += 1

        peak_use = rate_name.startswith('R-') or rate_name[:3] in ('RN-', 'RL-', 'RNL')
        if not peak_use:
            # eg: rate codes starting with RC-, RG- (as of Oct 2025)
            return  # are not a 'On/Off Peak kWh Usage' rate code

        if rate_name.endswith('OF') or rate_name.endswith('OFF'):
            # extract off-peak use and demand to custom fields
            self.off_peak_use = use
            self.off_peak_dmd = dmd
        if rate_name.endswith('ON'):
            # extract on-peak use and demand to custom fields
            self.on_peak_use = use
            self.on_peak_dmd = dmd

        # total banked usage of peak-use rates
        bnk_amt = str(self.cnvt_methods['convert_to_usage'](b_use))
        bnk_amt = bnk_amt.replace('.00', '')
        self.total_banked_usage = \
            f'{self.total_banked_usage}/{bnk_amt}' \
            if self.total_banked_usage \
            else bnk_amt

    def unpack_msg(self, raw_text):
        """Extract file messages after padding charge details."""
        for _ in range(
                self.counters.charge_count, self.rec_defs.max_num_charges):
            # pack columns for missing charges
            self.account.extend([''] * len(self.rec_defs.charges))
        self.counters.charge_count = 99
        self.account.append(raw_text[21:].strip())

    def unpack_mstr(self, raw_text):
        """Extract file account master details."""
        self.unpack_record(raw_text, self.rec_defs.master)

    def unpack_record(self, raw_text, specs, buffer='account'):
        """Unpack data from input and append to account field list."""
        for field in specs:
            field_val = raw_text[field[1]:field[2]]
            tmp = self.cnvt_methods[field[3]](field_val) \
                if field[3] else field_val.strip()
            if buffer == 'account':
                tmp_has_val = isinstance(tmp, int) \
                    or ('CR' not in tmp and tmp != '0.00')
                if field[0] == 'BUDGET_AR_AMT' and tmp_has_val:
                    # set new budget billing flag
                    self.bdgt_flg = 'BUDGET BILLING'
                if field[0] != 'BUDGET_BILL_MSG':
                    # so EBILL_SW stay in same column in output
                    self.account.append(tmp)
                else:
                    # save message to add to end of output
                    self.bdgt_msg = tmp
            elif self.counters.meter_count < self.rec_defs.max_num_meters:
                self.meters.append(tmp)

    # -------------- static methods ---------------

    @staticmethod
    def add_uses(val1, val2):
        """Add two string values that may be nulls."""
        return (int(val1) if val1 else 0) + (int(val2) if val2 else 0)

    @staticmethod
    def add_dmds(val1, val2):
        """Add two string values that may be nulls."""
        return (float(val1) if val1 else 0) + (float(val2) if val2 else 0)

    @staticmethod
    def convert_date(raw_date):
        """Convert ISO date to standard US date format."""
        bill_date_parts = {
            'mth': raw_date[4:6],
            'day': raw_date[6:8],
            'year': raw_date[:4]
            }
        return '{mth}/{day}/{year}'.format(**bill_date_parts)

    @staticmethod
    def convert_number(num, precision):
        """
        Convert input string to number with 'precision' decimal places.

        (with possible leading sign)
        """
        num = num[1:] if num[:2] == '0-' else num  # handle neg use like 0-7
        num_sign = num[0] if num[0] in '+-' else None
        fmt = '{:0' + str(precision + 1) + '}'  # +1 for digit before decimal
        _ = 1 if num_sign else 0
        num = fmt.format(int(num[_:])).strip()  # removes leading zeros
        if num == '0' and precision > 0:
            num = '0.' + ('0' * precision)
        elif precision > 0:
            num = f'{num[:-precision]}.{num[-precision:]}'
        return f'-{num}' if num_sign == '-' else num

    @staticmethod
    def format_acc_no(raw_text):
        """Format raw account number to Heber Light & Power requirements."""
        return raw_text[2:]

    @staticmethod
    def noop(raw_text):
        """
        Do nothing to handle blank lines.

        (only way I could get it to work).
        """
        return raw_text
