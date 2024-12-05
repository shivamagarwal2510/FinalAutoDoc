import os
import json
import asyncio
from urllib.parse import urljoin, urlparse
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import random

# Define the structure of the extracted documentation content
class DocumentationContent(BaseModel):
    title: str = Field(..., description="The title of the documentation page.")
    content: str = Field(..., description="The main content of the documentation page.")
    url: str = Field(..., description="The URL of the documentation page.")

# Implement a rate limiter to control the frequency of API calls
class RateLimiter:
    def __init__(self, rate_limit, time_period):
        self.rate_limit = rate_limit  # Maximum number of requests
        self.time_period = time_period  # Time period in seconds
        self.tokens = rate_limit  # Available tokens (requests)
        self.last_refill = time.time()  # Last time tokens were refilled

    async def acquire(self):
        while True:
            current_time = time.time()
            time_passed = current_time - self.last_refill
            # Refill tokens based on time passed
            self.tokens += time_passed * (self.rate_limit / self.time_period)
            if self.tokens > self.rate_limit:
                self.tokens = self.rate_limit
            self.last_refill = current_time

            if self.tokens >= 1:
                self.tokens -= 1
                return
            await asyncio.sleep(0.1)  # Wait before checking again

# Main crawler class
class DocumentationCrawler:
    def __init__(self, start_url, output_dir, max_concurrent=20, rate_limit=1000, time_period=60):
        self.start_url = start_url
        self.output_dir = output_dir
        self.visited_urls = set()
        parsed_url = urlparse(start_url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.base_path = parsed_url.path
        self.all_content = []
        self.rate_limiter = RateLimiter(rate_limit, time_period)
        self.unsuccessful_urls = set()  # Track unsuccessful URLs
        self.start_time = None  # Track start time
        self.extracted_urls = set()

    # Retry mechanism for API calls
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def extract_with_retry(self, crawler, url):
        try:
            print(f"Extracting inside e {url}")
            result = await crawler.arun(
                url=url,
                extraction_strategy=LLMExtractionStrategy(
                    provider="gemini/gemini-1.5-flash",
                    api_token="AIzaSyBp_-OPrIR5mXVghMDWqMnOsvZ9LGmE6zg",
                    schema=DocumentationContent.model_json_schema(),
                    extraction_type="schema",
                    instruction=(
                        "You are a documentation extractor specialized in developer documentation. "
                        "Your task is to extract ALL information from the documentation page exactly as it appears, "
                        "including every detail of:\n"
                        "- Installation instructions\n"
                        "- Code snippets (preserve all examples completely)\n"
                        "- API references and parameters\n"
                        "- Usage examples\n"
                        "- Configuration options\n"
                        "- Technical specifications\n"
                        "- Implementation details\n"
                        "- Error handling information\n"
                        "- Any warnings or notes\n\n"
                        "Do not summarize or omit any technical information. Preserve the original structure and "
                        "all technical details exactly as they appear in the documentation. Remove only the "
                        "non-documentation elements like navigation menus, headers, footers, and sidebars."
                    ),
                    bypass_cache=True  # Ensure cache is bypassed
                )
            )
            self.extracted_urls.add(url)
            return result
        except Exception as e:
            print(f"Unexpected error extracting {url}: {e}")
            self.unsuccessful_urls.add(url)
            return None

    # Main crawling method
    async def crawl(self):
        self.start_time = time.time()  # New: Record start time
        async with AsyncWebCrawler(verbose=True, always_by_pass_cache=True) as crawler:
            await self.crawl_page(crawler, self.start_url)
        self.save_combined_content()
        end_time = time.time()  # New: Record end time
        total_time = end_time - self.start_time
        print(f"Crawling completed.")
        print(f"Total URLs visited: {len(self.visited_urls)}")
        print(f"Successful extractions: {len(self.all_content)}")
        print(f"Unsuccessful URLs: {len(self.unsuccessful_urls)}")
        print(f"Total crawling time: {total_time:.2f} seconds")
        print(f"Extracted URLs: {len(self.extracted_urls)} {self.extracted_urls}")
        print(f"Visited URLs: {len(self.visited_urls)} {self.visited_urls}")
        return total_time, len(self.unsuccessful_urls)  # New: Return crawl stats

    # Method to crawl a single page
    async def crawl_page(self, crawler, url):
        """Remove anchor from URL for consistency"""
        base_url_without_anchor = url.split('#')[0]
        
        if base_url_without_anchor in {u.split('#')[0] for u in self.visited_urls}:
            return

        self.visited_urls.add(base_url_without_anchor)
        print(f"Crawling: {base_url_without_anchor}")

        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()
            result = await self.extract_with_retry(crawler, base_url_without_anchor)
            
            # Check if result is not None and has extracted content
            if result and result.extracted_content:
                content = json.loads(result.extracted_content)
                internal_links = result.links.get('internal', [])
                self.all_content.append(content)
                print(f"Links found on {base_url_without_anchor}: {internal_links}")

                # Crawl linked pages sequentially
                for link in internal_links:
                    link_url = link['href']
                    full_url = urljoin(self.base_url, link_url)
                    if self.should_crawl(full_url):
                        await self.crawl_page(crawler, full_url)
            else:
                print(f"No content extracted from {base_url_without_anchor}")
                self.unsuccessful_urls.add(base_url_without_anchor)

        except Exception as e:
            print(f"Unexpected error crawling {base_url_without_anchor}: {e}")
            self.unsuccessful_urls.add(base_url_without_anchor)

    # Method to determine if a URL should be crawled
    def should_crawl(self, url):
        """Determine if a URL should be crawled."""
        parsed_url = urlparse(url)
        full_path = parsed_url.path
        
        # Remove anchor from URL for comparison
        base_url_without_anchor = url.split('#')[0]
        
        return (
            base_url_without_anchor.startswith(self.base_url) and
            full_path.startswith(self.base_path) and
            base_url_without_anchor not in {u.split('#')[0] for u in self.visited_urls} and
            not url.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js'))
        )

    # Save all extracted content to a JSON file
    def save_combined_content(self):
        parsed_url = urlparse(self.start_url)
        domain = parsed_url.netloc
        # domain + random number 
        random_number = random.randint(1000, 9999)
        file_name = f"{domain}_documentation.json"
        file_path = os.path.join(self.output_dir, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.all_content, f, indent=2)

# Function to run the crawler
async def run_crawler(start_url):
    output_dir = "documentation_output"
    
    crawler = DocumentationCrawler(start_url, output_dir)
    try:
        total_time, unsuccessful_count = await crawler.crawl()
        return f"Crawling completed. Combined JSON output saved. Total time: {total_time:.2f} seconds. Unsuccessful URLs: {unsuccessful_count} Visited URLs: {crawler.visited_urls} Extracted URLs: {crawler.extracted_urls}"
    except Exception as e:
        return f"An error occurred during crawling: {e}"

# Main execution block
if __name__ == "__main__":
    print("This script is designed to be run from app.py")
    print("Please run app.py to use the web interface for crawling.")
