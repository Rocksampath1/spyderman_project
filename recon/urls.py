# recon/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('enumerate-subdomains/<int:project_id>/', views.enumerate_subdomains, name='enumerate_subdomains'),
    path('identify-technologies/', views.identify_technologies, name='identify_technologies'),
    path('brute-force-directories/', views.brute_force_directories, name='brute_force_directories'),
    path('create-project/', views.create_project, name='create_project'),
    path('projects/', views.list_projects, name='list_projects'),
    path('projects/<int:project_id>/recon/', views.project_recon, name='project_recon'),
    path('projects/<int:project_id>/start-crawl/', views.start_crawl_view, name='start_crawl_view'),
    path('projects/<int:project_id>/crawl-results/', views.crawl_results, name='crawl_results'),
    path('projects/<int:project_id>/check-subdomain-responsiveness/', views.check_subdomain_responsiveness,
         name='check_subdomain_responsiveness'),
    path('projects/<int:project_id>/start-technology-fingerprinting/', views.start_technology_fingerprinting,
         name='start_technology_fingerprinting'),
]
