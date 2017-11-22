# -*- coding:utf-8 -*-
import os
import json
import datetime
import sys
from dbOperator import dboperator, statusOptions

dbo = dboperator('test.db')
print dbo.getAllTasks()
