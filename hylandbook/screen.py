import datetime
import os
import subprocess
import sys
import time




class Screen:
    @staticmethod
    def clear() -> None:
        if os.name == 'nt':
            subprocess.run(['cls'], shell=True)
        elif os.name == 'posix':
            subprocess.run(['/usr/bin/clear'], shell=True)
        else:
            print('\033c', end='')


    @staticmethod
    def prompt_to_exit(exit_code: int = 0, /) -> None:
        input("\npress [Enter] to exit")
        sys.exit(exit_code)


    @staticmethod
    def msg(msg: str = '', /, start: str = '', end: str = "\n", level: int = 0, level_indent: int = 4, sleep: float = 0, sleep_cd: bool = True, ts: bool = False) -> None:
        if level > 0:
            msg = f"{' ' * (level * level_indent)}{msg}"

        if ts:
            msg = f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')}] {msg}"

        if sleep <= 0:
            sys.stdout.write(f'{start}{msg}{end}')
            sys.stdout.flush()
        else:
            until: float = time.time() + sleep

            while time.time() <= until:
                if not sleep_cd:
                    frame: str = f"{start}{msg} "
                else:
                    frame: str = f"{start}{msg} {int(until - time.time())}s "

                sys.stdout.write(frame)
                sys.stdout.flush()

                time.sleep(1)

                sys.stdout.write('\b' * len(frame))

            sys.stdout.write(end)
            sys.stdout.flush()
