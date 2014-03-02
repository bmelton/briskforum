from django.conf.urls import patterns, include, url
# from voting.views import vote_on_object
# from models import Article
from forum import api

urlpatterns = patterns('',
    url(r'^$',                                                      'forum.views.home',                 name='home'),
    url(r'^api/forums/$',                                           api.ForumList.as_view()),
    url(r'^api/forums/(?P<pk>[0-9]+)/$',                            api.ForumDetail.as_view()),
    url(r'^api/topics/$',                                           api.TopicList.as_view()),
    # url(r'^api/topics/(?P<pk>[0-9]+)/$',                            api.ForumDetail.as_view()),
    url(r'^api/categories/$',                                       api.CategoryList.as_view()),
    url(r'^api/categories/(?P<pk>[0-9]+)/$',                        api.CategoryDetail.as_view()),

    url(r'^(?P<slug>[-\w]+)/$',                                     'forum.views.forum',                name='forum'),
    url(r'^(?P<forum>[-\w]+)/(?P<topic>[-\w]+)/$',                  'forum.views.topic',                name='topic'),
    url(r'^create/topic/(?P<forum>[-\w]+)/(?P<topic>[-\w]+)/$',     'forum.views.create_topic',         name='create_topic'),
    url(r'^create/topic/(?P<forum>[-\w]+)/$',                       'forum.views.create_topic',         name='create_topic'),
    url(r'^delete/topic/(?P<forum>[-\w]+)/(?P<topic>[-\w]+)/$',     'forum.views.delete_topic',         name='delete_topic'),
    # url(r'^(?P<object_id>\d+)/(?P<direction>up|down|clear)vote/?$', vote_on_object, article_dict,   name='vote'),
)


from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

