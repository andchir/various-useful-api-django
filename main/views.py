import json
from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, filters, generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination

from main.filters import IsOwnerFilterBackend, IsPublishedFilterBackend
from main.models import ProductModel, LogOwnerModel, LogItemModel
from main.serializers import UserSerializer, GroupSerializer, ProductModelSerializer, ProductModelListSerializer, \
    LogOwnerModelSerializer, LogItemsModelSerializer
from main.permissions import IsOwnerOnly


# Create your views here.
def index(request, exception=None):

    return HttpResponse('Welcome.')


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


@api_view(['POST'])
def create_log_record(request):
    uuid = request.GET['uuid'] if 'uuid' in request.GET else None

    if uuid is None:
        return HttpResponse(json.dumps({'success': True, 'message': 'Log owner not found.'}),
                            content_type='application/json', status=404)

    log_owner = LogOwnerModel.objects.filter(uuid=uuid, user=request.user).first()

    if log_owner is None:
        return HttpResponse(json.dumps({'success': True, 'message': 'Log owner not found.'}),
                            content_type='application/json', status=404)

    log_data = request.data
    if log_data is None or len(log_data.keys()) == 0:
        for key in request.GET:
            if key == 'uuid':
                continue
            log_data[key] = request.GET[key]

    log_item = LogItemModel()
    log_item.user = request.user
    log_item.owner = log_owner
    log_item.data = log_data

    log_item.save()

    output = {'success': True}

    return HttpResponse(json.dumps(output), content_type='application/json', status=200)
