# -*- coding:utf-8 -*-
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate
import json
import datetime
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)


def index(req):
    if(req.session.has_key('username')):
        return render_to_response("index.html")
    return HttpResponseRedirect('/')


def loguserin(req):
    if(req.session.has_key('username')):
        return HttpResponseRedirect("/scanning/index")
    if req.method == 'POST':
        un = req.POST['username']
        pd = req.POST['password']
        user = authenticate(username=un, password=pd)
        if user is not None:
            req.session['username'] = un
            return HttpResponseRedirect("/scanning/index/")
    return render_to_response('login.html')


def logout(req):
    del req.session['username']
    return HttpResponseRedirect('/')


def pluginSetting(req):
    if(req.session.has_key('username')):
        return render_to_response("pluginSetting.html")


def task(req):
    if(req.session.has_key('username')):
        return render_to_response("task.html", {"taskIpRange": "{{task.ipRange}}", "taskDescription": "{{task.description}}", "taskProtocals": "{{task.protocals_str}}", "taskProgress": "{{task.progress}}"})


def target(req):
    if(req.session.has_key('username')):
        return render_to_response("target.html")
