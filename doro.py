import argparse
import atexit
import msvcrt
import os
import random
import sys
import time
import threading
from playsound import playsound

class cc: # cc as in console colors
    BLACK = '\033[90m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ORANGE = '\033[38;5;208m';
    BGGRAY = '\033[48;5;237m'
    
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    HIDECURSOR = '\033[?25l'
    SHOWCURSOR = '\033[?25h'
    INVERSE = '\033[7m'
    ENDC = f'\033[0m{HIDECURSOR}'
    
    ERASELINE = f'\033[2K'
    
    INA = '\033[38;5;63m'
    IINA = '\033[38;5;63m\033[48;5;210m'
    WORK = f'{IINA}{BOLD}{INVERSE}'
    REST = f'{IINA}{BOLD}'

class SoundPlayer(threading.Thread):
    def __init__(self, sound_path):
        self._sound_path = sound_path
    def play(self, sound_path=None):
        if sound_path is None:
            sound_path = self._sound_path
        threading.Thread(target=playsound, args=[sound_path]).start()
    

    
SHIONLAUGH = "C:/CS/Shion Laugh.wav"

# ascii from https://patorjk.com/software/taag/

asciiwork = f"""{cc.WORK}
░  ░░░░  ░░░      ░░░       ░░░  ░░░░  ░
▒  ▒  ▒  ▒▒  ▒▒▒▒  ▒▒  ▒▒▒▒  ▒▒  ▒▒▒  ▒▒
▓        ▓▓  ▓▓▓▓  ▓▓       ▓▓▓     ▓▓▓▓
█   ██   ██  ████  ██  ███  ███  ███  ██
█  ████  ███      ███  ████  ██  ████  █
{cc.ENDC}
"""

asciirest = f"""{cc.REST}
░       ░░░        ░░░      ░░░        ░
▒  ▒▒▒▒  ▒▒  ▒▒▒▒▒▒▒▒  ▒▒▒▒▒▒▒▒▒▒▒  ▒▒▒▒
▓       ▓▓▓      ▓▓▓▓▓      ▓▓▓▓▓▓  ▓▓▓▓
█  ███  ███  ██████████████  █████  ████
█  ████  ██        ███      ██████  ████
{cc.ENDC}
"""

def cprint(*argv):
    sys.stdout.write(cc.ENDC)
    for arg in argv:
        if not isinstance(arg, str):
            arg = str(arg)
        sys.stdout.write(arg)
        #print(color, *argv, cc.ENDC)
    sys.stdout.write(cc.ENDC)

def wstr():
    return "WORK" if work else "RESTING"

def cls():
    os.system('cls' if os.name=='nt' else 'clear')
    pass
    
def timetostr(time, secs=True):
    hours, rem = divmod(time, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{int(hours):0>2}:{int(minutes):0>2}{f':{seconds:05.2f}' if secs else ''}"

import re
strip_ANSI_pat = re.compile(r"""
    \x1b     # literal ESC
    \[       # literal [
    [;\d]*   # zero or more digits or semicolons
    [A-Za-z] # a letter
    """, re.VERBOSE).sub

def strip_ANSI(s):
    return strip_ANSI_pat("", s)

def exit_handler():
    if os.name == 'nt':
        import win32gui
        import win32con
        hwnd = win32gui.GetForegroundWindow()
        (left, top, right, bottom) = win32gui.GetWindowRect(hwnd)
        win32gui.SetWindowPos(hwnd,win32con.HWND_NOTOPMOST, left, top, right-left, bottom-top,0)

always_on_top = True

def toggle_always_on_top():
    if os.name == 'nt':
        global always_on_top
        always_on_top = not always_on_top
        import win32gui
        import win32con
        hwnd = win32gui.GetForegroundWindow()
        (left, top, right, bottom) = win32gui.GetWindowRect(hwnd)
        win32gui.SetWindowPos(hwnd,win32con.HWND_TOPMOST if always_on_top else win32con.HWND_NOTOPMOST, left, top, right-left, bottom-top,0)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Doro',
        description='A tui implementation of a pomodoro timer',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('work_minutes', nargs='?', type=int, default=25,
                help='Amount of minutes in work mode before sound plays')
    parser.add_argument('rest_minutes', nargs='?', type=int, default=5,
                help='Amount of minutes in rest mode before sound plays')
    parser.add_argument('-a', '--auto', action='store_true',
                help='Automatically switch modes when time exceeds set minutes')

    args = parser.parse_args()

    if os.name == 'nt':
        atexit.register(exit_handler)
        os.system("title DORO TIME")
        #os.system("color f5")
        
        import win32gui
        import win32con

        hwnd = win32gui.GetForegroundWindow()
        (left, top, right, bottom) = win32gui.GetWindowRect(hwnd)
        win32gui.SetWindowPos(hwnd,win32con.HWND_TOPMOST, left, top, 600, 600,0)
    cls()
    

    done = False

    past = time.time()
    now = time.time()
    work = True
    paused = False
    
    working_sum = 0

    elapsed_time = 0
    exceeded = False
    wexceed_time = args.work_minutes * 60
    rexceed_time = args.rest_minutes * 60
    
    
    status_str = None
    status_time = 0
    
    prev_key = None
    
    shion_sound = SoundPlayer(SHIONLAUGH)
    

    def set_status(new_status="", time=float('inf')):
        global status_str
        if status_str:
            cprint(cc.ERASELINE)
        if not isinstance(new_status, str):
            new_status = str(new_status)
        status_str = new_status + cc.ENDC
        global status_time
        status_time = time
    
    print(asciiwork if work else asciirest)
    while not done:
        time.sleep(1/10)
        delta = now - past
        elapsed_time += delta
        past = now
        
        if not paused:
            now = time.time()
            
        cprint(f'\rNOW {cc.WORK if work else cc.REST}{wstr()}{cc.ENDC} : {cc.PURPLE}{timetostr(elapsed_time)} {(cc.BGGRAY+"✔") * exceeded}')
        sys.stdout.flush()
        
        if not exceeded and ((work and elapsed_time >= wexceed_time) or (not work and elapsed_time >= rexceed_time)):
            shion_sound.play()
            exceeded = True
            
        if msvcrt.kbhit():
            key = msvcrt.getch()
            
            while True:
                if key == b'\r' or args.auto and exceeded:
                    work = not work
                    working_sum += elapsed_time
                    
                    elapsed_time = 0
                    exceeded = False
                    
                    cprint(f"Switching to {wstr()}\n")
                    set_status()
                    print(asciiwork if work else asciirest)
                
                if key == b'd':
                    set_status(cc.YELLOW +"Give Random Dice Number 0-9")
                
                if prev_key == b'd' and key.decode("utf-8").isnumeric():
                    num = int(key.decode("utf-8"))
                    if num == 0: num = 10
                    set_status(f"D{num} = {random.randint(1, num)}", 15)
                elif prev_key == b'd' and key != b'd':
                    set_status()
                
                if key == b's':
                    set_status(cc.YELLOW + "Set time for (w)ork or (r)rest")
                
                if prev_key == b's':
                    if key == b'w':
                        pass
                    else:
                        set_status()
                
                if key == b'p':
                    paused = not paused
                    if paused:
                        set_status(cc.BGGRAY + cc.BLUE + "Paused")
                    else:
                        set_status()
                    if not paused:
                        now = time.time()
                        past = now
                        
                if key == b'r':
                    elapsed_time = 0
                    exceeded = False
                    set_status(cc.RED + "RESET", 5.0)
                
                if key == b't':
                    toggle_always_on_top()
                    set_status(cc.BLUE + f"Always On Top Toggled ({always_on_top})", 5.0)
       
                if key == b'?':
                    set_status(f"work {args.work_minutes} rest {args.rest_minutes}", 5.0)
                

                if key == b'q':
                    done = True
                    if work:
                        working_sum += elapsed_time
                
                prev_key = key
                break
    
        if status_str and status_time > 0:
            status_time -= delta
            if status_time > 0:
                cprint(status_str)
            else:
                cprint(' ' * len(strip_ANSI(status_str)))
        
    print(f"\n\nWorked for {timetostr(working_sum)}")