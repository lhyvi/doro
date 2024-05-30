import os
import time
import sqlite3
import datetime
import argparse

class TimeReader:
    def __init__(self):
        self.con = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'worktime.db'))
        cur = self.con.cursor()
        res = cur.execute("SELECT name FROM sqlite_master WHERE name='worktime'")
        if res.fetchone() is None:
            cur.execute("CREATE TABLE worktime (date_ended, time_elapsed)")
    
    def read_latest(self):
        cur = self.con.cursor()
        res = cur.execute("SELECT * FROM worktime ORDER BY date_ended DESC LIMIT 1")
        dt = res.fetchone()
        if dt:
            print(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(dt[0])), "- ", time.strftime("%H:%M:%S", time.gmtime(dt[1])))
            
        self.con.commit()
    
    def read_from_timestamp(self, time_start):
        time_end = time_start + 86400
        cur = self.con.cursor()
        res = cur.execute("SELECT * FROM worktime WHERE date_ended >= ? AND date_ended <= ? ORDER BY date_ended DESC",(time_start, time_end))
        fetch = res.fetchall()
        return fetch
        if fetch == None or fetch == []:
            print("NONE")
            return
        for dt in fetch:
            print(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(dt[0])), "- ", time.strftime("%H:%M:%S", time.gmtime(dt[1])))
    
    def read_datestr(self, date): # date in YYYY/MM/DD format
        time_start = time.mktime(datetime.datetime.strptime(date, "%Y/%m/%d").timetuple())
        return self.read_from_timestamp(time_start)
    
    def read_today(self):
        dt = datetime.datetime.now()
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        time_start = dt.timestamp()
        return self.read_from_timestamp(time_start)
    
    def read_datetime(self, datetime):
        dt = datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        time_start = dt.timestamp()
        return self.read_from_timestamp(time_start)
        
    def heat_map(self):
        blocks = "-░▒▓█"
        date = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month = date.month
        print_offset = date.weekday()
        
        sums = []
        while date.month == month:
            s = sum(x[1] for x in self.read_datetime(date))
            sums.append(s)
            date += datetime.timedelta(days=1)
        
        m = max(sums)
        
        print("SMTWTFS")
        print(" " * print_offset, end='')
        for s in sums:
            i = 0 if s <= 0 else max(int(s / m * (len(blocks) - 1)), 1)
            print(blocks[i],end='')
            print_offset = (print_offset + 1) % 7
            if print_offset == 0:
                print()
        
        print()
        print("\nHours Worked This Month", sum(sums) / 60 / 60)
    
    def heat_week(self):
        blocks = "-░▒▓█"
        date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        date -= datetime.timedelta(days=date.weekday())
        
        sums = []
        while True:
            s = sum(x[1] for x in self.read_datetime(date))
            sums.append(s)
            date += datetime.timedelta(days=1)
            if date.weekday() == 0:
                break
        
        m = max(sums)
        print("SMTWTFS")
        for s in sums:
            i = 0 if s <= 0 else max(int(s / m * (len(blocks) - 1)), 1)
            print(blocks[i],end='')
        
        print()
        print("\nHours Worked This Week", sum(sums) / 60 / 60)
        
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--month", help='Show month heatmap', action="store_true")
    parser.add_argument("-w", "--week", help='Show week heatmap', action="store_true")
    parser.add_argument("-t", "--today", help='Show todays work', action="store_true")

    args = parser.parse_args()

    time_reader = TimeReader()
    
    if args.month:
        time_reader.heat_map()
        print()
    if args.week:
        time_reader.heat_week()
        print()
    if args.today:
        print("Minutes Worked Today:", sum(x[1] for x in time_reader.read_today()) // 60)