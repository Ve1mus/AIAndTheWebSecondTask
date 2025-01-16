# crawler.py

import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import os
import nltk
from langdetect import detect, DetectorFactory
import logging
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import StemmingAnalyzer

# Ensure deterministic behavior for langdetect
DetectorFactory.seed = 0

# ------------------ NLTK DATA SETTINGS ------------------

# Specify the local nltk_data folder inside your project
nltk_data_path = os.path.join(os.path.dirname(__file__), 'nltk_data')
if not os.path.exists(nltk_data_path):
    os.makedirs(nltk_data_path)

# Add this path to nltk's data search paths
nltk.data.path.append(nltk_data_path)

# Download 'punkt' resource to the specified folder
nltk.download('punkt', download_dir=nltk_data_path)

# ---------------- LOGGING CONFIGURATION ----------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)

# ---------------- WHOOSH INDEX SETTINGS ----------------

# Define the schema with 'content' field set to stored=True
schema = Schema(
    url=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    content=TEXT(stored=True, analyzer=StemmingAnalyzer())  # Ensure content is stored
)

# Create or open the Whoosh index directory
if not os.path.exists("indexdir"):
    os.mkdir("indexdir")
    ix = index.create_in("indexdir", schema)
    logging.info("Created new Whoosh index directory.")
else:
    ix = index.open_dir("indexdir")
    logging.info("Opened existing Whoosh index directory.")

# ---------------- GLOBAL DATA STRUCTURES ----------------

visited = set()           # Set of visited canonical URLs
unique_urls_data = set()  # Set of unique canonical URLs

# ---------------- HELPER FUNCTIONS ----------------

def canonical_url(url: str) -> str:
    """
    Convert the given URL into a canonical form:
    - Remove query parameters and fragment
    - Strip the trailing slash if the path is not the root
    """
    parsed = urlparse(url)
    scheme = parsed.scheme
    netloc = parsed.netloc
    path = parsed.path

    if path.endswith("/") and path != "/":
        path = path.rstrip("/")
    query = ""
    fragment = ""
    return urlunparse((scheme, netloc, path, "", query, fragment))

def crawl(url: str, depth: int = 0, max_depth: int = 10) -> None:
    """
    Recursively crawl the website, collecting unique links and indexing page text.
    """
    if depth > max_depth:
        return

    canonical = canonical_url(url)
    if canonical in visited:
        return
    visited.add(canonical)
    unique_urls_data.add(canonical)

    try:
        resp = requests.get(canonical, timeout=5)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for {canonical}: {e}")
        return

    ctype = resp.headers.get("Content-Type", "")
    if not ctype.startswith("text/html"):
        return

    text_lower = resp.text.lower()
    if "captcha" in text_lower or "g-recaptcha" in text_lower:
        logging.warning(f"CAPTCHA detected at {canonical}, skipping.")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else canonical

    # Adjust selectors to extract main content, including headers
    # Example: main content inside <div class="main-content">
    main_content = soup.find("div", class_="main-content")
    if not main_content:
        main_content = soup  # Use entire document if specific container not found

    # Extract text from main content
    page_text = main_content.get_text(separator=" ", strip=True)

    # ----------------- REMOVE EXCLUSION OF SENTENCES -----------------
    # Previously, the first two sentences were excluded to remove headers.
    # Now, we index the entire content without skipping any sentences.
    # Uncomment the following lines if you want to skip sentences again.

    # # Exclude headers by removing first N sentences (e.g., first 2 sentences)
    # sentences = nltk.sent_tokenize(page_text, language='english')
    # if len(sentences) > 2:
    #     page_text = ' '.join(sentences[2:])  # Skip first 2 sentences

    # Index the page with Whoosh
    writer = ix.writer()
    writer.add_document(url=canonical, title=title, content=page_text)
    writer.commit()
    logging.info(f"Indexed {canonical}")

    # Recursively follow internal links
    parsed_canon = urlparse(canonical)
    for link in main_content.find_all("a", href=True):
        child_abs = urljoin(canonical, link["href"])
        child_canon = canonical_url(child_abs)
        if urlparse(child_canon).netloc == parsed_canon.netloc:
            crawl(child_canon, depth + 1, max_depth)

def main():
    """Main function to start crawling."""
    start_url = "https://www.uni-osnabrueck.de/"  # Replace with your target URL
    logging.info("Starting crawl...")
    crawl(start_url, depth=0, max_depth=4)  # Adjust max_depth as needed
    logging.info("Crawling completed.")

if __name__ == "__main__":
    # Download 'punkt' if not already downloaded
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', download_dir=nltk_data_path)
    
    main()