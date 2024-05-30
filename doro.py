import argparse
import atexit
import msvcrt
import os
import random
import sys
import time
import threading
import sqlite3

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

script_dir = os.path.dirname(os.path.abspath(__file__))
SHIONLAUGH = os.path.join(script_dir, 'Shion Laugh.wav')

class TimeSaver:
    def __init__(self):
        self.con = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'worktime.db'))
        cur = self.con.cursor()
        res = cur.execute("SELECT name FROM sqlite_master WHERE name='worktime'")
        if res.fetchone() is None:
            cur.execute("CREATE TABLE worktime (date_ended, time_elapsed)")
    
    def save_time(self, time_elapsed):
        if time_elapsed <= 60:
            return
        cur = self.con.cursor()
        cur.execute("INSERT INTO worktime (date_ended, time_elapsed) VALUES(?, ?)", (time.time(), time_elapsed))
        self.con.commit()

class TimeMeasurer:
    def __init__(self, work_minutes, rest_minutes):
        self.past = time.time()
        self.now = time.time()
        self.delta = 0
        
        self.paused = False
        
        self.working_sum = 0

        self.elapsed_time = 0
        self.exceeded = 0
        self.wexceed_time = work_minutes * 60
        self.rexceed_time = rest_minutes * 60
        
        self.time_saver = TimeSaver()

    def get_delta(self):
        if not self.paused:
            self.now = time.time()
        self.delta = self.now - self.past
        self.past = self.now
        return self.delta
    
    def is_exceed(self, work):
        if (work and self.elapsed_time >= self.wexceed_time * (self.exceeded + 1)) or (not work and self.elapsed_time >= self.rexceed_time * (self.exceeded + 1)):
            self.exceeded += 1
            return True
        return False
    
    def pause(self):
        self.paused = True
        
    def unpause(self):
        self.paused = False
        self.past = time.time()
        self.now = time.time()
    
    def update_elapsed_time(self):
        self.elapsed_time += self.get_delta()
    
    def end(self, work):
        if work:
            self.working_sum += self.elapsed_time
            self.time_saver.save_time(self.working_sum)
        self.elapsed_time = 0
        self.exceeded = 0
    
    def reset(self):
        self.elapsed_time = 0
        self.exceeded = 0
    
    def subtract(self, minutes):
        self.elapsed_time -= minutes * 60
        self.elapsed_time = max(self.elapsed_time, 0)
    
    def add(self, minutes):
        self.elapsed_time += minutes * 60

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
    return "WORK" if work else "REST"

def cls():
    os.system('cls' if os.name=='nt' else 'clear')
    pass
    
def timetostr(time, secs=True):
    hours, rem = divmod(time, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{int(hours):0>2}:{int(minutes):0>2}{f':{seconds:02.0f}' if secs else ''}"

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
        import win32api
        hwnd = win32gui.GetForegroundWindow()
        (left, top, right, bottom) = win32gui.GetWindowRect(hwnd)
        win32gui.SetWindowPos(hwnd,win32con.HWND_NOTOPMOST, left, top, right-left, bottom-top,0)
        
        lStyle = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE);
        lStyle |= (win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_MINIMIZEBOX | win32con.WS_MAXIMIZEBOX | win32con.WS_SYSMENU);
        win32api.SetWindowLong(hwnd, win32con.GWL_STYLE, lStyle);

def toggle_titlebar():
    lStyle = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE);
    lStyle ^= (win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_MINIMIZEBOX | win32con.WS_MAXIMIZEBOX | win32con.WS_SYSMENU);
    win32api.SetWindowLong(hwnd, win32con.GWL_STYLE, lStyle);
    return bool(lStyle & win32con.WS_CAPTION)

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
        
        import win32gui
        import win32api
        import win32con
        # screen_w, screen_h = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN), win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        # print(screen_w, screen_h)
        hwnd = win32gui.GetForegroundWindow()
        (left, top, right, bottom) = win32gui.GetWindowRect(hwnd)
        win32gui.SetWindowPos(hwnd,win32con.HWND_TOPMOST, left, top, 360, 170,0)
        
        lStyle = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE);
        lStyle &= ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_MINIMIZEBOX | win32con.WS_MAXIMIZEBOX | win32con.WS_SYSMENU);
        win32api.SetWindowLong(hwnd, win32con.GWL_STYLE, lStyle);

    cls()
    

    done = False
    work = True    
    
    status_str = None
    status_time = 0
    
    prev_key = None
    
    tm = TimeMeasurer(args.work_minutes, args.rest_minutes)
    

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
        time.sleep(1/24)
        tm.update_elapsed_time()
        
                    
        cprint(f'\r{cc.WORK if work else cc.REST}{wstr()}{cc.ENDC} {cc.PURPLE}{timetostr(tm.elapsed_time)} {(cc.BGGRAY+f"✔{tm.exceeded}") if tm.exceeded else ""}')
        sys.stdout.flush()
        
        if tm.is_exceed(work):
            playsound(SHIONLAUGH, False)
            
        while msvcrt.kbhit():
            key = msvcrt.getch()
            
            while True:
                if key == b'\r' or args.auto and exceeded:
                    tm.end(work)
                    work = not work
                    
                    cprint(f"Switching to {wstr()}\n")
                    set_status()
                    print(asciiwork if work else asciirest)
                try:
                    key_str = key.decode("utf-8")
                except:
                    key_str = ""
                is_key_num = key_str.isnumeric()
                
                # TODO turn key prev_key pattern into something else
                if key == b'd':
                    set_status(cc.YELLOW +"Dice Number (0-9)")
                
                if prev_key == b'd' and is_key_num:
                    num = int(key_str)
                    if num == 0: num = 10
                    if num == 1: num = 11
                    set_status(f"D{num} = {random.randint(1, num)}", 15)
                elif prev_key == b'd' and key != b'd':
                    set_status()
                
                if key == b'-':
                    set_status(cc.YELLOW +"Subtract Minutes (0-9)")
                
                if prev_key == b'-' and is_key_num:
                    num = int(key_str)
                    if num == 0: num = 10
                    set_status(f"Subtracted {num}", 5)
                    tm.subtract(num)
                elif prev_key == b'-' and key != b'-':
                    set_status()
                
                if key == b'+':
                    set_status(cc.YELLOW +"Add Minutes (0-9)")
                
                if prev_key == b'+' and is_key_num:
                    num = int(key_str)
                    if num == 0: num = 10
                    set_status(f"Added {num}", 5)
                    tm.add(num)
                elif prev_key == b'+' and key != b'+':
                    set_status()

                
                if key == b's':
                    set_status(cc.YELLOW + "Set time for (w)ork or (r)rest")
                    # TODO
                
                if prev_key == b's':
                    if key == b'w':
                        pass
                    else:
                        set_status()
                
                if key == b'p':
                    if tm.paused:
                        tm.unpause()
                        set_status()
                    else:
                        tm.pause()
                        set_status(cc.BGGRAY + cc.BLUE + "Paused")
                        
                if key == b'r':
                    tm.reset()
                    set_status(cc.RED + "RESET", 5.0)
                
                if key == b't':
                    toggle_always_on_top()
                    set_status(cc.BLUE + f'Always On Top ({"ON" if always_on_top else "OFF"})', 5.0)
                
                if key == b'm':
                    is_title_on = toggle_titlebar()
                    set_status(cc.BLUE + f'Title Bar ({"ON" if is_title_on else "OFF"})', 5.0)
       
                if key == b'?':
                    set_status(f"work {args.work_minutes} rest {args.rest_minutes}", 5.0)
                
                if key == b'.':
                    set_status(f"Worked for {timetostr(tm.working_sum + (tm.elapsed_time if work else 0))}", 5.0)
                
                if key == b'x':
                    cls()
                    print(asciiwork if work else asciirest)

                if key == b'q':
                    done = True
                    tm.end(work)
                
                prev_key = key
                break
    
        if status_str and status_time > 0:
            status_time -= tm.delta
            if status_time > 0:
                cprint(status_str)
            else:
                cprint(' ' * len(strip_ANSI(status_str)))
        
    print(f"\n\nWorked for {timetostr(tm.working_sum)}")