"""Check if required background programs for FreedomMailingETL are running."""


import subprocess
import os


# use subprocess to get output of program status list
PS_OUT = subprocess.check_output(['ps', '-eaf']).decode('utf-8')

# should already be in FreedomMailingETL directory
UV_RUN = '/home/operations/.local/bin/uv run'
if 'dropbox' not in PS_OUT:
    print('Starting Dropbox monitoring')
    os.system(f'{UV_RUN} ../dropbox.py start &')
if 'hlp_monitor_sftp.py' not in PS_OUT:
    print('Starting Heber Light & Power SFTP monitoring')
    os.system(f'{UV_RUN} /home/hlap/.monitor/hlp_monitor_sftp.py &')
if 'dispatcher.py' not in PS_OUT:
    print('Starting FreedomMailingETL monitoring of Dropbox directory.')
    os.system(f'{UV_RUN} dispatcher.py &')
