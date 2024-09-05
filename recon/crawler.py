# crawler.py
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from django.utils import timezone
from urllib.parse import urljoin, urlparse
from .models import Project, CrawledData


def fetch_page(url, project, visited):
    if url in visited:
        return []

    try:
        response = requests.get(url)
        visited.add(url)

        page_title = BeautifulSoup(response.content, 'html.parser').title.string if response.content else 'No Title'
        headers = dict(response.headers)

        crawled_data = CrawledData(
            project=project,
            url=url,
            title=page_title,
            response_code=response.status_code,
            response_headers=headers,
            timestamp=timezone.now()
        )
        crawled_data.save()

        soup = BeautifulSoup(response.content, 'html.parser')
        links = [urljoin(url, link.get('href')) for link in soup.find_all('a', href=True)]

        # Filter out URLs that do not belong to the same domain
        domain = urlparse(url).netloc
        links = [link for link in links if urlparse(link).netloc == domain]

        return links

    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return []


def start_crawl(project_id):
    project = Project.objects.get(pk=project_id)
    start_urls = [project.project_url]
    visited_urls = set()
    to_crawl = start_urls

    with ThreadPoolExecutor(max_workers=10) as executor:
        while to_crawl:
            futures = {executor.submit(fetch_page, url, project, visited_urls): url for url in to_crawl}
            to_crawl = []

            for future in futures:
                try:
                    result = future.result()
                    new_urls = set(result) - visited_urls
                    visited_urls.update(new_urls)
                    to_crawl.extend(new_urls)
                except Exception as e:
                    print(f"Error during crawling: {e}")

    print("Crawling completed.")
