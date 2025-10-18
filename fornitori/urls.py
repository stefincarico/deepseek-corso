from django.urls import path
from . import views

app_name = 'fornitori'

urlpatterns = [
    path('', views.lista_fornitori, name='lista_fornitori'),
    path('<int:pk>/', views.dettaglio_fornitore, name='dettaglio_fornitore'),
]