from django.urls import path
from . import views

app_name = 'contabilita'

urlpatterns = [
    path('prima-nota/', views.prima_nota, name='prima_nota'),
]