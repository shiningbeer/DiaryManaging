# -*- coding:utf-8 -*-
import os
import json
import datetime
import sys
from time import sleep
from dbOperator import dboperator, statusOptions

dbo = dboperator('test.db')

# dbo.updateStatusById('5a142a2b5919ba5b98435f0a', 0)
# dbo.updateLastIpById('5a142a2b5919ba5b98435f0a', '192.68.1.200')
# dbo.deleteTableLastip()
# for i in range(0, 10):
#     print str(i) + '\r',
#     sys.stdout.flush()
#     sleep(1)
x = dbo.getIpFinishedFromUnfinishedTasks()
d = json.dumps(x)
p = eval(d)
for i in p:
    h, g = i
    print h
    print g
