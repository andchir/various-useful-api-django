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

class VideoTrimRequestSerializer(serializers.Serializer):
    second_start = serializers.FloatField(default=0, required=False)
    second_end = serializers.FloatField(required=False)

class VideoTrimResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    video_url = serializers.CharField()

class VideoTrimErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()

class VideoConcatenationRequestSerializer(serializers.Serializer):
    pass  # Files are handled via multipart/form-data

class VideoConcatenationResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    video_url = serializers.CharField()

class VideoConcatenationErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()

class WebsiteScreenshotRequestSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)
    width = serializers.IntegerField(required=True, min_value=1, max_value=3840)
    height = serializers.IntegerField(required=True, min_value=1, max_value=2160)
    full = serializers.BooleanField(default=False, required=False)
    crop_left = serializers.IntegerField(default=0, required=False, min_value=0)
    crop_top = serializers.IntegerField(default=0, required=False, min_value=0)
    crop_width = serializers.IntegerField(default=0, required=False, min_value=0)
    crop_height = serializers.IntegerField(default=0, required=False, min_value=0)

class WebsiteScreenshotResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    screenshot_url = serializers.CharField()

class WebsiteScreenshotErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()

class WidgetEmbedCodeRequestSerializer(serializers.Serializer):
    app_embed_url = serializers.URLField(required=True)
    button_color = serializers.CharField(required=False, default='#007bff')
    hover_color = serializers.CharField(required=False, default='#0056b3')
    position = serializers.ChoiceField(
        choices=['bottom-right', 'bottom-left', 'top-right', 'top-left'],
        default='bottom-right',
        required=False
    )
    width = serializers.IntegerField(default=350, required=False, min_value=1)
    height = serializers.IntegerField(default=465, required=False, min_value=1)
    button_text = serializers.CharField(required=False, default='Открыть чат')

    whatsapp_text = serializers.CharField(required=False, allow_blank=True, default='')
    whatsapp_href = serializers.URLField(required=False, allow_blank=True, default='')
    telegram_text = serializers.CharField(required=False, allow_blank=True, default='')
    telegram_href = serializers.URLField(required=False, allow_blank=True, default='')
    vk_text = serializers.CharField(required=False, allow_blank=True, default='')
    vk_href = serializers.URLField(required=False, allow_blank=True, default='')
    instagram_text = serializers.CharField(required=False, allow_blank=True, default='')
    instagram_href = serializers.URLField(required=False, allow_blank=True, default='')
    facebook_text = serializers.CharField(required=False, allow_blank=True, default='')
    facebook_href = serializers.URLField(required=False, allow_blank=True, default='')
    youtube_text = serializers.CharField(required=False, allow_blank=True, default='')
    youtube_href = serializers.URLField(required=False, allow_blank=True, default='')
    tiktok_text = serializers.CharField(required=False, allow_blank=True, default='')
    tiktok_href = serializers.URLField(required=False, allow_blank=True, default='')

class WidgetEmbedCodeResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    embed_code = serializers.CharField()

class WidgetEmbedCodeErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


# QR Code Generator Serializers
class QRCodeGeneratorRequestSerializer(serializers.Serializer):
    text = serializers.CharField(help_text="Text or URL to encode in QR code")
    size = serializers.IntegerField(default=10, required=False, help_text="Box size (1-40)")
    border = serializers.IntegerField(default=4, required=False, help_text="Border size in boxes")
    error_correction = serializers.ChoiceField(
        choices=['L', 'M', 'Q', 'H'],
        default='M',
        required=False,
        help_text="Error correction level: L(7%), M(15%), Q(25%), H(30%)"
    )
    fill_color = serializers.CharField(default='black', required=False, help_text="Fill color")
    back_color = serializers.CharField(default='white', required=False, help_text="Background color")


class QRCodeGeneratorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    qr_code_url = serializers.CharField()


class QRCodeGeneratorErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


# OCR Text Recognition Serializers
class OCRTextRecognitionRequestSerializer(serializers.Serializer):
    image = serializers.ImageField(help_text="Image file to extract text from")
    language = serializers.CharField(
        default='eng',
        required=False,
        help_text="Language code (eng, rus, etc.)"
    )


class OCRTextRecognitionResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    text = serializers.CharField()
    confidence = serializers.FloatField()


class OCRTextRecognitionErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


# Currency Converter Serializers
class CurrencyConverterRequestSerializer(serializers.Serializer):
    amount = serializers.FloatField(help_text="Amount to convert")
    from_currency = serializers.CharField(help_text="Source currency code (USD, EUR, RUB, etc.)")
    to_currency = serializers.CharField(help_text="Target currency code (USD, EUR, RUB, etc.)")


class CurrencyConverterResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    amount = serializers.FloatField()
    from_currency = serializers.CharField()
    to_currency = serializers.CharField()
    converted_amount = serializers.FloatField()
    rate = serializers.FloatField()
    date = serializers.CharField()


class CurrencyConverterErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


# Weather API Serializers
class WeatherAPIRequestSerializer(serializers.Serializer):
    location = serializers.CharField(help_text="City name or coordinates (lat,lon)")


class WeatherAPIResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    location = serializers.CharField()
    temperature = serializers.FloatField()
    feels_like = serializers.FloatField()
    humidity = serializers.IntegerField()
    pressure = serializers.IntegerField()
    wind_speed = serializers.FloatField()
    description = serializers.CharField()
    icon = serializers.CharField()


class WeatherAPIErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


# Plagiarism Checker Serializers
class PlagiarismCheckerRequestSerializer(serializers.Serializer):
    text1 = serializers.CharField(help_text="First text to compare")
    text2 = serializers.CharField(help_text="Second text to compare")
    algorithm = serializers.ChoiceField(
        choices=['difflib', 'tfidf'],
        default='difflib',
        required=False,
        help_text="Comparison algorithm"
    )


class PlagiarismCheckerResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    similarity_percentage = serializers.FloatField()
    is_plagiarized = serializers.BooleanField()
    algorithm = serializers.CharField()
    details = serializers.DictField()


class PlagiarismCheckerErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


# CSS APIs Serializers

# 1. SVG to CSS background-image URL
class SvgToCssBackgroundRequestSerializer(serializers.Serializer):
    svg_code = serializers.CharField(help_text="SVG code to convert to CSS background-image URL")


class SvgToCssBackgroundResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    css_url = serializers.CharField()
    css_code = serializers.CharField()


class SvgToCssBackgroundErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


# 2. CSS Gradient Generator
class CssGradientColorStopSerializer(serializers.Serializer):
    color = serializers.CharField()
    position = serializers.IntegerField(required=False)


class CssGradientRequestSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=['linear', 'radial', 'conic'],
        default='linear',
        help_text="Gradient type: linear, radial, or conic"
    )
    colors = CssGradientColorStopSerializer(many=True, help_text="Array of color stops")
    angle = serializers.IntegerField(default=180, required=False, help_text="Angle in degrees (for linear gradient)")
    shape = serializers.ChoiceField(
        choices=['circle', 'ellipse'],
        default='ellipse',
        required=False,
        help_text="Shape for radial gradient"
    )
    position = serializers.CharField(default='center', required=False, help_text="Position (center, top left, etc.)")


class CssGradientResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    css_code = serializers.CharField()
    type = serializers.CharField()


class CssGradientErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


# 3. CSS Box Shadow Generator
class CssBoxShadowRequestSerializer(serializers.Serializer):
    h_offset = serializers.IntegerField(default=0, help_text="Horizontal offset in pixels")
    v_offset = serializers.IntegerField(default=0, help_text="Vertical offset in pixels")
    blur = serializers.IntegerField(default=10, help_text="Blur radius in pixels")
    spread = serializers.IntegerField(default=0, required=False, help_text="Spread radius in pixels")
    color = serializers.CharField(default='rgba(0, 0, 0, 0.5)', help_text="Shadow color")
    inset = serializers.BooleanField(default=False, required=False, help_text="Inset shadow")


class CssBoxShadowResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    css_code = serializers.CharField()


class CssBoxShadowErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


# 4. CSS Transform Generator
class CssTransformOperationSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=['rotate', 'scale', 'scaleX', 'scaleY', 'translate', 'translateX', 'translateY', 'skew', 'skewX', 'skewY'],
        help_text="Transform operation type"
    )
    value = serializers.CharField(help_text="Transform value (e.g., '45deg', '1.5', '20px')")


class CssTransformRequestSerializer(serializers.Serializer):
    operations = CssTransformOperationSerializer(many=True, help_text="Array of transform operations")


class CssTransformResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    css_code = serializers.CharField()


class CssTransformErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


# 5. CSS Animation/Keyframes Generator
class CssKeyframeSerializer(serializers.Serializer):
    percentage = serializers.IntegerField(help_text="Keyframe percentage (0-100)")
    properties = serializers.DictField(help_text="CSS properties for this keyframe")


class CssAnimationRequestSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="Animation name")
    keyframes = CssKeyframeSerializer(many=True, help_text="Array of keyframe definitions")
    duration = serializers.CharField(default='1s', required=False, help_text="Animation duration (e.g., '1s', '500ms')")
    timing_function = serializers.ChoiceField(
        choices=['ease', 'linear', 'ease-in', 'ease-out', 'ease-in-out'],
        default='ease',
        required=False,
        help_text="Timing function"
    )
    iteration_count = serializers.CharField(default='1', required=False, help_text="Iteration count (number or 'infinite')")
    direction = serializers.ChoiceField(
        choices=['normal', 'reverse', 'alternate', 'alternate-reverse'],
        default='normal',
        required=False,
        help_text="Animation direction"
    )
    fill_mode = serializers.ChoiceField(
        choices=['none', 'forwards', 'backwards', 'both'],
        default='none',
        required=False,
        help_text="Fill mode"
    )


class CssAnimationResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    keyframes_code = serializers.CharField()
    animation_code = serializers.CharField()


class CssAnimationErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


# 6. CSS Filter Effects Generator
class CssFilterOperationSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=['blur', 'brightness', 'contrast', 'grayscale', 'hue-rotate', 'invert', 'opacity', 'saturate', 'sepia', 'drop-shadow'],
        help_text="Filter type"
    )
    value = serializers.CharField(help_text="Filter value (e.g., '5px', '1.5', '120deg', '0.5')")


class CssFilterRequestSerializer(serializers.Serializer):
    filters = CssFilterOperationSerializer(many=True, help_text="Array of filter operations")


class CssFilterResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    css_code = serializers.CharField()


class CssFilterErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
