"""
Program dispatches given file to the appropriate program module.

I this program given a filename with an -f argument it processes the given file.
If program called without a filename it monitors the given file directory and
respond to files created in that directory.

If called with -d aurgument the given directory will be monitored, otherwise the
the default utils.FILE_PATH directory will be monitored.


Based on https://pypi.org/project/watchdog/ and
http://brunorocha.org/python/watching-a-directory-for-file-changes-with-python.html
"""


import argparse
import os
import sys
import time
import contextlib

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

import app_modules.utilities as utils


WATCH_ME = utils.FILE_PATH


def dispatch_file(filename: str):
    """Dispatch the file to the appropriate program module."""
    cname, fname, ftype, nname, _ = utils.parse_filename_new(filename)
    utils.logger.info('*' * 80)
    utils.logger.info('Processing file "%s"', fname)
    prep = 'an' if cname[0] in ('a', 'e', 'i', 'o', 'u') else 'a'
    utils.logger.info(
        'IDed as %s "%s" file of type "%s"',
        prep, cname, ftype)
    if fname == nname:
        # parse_filename may have created new file with corrected name
        # if so, skip this process, program will delete old file below
        # detect the creation of the new file and process it
        if cname == 'hlap':
            program = ('src/pdf_bill_indexing/hlap_pdf_idx'
                        if ftype == 'pdf'
                        else 'transforms/hlap_cnvrt')
        elif 'dupes' in fname.lower():
            program = 'src/dupes_sorting/sort_multiples'
        else:  # try processing as specialized transform
            program = 'src/transforms/transform_file'
        prob = os.system(f'\
            py {program}.py \
            -n {cname} \
            -t {ftype} \
            -f "{fname}" \
            -p "{WATCH_ME}"\
            ')
    else:
        # rename file for easier processing later
        time.sleep(5)  # give time to release file
        try:
            utils.logger.info('Renaming "%s" to "%s" in "%s"', fname, nname, WATCH_ME)
            os.rename(f'{WATCH_ME}{fname}', f'{WATCH_ME}{nname}')
        except PermissionError:
            utils.logger.info('Error renaming "%s" to "%s" in "%s"', fname, nname, WATCH_ME)
            utils.logger.info('%s', sys.exc_info())
            prob = True
        prob = False

    with contextlib.suppress(FileNotFoundError):
        if os.path.exists(fname):
            if not prob:
                # leave file behind if there is a problem
                utils.logger.info('Deleting "%s" to cleanup.', fname)
                os.remove(f'{WATCH_ME}{fname}')
            else:
                # archive the source file if there is a problem
                utils.logger.info('Archiving "%s" for analysis.', fname)
                os.rename(
                    f"{WATCH_ME}{fname}",
                    f"{'/'.join(WATCH_ME.split('/')[:-2])}/archive/{fname}"
                    )


class MyHandler(PatternMatchingEventHandler):
    """Capture created file in directory & process it."""
    def on_created(self, event):
        """Process created file."""
        if [x for x in utils.IGNORE if x in event.src_path]:
            return
        dispatch_file(event.src_path)


def watch_directory(directory=WATCH_ME):
    """Watch directory for file changes."""
    observer = Observer()
    observer.schedule(MyHandler(), path=directory, recursive=False)
    observer.start()
    utils.logger.info('Watching "%s"', WATCH_ME)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
    observer.stop()
    observer.join()


def parse_user_input(desc='Dispatch files to be processed to the appropriate program.'):
    """
    Parse user input for optional directory to monitor or file to dispatched.
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '-f', action='store', dest='file_name', default='',
        help='name of file to be distached for processing.')
    parser.add_argument(
        '-d', action='store', dest='watch_dir', default='',
        help='path to directory to be monitored.')
    return parser


if __name__ == '__main__':
    options = parse_user_input().parse_args()
    if options.file_name:  # dispatch given file
        dispatch_file(options.file_name)
    else:  # watch given directory or default directory
        watch_directory(options.watch_dir or utils.FILE_PATH)
