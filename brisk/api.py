from models import *
from rest_framework import status, mixins, generics
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from serializers import *

class TopicList(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

    filter_fields = ('forum', 'user')
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class ForumList(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class ForumDetail(APIView):
    def get_object(self, pk):
        try:
            return Forum.objects.get(pk=pk)
        except Forum.DoesNotExist, e:
            raise Http404

    def get(self, request, pk, format=None):
        forum = self.get_object(pk)
        serializer = ForumSerializer(forum)
        return Response(serializer.data)

class CategoryList(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

class CategoryDetail(APIView):
    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist, e:
            raise Http404

    def get(self, request, pk, format=None):
        category = self.get_object(pk)
        serializer  = CategorySerializer(category)
        return Response(serializer.data)
