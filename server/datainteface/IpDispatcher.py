# -*- coding:utf-8 -*-
import os
import sys
from IPy import IP

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)


def IpDispatch(list_IpRange, splitNum):
    # 总数
    totalsum = 0
    # 每个ipRange切分后的列表
    splitted_list_of_each_range = []

    # 对于列表中每一个ip段
    for iprange in list_IpRange:
        # 获取头尾ip
        split = iprange.split('-')
        ipstart = split[0]
        ipend = split[1]

        # 获取头尾的整数
        intStart = IP(ipstart).int()
        intEnd = IP(ipend).int()

        # 获取该ip段数量，并加入总数
        sum = intEnd - intStart + 1
        totalsum = totalsum + sum

        # 整除结果和余数
        eachVolume = sum / splitNum  # 平均每份多少
        left = sum % splitNum  # 多出来多少

        dispatch_result_for_this_ipRange = []
        laststart = intStart

        # 分配思路简单粗暴，平均分，余数给最后一个
        # 除了最后一个，前面的全拿平均数
        for i in range(0, splitNum - 1):
            eachPiece = {}
            # eachPiece['startIP'] = str(IP(intStart + i * eachVolume))
            # eachPiece['endIP'] = str(IP(intStart + (i + 1) * eachVolume - 1))
            eachPiece['count'] = eachVolume
            eachPiece['range'] = str(IP(intStart + i * eachVolume)) + \
                '-' + str(IP(intStart + (i + 1) * eachVolume - 1))

            dispatch_result_for_this_ipRange.append(eachPiece)
            # 更新最后一个开始的数字
            laststart = intStart + (i + 1) * eachVolume - 1 + 1

        # 剩下的全归最后一个
        lastPiece = {}
        # lastPiece['startIP'] = str(IP(laststart))
        # lastPiece['endIP'] = str(IP(intEnd))
        lastPiece['count'] = intEnd - laststart + 1
        lastPiece['range'] = str(IP(laststart)) + "-" + str(IP(intEnd))

        # 这一个ipRange
        dispatch_result_for_this_ipRange.append(lastPiece)
        # 把这一个加入总的
        splitted_list_of_each_range.append(dispatch_result_for_this_ipRange)
    # 循环过后获得一个总表，现在要把每个list的第1项汇成一个list，第2项汇成一个list,...第splitNum项汇成一个list
    finalResult = []
    # 对于从0到splitNum的n
    for i in range(0, splitNum):
        onelistResult = []
        # 把每个表的第n项加入进来
        for onelist in splitted_list_of_each_range:
            onelistResult.append(onelist[i])

        # 加入总表
        finalResult.append(onelistResult)
    return totalsum, finalResult


if __name__ == '__main__':
    a = '192.68.1.1-192.68.1.16'
    b = '192.68.1.1-192.68.2.255'
    list_test = []
    list_test.append(a)
    list_test.append(b)

    IpDispatch(list_test, 10)
