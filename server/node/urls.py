from django.conf.urls import url
from . import node

urlpatterns = [
    url(r'^register', node.register),
    url(r'^pulse', node.pulse),
    url(r'^taskProcessReport', node.taskProcessReport),
    url(r'^nodeTaskConfirm', node.nodeTaskConfirm),


]
