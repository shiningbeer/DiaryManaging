from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.loguserin),
    url(r'^index/', views.index),
    url(r'^logout/', views.logout),
    url(r'^pluginSetting/', views.pluginSetting),
    url(r'^task/', views.task),
    url(r'^target/', views.target),

]
