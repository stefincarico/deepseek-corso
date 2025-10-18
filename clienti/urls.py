from django.urls import path
from . import views

app_name = 'clienti'

urlpatterns = [
    path('', views.lista_clienti, name='lista_clienti'),
    path('<int:pk>/', views.dettaglio_cliente, name='dettaglio_cliente'),
]