from django.forms import widgets
from rest_framework import serializers
from models import Category, Forum, Topic
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'is_staff', 'is_active')

class ForumSerializer(serializers.ModelSerializer):
    category = serializers.Field(source='forum.category')
    moderators = UserSerializer(many=True)
    class Meta:
        model = Forum
        fields = ('id', 'name', 'slug', 'position', 'description', 'moderators', 'updated', 'active',)

class CategorySerializer(serializers.ModelSerializer):
    forums = ForumSerializer(many=True)
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'position', 'active', 'forums',)

class TopicSerializer(serializers.ModelSerializer):
    forum = ForumSerializer()
    user = UserSerializer()
    class Meta:
        model = Topic
        fields = ('id', 'forum', 'user', 'legacy_username', 'name', 'slug', 'created', 'modified', 'updated', 'poll', 'views', 'sticky', 'closed', 'active', 'post_count',)
