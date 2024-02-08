"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import include, path
from django.conf.urls.static import static
from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.views.decorators.cache import cache_page

from app import settings
from main import views

schema_view = get_schema_view(
   openapi.Info(
      title='Price Monitoring API',
      default_version='v1',
      description='API for monitoring changes in prices for products.',
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'products', views.ProductsViewSet)
router.register(r'log_owners', views.LogOwnerViewSet)
router.register(r'log', views.LogItemsViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('api/v1/', include(router.urls)),
    path('api/v1/youtube_dl', views.youtube_dl_info, name='youtube_dl'),
    path('api/v1/youtube_dl/download', views.youtube_dl_download, name='youtube_dl_action'),
    path('api/v1/create_log_record', views.create_log_record, name='create_log_record'),
    path('api/v1/create_log_record/<str:owner_uuid>', views.create_log_record, name='create_log_record_by_uuid'),
    path('api/v1/edge_tts/<str:voice_id>', views.edge_tts, name='edge_tts'),
    path('api/v1/edge_tts_voices_list', cache_page(60 * 120)(views.edge_tts_voices_list),
         name='edge_tts_voices_list'),
    path('api/v1/edge_tts_voices_list_by_lang/<str:language>', cache_page(60 * 120)(views.edge_tts_voices_list_by_lang),
         name='edge_tts_voices_list_by_lang'),
]

urlpatterns += [
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'Administration'
