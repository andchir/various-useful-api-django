from django.contrib.auth import get_user_model
from django.contrib.auth.models import User, Group
from rest_framework import serializers

from main.models import ProductModel, ImageModel


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = get_user_model().objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'])
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super(UserSerializer, self).update(instance, validated_data)


class UserDataSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class ImageModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = '__all__'


class ProductModelSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    lookup_field = 'id'

    published = serializers.ReadOnlyField()
    images = ImageModelSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True
    )

    class Meta:
        model = ProductModel
        fields = '__all__'

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images')
        product = ProductModel.objects.create(**validated_data)
        print('uploaded_images', uploaded_images)

        for image in uploaded_images:
            ImageModel.objects.create(product=product, image=image)

        return product


class ProductModelListSerializer(serializers.HyperlinkedModelSerializer):
    lookup_field = 'id'
    user = UserDataSerializer(many=False, read_only=True)

    class Meta:
        model = ProductModel
        fields = ('url', 'id', 'date', 'date_created', 'name', 'user')
