from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from tinyuid import uuid
from uuslug import uuslug
from django.utils.translation import ugettext_lazy as _
from datetime import datetime
from postmarkup import render_bbcode
from django.utils import timezone
from poll.models import Poll

# This is for tracking forum conversions only.
class SMFConversion(models.Model):
    forum                       = models.PositiveIntegerField()
    name                        = models.CharField(max_length=255)
    active                      = models.BooleanField(default=True)
    has_begun                   = models.BooleanField(default=True)
    begun                       = models.DateTimeField(null=True, blank=True)
    has_finished                = models.BooleanField(default=False)
    finished                    = models.DateTimeField(null=True, blank=True)

    @property
    def time_taken(self):
        if self.finished:
            start   = self.begun
            end     = self.finished
            return end - start
        else:
            return None

    def __unicode__(self):
        if self.active == True:
            return "%s -- RUNNING" % (self.name)
        else: 
            return "%s" % (self.name)

    def save(self, *args, **kwargs):
        if not self.begun:
            self.begun = datetime.datetime.now()

        return super(SMFConversion, self).save(*args, **kwargs)

class Category(models.Model):
    old_category_id             = models.PositiveIntegerField(_('Old Category'), null=True, blank=True)
    name                        = models.CharField(_('Name'), max_length=80)
    groups                      = models.ManyToManyField(Group, blank=True, verbose_name=_('Groups'), help_text=('Only visible to members of these groups'))
    slug                        = models.CharField(_('Slug'), max_length=80, null=True, blank=True)
    position                    = models.PositiveIntegerField(_('Position'), blank=True, default=0)
    active                      = models.BooleanField(_('Active'), blank=True, default=False)

    class Meta:
        ordering                = ['position']
        verbose_name            = _('Category')
        verbose_name_plural     = _('Categories')

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug           = uuslug(self.name, instance=self)
        super(Category, self).save(*args, **kwargs)

    @property
    def forum_count(self):
        return self.forums.filter(category=self).count()

    def has_access(self, user):
        if user.is_superuser:
            return True
        if self.groups.exists():
            if user.is_authenticated():
                if not self.groups.filter(user__pk=user.id).exists():
                    return False
            else:
                return False
        return True

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

    class Meta:
        ordering                = ['position']
        verbose_name            = _('Forum')
        verbose_name_plural     = _('Forums')

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug           = uuslug(self.name, instance=self)
        super(Forum, self).save(*args, **kwargs)

    @property
    def topic_count(self):
        return self.topics.all().count()

    @property
    def post_count(self):
        return self.posts.all().count()

    def get_absolute_url(self):
        return reverse('forum:forum', args=[str(self.slug)])

    @property
    def posts(self):
        return Post.objects.filter(topic__forum__id=self.id).select_related()
 
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

    old_poll_id                 = models.PositiveIntegerField(null=True, blank=True)
    poll                        = models.ForeignKey(Poll, null=True, blank=True)

    views                       = models.PositiveIntegerField(_('View count'), blank=True, default=0)
    sticky                      = models.BooleanField(_('Sticky'), blank=True, default=False)
    closed                      = models.BooleanField(_('Closed'), blank=True, default=False)
    active                      = models.BooleanField(_('Active'), blank=True, default=False)
    post_count                  = models.PositiveIntegerField(_('Post count'), blank=True, default=0)
    last_post                   = models.ForeignKey('Post', related_name='last_topic_post', blank=True, null=True)
    user_ip                     = models.GenericIPAddressField(_('User IP'), null=True, blank=True)

    class Meta:
        ordering                = ['-updated']
        get_latest_by           = 'updated'
        verbose_name            = _('Topic')
        verbose_name_plural     = _('Topics')

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.created:
            self.created        = datetime.now()

        if not self.slug:
            self.slug           = uuslug(self.name, instance=self)
            # self.legacy_username= str(self.user.username)
        super(Topic, self).save(*args, **kwargs)

    @property
    def reply_count(self):
        count = self.posts.all().count() - 1
        if count < 0:
            return 0
        else:
            return count

    @property
    def get_body(self):
        return self.posts.first()

    def get_absolute_url(self):
        return reverse('forum:topic', args=[str(self.forum.slug), str(self.slug)])

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

    class Meta:
        ordering                = ['created']
        get_latest_by           = 'created'
        verbose_name            = _('Post')
        verbose_name_plural     = _('Posts')

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.now()

        if not self.uuid:
            self.uuid           = uuid()

        if not self.body_html:
            self.body_html      = render_bbcode(self.body)

        super(Post, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('forum:post', args[str(self.topic.forum.slug), str(self.topic.slug), str(self.uuid)])
