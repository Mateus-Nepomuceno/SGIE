from django.urls import include, path

urlpatterns = [
    path('auth/', include('core.auth')),
    path('', include('usuarios.urls')),
    path('', include('eventos.urls')),
]
