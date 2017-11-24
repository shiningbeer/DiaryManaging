from django.conf.urls import url
from . import node

urlpatterns = [
    url(r'^register', node.register),
    url(r'^pulse', node.pulse),
    url(r'^syncTaskInfo', node.syncTaskInfo),
    url(r'^nodeTaskConfirm', node.nodeTaskConfirm),


]
