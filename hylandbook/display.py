import datetime
import os
import subprocess
import sys
import time
from typing import Any




def msg(msg: str | Any = '', /, start: str = '', end: str = '\n', ts: bool = False, ts_fmt: str = '%H:%M:%S.%f', delay: float = 0) -> None:
    if delay > 0:
        time.sleep(delay)

    if ts:
        msg = f"[{datetime.datetime.now().strftime(ts_fmt)}] {msg}"

    sys.stdout.write(f"{start}{msg}{end}")
    sys.stdout.flush()


def clear() -> None:
    if os.name == 'nt':
        subprocess.run(['cls'], shell=True)
    elif os.name == 'posix':
        subprocess.run(['/usr/bin/clear'], shell=True)
    else:
        print('\033c', end='')
