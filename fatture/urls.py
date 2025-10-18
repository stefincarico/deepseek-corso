from django.urls import path
from . import views

app_name = 'fatture'

urlpatterns = [
    path('', views.lista_fatture, name='lista_fatture'),
    path('scadenziario/', views.scadenziario, name='scadenziario'),
    path('<int:pk>/', views.dettaglio_fattura, name='dettaglio_fattura'),
    path('nuova/', views.fattura_create, name='fattura_create'),
    path('<int:pk>/modifica/', views.fattura_update, name='fattura_update'),
]