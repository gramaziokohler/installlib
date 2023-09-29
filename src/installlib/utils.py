import os
import subprocess


def start_command(command):
    subprocess.check_call(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=subprocess.STARTUPINFO(),
        env=os.environ,
    )
