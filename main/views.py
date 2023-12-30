import os
from django.http import HttpResponse
from django.shortcuts import render
from django.template import Template, Context
from django.contrib.auth.models import User, Group
from rest_framework import status, viewsets, filters
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination

from main.filters import IsOwnerFilterBackend, IsPublishedFilterBackend
from main.models import ProductModel
from main.serializers import UserSerializer, GroupSerializer, ProductModelSerializer, ProductModelListSerializer
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
    queryset = ProductModel.objects.all()
    serializer_class = ProductModelSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOnly]
    pagination_class = ItemsListPagination

    filter_backends = [IsOwnerFilterBackend, IsPublishedFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'shop_name', 'city']
    ordering_fields = ['date_created', 'date', 'name']
    ordering = ['-date']

    def list(self, request):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductModelListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ProductModelListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
