#!/usr/bin/env python3
import os, stat
import datetime
import sys

'''
用来统计在任务运行期间， CPU 被任务（和其它进程）使用的情况。
'''

# 包含 task_list 中字符串的任务会被认为是超算任务
# 其它会被归类为「其它任务」
task_list = ['graph500_reference_bfs']

def eprint(s, *args, **kwargs):
    ''' a error print function '''
    print("[ Warning ] " + s, *args, file=sys.stderr, **kwargs)

# "ps -aux" -> list of ProcRecord
class ProcRecord:
    def __init__(self):
        self.records = []

    # Override existing repr
    def __repr__(self):
        return str(self.records)

    def addRecord(self, user, pid, cpu_usage, mem_usage, command):
        # Check if it is in task_list
        in_task_list = False
        for i in task_list:
            if command.find(i) != -1:
                in_task_list = True
                break
            
        tmp = {
           'user'         : user,
           'pid'          : pid,
           'cpu_usage'    : float(cpu_usage), 
           'mem_usage'    : float(mem_usage),
           'command'      : command,
           'in_task_list' : in_task_list
        }
        self.records.append(tmp)
    
    # Get usage for processes
    def getUsage(self):
        cpu_tasks = 0.0
        cpu_nontasks = 0.0
        cpu_total = 0.0
        total_count = 0
        total_tasks_running = 0

        for i in self.records:
            cpu_total = cpu_total + i['cpu_usage']
            if i['in_task_list']:
                cpu_tasks = cpu_tasks + i['cpu_usage']
                total_tasks_running = total_tasks_running + 1
            else:
                cpu_nontasks = cpu_nontasks + i['cpu_usage']
            total_count = total_count + 1
        
        return {
            'total_tasks_running' : total_tasks_running,
            'total_count'         : total_count,
            'cpu_total'           : cpu_total, 
            'cpu_tasks'           : cpu_tasks,
            'cpu_nontasks'        : cpu_nontasks
        }

class RecordParser:
    def __init__(self, dirname, record_callback):
        self.dirname = dirname
        self.record_callback = record_callback

    def parseDate(self, s):
        time_str = s.split('_')[1].split('.')[0]
        year = int(time_str[:4])
        month = int(time_str[4:6])
        day = int(time_str[6:8])
        hour = int(time_str[9:11])
        minute = int(time_str[11:13])
        second = int(time_str[13:15])
        return datetime.datetime(year, month, day, hour, minute, second)

    # Check if valid, currently we only check if it ends in '.txt'
    def checkName(self, s):
        return s[-4:] == '.txt'

    def parseHostname(self, s):
        return s.split('_')[0]

#'USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\n'
    def parse(self):
        for i in os.listdir(self.dirname):
            pathname = os.path.join(self.dirname, i) # Full path
            mode = os.stat(pathname).st_mode
            if stat.S_ISDIR(mode):
                eprint("Got folder %s, ignored" % (pathname))
            elif stat.S_ISREG(mode):
                # Good, take it in
                if not self.checkName(i):
                    eprint("Ignored %s, for checkName() failed" % i)
                    continue
                rec_time = self.parseDate(i)
                hostname = self.parseHostname(i)

                with open(pathname, "r") as f:
                    # Merely discarding first line will fall for testcase no. 10009
                    # f.readline() # Discard first line
                    for pre_line in f:
                        if pre_line[:4] == "USER":
                            break

                    for line in f:
                        li = line.split()
                        # join cmd with args together (might be wrong, eg with "")
                        ss = ""
                        for m in li[10:]:
                            ss = ss + m + " "
                        self.record_callback(hostname, rec_time, li[0], li[1], li[2], li[3], ss)
            else:
                raise Exception("Something wrong!")


class ProcRecordSeries():
    def __init__(self, hostname):
        self.hostname = hostname
        self.series = {}

    def getPage(self, rec_time):
        if self.series.get(rec_time) == None: # No such record
            self.series[rec_time] = ProcRecord()
        return self.series[rec_time]
    
    def printAll(self):
        print(self.series)

    def showStat(self):
        ''' Show statistics per page, and others '''
        print("Time\tTasks\tTotal\tPercentage")

        for pair in sorted(self.series.items()):
            dic = pair[1].getUsage()
            print("%s\t%f\t%f\t%f\t" % (str(pair[0]), 
                dic['cpu_tasks'], dic['cpu_total'], 
                dic['cpu_tasks'] / dic['cpu_total'] * 100 ))


# Main program

def callback(hostname, rec_time, *args):
    if hostname == first_node_name:
        first_node.getPage(rec_time).addRecord(*args)
    elif hostname == second_node_name:
        second_node.getPage(rec_time).addRecord(*args)

if len(sys.argv) != 4:
    eprint("Usage: %s dirname first_node_name second_node_name" % (sys.argv[0]))
    sys.exit(-1)

dirname = sys.argv[1]
first_node_name = sys.argv[2]
second_node_name = sys.argv[3]

parser = RecordParser(dirname, callback)
first_node = ProcRecordSeries(first_node_name)
second_node = ProcRecordSeries(second_node_name)

parser.parse()
#node2.printAll()
#node2.showStat()

print("dirname=%s\nfirst_node_name=%s\nsecond_node_name=%s" % (dirname, first_node_name, second_node_name))

print("============== Node %s ================" % first_node_name )
first_node.showStat()
print("=======================================\n")

print("============== Node %s ================" % second_node_name )
second_node.showStat()
print("=======================================")
