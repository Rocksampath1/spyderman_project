# recon/views.py
import multiprocessing

import requests
import threading
import time
import logging
import subprocess
import httpx
import concurrent.futures
from django.shortcuts import render, redirect, get_object_or_404
from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone
from .models import *
from .forms import ProjectForm
from .crawler import start_crawl
import whois

from bs4 import BeautifulSoup

# VirusTotal API key from settings
VIRUSTOTAL_API_KEY = settings.VIRUSTOTAL_API_KEY


def fetch_subdomains(domain, project):
    print(f"Fetching subdomains for {domain}")
    url = f"https://www.virustotal.com/vtapi/v2/domain/report"
    params = {'apikey': VIRUSTOTAL_API_KEY, 'domain': domain}

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data.get('response_code') == 1:
            subdomains = data.get('subdomains', [])
            for subdomain in subdomains:
                subdomain_url = f"https://{subdomain}"
                print(f"Found subdomain: {subdomain_url}")
                Subdomain.objects.get_or_create(
                    url=subdomain_url,
                    project=project,
                    defaults={'date_fetched': timezone.now()}
                )
        else:
            print(f"No subdomains found for {domain}")

    except Exception as e:
        print(f"Error fetching subdomains for {domain}: {e}")


def enumerate_subdomains(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    scopes = project.scopes.split('\n')  # Assuming scopes are stored as newline-separated values

    # Clean up scopes list
    wildcard_domains = [scope.strip() for scope in scopes if scope.startswith('*.')]

    print(f"Wildcard domains to be fetched: {wildcard_domains}")

    threads = []

    for wildcard in wildcard_domains:
        domain = wildcard.lstrip('*.').strip()
        print(f"Processing domain: {domain}")
        thread = threading.Thread(target=fetch_subdomains, args=(domain, project))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Fetch all subdomains for the current project
    subdomains = Subdomain.objects.filter(project=project)

    # Pass the subdomains to the template for rendering
    context = {
        'project': project,
        'subdomains': subdomains,
    }

    return render(request, 'recon/project_recon.html', context)


def index(request):
    return render(request, 'recon/index.html')


def identify_technologies(request):
    # Placeholder for technology identification logic
    return JsonResponse({'status': 'success', 'message': 'Technology identification not yet implemented'})


def brute_force_directories(request):
    # Placeholder for directory brute force logic
    return JsonResponse({'status': 'success', 'message': 'Directory brute force not yet implemented'})


def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = ProjectForm()
    return render(request, 'recon/create_project.html', {'form': form})


def list_projects(request):
    projects = Project.objects.all()
    return render(request, 'recon/list_projects.html', {'projects': projects})


def project_recon(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    # Fetch subdomains related to the project
    subdomains = Subdomain.objects.filter(project=project)

    # Fetch technology information related to the project
    technology = Technology.objects.filter(project=project).first()

    # Pagination for subdomains
    paginator = Paginator(subdomains, 10)  # Show 10 subdomains per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Check if "Show only Active" filter is applied
    show_active = request.GET.get('show_active')
    if show_active:
        page_obj = paginator.get_page(page_number)
        page_obj.object_list = page_obj.object_list.filter(active=True)

    context = {
        'project': project,
        'subdomains': page_obj,
        'technology': technology
    }

    return render(request, 'recon/project_recon.html', context)


def start_crawl_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    start_crawl(project_id)
    return redirect('crawl_results', project_id=project_id)


def crawl_results(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    crawled_data = CrawledData.objects.filter(project=project)
    return render(request, 'recon/crawl_results.html', {'project': project, 'crawled_data': crawled_data})


def check_subdomain_responsiveness(request, project_id):
    project = get_object_or_404(Project, project_id=project_id)
    subdomains = Subdomain.objects.filter(project=project)

    # Create a thread pool to manage asynchronous requests
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(check_responsiveness, subdomain) for subdomain in subdomains]
        for future in concurrent.futures.as_completed(futures):
            future.result()  # Ensure any exceptions are raised

    return redirect('project_recon', project_id=project_id)


def check_responsiveness(subdomain):
    url = subdomain.url
    try:
        response = httpx.get(url, timeout=5.0)
        if response.status_code == 200:
            print(f"{url} is responsive.")
            subdomain.active = True
        else:
            print(f"{url} returned status code {response.status_code}.")
            subdomain.active = False
    except httpx.RequestError as e:
        print(f"{url} failed to respond: {e}")
        subdomain.active = False

    # Save the subdomain status synchronously
    subdomain.save()


''' Technoloy Fingeprinting START '''
# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def perform_technology_fingerprinting(project):
    built_with_url = f"https://builtwith.com/{project.project_url.strip('https://')}"
    print(built_with_url)
    response = requests.get(built_with_url)
    bs4 = BeautifulSoup(response.text, 'html.parser')

    # Extracting Content Delivery Network (CDN)
    try:
        cdn = bs4.find_all(class_="card mt-4 mb-2")[4].find_all(class_="row mb-1 mt-1")
        cdn_txt = "\n\n".join([txt.text for txt in cdn])
    except IndexError:
        cdn_txt = ""

    # Extracting Content Management System (CMS)
    try:
        cms = bs4.find_all(class_="card mt-4 mb-2")[9].find_all(class_="row mb-1 mt-1")
        cms_txt = "\n\n".join([txt.text for txt in cms])
    except IndexError:
        cms_txt = ""

    # Extracting Web Hosting Provider (WHP)
    try:
        whp = bs4.find_all(class_="card mt-4 mb-2")[16].find_all(class_="row mb-1 mt-1")
        whp_txt = "\n\n".join([txt.text for txt in whp])
    except IndexError:
        whp_txt = ""

    # Extracting Web Server
    try:
        ws = bs4.find_all(class_="card mt-4 mb-2")[17].find_all(class_="row mb-1 mt-1")
        ws_txt = "\n\n".join([txt.text for txt in ws])
    except IndexError:
        ws_txt = ""

    # Performing WHOIS lookup
    w = whois.whois(project.project_url)
    whois_data = {
        'domain_name': w.domain_name,
        'registrar': w.registrar,
        'whois_server': w.whois_server,
        'referral_url': w.referral_url,
        'updated_date': w.updated_date,
        'creation_date': w.creation_date,
        'expiration_date': w.expiration_date,
        'name_servers': w.name_servers,
        'status': w.status,
        'emails': w.emails,
        'dnssec': w.dnssec,
        'name': w.name,
        'org': w.org,
        'address': w.address,
        'city': w.city,
        'state': w.state,
        'zipcode': w.zipcode,
        'country': w.country
    }

    Technology.objects.get_or_create(
        project=project,
        name=project.project_url,
        defaults={
            'content_delivery_network': cdn_txt,
            'content_management_system': cms_txt,
            'web_hosting_provider': whp_txt,
            'who_is_lookup': whois_data,
            'web_server': ws_txt
        }
    )
    print("Technology Fingerprinting Completed...")


def start_technology_fingerprinting(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    threading.Thread(target=perform_technology_fingerprinting, args=(project,)).start()
    return redirect('project_recon', project_id=project_id)


''' Technoloy Fingeprinting END '''
