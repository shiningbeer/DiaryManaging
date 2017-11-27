# -*- coding:utf-8 -*-
import sqlite3

statusOptions = {"未完成": 0, "完成": 1, "完成并已通知": 2}
instructionOptions = {"删除": -1, "执行": 0, "暂停": 1}


class dboperator(object):
    def __init__(self, dbfile):
        '''
        构造函数
        连接数据库并建表
        '''
        # 常量定义
        self.__tableName = 'bbasks'
        self.__tableName_lastIp = "lastIP"

        self.__con = sqlite3.connect(dbfile)
        self.__cur = self.__con.cursor()
        self.__cur.execute(
            "create table if not exists " + self.__tableName + " (" +
            "id text primary key, " +
            "taskName text, " +
            "ipRange text, " +
            "plugin text, " +
            "startTime timestamp not null default (datetime('now','localtime')), " +
            "endTime timestamp, " +
            "ipTotal integer, " +
            "ipFinished integer, " +
            "status integer, " +
            "instruction integer)")
        self.__cur.execute(
            "create table if not exists " + self.__tableName_lastIp + " (" +
            "id text primary key, " +
            "lastip text)")

    def __del__(self):
        '''析构函数'''
        self.__cur.close()
        self.__con.close()

    def insertTask(self, ntid, taskName, ipRange, plugin, ipTotal):
        '''新建一条记录'''
        # 依次插入字段，startTime、endTime为空，ipFinished为0,status为未完成，instruciton为执行，其它为参数
        self.__cur.execute(
            "insert into " + self.__tableName + "(id,taskName,ipRange,plugin,ipTotal,ipFinished,status,instruction) values('" +
            ntid + "','" + taskName + "','" + ipRange + "','" + plugin + "'," + str(ipTotal) + ",0," + str(statusOptions["未完成"]) +
            "," + str(instructionOptions['执行']) + ")")
        self.__con.commit()

    def updateLastIpById(self, id, lastip):
        sql = "replace into " + self.__tableName_lastIp + \
            "(id,lastip) values('" + id + "','" + lastip + "')"
        self.__cur.execute(sql)
        self.__con.commit()

    def getLastIpById(self, id):
        self.__cur.execute("select lastip from " +
                           self.__tableName_lastIp + " where id='" + id + "'")
        result = self.__cur.fetchone()
        if result != None:
            result = result[0]
        return result

    def isExistById(self, id):
        self.__cur.execute("select id from " +
                           self.__tableName + " where id='" + id + "'")
        if self.__cur.fetchone() != None:
            return True
        else:
            return False

    def getIpFinishedFromNotFinisedAndNotifiedTasks(self):
        '''
        搜索未完成和完成的，
        因为不同线程的时间差，执行任务完成之后，改了status=完成，此时sycn还没运行，也就是最后的ipfinished没同步上去。
        所以完成的也要汇报，后面完成的经过reportcomlete线程之后变成完成并已通知，这个就不汇报了。
        '''
        self.__cur.execute("select id,ipFinished from " +
                           self.__tableName + " where status=" +
                           str(statusOptions["未完成"]) + " or status=" +
                           str(statusOptions["完成"]) + " and instruction!=" +
                           str(instructionOptions["删除"]))
        return self.__cur.fetchall()

    def getFinished_but_not_report_Tasks(self):
        self.__cur.execute("select id from " +
                           self.__tableName + " where status=" +
                           str(statusOptions["完成"]) + " and instruction!=" +
                           str(instructionOptions["删除"]))
        ctl = self.__cur.fetchall()
        completeTasks = []
        for item in ctl:
            ct, = item
            completeTasks.append(ct)
        return completeTasks

    def getOneTaskForExecute(self):
        '''获取一条status="未完成"且instruction="执行"的记录'''
        self.__cur.execute("select id, taskName,plugin,ipRange,ipTotal from " +
                           self.__tableName + " where status=" +
                           str(statusOptions["未完成"]) + " and instruction=" +
                           str(instructionOptions["执行"]))
        return self.__cur.fetchone()

    def getIpLeftAll(self):
        '''获取所有status="未完成"的iptotal和ipfinished之差'''
        self.__cur.execute("select ipTotal,ipFinished from " +
                           self.__tableName + " where status=" + str(statusOptions["未完成"]) +
                           " and instruction!=" + str(instructionOptions['删除']))
        result = 0
        nextRow = True
        while nextRow:
            row = self.__cur.fetchone()
            if row:
                iptotal, ipfinished = row
                ipleft = iptotal - ipfinished
                result = result + ipleft
            else:
                nextRow = False
        return result

    def getInstructionById(self, id):
        ''' 获取某id的status '''
        self.__cur.execute("select instruction from " + self.__tableName +
                           " where id='" + id + "'")
        result = self.__cur.fetchone()
        if result:
            return result[0]  # result居然还是个元组(xx,)
        else:
            return None

    def updateEndTimeById(self, id):
        ''' 修改某id的endTime '''
        self.__cur.execute("update " + self.__tableName +
                           " set endTime=(datetime('now','localtime'))" +
                           " where id='" + id + "'")
        self.__con.commit()

    def updateStatusById(self, id, status):
        ''' 修改某id的status '''
        self.__cur.execute("update " + self.__tableName +
                           " set status=" + str(status) +
                           " where id='" + id + "'")
        self.__con.commit()

    def updateInstructionById(self, id, instruction):
        ''' 修改某id的Instruction '''
        self.__cur.execute("update " + self.__tableName +
                           " set instruction=" + str(instruction) +
                           " where id='" + id + "'")
        self.__con.commit()

    def updateIpFinishedById(self, id, ipFinished):
        ''' 修改某id的ipFinished '''
        self.__cur.execute("update " + self.__tableName +
                           " set ipFinished=" + str(ipFinished) +
                           " where id='" + id + "'")
        self.__con.commit()


#----------------------for debug----------------------------
    def updateStatusAll(self, status):
        self.__cur.execute("update " + self.__tableName +
                           " set status=" + str(status))
        self.__con.commit()

    def getAllTasks(self):
        self.__cur.execute("select * from " +
                           self.__tableName)
        return self.__cur.fetchall()

    def deleteTableLastip(self):
        self.__cur.execute("drop table " + self.__tableName_lastIp)
        self.__con.commit()

    def getAllFromLastIp(self):
        self.__cur.execute("select * from " +
                           self.__tableName_lastIp)
        return self.__cur.fetchall()
