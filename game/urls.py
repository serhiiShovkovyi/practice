"""game URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import ListView
from application.models import Game
from datetime import datetime
from django.contrib.auth.views import LoginView, LogoutView
from application import views, forms
from django.contrib.auth.decorators import login_required



urlpatterns = [
    url(r'^$', login_required(ListView.as_view(queryset=Game.get_available_games(),
            template_name='application/games.html'), login_url='/login/'), name='home'),
    url(r'^login/', LoginView.as_view(template_name='application/login.html',authentication_form=forms.AuthForm,
                extra_context={'title': 'Sign in', 'year': datetime.now().year}), name='login'),
    url(r'^register/', views.SignUp.as_view(), name='register'),
    url(r'^game/', include('application.urls')),
    url(r'^mygames/', views.mygames, name='mygames'),
    url(r'^statistic/', views.statistic, name='statistics'),
    url(r'^logout/', LogoutView.as_view(next_page='/login'), name='logout'),
    url(r'^auth/', include('social_django.urls', namespace='social')),
    url(r'^admin/', admin.site.urls)
]
