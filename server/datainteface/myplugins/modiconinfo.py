#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#

import socket
import struct
import binascii

import time

BUFSIZE = 1024  # 缓冲区大小1k
TIMEOUT = 15  #
modbus_req_ident_ori = "000000000005002b0e0200"
modbus_req_cpu_ori = "000100000004005a0002"
modbus_req_mem_ori = "01bf00000005005a000606"
# IPS = ["166.139.80.88","86.47.115.182"]
IPS = ["166.139.80.88"]


# universal function
def dataSwitch(data):
    str2 = ''
    while data:
        str1 = data[0:2]
        s = int(str1, 16)
        str2 += struct.pack('B', s)
        data = data[2:]
    return str2


def str_cut(str, a):
    x = a - 1
    for i in range(0, 1024):
        if str[(x + i) * 2:(x + i + 1) * 2] == "00":
            break
    return binascii.a2b_hex(str[x * 2:(x + i) * 2]).decode("utf8")


def str_cut_size(str, x, size):
    str2 = str[x * 2 - 2: (x + size) * 2 - 2]
    return binascii.a2b_hex(str2).decode("utf8")


def unsincharget(str, num):  # bin.pack  >S
    code = str[num * 2] + str[num * 2 + 1] + \
        str[num * 2 - 2] + str[num * 2 - 1]
    return int(code, 16)


def charget(str, num):
    code = str[num * 2 - 2] + str[num * 2 - 1]
    return int(code, 16)


# universal function


def init_comms(sock, output):
    try:
        payload = dataSwitch("000100000004005a0002")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)
        payload = dataSwitch("000200000005005a000100")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)
        # bi_response = binascii.b2a_hex(response)
        count = 0
        ice = "54"
        while count < 248:
            ice = ice + "54"
            count = count + 1
        payload = dataSwitch("0003000000fe005a00fe00" + ice)
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)
        payload = dataSwitch("000400000005005a000300")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)
        bi_response = binascii.b2a_hex(response)
        print response
        project_name = str_cut(bi_response, 50)
        project_sec = charget(bi_response, 38)
        project_min = charget(bi_response, 39)
        project_hour = charget(bi_response, 40)
        project_day = charget(bi_response, 41)
        project_month = charget(bi_response, 42)
        project_year = unsincharget(bi_response, 43)
        project_rev_1 = charget(bi_response, 45)
        project_rev_2 = charget(bi_response, 46)
        project_rev_3 = charget(bi_response, 47)

        payload = dataSwitch("000500000005005a000304")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)

        payload = dataSwitch("000600000004005a0004")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)

        payload = dataSwitch("000700000005005a000100")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)

        payload = dataSwitch("0008000000fe005a000a00000102030405060708090a0b0c0d0e0f10111213141516" +
                             "1718191a1b1c1d1e1f202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f40414243" +
                             "4445464748494a4b4c4d4e4f505152535455565758595a5b5c5d5e5f606162636465666768696a6b6c6d6e6f70" +
                             "7172737475767778797a7b7c7d7e7f808182838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d" +
                             "9e9fa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebfc0c1c2c3c4c5c6c7c8c9ca" +
                             "cbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedfe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8")

        sock.sendall(payload)
        response = sock.recv(BUFSIZE)

        payload = dataSwitch("000900000004005a0004")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)

        payload = dataSwitch("000a00000004005a0004")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)

        payload = dataSwitch("000b00000004005a0004")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)

        payload = dataSwitch("000c0000000d005a0020001300000000006400")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)

        payload = dataSwitch("000d0000000d005a0020001300640000009c00")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)

        payload = dataSwitch("000e0000000d005a0020001400000000006400")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)

        payload = dataSwitch("000f0000000d005a002000140064000000f600")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)
        bi_response = binascii.b2a_hex(response)
        size = charget(bi_response, 6)  # 253

        project_info = ""
        tmp_project_info = ""

        pos = 180
        while pos < size + 7:
            tmp_project_info = str_cut(bi_response, pos)
            if tmp_project_info is None or tmp_project_info == "":
                project_info = project_info + " "
                pos = pos + 1
            else:
                project_info = project_info + tmp_project_info
                pos = pos + len(tmp_project_info)
        payload = dataSwitch("00100000000d005a00200014005a010000f600")
        sock.sendall(payload)
        response = sock.recv(BUFSIZE)
        bi_response = binascii.b2a_hex(response)
        project_fn = ""

        output["Project Information"] = project_name + \
            " - " + project_info.strip() + project_fn
        output["Project Revision"] = project_rev_3.__str__(
        ) + "." + project_rev_2.__str__() + "." + project_rev_1.__str__()
        output["Project Last Modified"] = project_month.__str__() + "/" + project_day.__str__() + "/" + project_year.__str__() + \
            "/" + project_hour.__str__() + "/" + project_min.__str__() + \
            "/" + project_sec.__str__()
        # print output

    except:
        print "error!"

        return output


def action(TargetAddr):
    ret = {}
    output = {}
    ret["IP_port"] = TargetAddr
    ret["modbus"] = 0
    ret["info"] = output

    modbus_req_ident = dataSwitch(modbus_req_ident_ori)
    modbus_req_cpu = dataSwitch(modbus_req_cpu_ori)
    modbus_req_mem = dataSwitch(modbus_req_mem_ori)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect(TargetAddr)
        sock.sendall(modbus_req_ident)
        rsv_data = sock.recv(BUFSIZE)
        bi_rsv_data = binascii.b2a_hex(rsv_data)
    except:
        print "connect error!"
        return ret

    if bi_rsv_data[16:18] == '07':
        return ret

    if bi_rsv_data[26:28] == '03':
        size = charget(bi_rsv_data, 16)
        output["Vendor Name"] = str_cut_size(bi_rsv_data, 17, size)
        pos = 19 + size
        size = charget(bi_rsv_data, 18 + size)
        output["Network Module"] = str_cut_size(bi_rsv_data, pos, size)
        pos = pos + size + 2
        size = charget(bi_rsv_data, pos)
        revision = str_cut_size(bi_rsv_data, pos, size)
        if output["Vendor Name"][0:9] == "Schneider":
            try:
                sock.sendall(modbus_req_cpu)
                rsv_data2 = sock.recv(BUFSIZE)
                bi_rsv_data2 = binascii.b2a_hex(rsv_data2)
                status = bi_rsv_data2[16:18]
                if status == "01":
                    ret["modbus"] = 1
                    output["Firmware"] = revision
                    return ret
                size = charget(bi_rsv_data2, 33)
                output["CPU Module"] = str_cut_size(bi_rsv_data2, 34, size)
                output["Firmware"] = revision

                try:
                    sock.sendall(modbus_req_mem)
                    rsv_data3 = sock.recv(BUFSIZE)
                    bi_rsv_data3 = binascii.b2a_hex(rsv_data3)
                    size = charget(bi_rsv_data3, 17)
                    if not size is None:
                        output["Memory Card"] = str_cut_size(
                            bi_rsv_data3, 18, size)
                        init_comms(sock, output)
                        ret["modbus"] = 1
                except:
                    return ret

            except:
                return ret
            finally:
                sock.close()

    return ret


def single_scan(IP, port):
    print action((IP, port))


def scan(IPList, funcallback1, funcallback2):
    for the_IP in IPList:
        result = action((the_IP, 502))
        if result["modbus"] == 1 or result["modbus"] == 2:
            funcallback1(the_IP)
            funcallback2(result)
        else:
            funcallback1(the_IP)
    return


# def func1(ip):
#     print ip
# def func2(result):
#     print result
#single_scan("86.47.115.182", 502)
# scan(IPS, func1, func2)
