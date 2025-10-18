from django.contrib import admin
from django.urls import path, include
from . import views  # 👈 IMPORTIAMO LE NOSTRE VISTE

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 👇 HOME PAGE - La dashboard principale
    path('', views.dashboard, name='dashboard'),
    
    # Includiamo le URL delle nostre app
    path('fatture/', include('fatture.urls')),
    path('tesoreria/', include('tesoreria.urls')),
    path('clienti/', include('clienti.urls')),
    path('fornitori/', include('fornitori.urls')),
    path('acquisti/', include('acquisti.urls')),
]