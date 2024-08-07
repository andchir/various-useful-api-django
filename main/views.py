import asyncio
import json
import os
import uuid

import yt_dlp
from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from password_generator import PasswordGenerator
from rest_framework import status, viewsets, filters, generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination

from app import settings
from main.filters import IsOwnerFilterBackend, IsPublishedFilterBackend
from main.lib import edge_tts_find_voice, edge_tts_create_audio, delete_old_files, edge_tts_locales
from main.models import ProductModel, LogOwnerModel, LogItemModel
from main.serializers import UserSerializer, GroupSerializer, ProductModelSerializer, ProductModelListSerializer, \
    LogOwnerModelSerializer, LogItemsModelSerializer, YoutubeDlRequestSerializer, YoutubeDlResponseDownloadSerializer, \
    YoutubeDlResponseSerializer, YoutubeDlRequestDownloadSerializer, YoutubeDlResponseErrorSerializer, \
    EdgeTtsVoicesSerializer, EdgeTtsLanguagesSerializer, EdgeTtsVoicesRequestSerializer, PasswordGeneratorSerializer, \
    PasswordGeneratorRequestSerializer
from main.permissions import IsOwnerOnly
# from pytube import YouTube
from pytubefix import YouTube


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
def yt_dlp_info(request):
    """
        API endpoint for information about the video from YouTube.
        """
    url = request.data['url'] if 'url' in request.data else None

    if url is None:
        return HttpResponse(json.dumps({'success': False, 'message': 'There are no required fields.'}),
                            content_type='application/json', status=422)

    def format_selector(ctx):
        """ Select the best video and the best audio that won't result in an mkv.
        NOTE: This is just an example and does not handle all cases """

        # formats are already sorted worst to best
        formats = ctx.get('formats')[::-1]

        # acodec='none' means there is no audio
        best_video = next(f for f in formats
                          if f['vcodec'] != 'none' and f['acodec'] == 'none')

        # find compatible audio extension
        audio_ext = {'mp4': 'm4a', 'webm': 'webm'}[best_video['ext']]
        # vcodec='none' means there is no video
        best_audio = next(f for f in formats if (
                f['acodec'] != 'none' and f['vcodec'] == 'none' and f['ext'] == audio_ext))

        # These are the minimum required fields for a merged format
        yield {
            'format_id': f'{best_video["format_id"]}+{best_audio["format_id"]}',
            'ext': best_video['ext'],
            'requested_formats': [best_video, best_audio],
            # Must be + separated list of protocols
            'protocol': f'{best_video["protocol"]}+{best_audio["protocol"]}'
        }

    ydl_opts = {
        'format': format_selector
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        data = ydl.sanitize_info(info)

        print(data)

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
    tags=['EdgeTTS'],
    responses={
        (200, 'application/json'): EdgeTtsVoicesSerializer
    }
)
@api_view(['GET'])
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
    responses={
        (200, 'audio/mpeg'): bytes
    }
)
@api_view(['POST'])
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

    f = open(audio_file_path, 'rb')
    response = HttpResponse()
    response.write(f.read())
    response['Content-Type'] = 'audio/mpeg'
    response['Content-Length'] = os.path.getsize(audio_file_path)

    return response


@extend_schema(
    tags=['Password generator'],
    request=PasswordGeneratorRequestSerializer,
    responses={
        (200, 'application/json'): PasswordGeneratorSerializer
    }
)
@api_view(['POST'])
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
