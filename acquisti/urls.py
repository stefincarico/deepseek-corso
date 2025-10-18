from django.urls import path
from . import views

app_name = 'acquisti'

urlpatterns = [
    path('', views.lista_fatture_acquisto, name='lista_fatture_acquisto'),
    path('<int:pk>/', views.dettaglio_fattura_acquisto, name='dettaglio_fattura_acquisto'),
]