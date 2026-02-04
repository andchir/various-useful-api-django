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
from main.views_screenshot import website_screenshot
from marketplace import views as marketplace_views

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
    path('api/v1/yt_dlp', views.yt_dlp_action, name='yt_dlp_action'),
    path('api/v1/create_log_record', views.create_log_record, name='create_log_record'),
    path('api/v1/create_log_record/<str:owner_uuid>', views.create_log_record, name='create_log_record_by_uuid'),

    # edge_tts
    path('api/v1/edge_tts/<str:voice_id>', views.edge_tts, name='edge_tts'),
    path('api/v1/edge_tts_languages_list', cache_page(60 * 360)(views.edge_tts_languages_list),
         name='edge_tts_languages_list'),
    path('api/v1/edge_tts_voices_list', cache_page(60 * 360)(views.edge_tts_voices_list),
         name='edge_tts_voices_list'),
    path('api/v1/edge_tts_voices_list_by_lang/<str:language>', cache_page(60 * 360)(views.edge_tts_voices_list_by_lang),
         name='edge_tts_voices_list_by_lang'),

    # fact_check_explorer
    path('api/v1/fact_check_explorer', views.fact_check_explorer, name='fact_check_explorer'),
    path('api/v1/upload_and_share_yadisk', views.upload_and_share_yadisk_action, name='upload_and_share_yadisk'),

    # googletrans_tts
    path('api/v1/googletrans_languages_list', cache_page(60 * 360)(views.googletrans_languages_list),
         name='googletrans_languages_list'),
    path('api/v1/google_tts_languages_list', cache_page(60 * 360)(views.google_tts_languages_list),
         name='google_tts_languages_list'),
    path('api/v1/googletrans_translate', views.googletrans_translate, name='googletrans_translate'),
    path('api/v1/google_tts', views.google_tts, name='google_tts'),

    # coggle
    path('api/v1/coggle_nodes/<str:diagram_id>/<str:node_id>', views.coggle_node_action, name='coggle_node'),

    # Other
    path('api/v1/password_generate', views.password_generate, name='password_generate'),

    # YandexGPT
    path('api/v1/yandexgpt_assistant', views.yandexgpt_assistant_action, name='yandexgpt_assistant'),

    # OpenAI Embeddings
    path('api/v1/store_create', views.embeddings_create_store_action, name='embeddings_create_store_action'),
    path('api/v1/store_question', views.embeddings_store_question_action, name='embeddings_store_question_action'),

    # Video
    path('api/v1/extract_video_frame', views.extract_video_frame, name='extract_video_frame'),
    path('api/v1/replace_video_audio', views.replace_video_audio, name='replace_video_audio'),
    path('api/v1/trim_video', views.trim_video, name='trim_video'),
    path('api/v1/concatenate_videos', views.concatenate_video_files, name='concatenate_videos'),

    # Screenshot
    path('api/v1/website_screenshot', website_screenshot, name='website_screenshot'),

    # Widget
    path('api/v1/widget_embed_code', views.widget_embed_code_generator, name='widget_embed_code'),

    # QR Code Generator
    path('api/v1/qr_code_generator', views.qr_code_generator, name='qr_code_generator'),

    # OCR Text Recognition
    path('api/v1/ocr_text_recognition', views.ocr_text_recognition, name='ocr_text_recognition'),

    # Currency Converter
    path('api/v1/currency_converter', views.currency_converter, name='currency_converter'),

    # Weather API
    path('api/v1/weather', views.weather_api, name='weather_api'),

    # Plagiarism Checker
    path('api/v1/plagiarism_checker', views.plagiarism_checker, name='plagiarism_checker'),

    # CSS Tools
    path('api/v1/svg_to_css_background', views.svg_to_css_background, name='svg_to_css_background'),
    path('api/v1/css_gradient_generator', views.css_gradient_generator, name='css_gradient_generator'),
    path('api/v1/css_box_shadow_generator', views.css_box_shadow_generator, name='css_box_shadow_generator'),
    path('api/v1/css_transform_generator', views.css_transform_generator, name='css_transform_generator'),
    path('api/v1/css_animation_generator', views.css_animation_generator, name='css_animation_generator'),
    path('api/v1/css_filter_generator', views.css_filter_generator, name='css_filter_generator'),
    path('api/v1/css_triangle_generator', views.css_triangle_generator, name='css_triangle_generator'),

    # Marketplace
    path('api/v1/store/create', marketplace_views.store_create, name='store_create'),
    path('api/v1/store/update/<uuid:write_uuid>', marketplace_views.store_update, name='store_update'),
    path('api/v1/store/<uuid:read_uuid>/menu', marketplace_views.store_menu_list, name='store_menu_list'),
    path('api/v1/store/<uuid:write_uuid>/menu/create', marketplace_views.menu_item_create, name='menu_item_create'),
    path('api/v1/cart/create/<uuid:read_uuid>', marketplace_views.cart_create, name='cart_create'),
    path('api/v1/cart/<uuid:cart_uuid>/add', marketplace_views.cart_add_item, name='cart_add_item'),
    path('api/v1/cart/<uuid:cart_uuid>/remove', marketplace_views.cart_remove_item, name='cart_remove_item'),
]

urlpatterns += [
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'), name='api_auth')
]

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'Administration'
