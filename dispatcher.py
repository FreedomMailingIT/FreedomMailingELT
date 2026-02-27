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
import contextlib
import os
from pathlib import Path
import subprocess
import sys
import time

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

import app_modules.utilities as utils


WATCH_ME = utils.FILE_PATH


#-----------------Setup------------------

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


#--------------------Processing-----------------

def build_command(program: str, cname: str, ftype: str, fname: str, watch_dir: str) -> list[str]:
    """Contruct the progam call with associated arguments."""
    # cmd = f'python ./src/{program}.py -n {cname} -t {ftype} -f "{fname}" -p "{watch_dir}"'
    cmd = [
        "python",
        f"./src/{program}.py",
        "-n", cname,
        "-t", ftype,
        "-f", fname,
        "-p", watch_dir,
    ]
    return cmd


def handle_processed_file(fname: str, prob: bool, watch_dir: str) -> None:
    """Delete the file if processed successfully (prob=False), or archive it one
    directory above watch_dir if there was a problem (prob=True).
    Missing files are silently ignored.
    """
    watch_path = Path(watch_dir)
    src = watch_path / fname
    with contextlib.suppress(FileNotFoundError):
        if prob:
            utils.logger.info('Archiving "%s" for analysis.', fname)
            archive_dir = watch_path.parent / "archive"
            archive_dir.mkdir(exist_ok=True)
            src.rename(archive_dir / fname)
        else:
            utils.logger.info('Deleting "%s" to cleanup.', fname)
            src.unlink()


def log_dispatch_msg(fname: str, cname: str, ftype: str) -> None:
    """Log what dispatcher is about to do."""
    utils.logger.info('*' * 80)
    utils.logger.info('Processing file "%s"', fname)
    prep = 'an' if cname[0] in 'aeiou' else 'a'
    utils.logger.info('IDed as %s "%s" file of type "%s"', prep, cname, ftype)


def rename_file(old: str, new: str) -> bool:
    """Rename file for easier processing."""
    time.sleep(5)
    try:
        utils.logger.info('Renaming "%s" to "%s" in "%s"', old, new, WATCH_ME)
        os.rename(f'{WATCH_ME}{old}', f'{WATCH_ME}{new}')
        return True
    except PermissionError:
        utils.logger.info('Error renaming "%s" to "%s" in "%s"', old, new, WATCH_ME)
        utils.logger.info('%s', sys.exc_info())
        return False


def select_program(cname: str, fname: str, ftype: str) -> str:
    """Select which program to call based on filename."""
    if cname == 'hlap':  # specialized hlap programs
        return ('pdf_bill_indexing/hlap_pdf_idx'
                if ftype == 'pdf' else 'transforms/hlap_cnvrt')
    if 'dupes' in fname.lower():
        return 'dupes_sorting/sort_multiples'
    return 'transforms/transform_file'  # if not hlap or dupes then look for transform


#-----------------------Dispatcher for auto processing--------------------
def dispatch_file(filename: str):
    """When new file added to watch directory, decide what to do with it."""
    cname, fname, ftype, nname, _ = utils.parse_filename_new(filename)
    log_dispatch_msg(fname, cname, ftype)
    if fname == nname:
        program = select_program(cname, fname, ftype)
        command = build_command(program, cname, ftype, fname, WATCH_ME)
        utils.logger.debug('Invoking: %s', ' '.join(command))
        result = subprocess.run(command, check=False)
        prob = result.returncode
    else:
        success = rename_file(fname, nname)
        prob = not success

    handle_processed_file(fname, prob, WATCH_ME)


#-----------------Single file request for testing----------------
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
