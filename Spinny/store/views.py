from .models import Box
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.settings import api_settings
from .serializers import BoxCreateSerializers, BoxOnlyLBHSerializers, BoxSerializers
from datetime import timedelta
from django.utils import timezone
from Spinny.settings import A1, V1, L1, L2
from store.filters import BoxFilter
from rest_framework.decorators import action

# Create your views here.


class BoxViewSet(ModelViewSet):
    queryset = Box.objects.all()
    serializer_class = BoxSerializers
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return BoxCreateSerializers
        elif self.action == 'list' or self.action == "retrieve" or self.action == "my_box":
            if self.request.user.is_staff == True:
                return BoxSerializers
            else:
                return BoxOnlyLBHSerializers
        else:
            return BoxOnlyLBHSerializers

    def get_queryset(self):
        return BoxFilter(self.request.GET,queryset=self.queryset).qs

    def validate_create(self, request):
        if request.user and request.user.is_staff:
            length = int(request.data.get("length", 0))
            width = int(request.data.get("width", 0))
            height = int(request.data.get("height", 0))
            one_week_ago = timezone.now().date() - timedelta(days=7)
            box_created = self.get_queryset()
            if box_created.filter(created_on__gte=one_week_ago).count() >= L1:
                raise Exception(f"Created box count in a week exceeded by {L1}")

            box_created_by_user = box_created.filter(created_by=request.user.id)
            if box_created_by_user.filter(created_on__gte=one_week_ago).count() >= L2:
                raise Exception(f" Created Box count by an user exceeded by {L2}")

            area = sum(box_created.values_list('area', flat=True))
            new_area = 2 * ((length * width) + (length * height) + (width * height))
            if (area + new_area)/( len(box_created) + 1) >= A1:
                raise Exception(f"Area exceeded by {A1}")

            volume = sum(box_created_by_user.values_list('volume', flat=True))
            new_volume = length * width * height
            if (volume+new_volume)/(len(box_created_by_user) + 1) >= V1:
                raise Exception(f"Volume exceeded by {V1}")
        else:
            raise Exception("User is not authorized to add a new box.")

    def validate_update(self, request, instance):
        if request.user and request.user.is_staff:
            length = int(request.data.get("length", 0))
            width = int(request.data.get("width", 0))
            height = int(request.data.get("height", 0))
            one_week_ago = timezone.now().date() - timedelta(days=7)
            box_created = self.get_queryset()
            if box_created.filter(created_on__gte=one_week_ago).count() > L1:
                raise Exception(f"Created box count in a week exceeded by {L1}")

            box_created_by_user = box_created.filter(created_by=request.user.id)
            if box_created_by_user.filter(created_on__gte=one_week_ago).count() > L2:
                raise Exception(f" Created Box count by an user exceeded by {L2}")

            area = sum(box_created.values_list('area', flat=True)) - instance.area
            new_area = 2 * ((length * width) + (length * height) + (width * height))
            if (area + new_area)/( len(box_created)) > A1:
                raise Exception(f"Area exceeded by {A1}")

            volume = sum(box_created_by_user.values_list('volume', flat=True)) - instance.volume
            new_volume = length * width * height
            if (volume+new_volume)/(len(box_created_by_user)) > V1:
                raise Exception(f"Volume exceeded by {V1}")
        else:
            raise Exception("User is not authorized to add a new box.")

    def create(self, request, *args, **kwargs):
        self.validate_create(request)
        data = {
            "length": request.data.get("length", 0),
            "width": request.data.get("width", 0),
            "height": request.data.get("height", 0),
            "created_by": request.user.id
        }
        serializer = self.get_serializer(data=data, many=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_success_headers(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self.validate_update(request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id == instance.created_by.id:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise Exception("Not authorized to delete.")

    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def my_box(self, request, *args, **kwargs):
        if request.user.is_staff:
            queryset = self.get_queryset().filter(created_by=request.user.id)
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        else:
            raise Exception("Not Authorized")