# recon/models.py

from django.db import models
from django.utils import timezone


class Project(models.Model):
    WEB = 'Web'
    MOBILE = 'Mobile'
    TYPE_CHOICES = [
        (WEB, 'Web'),
        (MOBILE, 'Mobile'),
    ]

    HACKERONE = 'HackerOne'
    BUGCROWD = 'Bugcrowd'
    OTHER = 'Other'
    SOURCE_CHOICES = [
        (HACKERONE, 'HackerOne'),
        (BUGCROWD, 'Bugcrowd'),
        (OTHER, 'Other'),
    ]

    name = models.CharField(max_length=255)
    project_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    project_url = models.URLField()
    scopes = models.TextField(help_text='Enter each URL in scope on a new line')
    out_of_scope = models.TextField(help_text='Enter each URL out of scope on a new line')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    source_other = models.CharField(max_length=255, blank=True, null=True)
    project_id = models.AutoField(primary_key=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Subdomain(models.Model):
    url = models.URLField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    date_fetched = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return self.url


class Technology(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    content_delivery_network = models.TextField(blank=True, null=True)
    content_management_system = models.TextField(blank=True, null=True)
    web_hosting_provider = models.TextField(blank=True, null=True)
    who_is_lookup = models.TextField(blank=True, null=True)
    web_server = models.TextField(blank=True, null=True)


class CrawledData(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    url = models.URLField()
    title = models.CharField(max_length=255, null=True, blank=True)
    response_code = models.IntegerField()
    response_headers = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
