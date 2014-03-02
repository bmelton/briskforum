from django.forms import ModelForm
from models import *
from django import forms
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User


"""
class Category(models.Model):
    old_category_id             = models.PositiveIntegerField(_('Old Category'), null=True, blank=True)
    name                        = models.CharField(_('Name'), max_length=80)
    groups                      = models.ManyToManyField(Group, blank=True, verbose_name=_('Groups'), help_text=('Only visible to members of these groups'))
    slug                        = models.CharField(_('Slug'), max_length=80, null=True, blank=True)
    position                    = models.PositiveIntegerField(_('Position'), blank=True, default=0)
    active                      = models.BooleanField(_('Active'), blank=True, default=False)

class Forum(models.Model):
    old_forum_id                = models.PositiveIntegerField(_('Old Forum'), null=True, blank=True)
    category                    = models.ForeignKey(Category, related_name='forums', verbose_name=_('Category'))
    name                        = models.CharField(_('Name'), max_length=80)
    slug                        = models.CharField(_('Slug'), max_length=80, null=True, blank=True)
    position                    = models.PositiveIntegerField(_('Position'), blank=True, default=0)
    description                 = models.TextField(_('Description'), blank=True, default='')
    moderators                  = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, null=True, verbose_name=_('Moderators'))
    updated                     = models.DateTimeField(_('Updated'), auto_now=True)
    post_count                  = models.PositiveIntegerField(_('Post Count'), blank=True, default=0)
    topic_count                 = models.PositiveIntegerField(_('Topic Count'), blank=True, default=0)
    last_post                   = models.ForeignKey('Post', related_name='last_forum_post', blank=True, null=True)
    active                      = models.BooleanField(_('Active'), blank=True, default=False)

class Topic(models.Model):
    forum                       = models.ForeignKey(Forum, related_name='topics', verbose_name=_('Forums'))
    user                        = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('User'), null=True, blank=True)
    # TODO - Revert null=True, blank=True to both be False
    legacy_username             = models.CharField(_('Legacy Username'), max_length=80, null=True, blank=True)
    # TODO - Revert null=True, blank=True to both be False
    name                        = models.CharField(_('Subject'), max_length=255, null=True, blank=True)
    slug                        = models.CharField(_('Slug'), max_length=255, null=True, blank=True)
    old_topic_id                = models.PositiveIntegerField(_('Old Topic'), null=True, blank=True)
    created                     = models.DateTimeField(_('Created'), null=True, blank=True)
    modified                    = models.DateTimeField(_('Modified'), null=True, blank=True)
    updated                     = models.DateTimeField(_('Updated'), null=True, blank=True)
    views                       = models.PositiveIntegerField(_('View count'), blank=True, default=0)
    sticky                      = models.BooleanField(_('Sticky'), blank=True, default=False)
    closed                      = models.BooleanField(_('Closed'), blank=True, default=False)
    active                      = models.BooleanField(_('Active'), blank=True, default=False)
    post_count                  = models.PositiveIntegerField(_('Post count'), blank=True, default=0)
    last_post                   = models.ForeignKey('Post', related_name='last_topic_post', blank=True, null=True)
    user_ip                     = models.GenericIPAddressField(_('User IP'), null=True, blank=True)

"""

class TopicForm(ModelForm):
    class Meta:
        model   = Topic
        fields  = ["forum", "name", "sticky"]

"""
class Post(models.Model):
    topic                       = models.ForeignKey(Topic, related_name='posts', verbose_name=_('Topic'))
    old_post_id                 = models.PositiveIntegerField(_('Old Post'), null=True, blank=True)
    uuid                        = models.CharField(_('Unique ID'), max_length=10, null=True, blank=True)
    user                        = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='posts', verbose_name=_('User'), null=True, blank=True)
    legacy_username             = models.CharField(max_length=80, null=True, blank=True)
    name                        = models.CharField(_('Subject'), max_length=255, null=True, blank=True)
    created                     = models.DateTimeField(_('Created'), null=True, blank=True)
    updated                     = models.DateTimeField(_('Updated'), null=True, blank=True)
    updated_by                  = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Updated by'), null=True, blank=True)
    body                        = models.TextField(_('Message'))
    body_html                   = models.TextField(_('HTML version'))
    user_ip                     = models.GenericIPAddressField(_('User IP'), null=True, blank=True)
"""

class PostForm(ModelForm):
    class Meta:
        model   = Post
        fields  = ["topic", "name", "body"]

class AddPostForm(forms.ModelForm):
    FORM_NAME = "AddPostForm" # used in view and template submit button
    subscribe = forms.BooleanField(label=_('Subscribe'), help_text=_("Subscribe to this topic."), required=False)
    name = forms.CharField(label=_('Subject'), max_length=255, widget=forms.TextInput(attrs={'size':'115'}))

    class Meta:
        model = Post
        fields = ['name', 'subscribe', 'body']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.topic = kwargs.pop('topic', None)
        self.forum = kwargs.pop('forum', None)
        self.ip = kwargs.pop('ip', None)
        super(AddPostForm, self).__init__(*args, **kwargs)

        if self.topic:
            self.fields['name'].widget = forms.HiddenInput()
            self.fields['name'].required = False

        self.fields['body'].widget = forms.Textarea(attrs={'class':'markup', 'rows':'20', 'cols':'95'})


    def clean(self):
        errmsg = "Can't be empty nor contain only whitespace characters"
        cleaned_data = self.cleaned_data
        subject = cleaned_data.get('name')
        body = cleaned_data.get('body')
        if subject:
            if not subject.strip():
                self._errors['name'] = self.error_class([errmsg])
                del cleaned_data['name']
        if body:
            if not body.strip():
                self._errors['body'] = self.error_class([errmsg])
                del cleaned_data['body']
        return cleaned_data

    def save(self):
        if self.forum:
            topic = Topic(forum=self.forum, user=self.user, name=self.cleaned_data['name'])
            topic.save()
        else:
            topic = self.topic

        post = Post(topic=topic, user=self.user, user_ip=self.ip, body=self.cleaned_data['body'])

        post.save()
        return post

class EditPostForm(forms.ModelForm):
    name = forms.CharField(required=False, label=_('Subject'), widget=forms.TextInput(attrs={'size':'115'}))

    class Meta:
        model = Post
        fields = ['body']

    def __init__(self, *args, **kwargs):
        topic = kwargs["topic"]
        self.topic = kwargs.pop('topic', None)
        super(EditPostForm, self).__init__(*args, **kwargs)
        self.fields['name'].initial = self.topic.name
        self.fields['body'].widget = forms.Textarea(attrs={'class':'markup'})

    def save(self, commit=True):
        post = super(EditPostForm, self).save(commit=False)
        # post.updated = timezone.now()
        topic_name = self.cleaned_data['name']
        if topic_name:
            post.topic.name = topic_name
        if commit:
            post.topic.save()
            post.save()
        return post
