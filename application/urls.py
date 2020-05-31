from django.conf.urls import url
from django.views.generic import  ListView
from .models import Game
from . import views
urlpatterns = [
       url(r'^(?P<room_name>[^/]+)/$', views.room, name='room'),
]
