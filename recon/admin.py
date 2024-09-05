from django.contrib import admin
from .models import *

admin.site.register(Project)
admin.site.register(Subdomain)
admin.site.register(CrawledData)
admin.site.register(Technology)

# Register your models here.
