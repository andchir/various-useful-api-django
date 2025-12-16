import asyncio
import json
import os
import subprocess
import tempfile
import urllib
import uuid
import logging
import requests
import googletrans
import gtts
from factcheckexplorer.factcheckexplorer import FactCheckLib
import yt_dlp
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
    VideoFrameExtractionResponseSerializer, VideoFrameExtractionErrorSerializer
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
    description='Download file by URL',
    summary='Download file',
    parameters=[
        OpenApiParameter(
            name='url',
            description='File URL to download',
            required=True,
            type=str,
            location=OpenApiParameter.QUERY
        ),
    ],
    methods=['GET']
)
@api_view(['GET'])
def download_file(request):
    file_url = request.GET.get('url')

    if not file_url:
        return Response(
            {'error': 'The \'url\' parameter is required.'},
            status=400
        )

    if is_internal_url(file_url, request):
        return Response(
            {'error': 'Forbidden URL.'},
            status=403
        )

    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            with urllib.request.urlopen(file_url) as response:
                tmp_file.write(response.read())
                content_type = response.headers.get('Content-Type', 'application/octet-stream')
                headers = response.headers

            filename = get_safe_filename(
                file_url,
                content_type,
                headers
            )

            file = open(tmp_file.name, 'rb')
            response = FileResponse(file)

            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Type'] = 'application/octet-stream'

            return response

    except Exception as e:
        return Response(
            {'error': f'Error downloading file: {str(e)}'},
            status=400
        )


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

    # Create frames directory if it doesn't exist
    frames_dir = os.path.join(settings.MEDIA_ROOT, 'frames')
    if not os.path.isdir(frames_dir):
        os.makedirs(frames_dir)

    # Delete old files
    delete_old_files(frames_dir, max_hours=1)

    # Generate unique filename for the output frame
    frame_uuid = uuid.uuid1()
    output_file_path = os.path.join(frames_dir, f'{frame_uuid}.jpg')

    try:
        # Save uploaded video to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video_file.name)[1]) as temp_video:
            for chunk in video_file.chunks():
                temp_video.write(chunk)
            temp_video_path = temp_video.name

        # Prepare ffmpeg command
        ffmpeg_path = '/usr/bin/ffmpeg'

        if is_last:
            # Extract the last frame
            # First, get video duration
            probe_cmd = [
                ffmpeg_path,
                '-i', temp_video_path,
                '-hide_banner'
            ]

            try:
                probe_result = subprocess.run(
                    probe_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # Parse duration from ffmpeg output
                duration_str = None
                for line in probe_result.stderr.split('\n'):
                    if 'Duration:' in line:
                        duration_str = line.split('Duration:')[1].split(',')[0].strip()
                        break

                if duration_str:
                    # Convert duration to seconds
                    time_parts = duration_str.split(':')
                    duration_seconds = float(time_parts[0]) * 3600 + float(time_parts[1]) * 60 + float(time_parts[2])
                    # Seek to a moment slightly before the end to ensure we get a frame
                    seek_time = max(0, duration_seconds - 0.1)
                else:
                    # If we can't determine duration, use reverse seeking
                    seek_time = None
            except subprocess.TimeoutExpired:
                os.unlink(temp_video_path)
                return HttpResponse(
                    json.dumps({'success': False, 'message': 'Video processing timeout.'}),
                    content_type='application/json',
                    status=422
                )
            except Exception as e:
                os.unlink(temp_video_path)
                return HttpResponse(
                    json.dumps({'success': False, 'message': f'Error processing video: {str(e)}'}),
                    content_type='application/json',
                    status=422
                )

            if seek_time is not None:
                # Extract frame from calculated position
                cmd = [
                    ffmpeg_path,
                    '-ss', str(seek_time),
                    '-i', temp_video_path,
                    '-vframes', '1',
                    '-q:v', '2',  # High quality (2-5 is good, lower is better)
                    '-y',
                    output_file_path
                ]
            else:
                # Alternative: use sseof to seek from end
                cmd = [
                    ffmpeg_path,
                    '-sseof', '-0.1',
                    '-i', temp_video_path,
                    '-update', '1',
                    '-q:v', '2',
                    '-y',
                    output_file_path
                ]
        else:
            # Extract frame at specified second
            cmd = [
                ffmpeg_path,
                '-ss', str(second),
                '-i', temp_video_path,
                '-vframes', '1',
                '-q:v', '2',  # High quality JPG
                '-y',
                output_file_path
            ]

        # Execute ffmpeg command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Clean up temporary video file
        os.unlink(temp_video_path)

        if result.returncode != 0:
            logger.error(f'FFmpeg error: {result.stderr}')
            return HttpResponse(
                json.dumps({'success': False, 'message': 'Failed to extract frame from video.'}),
                content_type='application/json',
                status=422
            )

        # Check if output file was created
        if not os.path.exists(output_file_path):
            return HttpResponse(
                json.dumps({'success': False, 'message': 'Frame extraction failed.'}),
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

    except subprocess.TimeoutExpired:
        if os.path.exists(temp_video_path):
            os.unlink(temp_video_path)
        return HttpResponse(
            json.dumps({'success': False, 'message': 'Video processing timeout.'}),
            content_type='application/json',
            status=422
        )
    except Exception as e:
        logger.error(f'Error extracting video frame: {str(e)}')
        if os.path.exists(temp_video_path):
            os.unlink(temp_video_path)
        return HttpResponse(
            json.dumps({'success': False, 'message': f'Error: {str(e)}'}),
            content_type='application/json',
            status=422
        )
