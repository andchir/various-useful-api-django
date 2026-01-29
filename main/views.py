import asyncio
import json
import os
import tempfile
import urllib
import uuid
import logging
import requests
import googletrans
import gtts
from factcheckexplorer.factcheckexplorer import FactCheckLib
import yt_dlp
import qrcode
from io import BytesIO
import base64
from datetime import datetime
import difflib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.http import HttpResponse, FileResponse
from django.contrib.auth.models import User, Group
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authentication import BasicAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter
from password_generator import PasswordGenerator
from rest_framework import status, viewsets, filters, generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.pagination import PageNumberPagination
from django.core.files.uploadedfile import TemporaryUploadedFile
from yandex_cloud_ml_sdk import YCloudML

from app import settings
from main.embeddings import create_and_store_embeddings, get_answer_with_embeddings
from main.filters import IsOwnerFilterBackend, IsPublishedFilterBackend
from main.lib import edge_tts_find_voice, edge_tts_create_audio, delete_old_files, edge_tts_locales, \
    upload_and_share_yadisk, is_internal_url, get_safe_filename
from main.lib_ffmpeg import extract_frame_from_video, replace_audio_in_video, trim_video_segment, \
    save_uploaded_file_to_temp, concatenate_videos
from main.models import ProductModel, LogOwnerModel, LogItemModel
from main.serializers import UserSerializer, GroupSerializer, ProductModelSerializer, ProductModelListSerializer, \
    LogOwnerModelSerializer, LogItemsModelSerializer, YoutubeDlRequestSerializer, YoutubeDlResponseDownloadSerializer, \
    YoutubeDlResponseSerializer, YoutubeDlRequestDownloadSerializer, YoutubeDlResponseErrorSerializer, \
    EdgeTtsVoicesSerializer, EdgeTtsLanguagesSerializer, EdgeTtsVoicesRequestSerializer, PasswordGeneratorSerializer, \
    PasswordGeneratorRequestSerializer, FactCheckExplorerRequestSerializer, FactCheckExplorerSerializer, \
    YandexDiskUploadResponseSerializer, GoogleTtsLanguagesSerializer, GoogleTransOutputSerializer, \
    GoogleTransRequestSerializer, GoogleTTSRequestSerializer, GoogleTTSResponseSerializer, EdgeTtsResponseSerializer, \
    EdgeTtsRequestSerializer, YandexGPTResponseSerializer, OpenAIEmbeddingsResponseSerializer, \
    OpenAIEmbeddingsQuestionResponseSerializer, VideoFrameExtractionRequestSerializer, \
    VideoFrameExtractionResponseSerializer, VideoFrameExtractionErrorSerializer, \
    VideoAudioReplacementRequestSerializer, VideoAudioReplacementResponseSerializer, \
    VideoAudioReplacementErrorSerializer, VideoTrimRequestSerializer, VideoTrimResponseSerializer, \
    VideoTrimErrorSerializer, VideoConcatenationRequestSerializer, VideoConcatenationResponseSerializer, \
    VideoConcatenationErrorSerializer, WebsiteScreenshotRequestSerializer, WebsiteScreenshotResponseSerializer, \
    WebsiteScreenshotErrorSerializer, WidgetEmbedCodeRequestSerializer, WidgetEmbedCodeResponseSerializer, \
    WidgetEmbedCodeErrorSerializer, QRCodeGeneratorRequestSerializer, QRCodeGeneratorResponseSerializer, \
    QRCodeGeneratorErrorSerializer, OCRTextRecognitionRequestSerializer, OCRTextRecognitionResponseSerializer, \
    OCRTextRecognitionErrorSerializer, CurrencyConverterRequestSerializer, CurrencyConverterResponseSerializer, \
    CurrencyConverterErrorSerializer, WeatherAPIRequestSerializer, WeatherAPIResponseSerializer, \
    WeatherAPIErrorSerializer, PlagiarismCheckerRequestSerializer, PlagiarismCheckerResponseSerializer, \
    PlagiarismCheckerErrorSerializer
from main.permissions import IsOwnerOnly
# from pytube import YouTube
from pytubefix import YouTube

logger = logging.getLogger('django')


# Create your views here.
def index(request, exception=None):

    return HttpResponse('Welcome.')


@extend_schema(
    tags=['Users'],
)
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email']
    ordering_fields = ['date_joined', 'username', 'email']
    ordering = ['-date_joined']

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def current(self, request, pk=None):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)


@extend_schema(
    tags=['Users groups'],
)
class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAdminUser]


class ItemsListPagination(PageNumberPagination):
    page_size = 16
    page_size_query_param = 'page_size'


@extend_schema(
    tags=['Price monitoring'],
)
class ProductsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows products to be viewed or edited.
    """
    queryset = ProductModel.objects.all()
    serializer_class = ProductModelSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOnly]
    pagination_class = ItemsListPagination

    filter_backends = [IsOwnerFilterBackend, IsPublishedFilterBackend, DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'shop_name', 'city']
    ordering_fields = ['date_created', 'date', 'name']
    filterset_fields = ['name', 'city', 'shop_name']
    ordering = ['date']

    @method_decorator(cache_page(60 * 5))
    @action(methods=['get'], detail=False, permission_classes=[permissions.IsAuthenticated])
    def list_names(self, request):
        queryset = (ProductModel.objects.order_by('name').filter(published=True)
                    .values_list('name', flat=True).distinct())
        return Response(list(queryset))

    @method_decorator(cache_page(60 * 2))
    @action(methods=['get'], detail=False, permission_classes=[permissions.IsAuthenticated])
    def list_cities(self, request):
        queryset = (ProductModel.objects.order_by('city').filter(published=True)
                    .values_list('city', flat=True).distinct())
        return Response(list(queryset))

    @method_decorator(cache_page(60 * 2))
    @action(methods=['get'], detail=False, permission_classes=[permissions.IsAuthenticated])
    def list_shop_names(self, request):
        queryset = (ProductModel.objects.order_by('shop_name').filter(published=True)
                    .values_list('shop_name', flat=True).distinct())
        return Response(list(queryset))

    @method_decorator(cache_page(60 * 2))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 2))
    def list(self, request):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductModelListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ProductModelListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


@extend_schema(
    tags=['Logging'],
)
class LogOwnerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows log owners to be viewed or edited.
    """
    queryset = LogOwnerModel.objects.all()
    serializer_class = LogOwnerModelSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOnly]
    pagination_class = ItemsListPagination

    filter_backends = [IsOwnerFilterBackend]
    ordering = ['-id']


@extend_schema(
    tags=['Logging'],
)
class LogItemsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows log to be viewed or edited.
    """
    queryset = LogItemModel.objects.all()
    serializer_class = LogItemsModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ItemsListPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = []
    ordering_fields = ['date_created']
    filterset_fields = ['owner__uuid']
    ordering = ['-id']

    def list(self, request):
        if 'owner__uuid' not in request.GET or not request.GET['owner__uuid']:
            return Response({'results': []})
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = LogItemsModelSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = LogItemsModelSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


@extend_schema(
    tags=['Logging'],
)
@api_view(['POST'])
def create_log_record(request, owner_uuid=None):
    if owner_uuid is None and 'uuid' in request.GET:
        owner_uuid = request.GET['uuid']

    if owner_uuid is None:
        return HttpResponse(json.dumps({'success': True, 'message': 'Log owner not found.'}),
                            content_type='application/json', status=404)

    log_owner = LogOwnerModel.objects.filter(uuid=owner_uuid).first()

    if log_owner is None:
        return HttpResponse(json.dumps({'success': True, 'message': 'Log owner not found.'}),
                            content_type='application/json', status=404)

    log_data = request.data

    log_uuid = log_data['uid'] if 'uid' in log_data else None
    if not log_uuid and 'uuid' in log_data:
        log_uuid = log_data['uuid']

    if log_data is None or len(log_data.keys()) == 0:
        for key in request.GET:
            if key == 'uuid':
                continue
            log_data[key] = request.GET[key]

    log_item = LogItemModel()
    log_item.user = request.user
    log_item.owner = log_owner
    log_item.data = log_data
    log_item.uuid = log_uuid

    log_item.save()

    output = {'success': True}

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['YouTube'],
    request=YoutubeDlRequestSerializer,
    responses={
        (200, 'application/json'): YoutubeDlResponseSerializer,
        (422, 'application/json'): YoutubeDlResponseErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def yt_dlp_action(request):
    """
    API endpoint for information about the video from YouTube.
    """
    url = request.data['url'] if 'url' in request.data else None
    download = request.data['download'] if 'download' in request.data else False
    MAX_DURATION = 60 * 40  # 40 minutes
    MAX_RESOLUTION = '1280x720'
    MAX_RESOLUTION_VERT = '720x1280'

    if url is None:
        return HttpResponse(json.dumps({'success': False, 'message': 'There are no required fields.'}),
                            content_type='application/json', status=422)

    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'video'), exist_ok=True)

    deleted = delete_old_files(os.path.join(settings.MEDIA_ROOT, 'video'), max_hours=1)
    # print('deleted:', deleted)

    def video_match_filter(info, *, incomplete):
        duration = info.get('duration')
        if duration and duration > MAX_DURATION:
            return 'The video is too long.'

    def format_selector(ctx):
        """ Select the best video and the best audio that won't result in an mkv.
        NOTE: This is just an example and does not handle all cases """

        # formats are already sorted worst to best
        formats = ctx.get('formats')[::-1]

        resolutions = list(map(lambda x: x['resolution'] if 'resolution' in x else '', formats))
        tmp_res_value = next(r for r in resolutions if 'x' in r)
        tmp_res = tmp_res_value.split('x') if tmp_res_value else MAX_RESOLUTION.split('x')
        is_vertical = int(tmp_res[0]) / int(tmp_res[1]) < 1
        # print('resolutions', resolutions)
        # print('is_vertical', is_vertical)
        if is_vertical:
            target_resolution = MAX_RESOLUTION_VERT if MAX_RESOLUTION_VERT in resolutions else resolutions[0]
        else:
            target_resolution = MAX_RESOLUTION if MAX_RESOLUTION in resolutions else resolutions[0]
        format_index = resolutions.index(target_resolution)

        # acodec='none' means there is no audio
        try:
            best_video = next(f for f in formats
                              if (('vcodec' not in f or f['vcodec'] != 'none') and ('acodec' not in f or f['acodec'] == 'none'))
                              and f['resolution'] == target_resolution)
        except StopIteration:
            best_video = formats[format_index]

        # find compatible audio extension
        audio_ext = {'mp4': 'm4a', 'webm': 'webm'}[best_video['ext']]
        # vcodec='none' means there is no video
        try:
            best_audio = next(f for f in formats
                              if (('acodec' not in f or f['acodec'] != 'none')
                                  and ('vcodec' not in f or f['vcodec'] == 'none') and f['ext'] == audio_ext))
        except StopIteration:
            best_audio = formats[format_index]

        # These are the minimum required fields for a merged format
        yield {
            'format_id': f'{best_video["format_id"]}+{best_audio["format_id"]}',
            'ext': best_video['ext'],
            'requested_formats': [best_video, best_audio],
            # Must be + separated list of protocols
            'protocol': f'{best_video["protocol"]}+{best_audio["protocol"]}',
            'url': best_video['url'],
            'resolution': best_video['resolution'],
            'comment_count': best_video['comment_count'] if 'comment_count' in best_video else 0
        }

    ydl_opts = {
        'format': format_selector,
        'outtmpl': 'media/video/output-%(id)s.%(ext)s'
    }
    if download:
        ydl_opts['match_filter'] = video_match_filter
        ydl_opts['writethumbnail'] = True

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        try:
            info = ydl.extract_info(url, download=False)
            info = ydl.sanitize_info(info)
            if download:
                ydl.download(url)
        except Exception as e:
            print('ERROR:', str(e))
            info = {}

        host_url = "{}://{}".format(request.scheme, request.get_host())
        video_ext = info['ext'] if 'ext' in info else ''
        thumbnail_ext = info['thumbnail'].split('.')[-1] if 'thumbnail' in info else ''
        video_id = info['id'] if 'id' in info else ''
        video_duration = info['duration'] if 'duration' in info else 0
        video_url = (f"{host_url}/media/video/output-{video_id}.{video_ext}" if download and video_ext
                         else (info['url'] if 'url' in info else ''))
        thumbnail_url = (f"{host_url}/media/video/output-{video_id}.{thumbnail_ext}" if download and thumbnail_ext
                         else (info['thumbnail'] if 'thumbnail' in info else ''))

        result = {
            'id': video_id,
            'title': info['title'] if 'title' in info else '',
            # 'thumbnails': info['thumbnails'] if 'thumbnails' in info else [],
            'thumbnail': info['thumbnail'] if 'thumbnail' in info else '',
            'channel': info['channel'] if 'channel' in info else '',
            'channel_id': info['channel_id'] if 'channel_id' in info else '',
            'channel_url': info['channel_url'] if 'channel_id' in info else '',
            'description': info['description'] if 'description' in info else '',
            'duration': info['duration'] if 'duration' in info else 0,
            'resolution': info['resolution'] if 'resolution' in info else '',
            'comment_count': info['comment_count'] if 'comment_count' in info else 0,
            'view_count': info['view_count'] if 'view_count' in info else 0,
            'video_url': video_url,
            'thumbnail_url': thumbnail_url
        }

    if not result['id']:
        return HttpResponse(json.dumps({'success': False, 'message': 'Video not found.'}),
                            content_type='application/json', status=422)

    if video_duration > MAX_DURATION:
        return HttpResponse(json.dumps({'success': False, 'message': 'The video is too long.'}),
                            content_type='application/json', status=422)

    output = {'success': result['id'] != '', 'result': result}

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['YouTube'],
    request=YoutubeDlRequestSerializer,
    responses={
        (200, 'application/json'): YoutubeDlResponseSerializer,
        (422, 'application/json'): YoutubeDlResponseErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def youtube_dl_info(request):
    """
    API endpoint for information about the video from YouTube.
    """
    url = request.data['url'] if 'url' in request.data else None

    if url is None:
        return HttpResponse(json.dumps({'success': False, 'message': 'There are no required fields.'}),
                            content_type='application/json', status=422)

    try:
        yt = YouTube(url, use_oauth=False, allow_oauth_cache=True)
    except Exception as e:
        return HttpResponse(json.dumps({'success': False, 'message': str(e)}),
                            content_type='application/json', status=500)

    output = {
        'success': True,
        'author': yt.author,
        'channel_id': yt.channel_id,
        'channel_url': yt.channel_url,
        'title': yt.title,
        'description': yt.description,
        'video_id': yt.video_id,
        'thumbnail_url': yt.thumbnail_url,
        'length': yt.length,
        'publish_date': str(yt.publish_date),
        'rating': yt.rating,
        'url': yt.watch_url,
        # 'vid_info': yt.vid_info,
        'streams': []
    }

    streams = yt.streams.filter(type='video').order_by('resolution').desc()

    for stream in streams:
        output['streams'].append({
            'itag': stream.itag,
            'type': stream.type,
            'mime_type': stream.mime_type,
            'subtype': stream.subtype,
            'file_extension': stream.file_extension if hasattr(stream, 'file_extension') else None,
            'bitrate': stream.bitrate,
            'fps': stream.fps if hasattr(stream, 'fps') else None,
            'resolution': stream.resolution if hasattr(stream, 'resolution') else None,
            'resolution_string': f'{stream.mime_type} - {stream.resolution} - {int(stream.bitrate / 1024)} kb/sec'
            if hasattr(stream, 'resolution') and stream.resolution
            else f'{stream.mime_type} - {int(stream.bitrate / 1024)} kb/sec',
            'video_codec': stream.video_codec,
            'audio_codec': stream.audio_codec
        })

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['YouTube'],
    request=YoutubeDlRequestDownloadSerializer,
    responses={
        (200, 'application/json'): YoutubeDlResponseDownloadSerializer,
        (422, 'application/json'): YoutubeDlResponseErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def youtube_dl_download(request):
    """
    API endpoint for downloading videos from YouTube.
    """
    url = request.data['url'] if 'url' in request.data else None
    itag = request.data['itag'] if 'itag' in request.data else None
    if url is None or itag is None:
        return HttpResponse(json.dumps({'success': False, 'message': 'There are no required fields.'}),
                            content_type='application/json', status=422)

    try:
        yt = YouTube(url, use_oauth=False, allow_oauth_cache=True)
    except Exception as e:
        return HttpResponse(json.dumps({'success': False, 'message': str(e)}),
                            content_type='application/json', status=200)

    stream = yt.streams.get_by_itag(int(itag))
    output = {
        'success': True,
        'download_url': stream.url
    }

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['GoogleTransTTS'],
    responses={
        (200, 'application/json'): GoogleTtsLanguagesSerializer
    }
)
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def googletrans_languages_list(request):

    languages = googletrans.LANGUAGES
    languages_out = []
    for key, value in languages.items():
        languages_out.append({
            'name': value.capitalize(),
            'locale': key
        })
    output = {
        'success': True,
        'languages': languages_out
    }

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['GoogleTransTTS'],
    request=GoogleTransRequestSerializer,
    responses={
        (200, 'application/json'): GoogleTransOutputSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def googletrans_translate(request):
    text = request.data['text'] if 'text' in request.data else None
    lang_src = request.data['lang_src'] if 'lang_src' in request.data and request.data['lang_src'] else 'auto'
    lang_dest = request.data['lang_dest'] if 'lang_dest' in request.data else 'en'

    translator = googletrans.Translator()

    loop = asyncio.new_event_loop()
    try:
        res = loop.run_until_complete(translator.translate(text, dest=lang_dest, src=lang_src))
    finally:
        loop.close()

    output = {
        'text':  res.text,
        'lang_src':  res.src,
        'lang_dest': lang_dest
    }

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['GoogleTransTTS'],
    responses={
        (200, 'application/json'): GoogleTtsLanguagesSerializer
    }
)
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def google_tts_languages_list(request):

    languages = gtts.lang.tts_langs()
    languages_out = []
    for key, value in languages.items():
        languages_out.append({
            'name': value.capitalize(),
            'locale': key
        })

    output = {
        'success': True,
        'languages': languages_out
    }

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['GoogleTransTTS'],
    request=GoogleTTSRequestSerializer,
    responses={
        # (200, 'audio/mp3'): bytes
        (200, 'application/json'): GoogleTTSResponseSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def google_tts(request):
    text = request.data['text'] if 'text' in request.data else None
    lang_dest = request.data['lang_dest'] if 'lang_dest' in request.data else 'en'
    slow = request.data['slow'] if 'slow' in request.data else False

    if text is None:
        return HttpResponse(json.dumps({'success': False, 'message': 'The text cannot be empty.'}),
                            content_type='application/json', status=422)

    item_uuid = uuid.uuid1()
    if not os.path.isdir(os.path.join(settings.MEDIA_ROOT, 'audio')):
        os.mkdir(os.path.join(settings.MEDIA_ROOT, 'audio'))
    audio_file_path = os.path.join(settings.MEDIA_ROOT, 'audio', str(item_uuid) + '.mp3')

    delete_old_files(os.path.join(settings.MEDIA_ROOT, 'audio'))

    tts = gtts.gTTS(text, lang=lang_dest, slow=slow)
    tts.save(audio_file_path)

    host_url = "{}://{}".format(request.scheme, request.get_host())

    output = {
        'audio': f"{host_url}/media/audio/{item_uuid}.mp3",
    }

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['EdgeTTS'],
    responses={
        (200, 'application/json'): EdgeTtsVoicesSerializer
    }
)
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def edge_tts_voices_list(request):
    loop = asyncio.new_event_loop()
    try:
        res = loop.run_until_complete(edge_tts_find_voice())
    finally:
        loop.close()

    output = {
        'success': True,
        'voices': res
    }

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['EdgeTTS'],
    parameters=[EdgeTtsVoicesRequestSerializer],
    responses={
        (200, 'application/json'): EdgeTtsVoicesSerializer
    }
)
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def edge_tts_voices_list_by_lang(request, language):
    gender = request.GET['gender'] if 'gender' in request.GET else None
    loop = asyncio.new_event_loop()
    try:
        res = loop.run_until_complete(edge_tts_find_voice(language, gender))
    finally:
        loop.close()

    output = {
        'success': True,
        'voices': res
    }

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['EdgeTTS'],
    responses={
        (200, 'application/json'): EdgeTtsLanguagesSerializer
    }
)
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def edge_tts_languages_list(request):
    loop = asyncio.new_event_loop()
    try:
        res = loop.run_until_complete(edge_tts_locales())
    finally:
        loop.close()

    output = {
        'success': True,
        'languages': res
    }

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['EdgeTTS'],
    request=EdgeTtsRequestSerializer,
    responses={
        (200, 'application/json'): EdgeTtsResponseSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def edge_tts(request, voice_id):
    text = request.data['text'] if 'text' in request.data else None

    if text is None:
        return HttpResponse(json.dumps({'success': False, 'message': 'The text cannot be empty.'}),
                            content_type='application/json', status=422)

    item_uuid = uuid.uuid1()
    if not os.path.isdir(os.path.join(settings.MEDIA_ROOT, 'audio')):
        os.mkdir(os.path.join(settings.MEDIA_ROOT, 'audio'))
    audio_file_path = os.path.join(settings.MEDIA_ROOT, 'audio', str(item_uuid) + '.mp3')
    delete_old_files(os.path.join(settings.MEDIA_ROOT, 'audio'))

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(edge_tts_create_audio(text, voice_id, audio_file_path))
    finally:
        loop.close()

    host_url = "{}://{}".format(request.scheme, request.get_host())

    output = {
        'audio': f"{host_url}/media/audio/{item_uuid}.mp3",
    }

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['Other'],
    request=PasswordGeneratorRequestSerializer,
    responses={
        (200, 'application/json'): PasswordGeneratorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def password_generate(request):
    minlen = int(request.data['minlen']) if 'minlen' in request.data else 8
    maxlen = int(request.data['maxlen']) if 'maxlen' in request.data else 0
    minschars = int(request.data['minschars']) if 'minschars' in request.data else 1
    use_schars = bool(request.data['use_schars']) if 'use_schars' in request.data else True

    if not maxlen:
        maxlen = minlen

    pwo = PasswordGenerator()
    pwo.minlen = minlen
    pwo.maxlen = maxlen
    pwo.minschars = minschars
    if not use_schars:
        pwo.minschars = 0
        pwo.excludeschars = '!#$%^&*(),.-_+=<>?'

    try:
        password = pwo.generate()
    except ValueError as e:
        return HttpResponse(json.dumps({'success': False, 'message': str(e)}),
                            content_type='application/json', status=422)

    output = {
        'success': True,
        'password': password
    }

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['FactCheckExplorer'],
    request=FactCheckExplorerRequestSerializer,
    responses={
        (200, 'application/json'): FactCheckExplorerSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def fact_check_explorer(request):

    query = request.data['query'] if 'query' in request.data else ''
    language = request.data['language'] if 'language' in request.data and request.data['language'] else None
    num_results = int(request.data['num_results']) if 'num_results' in request.data and int(request.data['num_results']) else 200

    num_results = min(num_results, 500)

    if not query:
        return HttpResponse(json.dumps({'success': False, 'detail': 'The request is empty.'}), content_type='application/json', status=420)

    data = []

    fact_check = FactCheckLib(query=query, language=language, num_results=num_results)
    raw_json = fact_check.fetch_data()
    if raw_json:
        try:
            cleaned_json = fact_check.clean_json(raw_json)
        except:
            cleaned_json = None
        if cleaned_json:
            try:
                extracted_info = fact_check.extract_info(cleaned_json)
            except Exception as e:
                print(str(e))
                extracted_info = None
            if extracted_info:
                data = extracted_info
                # fact_check.convert_to_csv(extracted_info)

    output = {
        'success': True,
        'data': data
    }

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['YandexDisk'],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'string',
                    'format': 'binary'
                    },
                'file_type': {'type': 'string'},
                'dir_path': {'type': 'string'}
                }
            }
        },
    parameters=[
        OpenApiParameter(
            name='X-Yadisk-Token',
            type=str,
            location=OpenApiParameter.HEADER,
            description='YandexDisk Token',
        )
    ],
    responses={
        (200, 'application/json'): YandexDiskUploadResponseSerializer
    }
)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def upload_and_share_yadisk_action(request):
    yadisk_token = request.headers.get('X-Yadisk-Token')
    yadisk_dir_path = request.data['dir_path'] if 'dir_path' in request.data else ''
    file_type = request.data['file_type'] if 'file_type' in request.data else 'image'
    file: TemporaryUploadedFile = request.data['file'] if 'file' in request.data else None

    if file is None or file_type not in ['image', 'video', 'audio']:
        return HttpResponse(json.dumps({'success': False, 'detail': 'The request is empty.'}),
                            content_type='application/json', status=420)

    if file_type:
        valid_types = {
            'image': ['image/png', 'image/jpeg', 'image/jpg'],
            'video': ['video/mp4', 'video/webm'],
            'audio': ['audio/mp3', 'audio/mpeg', 'audio/wav']
        }
        if file.content_type not in valid_types[file_type]:
            return HttpResponse(json.dumps({'success': False, 'detail': f'Unsupported {file_type} file type.'}),
                                content_type='application/json', status=420)

    valid_file_sizes = {
        'image': 20 * 1024 * 1024,  # 20MB
        'video': 100 * 1024 * 1024,  # 100 MB
        'audio': 10 * 1024 * 1024  # 10 MB
    }

    if file.size > valid_file_sizes[file_type]:
        return HttpResponse(json.dumps({'success': False, 'detail': 'The file is too large.'}),
                            content_type='application/json', status=420)

    try:
        file_url, public_url, error_message = upload_and_share_yadisk(file.temporary_file_path(), yadisk_dir_path,
                                                                      yadisk_token)
    except Exception as e:
        print(e)
        file_url, public_url, error_message = (None, None, str(e))

    output = {
        'success': not error_message,
        'file_url': file_url,
        'public_url': public_url,
        'details': error_message
    }

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['YandexGPT'],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'folder_id': {'type': 'string'},
                'search_index_id': {'type': 'string'},
                'type': {'type': 'string'},
                'system': {'type': 'string'},
                'question': {'type': 'string'}
                }
            }
        },
    parameters=[
        OpenApiParameter(
            name='X-Yacloud-Api-Key',
            type=str,
            location=OpenApiParameter.HEADER,
            description='YandexCloud API Key',
        )
    ],
    responses={
        (200, 'application/json'): YandexGPTResponseSerializer
    }
)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def yandexgpt_assistant_action(request):
    token = request.headers.get('X-Yacloud-Api-Key')
    folder_id = request.data['folder_id'] if 'folder_id' in request.data else None
    search_index_id = request.data['search_index_id'] if 'search_index_id' in request.data else None
    type = request.data['type'] if 'type' in request.data else 'model'
    system = request.data['system'] if 'system' in request.data else ''
    question = request.data['question'] if 'question' in request.data else None

    if question is None:
        return HttpResponse(json.dumps({'success': False, 'detail': 'The question cannot be empty.'}),
                            content_type='application/json', status=420)

    if folder_id is None:
        return HttpResponse(json.dumps({'success': False, 'detail': 'The folder identifier is empty.'}),
                            content_type='application/json', status=420)

    # if search_index_id is None:
    #     return HttpResponse(json.dumps({'success': False, 'detail': 'The index ID is empty.'}),
    #                         content_type='application/json', status=420)

    sdk = YCloudML(folder_id=folder_id, auth=token)

    if type == 'model':

        model = sdk.models.completions('yandexgpt')
        model = model.configure(temperature=0.5)
        messages = [
            {
                'role': 'system',
                'text': system
            },
            {
                'role': 'user',
                'text': question
            }
        ]
        result = model.run(messages)

        result_text = ''
        for alternative in result:
            if len(result_text) > 0:
                result_text += ' '
            result_text += alternative.text

    else:

        try:
            search_index = sdk.search_indexes.get(search_index_id)
        except Exception as e:
            print(e)
            return HttpResponse(json.dumps({'success': False, 'detail': 'Index not found.'}),
                                content_type='application/json', status=420)

        tool = sdk.tools.search_index(search_index)

        try:
            assistant = sdk.assistants.create('yandexgpt', tools=[tool])
        except Exception as e:
            print(e)
            return HttpResponse(json.dumps({'success': False, 'detail': 'Incorrect authorization data.'}),
                                content_type='application/json', status=420)

        thread = sdk.threads.create()

        thread.write(question)
        run = assistant.run(thread)
        result = run.wait(poll_interval=2)
        result_text = result.text

    output = {
        'success': True,
        'result': result_text
    }

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['Coggle']
)
@api_view(['GET'])
def coggle_node_action(request, diagram_id, node_id):
    access_token = request.GET['access_token'] if 'access_token' in request.GET else None
    if access_token is None:
        return HttpResponse(json.dumps({'success': False, 'detail': 'access_token - missing.'}),
                            content_type='application/json', status=420)

    url = f'https://coggle.it/api/1/diagrams/{diagram_id}/nodes'
    r = requests.get(url, params={'access_token': access_token})
    if r.status_code != 200:
        return HttpResponse(json.dumps(r.json()), content_type='application/json', status=r.status_code)

    data = r.json()

    def find_nodes(tree, id):
        if tree['_id'] == id:
            return tree
        if len(tree['children']) == 0:
            return None
        for child in tree['children']:
            node = find_nodes(child, id)
            if node is not None:
                return node
        return None

    output = find_nodes(data[0], node_id)
    if output is None:
        output = []

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['OpenAI Embeddings'],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'openai_api_url_base': {'type': 'string'},
                'openai_model_name': {'type': 'string'},
                'knowledge_content': {'type': 'text'}
                }
            }
        },
    parameters=[
        OpenApiParameter(
            name='X-OpenAI-Api-Key',
            type=str,
            location=OpenApiParameter.HEADER,
            description='OpenAI API Key',
        )
    ],
    responses={
        (200, 'application/json'): OpenAIEmbeddingsResponseSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def embeddings_create_store_action(request):
    api_key = request.headers.get('X-OpenAI-Api-Key')
    openai_api_url_base = request.data.get('openai_api_url_base')
    openai_model_name = request.data.get('openai_model_name')
    knowledge_content = request.data.get('knowledge_content')

    if api_key is None:
        return HttpResponse(json.dumps({'success': False, 'detail': 'API key is required.'}),
                            content_type='application/json', status=420)

    if not knowledge_content:
        return HttpResponse(json.dumps({'success': False, 'detail': 'Content is required.'}),
                            content_type='application/json', status=420)

    if not openai_api_url_base:
        openai_api_url_base = 'https://api.openai.com/v1/'

    if not openai_model_name:
        openai_model_name = 'text-embedding-ada-002'

    try:
        store_uuid = create_and_store_embeddings(
            knowledge_content,
            model=openai_model_name,
            api_key=api_key,
            api_url_base=openai_api_url_base
        )
    except Exception as e:
        error_message = str(e)
        return HttpResponse(json.dumps({'success': False, 'detail': error_message}),
                            content_type='application/json', status=400)

    output = {'success': True, 'store_uuid': store_uuid}

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['OpenAI Embeddings'],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'openai_api_url_base': {'type': 'string'},
                'openai_embedding_model_name': {'type': 'string'},
                'openai_model_name': {'type': 'string'},
                'store_uuid': {'type': 'string'},
                'instructions': {'type': 'text'},
                'question': {'type': 'text'}
                }
            }
        },
    parameters=[
        OpenApiParameter(
            name='X-OpenAI-Api-Key',
            type=str,
            location=OpenApiParameter.HEADER,
            description='OpenAI API Key',
        )
    ],
    responses={
        (200, 'application/json'): OpenAIEmbeddingsQuestionResponseSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def embeddings_store_question_action(request):
    api_key = request.headers.get('X-OpenAI-Api-Key')
    openai_api_url_base = request.data.get('openai_api_url_base')
    openai_embedding_model_name = request.data.get('openai_embedding_model_name')
    openai_model_name = request.data.get('openai_model_name')
    store_uuid = request.data.get('store_uuid')
    question = request.data.get('question')
    instructions = request.data.get('instructions')

    if api_key is None:
        return HttpResponse(json.dumps({'success': False, 'detail': 'API key is required.'}),
                            content_type='application/json', status=420)

    if not store_uuid:
        return HttpResponse(json.dumps({'success': False, 'detail': 'Store ID is required.'}),
                            content_type='application/json', status=420)

    if not question:
        return HttpResponse(json.dumps({'success': False, 'detail': 'Question is required.'}),
                            content_type='application/json', status=420)

    if not openai_api_url_base:
        openai_api_url_base = 'https://api.openai.com/v1/'

    if not openai_model_name:
        openai_model_name = 'gpt-3.5-turbo'

    if not openai_embedding_model_name:
        openai_embedding_model_name = 'text-embedding-ada-002'

    try:
        answer = get_answer_with_embeddings(
            question,
            store_uuid,
            embedding_model=openai_embedding_model_name,
            model=openai_model_name,
            instructions=instructions,
            api_key=api_key,
            api_url_base=openai_api_url_base
        )
    except Exception as e:
        error_message = str(e)
        print(f'Error: {error_message}')
        return HttpResponse(json.dumps({'success': False, 'detail': error_message}),
                            content_type='application/json', status=400)

    output = {'success': True, 'answer': answer}

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)


@extend_schema(
    tags=['Video'],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'video': {
                    'type': 'string',
                    'format': 'binary'
                },
                'second': {'type': 'number', 'default': 0},
                'is_last': {'type': 'boolean', 'default': False}
            },
            'required': ['video']
        }
    },
    responses={
        (200, 'application/json'): VideoFrameExtractionResponseSerializer,
        (422, 'application/json'): VideoFrameExtractionErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def extract_video_frame(request):
    """
    API endpoint for extracting a frame from a video file.
    Accepts video file and extracts a frame at specified second or the last frame.
    Returns JPG image with high quality.
    """
    video_file: TemporaryUploadedFile = request.data.get('video') if 'video' in request.data else None
    second = float(request.data.get('second', 0))
    is_last = request.data.get('is_last', 'false').lower() in ['true', '1', 'yes'] if isinstance(request.data.get('is_last'), str) else bool(request.data.get('is_last', False))

    if video_file is None:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Video file is required.'}),
            content_type='application/json',
            status=422
        )

    # Validate video file type
    valid_video_types = ['video/mp4', 'video/webm', 'video/mpeg', 'video/quicktime', 'video/x-msvideo']
    if video_file.content_type not in valid_video_types:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Unsupported video file type.'}),
            content_type='application/json',
            status=422
        )

    # Validate file sizes
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB

    if video_file.size > MAX_VIDEO_SIZE:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Video file is too large. Maximum size is 100 MB.'}),
            content_type='application/json',
            status=422
        )

    # Create frames directory if it doesn't exist
    frames_dir = os.path.join(settings.MEDIA_ROOT, 'frames')
    if not os.path.isdir(frames_dir):
        os.makedirs(frames_dir)

    # Delete old files
    delete_old_files(frames_dir, max_hours=1)

    # Generate unique filename for the output frame
    frame_uuid = uuid.uuid1()
    output_file_path = os.path.join(frames_dir, f'{frame_uuid}.jpg')

    temp_video_path = None
    try:
        # Save uploaded video to temporary file
        temp_video_path = save_uploaded_file_to_temp(video_file, suffix=os.path.splitext(video_file.name)[1])

        # Extract frame using lib_ffmpeg
        success, error_message = extract_frame_from_video(
            video_path=temp_video_path,
            output_path=output_file_path,
            second=second,
            is_last=is_last,
            quality=2,
            timeout=60
        )

        # Clean up temporary video file
        if temp_video_path and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)

        if not success:
            return HttpResponse(
                json.dumps({'success': False, 'message': error_message}),
                content_type='application/json',
                status=422
            )

        # Return the URL to the extracted frame
        host_url = f"{request.scheme}://{request.get_host()}"
        frame_url = f"{host_url}/media/frames/{frame_uuid}.jpg"

        output = {
            'success': True,
            'image_url': frame_url
        }

        return HttpResponse(json.dumps(output), content_type='application/json', status=200)

    except Exception as e:
        logger.error(f'Error extracting video frame: {str(e)}')
        if temp_video_path and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)
        return HttpResponse(
            json.dumps({'success': False, 'message': f'Error: {str(e)}'}),
            content_type='application/json',
            status=422
        )


@extend_schema(
    tags=['Video'],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'video': {
                    'type': 'string',
                    'format': 'binary'
                },
                'audio': {
                    'type': 'string',
                    'format': 'binary'
                },
                'use_fade_out': {'type': 'boolean', 'default': False}
            },
            'required': ['video', 'audio']
        }
    },
    responses={
        (200, 'application/json'): VideoAudioReplacementResponseSerializer,
        (422, 'application/json'): VideoAudioReplacementErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def replace_video_audio(request):
    """
    API endpoint for replacing or adding audio track to a video file.
    Accepts video file (max 100 MB) and audio file (max 50 MB).
    If audio duration is longer than video duration, uses video duration.
    If use_fade_out is enabled and audio duration is longer than video duration,
    adds a 3-second fade-out to the audio before the end.
    """
    video_file: TemporaryUploadedFile = request.data.get('video') if 'video' in request.data else None
    audio_file: TemporaryUploadedFile = request.data.get('audio') if 'audio' in request.data else None
    use_fade_out = request.data.get('use_fade_out', 'false').lower() in ['true', '1', 'yes'] if isinstance(request.data.get('use_fade_out'), str) else bool(request.data.get('use_fade_out', False))

    # Validate required files
    if video_file is None:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Video file is required.'}),
            content_type='application/json',
            status=422
        )

    if audio_file is None:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Audio file is required.'}),
            content_type='application/json',
            status=422
        )

    # Validate video file type
    valid_video_types = ['video/mp4', 'video/webm', 'video/mpeg', 'video/quicktime', 'video/x-msvideo']
    if video_file.content_type not in valid_video_types:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Unsupported video file type.'}),
            content_type='application/json',
            status=422
        )

    # Validate audio file type
    valid_audio_types = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/aac', 'audio/m4a', 'audio/ogg']
    if audio_file.content_type not in valid_audio_types:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Unsupported audio file type.'}),
            content_type='application/json',
            status=422
        )

    # Validate file sizes
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB
    MAX_AUDIO_SIZE = 50 * 1024 * 1024   # 50 MB

    if video_file.size > MAX_VIDEO_SIZE:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Video file is too large. Maximum size is 100 MB.'}),
            content_type='application/json',
            status=422
        )

    if audio_file.size > MAX_AUDIO_SIZE:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Audio file is too large. Maximum size is 50 MB.'}),
            content_type='application/json',
            status=422
        )

    # Create output directory if it doesn't exist
    output_dir = os.path.join(settings.MEDIA_ROOT, 'video')
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # Delete old files
    delete_old_files(output_dir, max_hours=1)

    # Generate unique filename for the output video
    video_uuid = uuid.uuid1()
    output_file_path = os.path.join(output_dir, f'{video_uuid}.mp4')

    temp_video_path = None
    temp_audio_path = None

    try:
        # Save uploaded files to temporary locations
        temp_video_path = save_uploaded_file_to_temp(video_file, suffix=os.path.splitext(video_file.name)[1])
        temp_audio_path = save_uploaded_file_to_temp(audio_file, suffix=os.path.splitext(audio_file.name)[1])

        # Replace audio using lib_ffmpeg
        success, error_message = replace_audio_in_video(
            video_path=temp_video_path,
            audio_path=temp_audio_path,
            output_path=output_file_path,
            use_fade_out=use_fade_out,
            fade_duration=3.0,
            audio_bitrate='192k',
            timeout=180
        )

        # Clean up temporary files
        if temp_video_path and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)

        if not success:
            return HttpResponse(
                json.dumps({'success': False, 'message': error_message}),
                content_type='application/json',
                status=422
            )

        # Return the URL to the processed video
        host_url = f"{request.scheme}://{request.get_host()}"
        video_url = f"{host_url}/media/video/{video_uuid}.mp4"

        output = {
            'success': True,
            'video_url': video_url
        }

        return HttpResponse(json.dumps(output), content_type='application/json', status=200)

    except Exception as e:
        logger.error(f'Error replacing video audio: {str(e)}')
        if temp_video_path and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
        return HttpResponse(
            json.dumps({'success': False, 'message': f'Error: {str(e)}'}),
            content_type='application/json',
            status=422
        )


@extend_schema(
    tags=['Video'],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'video': {
                    'type': 'string',
                    'format': 'binary'
                },
                'second_start': {'type': 'number', 'default': 0},
                'second_end': {'type': 'number'}
            },
            'required': ['video']
        }
    },
    responses={
        (200, 'application/json'): VideoTrimResponseSerializer,
        (422, 'application/json'): VideoTrimErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def trim_video(request):
    """
    API endpoint for trimming a video file.
    Accepts video file (max 100 MB) and extracts a segment from second_start to second_end.
    Returns trimmed video in MP4 format.
    """
    video_file: TemporaryUploadedFile = request.data.get('video') if 'video' in request.data else None
    second_start = float(request.data.get('second_start', 0))
    second_end = request.data.get('second_end')

    # Validate video file is provided
    if video_file is None:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Video file is required.'}),
            content_type='application/json',
            status=422
        )

    # Validate second_end is provided
    if second_end is None:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Parameter second_end is required.'}),
            content_type='application/json',
            status=422
        )

    try:
        second_end = float(second_end)
    except (ValueError, TypeError):
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Parameter second_end must be a number.'}),
            content_type='application/json',
            status=422
        )

    # Validate time parameters
    if second_start < 0:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Parameter second_start must be non-negative.'}),
            content_type='application/json',
            status=422
        )

    if second_end <= second_start:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Parameter second_end must be greater than second_start.'}),
            content_type='application/json',
            status=422
        )

    # Validate video file type
    valid_video_types = ['video/mp4', 'video/webm', 'video/mpeg', 'video/quicktime', 'video/x-msvideo']
    if video_file.content_type not in valid_video_types:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Unsupported video file type.'}),
            content_type='application/json',
            status=422
        )

    # Validate file size (max 100 MB)
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB
    if video_file.size > MAX_VIDEO_SIZE:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Video file is too large. Maximum size is 100 MB.'}),
            content_type='application/json',
            status=422
        )

    # Create output directory if it doesn't exist
    output_dir = os.path.join(settings.MEDIA_ROOT, 'video')
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # Delete old files
    delete_old_files(output_dir, max_hours=1)

    # Generate unique filename for the output video
    video_uuid = uuid.uuid1()
    output_file_path = os.path.join(output_dir, f'{video_uuid}.mp4')

    temp_video_path = None

    try:
        # Save uploaded video to temporary file
        temp_video_path = save_uploaded_file_to_temp(video_file, suffix=os.path.splitext(video_file.name)[1])

        # Trim video using lib_ffmpeg
        success, error_message, video_duration = trim_video_segment(
            video_path=temp_video_path,
            output_path=output_file_path,
            start_time=second_start,
            end_time=second_end,
            timeout=180
        )

        # Clean up temporary video file
        if temp_video_path and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)

        if not success:
            return HttpResponse(
                json.dumps({'success': False, 'message': error_message}),
                content_type='application/json',
                status=422
            )

        # Return the URL to the trimmed video
        host_url = f"{request.scheme}://{request.get_host()}"
        video_url = f"{host_url}/media/video/{video_uuid}.mp4"

        output = {
            'success': True,
            'video_url': video_url
        }

        return HttpResponse(json.dumps(output), content_type='application/json', status=200)

    except Exception as e:
        logger.error(f'Error trimming video: {str(e)}')
        if temp_video_path and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)
        return HttpResponse(
            json.dumps({'success': False, 'message': f'Error: {str(e)}'}),
            content_type='application/json',
            status=422
        )


@extend_schema(
    tags=['Video'],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'videos': {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            },
            'required': ['videos']
        }
    },
    responses={
        (200, 'application/json'): VideoConcatenationResponseSerializer,
        (422, 'application/json'): VideoConcatenationErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def concatenate_video_files(request):
    """
    API endpoint for concatenating multiple video files into one.
    Accepts multiple video files (each max 100 MB).
    All videos are scaled to match the first video's dimensions while preserving aspect ratio.
    Videos are concatenated in the order they are provided.
    """
    # Get list of video files from request
    video_files = request.FILES.getlist('videos')

    # Validate that at least one video file is provided
    if not video_files or len(video_files) == 0:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'At least one video file is required.'}),
            content_type='application/json',
            status=422
        )

    # Validate video file types and sizes
    valid_video_types = ['video/mp4', 'video/webm', 'video/mpeg', 'video/quicktime', 'video/x-msvideo']
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB

    for i, video_file in enumerate(video_files):
        if video_file.content_type not in valid_video_types:
            return HttpResponse(
                json.dumps({'success': False, 'message': f'Unsupported video file type for video {i + 1}.'}),
                content_type='application/json',
                status=422
            )

        if video_file.size > MAX_VIDEO_SIZE:
            return HttpResponse(
                json.dumps({'success': False, 'message': f'Video file {i + 1} is too large. Maximum size is 100 MB.'}),
                content_type='application/json',
                status=422
            )

    # Create output directory if it doesn't exist
    output_dir = os.path.join(settings.MEDIA_ROOT, 'video')
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # Delete old files
    delete_old_files(output_dir, max_hours=1)

    # Generate unique filename for the output video
    video_uuid = uuid.uuid1()
    output_file_path = os.path.join(output_dir, f'{video_uuid}.mp4')

    temp_video_paths = []

    try:
        # Save all uploaded videos to temporary files
        for video_file in video_files:
            temp_path = save_uploaded_file_to_temp(video_file, suffix=os.path.splitext(video_file.name)[1])
            temp_video_paths.append(temp_path)

        # Concatenate videos using lib_ffmpeg
        success, error_message = concatenate_videos(
            video_paths=temp_video_paths,
            output_path=output_file_path,
            timeout=300
        )

        # Clean up temporary video files
        for temp_path in temp_video_paths:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

        if not success:
            return HttpResponse(
                json.dumps({'success': False, 'message': error_message}),
                content_type='application/json',
                status=422
            )

        # Return the URL to the concatenated video
        host_url = f"{request.scheme}://{request.get_host()}"
        video_url = f"{host_url}/media/video/{video_uuid}.mp4"

        output = {
            'success': True,
            'video_url': video_url
        }

        return HttpResponse(json.dumps(output), content_type='application/json', status=200)

    except Exception as e:
        logger.error(f'Error concatenating videos: {str(e)}')
        # Clean up temporary files
        for temp_path in temp_video_paths:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
        return HttpResponse(
            json.dumps({'success': False, 'message': f'Error: {str(e)}'}),
            content_type='application/json',
            status=422
        )


@extend_schema(
    tags=['Widget'],
    request=WidgetEmbedCodeRequestSerializer,
    responses={
        (200, 'application/json'): WidgetEmbedCodeResponseSerializer,
        (422, 'application/json'): WidgetEmbedCodeErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def widget_embed_code_generator(request):
    """
    API endpoint for generating widget embed code.
    Creates JavaScript code for embedding a chat widget on a website.
    """
    app_embed_url = request.data.get('app_embed_url')
    button_color = request.data.get('button_color', '#007bff')
    hover_color = request.data.get('hover_color', '#0056b3')
    position = request.data.get('position', 'bottom-right')
    width = int(request.data.get('width', 350))
    height = int(request.data.get('height', 465))
    button_text = request.data.get('button_text', 'Открыть чат')

    whatsapp_text = request.data.get('whatsapp_text', '')
    whatsapp_href = request.data.get('whatsapp_href', '')
    telegram_text = request.data.get('telegram_text', '')
    telegram_href = request.data.get('telegram_href', '')
    vk_text = request.data.get('vk_text', '')
    vk_href = request.data.get('vk_href', '')
    instagram_text = request.data.get('instagram_text', '')
    instagram_href = request.data.get('instagram_href', '')
    facebook_text = request.data.get('facebook_text', '')
    facebook_href = request.data.get('facebook_href', '')

    if not app_embed_url:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'The app_embed_url field is required.'}),
            content_type='application/json',
            status=422
        )

    # Social media icons
    icons = {
        'whatsapp': '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path fill-rule="evenodd" clip-rule="evenodd" d="M3.50002 12C3.50002 7.30558 7.3056 3.5 12 3.5C16.6944 3.5 20.5 7.30558 20.5 12C20.5 16.6944 16.6944 20.5 12 20.5C10.3278 20.5 8.77127 20.0182 7.45798 19.1861C7.21357 19.0313 6.91408 18.9899 6.63684 19.0726L3.75769 19.9319L4.84173 17.3953C4.96986 17.0955 4.94379 16.7521 4.77187 16.4751C3.9657 15.176 3.50002 13.6439 3.50002 12ZM12 1.5C6.20103 1.5 1.50002 6.20101 1.50002 12C1.50002 13.8381 1.97316 15.5683 2.80465 17.0727L1.08047 21.107C0.928048 21.4637 0.99561 21.8763 1.25382 22.1657C1.51203 22.4552 1.91432 22.5692 2.28599 22.4582L6.78541 21.1155C8.32245 21.9965 10.1037 22.5 12 22.5C17.799 22.5 22.5 17.799 22.5 12C22.5 6.20101 17.799 1.5 12 1.5ZM14.2925 14.1824L12.9783 15.1081C12.3628 14.7575 11.6823 14.2681 10.9997 13.5855C10.2901 12.8759 9.76402 12.1433 9.37612 11.4713L10.2113 10.7624C10.5697 10.4582 10.6678 9.94533 10.447 9.53028L9.38284 7.53028C9.23954 7.26097 8.98116 7.0718 8.68115 7.01654C8.38113 6.96129 8.07231 7.046 7.84247 7.24659L7.52696 7.52195C6.76823 8.18414 6.3195 9.2723 6.69141 10.3741C7.07698 11.5163 7.89983 13.314 9.58552 14.9997C11.3991 16.8133 13.2413 17.5275 14.3186 17.8049C15.1866 18.0283 16.008 17.7288 16.5868 17.2572L17.1783 16.7752C17.4313 16.5691 17.5678 16.2524 17.544 15.9269C17.5201 15.6014 17.3389 15.308 17.0585 15.1409L15.3802 14.1409C15.0412 13.939 14.6152 13.9552 14.2925 14.1824Z" fill="#ffffff"></path> </g></svg>',
        'telegram': '<svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M41.4193 7.30899C41.4193 7.30899 45.3046 5.79399 44.9808 9.47328C44.8729 10.9883 43.9016 16.2908 43.1461 22.0262L40.5559 39.0159C40.5559 39.0159 40.3401 41.5048 38.3974 41.9377C36.4547 42.3705 33.5408 40.4227 33.0011 39.9898C32.5694 39.6652 24.9068 34.7955 22.2086 32.4148C21.4531 31.7655 20.5897 30.4669 22.3165 28.9519L33.6487 18.1305C34.9438 16.8319 36.2389 13.8019 30.8426 17.4812L15.7331 27.7616C15.7331 27.7616 14.0063 28.8437 10.7686 27.8698L3.75342 25.7055C3.75342 25.7055 1.16321 24.0823 5.58815 22.459C16.3807 17.3729 29.6555 12.1786 41.4193 7.30899Z" fill="#ffffff"></path> </g></svg>',
        'vk': '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path fill-rule="evenodd" clip-rule="evenodd" d="M3.4 3.4C2 4.81333 2 7.07333 2 11.6V12.4C2 16.92 2 19.18 3.4 20.6C4.81333 22 7.07333 22 11.6 22H12.4C16.92 22 19.18 22 20.6 20.6C22 19.1867 22 16.9267 22 12.4V11.6C22 7.08 22 4.82 20.6 3.4C19.1867 2 16.9267 2 12.4 2H11.6C7.08 2 4.82 2 3.4 3.4ZM5.37333 8.08667C5.48 13.2867 8.08 16.4067 12.64 16.4067H12.9067V13.4333C14.58 13.6 15.8467 14.8267 16.3533 16.4067H18.72C18.4773 15.5089 18.0469 14.6727 17.4574 13.9533C16.8679 13.234 16.1326 12.6478 15.3 12.2333C16.0461 11.779 16.6905 11.1756 17.1929 10.461C17.6953 9.7464 18.045 8.93585 18.22 8.08H16.0733C15.6067 9.73334 14.22 11.2333 12.9067 11.3733V8.08667H10.7533V13.8467C9.42 13.5133 7.74 11.9 7.66666 8.08667H5.37333Z" fill="#ffffff"></path> </g></svg>',
        'instagram': '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path fill-rule="evenodd" clip-rule="evenodd" d="M12 18C15.3137 18 18 15.3137 18 12C18 8.68629 15.3137 6 12 6C8.68629 6 6 8.68629 6 12C6 15.3137 8.68629 18 12 18ZM12 16C14.2091 16 16 14.2091 16 12C16 9.79086 14.2091 8 12 8C9.79086 8 8 9.79086 8 12C8 14.2091 9.79086 16 12 16Z" fill="#ffffff"></path> <path d="M18 5C17.4477 5 17 5.44772 17 6C17 6.55228 17.4477 7 18 7C18.5523 7 19 6.55228 19 6C19 5.44772 18.5523 5 18 5Z" fill="#ffffff"></path> <path fill-rule="evenodd" clip-rule="evenodd" d="M1.65396 4.27606C1 5.55953 1 7.23969 1 10.6V13.4C1 16.7603 1 18.4405 1.65396 19.7239C2.2292 20.8529 3.14708 21.7708 4.27606 22.346C5.55953 23 7.23969 23 10.6 23H13.4C16.7603 23 18.4405 23 19.7239 22.346C20.8529 21.7708 21.7708 20.8529 22.346 19.7239C23 18.4405 23 16.7603 23 13.4V10.6C23 7.23969 23 5.55953 22.346 4.27606C21.7708 3.14708 20.8529 2.2292 19.7239 1.65396C18.4405 1 16.7603 1 13.4 1H10.6C7.23969 1 5.55953 1 4.27606 1.65396C3.14708 2.2292 2.2292 3.14708 1.65396 4.27606ZM13.4 3H10.6C8.88684 3 7.72225 3.00156 6.82208 3.0751C5.94524 3.14674 5.49684 3.27659 5.18404 3.43597C4.43139 3.81947 3.81947 4.43139 3.43597 5.18404C3.27659 5.49684 3.14674 5.94524 3.0751 6.82208C3.00156 7.72225 3 8.88684 3 10.6V13.4C3 15.1132 3.00156 16.2777 3.0751 17.1779C3.14674 18.0548 3.27659 18.5032 3.43597 18.816C3.81947 19.5686 4.43139 20.1805 5.18404 20.564C5.49684 20.7234 5.94524 20.8533 6.82208 20.9249C7.72225 20.9984 8.88684 21 10.6 21H13.4C15.1132 21 16.2777 20.9984 17.1779 20.9249C18.0548 20.8533 18.5032 20.7234 18.816 20.564C19.5686 20.1805 20.1805 19.5686 20.564 18.816C20.7234 18.5032 20.8533 18.0548 20.9249 17.1779C20.9984 16.2777 21 15.1132 21 13.4V10.6C21 8.88684 20.9984 7.72225 20.9249 6.82208C20.8533 5.94524 20.7234 5.49684 20.564 5.18404C20.1805 4.43139 19.5686 3.81947 18.816 3.43597C18.5032 3.27659 18.0548 3.14674 17.1779 3.0751C16.2777 3.00156 15.1132 3 13.4 3Z" fill="#ffffff"></path> </g></svg>',
        'facebook': '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M20 12.05C19.9813 10.5255 19.5273 9.03809 18.6915 7.76295C17.8557 6.48781 16.673 5.47804 15.2826 4.85257C13.8921 4.2271 12.3519 4.01198 10.8433 4.23253C9.33473 4.45309 7.92057 5.10013 6.7674 6.09748C5.61422 7.09482 4.77005 8.40092 4.3343 9.86195C3.89856 11.323 3.88938 12.8781 4.30786 14.3442C4.72634 15.8103 5.55504 17.1262 6.69637 18.1371C7.83769 19.148 9.24412 19.8117 10.75 20.05V14.38H8.75001V12.05H10.75V10.28C10.7037 9.86846 10.7483 9.45175 10.8807 9.05931C11.0131 8.66687 11.23 8.30827 11.5161 8.00882C11.8022 7.70936 12.1505 7.47635 12.5365 7.32624C12.9225 7.17612 13.3368 7.11255 13.75 7.14003C14.3498 7.14824 14.9482 7.20173 15.54 7.30003V9.30003H14.54C14.3676 9.27828 14.1924 9.29556 14.0276 9.35059C13.8627 9.40562 13.7123 9.49699 13.5875 9.61795C13.4627 9.73891 13.3667 9.88637 13.3066 10.0494C13.2464 10.2125 13.2237 10.387 13.24 10.56V12.07H15.46L15.1 14.4H13.25V20C15.1399 19.7011 16.8601 18.7347 18.0985 17.2761C19.3369 15.8175 20.0115 13.9634 20 12.05Z" fill="#ffffff"></path> </g></svg>'
    }

    # Social media button configurations
    social_configs = {
        'whatsapp': {'buttonColor': '#25d366', 'hoverColor': '#12a649'},
        'telegram': {'buttonColor': '#0088cc', 'hoverColor': '#036ca1'},
        'vk': {'buttonColor': '#0077FF', 'hoverColor': '#045abd'},
        'instagram': {'buttonColor': '#d62976', 'hoverColor': '#a81b5a'},
        'facebook': {'buttonColor': '#4267B2', 'hoverColor': '#2b4a8a'}
    }

    # Build hoverButtons array
    hover_buttons = []
    social_data = [
        ('whatsapp', whatsapp_text, whatsapp_href),
        ('telegram', telegram_text, telegram_href),
        ('vk', vk_text, vk_href),
        ('instagram', instagram_text, instagram_href),
        ('facebook', facebook_text, facebook_href)
    ]

    for social, text, href in social_data:
        if href:  # Only add if href is not empty
            hover_buttons.append({
                'buttonColor': social_configs[social]['buttonColor'],
                'hoverColor': social_configs[social]['hoverColor'],
                'tooltipText': text if text else '',
                'href': href,
                'icon': icons[social]
            })

    # Generate embed code
    hover_buttons_json = json.dumps(hover_buttons, ensure_ascii=False, indent=16)

    embed_code = f'''<script src="https://andchir.github.io/api2app-chat-widget/api2app-chat-widget.js"></script>
<script>
    const chatWidget = new Api2AppChatWidget(
        '{app_embed_url}', {{
            buttonColor: '{button_color}',
            hoverColor: '{hover_color}',
            position: '{position}',
            width: {width},
            height: {height},
            tooltipText: '{button_text}',
            hoverButtons: {hover_buttons_json}
        }});
</script>'''

    output = {
        'success': True,
        'embed_code': embed_code
    }

    return HttpResponse(json.dumps(output, ensure_ascii=False), content_type='application/json; charset=utf-8', status=200)


@extend_schema(
    tags=['QR Code Generator'],
    request=QRCodeGeneratorRequestSerializer,
    responses={
        (200, 'application/json'): QRCodeGeneratorResponseSerializer,
        (422, 'application/json'): QRCodeGeneratorErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def qr_code_generator(request):
    """
    API endpoint for generating QR codes from text or URLs.
    """
    text = request.data.get('text')
    size = int(request.data.get('size', 10))
    border = int(request.data.get('border', 4))
    error_correction_map = {
        'L': qrcode.constants.ERROR_CORRECT_L,
        'M': qrcode.constants.ERROR_CORRECT_M,
        'Q': qrcode.constants.ERROR_CORRECT_Q,
        'H': qrcode.constants.ERROR_CORRECT_H
    }
    error_correction = error_correction_map.get(request.data.get('error_correction', 'M'))
    fill_color = request.data.get('fill_color', 'black')
    back_color = request.data.get('back_color', 'white')

    if not text:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Text field is required.'}),
            content_type='application/json',
            status=422
        )

    try:
        # Validate size and border
        if size < 1 or size > 40:
            size = 10
        if border < 0 or border > 10:
            border = 4

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=error_correction,
            box_size=size,
            border=border,
        )
        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color=fill_color, back_color=back_color)

        # Save to media directory
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'qrcodes'), exist_ok=True)
        delete_old_files(os.path.join(settings.MEDIA_ROOT, 'qrcodes'), max_hours=1)

        filename = f"qr-{uuid.uuid4()}.png"
        filepath = os.path.join(settings.MEDIA_ROOT, 'qrcodes', filename)
        img.save(filepath)

        host_url = "{}://{}".format(request.scheme, request.get_host())
        qr_code_url = f"{host_url}/media/qrcodes/{filename}"

        output = {
            'success': True,
            'qr_code_url': qr_code_url
        }

        return HttpResponse(json.dumps(output), content_type='application/json', status=200)

    except Exception as e:
        logger.error(f"QR Code generation error: {str(e)}")
        return HttpResponse(
            json.dumps({'success': False, 'message': f'QR code generation failed: {str(e)}'}),
            content_type='application/json',
            status=422
        )


@extend_schema(
    tags=['OCR Text Recognition'],
    request=OCRTextRecognitionRequestSerializer,
    responses={
        (200, 'application/json'): OCRTextRecognitionResponseSerializer,
        (422, 'application/json'): OCRTextRecognitionErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def ocr_text_recognition(request):
    """
    API endpoint for extracting text from images using OCR (pytesseract).
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return HttpResponse(
            json.dumps({
                'success': False,
                'message': 'OCR libraries not installed. Please install pytesseract and Tesseract-OCR.'
            }),
            content_type='application/json',
            status=422
        )

    image_file = request.FILES.get('image')
    language = request.data.get('language', 'eng')

    if not image_file:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Image file is required.'}),
            content_type='application/json',
            status=422
        )

    try:
        # Open image
        image = Image.open(image_file)

        # Perform OCR
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, lang=language, config=custom_config)

        # Get confidence data
        try:
            data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
            confidences = [float(conf) for conf in data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        except:
            avg_confidence = 0.0

        output = {
            'success': True,
            'text': text.strip(),
            'confidence': round(avg_confidence, 2)
        }

        return HttpResponse(json.dumps(output), content_type='application/json', status=200)

    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        return HttpResponse(
            json.dumps({'success': False, 'message': f'OCR processing failed: {str(e)}'}),
            content_type='application/json',
            status=422
        )


@extend_schema(
    tags=['Currency Converter'],
    request=CurrencyConverterRequestSerializer,
    responses={
        (200, 'application/json'): CurrencyConverterResponseSerializer,
        (422, 'application/json'): CurrencyConverterErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def currency_converter(request):
    """
    API endpoint for converting currencies using forex-python library.
    """
    try:
        from forex_python.converter import CurrencyRates
    except ImportError:
        return HttpResponse(
            json.dumps({
                'success': False,
                'message': 'Currency converter library not installed. Please install forex-python.'
            }),
            content_type='application/json',
            status=422
        )

    amount = request.data.get('amount')
    from_currency = request.data.get('from_currency', '').upper()
    to_currency = request.data.get('to_currency', '').upper()

    if not all([amount, from_currency, to_currency]):
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Amount, from_currency, and to_currency are required.'}),
            content_type='application/json',
            status=422
        )

    try:
        amount = float(amount)
        c = CurrencyRates()

        # Get exchange rate
        rate = c.get_rate(from_currency, to_currency)
        converted_amount = amount * rate

        output = {
            'success': True,
            'amount': amount,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'converted_amount': round(converted_amount, 2),
            'rate': round(rate, 6),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return HttpResponse(json.dumps(output), content_type='application/json', status=200)

    except ValueError as e:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Invalid amount value.'}),
            content_type='application/json',
            status=422
        )
    except Exception as e:
        logger.error(f"Currency conversion error: {str(e)}")
        return HttpResponse(
            json.dumps({'success': False, 'message': f'Currency conversion failed: {str(e)}'}),
            content_type='application/json',
            status=422
        )


@extend_schema(
    tags=['Weather API'],
    request=WeatherAPIRequestSerializer,
    responses={
        (200, 'application/json'): WeatherAPIResponseSerializer,
        (422, 'application/json'): WeatherAPIErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def weather_api(request):
    """
    API endpoint for getting weather information using python-weather library.
    """
    try:
        import python_weather
    except ImportError:
        return HttpResponse(
            json.dumps({
                'success': False,
                'message': 'Weather library not installed. Please install python-weather.'
            }),
            content_type='application/json',
            status=422
        )

    location = request.data.get('location')

    if not location:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Location field is required.'}),
            content_type='application/json',
            status=422
        )

    try:
        async def get_weather():
            async with python_weather.Client(unit=python_weather.METRIC) as client:
                weather = await client.get(location)
                return weather

        # Run async function
        weather = asyncio.run(get_weather())

        output = {
            'success': True,
            'location': location,
            'temperature': weather.temperature,
            'feels_like': weather.feels_like if hasattr(weather, 'feels_like') else weather.temperature,
            'humidity': weather.humidity if hasattr(weather, 'humidity') else 0,
            'pressure': weather.pressure if hasattr(weather, 'pressure') else 0,
            'wind_speed': weather.wind_speed if hasattr(weather, 'wind_speed') else 0.0,
            'description': weather.description if hasattr(weather, 'description') else str(weather.kind),
            'icon': str(weather.kind) if hasattr(weather, 'kind') else ''
        }

        return HttpResponse(json.dumps(output), content_type='application/json', status=200)

    except Exception as e:
        logger.error(f"Weather API error: {str(e)}")
        return HttpResponse(
            json.dumps({'success': False, 'message': f'Weather data retrieval failed: {str(e)}'}),
            content_type='application/json',
            status=422
        )


@extend_schema(
    tags=['Plagiarism Checker'],
    request=PlagiarismCheckerRequestSerializer,
    responses={
        (200, 'application/json'): PlagiarismCheckerResponseSerializer,
        (422, 'application/json'): PlagiarismCheckerErrorSerializer
    }
)
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([permissions.IsAuthenticated])
def plagiarism_checker(request):
    """
    API endpoint for checking text similarity/plagiarism using difflib or TF-IDF.
    """
    text1 = request.data.get('text1', '')
    text2 = request.data.get('text2', '')
    algorithm = request.data.get('algorithm', 'difflib')

    if not text1 or not text2:
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Both text1 and text2 are required.'}),
            content_type='application/json',
            status=422
        )

    try:
        similarity_percentage = 0.0
        details = {}

        if algorithm == 'difflib':
            # Use difflib SequenceMatcher
            matcher = difflib.SequenceMatcher(None, text1, text2)
            similarity_percentage = matcher.ratio() * 100

            # Get matching blocks for details
            matching_blocks = matcher.get_matching_blocks()
            details = {
                'matching_blocks_count': len(matching_blocks) - 1,  # Last one is dummy
                'longest_match_size': max([block.size for block in matching_blocks[:-1]], default=0)
            }

        elif algorithm == 'tfidf':
            # Use TF-IDF vectorization
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            similarity_percentage = similarity * 100

            details = {
                'cosine_similarity': round(similarity, 4),
                'vocabulary_size': len(vectorizer.vocabulary_)
            }

        # Determine if plagiarized (threshold: 70%)
        is_plagiarized = similarity_percentage >= 70.0

        output = {
            'success': True,
            'similarity_percentage': round(similarity_percentage, 2),
            'is_plagiarized': is_plagiarized,
            'algorithm': algorithm,
            'details': details
        }

        return HttpResponse(json.dumps(output), content_type='application/json', status=200)

    except Exception as e:
        logger.error(f"Plagiarism check error: {str(e)}")
        return HttpResponse(
            json.dumps({'success': False, 'message': f'Plagiarism check failed: {str(e)}'}),
            content_type='application/json',
            status=422
        )
