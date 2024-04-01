from django.contrib.auth import get_user_model
from django.contrib.auth.models import User, Group
from rest_framework import serializers

from main.models import ProductModel, ImageModel, LogOwnerModel, LogItemModel


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

        for image in uploaded_images:
            ImageModel.objects.create(product=product, image=image)

        return product


class ProductModelListSerializer(serializers.HyperlinkedModelSerializer):
    lookup_field = 'id'

    class Meta:
        model = ProductModel
        fields = ('url', 'id', 'date', 'date_created', 'name', 'price', 'price_currency', 'city', 'shop_name')


class LogOwnerModelSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    lookup_field = 'id'

    class Meta:
        model = LogOwnerModel
        fields = '__all__'


class LogItemsModelSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    lookup_field = 'id'

    class Meta:
        model = LogItemModel
        fields = '__all__'


class YoutubeDlRequestSerializer(serializers.Serializer):
    url = serializers.CharField()


class YoutubeDlStreamSerializer(serializers.Serializer):
    itag = serializers.IntegerField()
    type = serializers.CharField()
    mime_type = serializers.CharField()
    bitrate = serializers.IntegerField()
    fps = serializers.IntegerField()
    resolution = serializers.CharField()
    resolution_string = serializers.CharField()
    video_codec = serializers.CharField()
    audio_codec = serializers.CharField()


class YoutubeDlResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    author = serializers.CharField()
    channel_id = serializers.CharField()
    channel_url = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    video_id = serializers.CharField()
    thumbnail_url = serializers.CharField()
    length = serializers.IntegerField()
    publish_date = serializers.CharField()
    url = serializers.CharField()
    streams = YoutubeDlStreamSerializer(many=True)


class YoutubeDlRequestDownloadSerializer(serializers.Serializer):
    url = serializers.CharField()
    itag = serializers.IntegerField()


class YoutubeDlResponseDownloadSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    download_url = serializers.CharField()


class YoutubeDlResponseErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


class EdgeTtsVoiceSerializer(serializers.Serializer):
    Name = serializers.CharField()
    ShortName = serializers.CharField()
    Gender = serializers.CharField()
    Locale = serializers.CharField()
    SuggestedCodec = serializers.CharField()
    FriendlyName = serializers.CharField()
    Status = serializers.CharField()
    Language = serializers.CharField()


class EdgeTtsLanguageSerializer(serializers.Serializer):
    name = serializers.CharField()
    locale = serializers.CharField()
    code = serializers.CharField()


class EdgeTtsVoicesSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    voices = EdgeTtsVoiceSerializer(many=True)


class EdgeTtsLanguagesSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    languages = EdgeTtsLanguageSerializer(many=True)


class EdgeTtsVoicesRequestSerializer(serializers.Serializer):
    gender = serializers.CharField()


class PasswordGeneratorRequestSerializer(serializers.Serializer):
    minlen = serializers.IntegerField(default=8)
    maxlen = serializers.IntegerField(default=0)
    minschars = serializers.IntegerField(default=1)


class PasswordGeneratorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    password = serializers.CharField()
