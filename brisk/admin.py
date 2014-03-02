from django.contrib import admin

from models import *

class TopicAdmin(admin.ModelAdmin):
    # list_display = ('user', )
    list_filter = ('sticky',)
    # search_fields = ('user__username', )

class ConversionAdmin(admin.ModelAdmin):
    list_display    = ('forum', 'name', 'time_taken','active',)

admin.site.register(SMFConversion, ConversionAdmin)
admin.site.register(Category)
admin.site.register(Forum)
admin.site.register(Post)
admin.site.register(Topic, TopicAdmin)
