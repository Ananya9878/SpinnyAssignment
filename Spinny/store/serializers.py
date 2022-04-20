from .models import Box
from django.contrib.auth.models import User
from rest_framework.serializers import ModelSerializer


class UserSerializers(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]


class BoxCreateSerializers(ModelSerializer):
    class Meta:
        model = Box
        fields = ['length', 'width', 'height', "created_by" ]


class BoxOnlyLBHSerializers(ModelSerializer):
    class Meta:
        model = Box
        fields = ['length', 'width', 'height']


class BoxSerializers(ModelSerializer):
    created_by = UserSerializers(many=False)

    class Meta:
        model = Box
        depth = 1
        fields = '__all__'


