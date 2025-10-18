from django.urls import path
from . import views

app_name = 'tesoreria'

urlpatterns = [
    path('saldi/', views.saldi_conti, name='saldi_conti'),
    path('movimenti/', views.lista_movimenti, name='lista_movimenti'),
    path('estratto-conto/<int:pk>/', views.estratto_conto, name='estratto_conto'),
]