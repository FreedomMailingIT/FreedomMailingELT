"""Check if required background programs for FreedomMailingETL are running.

Initiate program from the project directory (FreedomMailingETL).
"""


import subprocess
import shlex


# use subprocess to get output of program status list
PS_OUT = subprocess.check_output(['ps', '-eaf']).decode('utf-8')

UVR = 'uv run'
if 'dropbox' not in PS_OUT:
    print('Starting Dropbox monitoring')
    subprocess.Popen(shlex.split(UVR) + ['../dropbox.py', 'start'])

if 'hlp_monitor_sftp.py' not in PS_OUT:
    print('Starting Heber Light & Power SFTP monitoring')
    subprocess.Popen(shlex.split(UVR) + ['/home/hlap/.monitor/hlp_monitor_sftp.py'])

if 'dispatcher.py' not in PS_OUT:
    print('Starting FreedomMailingETL monitoring of Dropbox directory.')
    subprocess.Popen(shlex.split(UVR) + ['dispatcher.py'])
