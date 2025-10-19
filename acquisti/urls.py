from django.urls import path
from . import views

app_name = 'acquisti'

urlpatterns = [
    path('', views.lista_fatture_acquisto, name='lista_fatture_acquisto'),
    path('<int:pk>/', views.dettaglio_fattura_acquisto, name='dettaglio_fattura_acquisto'),
    path('nuova/', views.fattura_acquisto_create, name='fattura_acquisto_create'),
    path('<int:pk>/modifica/', views.fattura_acquisto_update, name='fattura_acquisto_update'),
]

