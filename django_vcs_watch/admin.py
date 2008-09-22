from django.contrib import admin
from models import Repository

class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('hash', 'url', 'last_rev')

admin.site.register(Repository, RepositoryAdmin)

