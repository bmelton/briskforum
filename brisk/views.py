from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from models import Category, Forum, Topic, Post
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

def home(request):
    categories = []
    for category in Category.objects.filter(active=True):
        if category.has_access(request.user):
            categories.append(category)

    return render(request, "forum/index.html", {
        "categories"        : categories,
    })

def forum(request, slug):
    forum = get_object_or_404(Forum, active=True, slug=slug)
    topic_list = Topic.objects.filter(forum=forum).order_by('-sticky', '-id')
    
    paginator = Paginator(topic_list, 20)

    page = request.GET.get("page")
    try: 
        topics = paginator.page(page)
    except PageNotAnInteger:
        topics = paginator.page(1)
    except EmptyPage:
        topics = paginator.page(topics.num_pages)

    return render(request, "forum/forum.html", {
        "forum"             : forum,
        "topics"            : topics,
    })

@login_required
def delete_topic(request, forum, topic):
    topic = get_object_or_404(Topic, forum__slug=forum, pk=topic)
    if request.user.is_superuser:
        url = topic.forum.get_absolute_url()
        topic.delete()
        return redirect(url)
    return HttpResponse(topic)

def create_topic(request, forum, topic=None):
    from forms import TopicForm, PostForm, AddPostForm, EditPostForm
    from django import forms

    forum = get_object_or_404(Forum, active=True, slug=forum)
    if request.method == "GET":
        if topic:
            topic       = get_object_or_404(Topic, id=topic)
            apf         = EditPostForm(topic=topic, instance=topic.get_body)
        else:
            apf         = AddPostForm()

        return render(request, "forum/create_topic.html", {
            "forum"         : forum,
            "apf"           : apf,
        })
    if request.method == "POST":
        ip = request.META.get('HTTP_X_FORWARDED_FOR', None)
        post_form_kwargs = {
            "forum"     : forum, 
            "user"      : request.user, 
            "ip"        : ip, 
        }

        apf         = AddPostForm(request.POST, **post_form_kwargs)
        if apf.is_valid():
            url = reverse('forum:forum', args=[str(forum.slug),])
            apf.save()
            return redirect(url)
        else:
            return HttpResponse("Invalid")

def topic(request, forum, topic):
    topic = get_object_or_404(Topic, slug=topic)
    topic.views += 1
    topic.save()
    paginator = Paginator(topic.posts.all(), 20)

    page = request.GET.get("page")
    try:
        posts   = paginator.page(page)
    except PageNotAnInteger:
        posts   = paginator.page(1)
    except EmptyPage:
        posts   = paginator.page(posts.num_pages)

    return render(request, "forum/topic.html", {
        "topic"             : topic,
        "posts"             : posts,
    })
