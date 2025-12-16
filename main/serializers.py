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
    download = serializers.BooleanField()


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


class EdgeTtsRequestSerializer(serializers.Serializer):
    text = serializers.CharField()


class EdgeTtsLanguagesSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    languages = EdgeTtsLanguageSerializer(many=True)


class EdgeTtsVoicesRequestSerializer(serializers.Serializer):
    gender = serializers.CharField()


class EdgeTtsResponseSerializer(serializers.Serializer):
    audio = serializers.CharField()


class PasswordGeneratorRequestSerializer(serializers.Serializer):
    minlen = serializers.IntegerField(default=8)
    maxlen = serializers.IntegerField(default=0)
    minschars = serializers.IntegerField(default=1)
    use_schars = serializers.BooleanField(default=True)


class PasswordGeneratorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    password = serializers.CharField()

class FactCheckExplorerRequestSerializer(serializers.Serializer):
    query = serializers.CharField()
    language = serializers.CharField()
    num_results = serializers.IntegerField(default=200)


class FactCheckExplorerSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    download_url = serializers.CharField()
    data = serializers.ListField(child=serializers.CharField())


class YandexDiskUploadResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    file_url = serializers.CharField()
    public_url = serializers.CharField()
    details = serializers.CharField()


class YandexGPTResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    result = serializers.CharField()


class GoogleTtsLanguageSerializer(serializers.Serializer):
    name = serializers.CharField()
    locale = serializers.CharField()


class GoogleTtsLanguagesSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    languages = GoogleTtsLanguageSerializer(many=True)


class GoogleTransOutputSerializer(serializers.Serializer):
    text = serializers.CharField()
    lang_src = serializers.CharField()
    lang_dest = serializers.CharField()


class GoogleTransRequestSerializer(serializers.Serializer):
    lang_src = serializers.CharField()
    lang_dest = serializers.CharField()
    text = serializers.CharField()


class GoogleTTSRequestSerializer(serializers.Serializer):
    lang_dest = serializers.CharField()
    text = serializers.CharField()
    slow = serializers.BooleanField()


class GoogleTTSResponseSerializer(serializers.Serializer):
    audio = serializers.CharField()

class OpenAIEmbeddingsResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    store_uuid = serializers.CharField()

class OpenAIEmbeddingsQuestionResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    answer = serializers.CharField()

class VideoFrameExtractionRequestSerializer(serializers.Serializer):
    second = serializers.FloatField(default=0, required=False)
    is_last = serializers.BooleanField(default=False, required=False)

class VideoFrameExtractionResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    image_url = serializers.CharField()

class VideoFrameExtractionErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()

class VideoAudioReplacementRequestSerializer(serializers.Serializer):
    pass  # Files are handled via multipart/form-data

class VideoAudioReplacementResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    video_url = serializers.CharField()

class VideoAudioReplacementErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
