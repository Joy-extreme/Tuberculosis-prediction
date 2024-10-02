"""core URL Configuration

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
from django.contrib import admin
from django.urls import path
from TBApp.views import *
urlpatterns = [
    path('', homeView, name="homeView"),
    path('register/', signupView, name="signupView"),
    path('signin/', signinView, name="signinView"),
    path('logout/', logoutView, name="logoutView"),
    path('UpdatePassword/', UpdatePasswordView, name="UpdatePasswordView"),
    path('adminDashboard/', adminDashboardView, name="adminDashboardView"),
    path('verify/<token>', accountVerification, name="accountVerification"),
    path('userDashboard/', userDashboardView, name="userDashboardView"),
    path('predictDisease/', predictDiseaseView, name="predictDiseaseView"),
    path('webhooks/stripe/', stripe_webhook, name='stripe_webhook'),
    path('error/', errorPageView, name="errorPageView"),
    path('subscription/<str:plan>/', create_checkout_session, name='create_checkout_session'),
    path('admin/', admin.site.urls),
]
