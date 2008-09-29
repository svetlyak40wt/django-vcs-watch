from django.contrib import admin
from models import Repository

class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('hash', 'url_link', 'last_rev')

    def url_link(self, instance):
        return '<a href="%s">%s</a>' % (instance.get_absolute_url(), instance.url)
    url_link.allow_tags = True

admin.site.register(Repository, RepositoryAdmin)

