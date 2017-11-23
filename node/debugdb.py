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
x = dbo.getAllUnfinishedTasks()
for i in x:
    d, e = i
    print d
    print e
u = dbo.getInstructionById('5a16e6ee33339d0b920fd8a3')
print u
