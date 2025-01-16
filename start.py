# start.py

from flask import Flask, render_template, request
from whoosh import index
from whoosh.qparser import MultifieldParser
from whoosh.analysis import StemmingAnalyzer
import os
import logging

app = Flask(__name__)

# ------------------ WHOOSH INDEX SETTINGS ------------------

INDEX_DIR = "indexdir"

# Check if the index directory exists
if not os.path.exists(INDEX_DIR):
    raise Exception(f"Index directory '{INDEX_DIR}' does not exist. Please run crawler.py first to build the index.")

# Open the existing Whoosh index
ix = index.open_dir(INDEX_DIR)

# ---------------- LOGGING CONFIGURATION ----------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("flask_app.log"),
        logging.StreamHandler()
    ]
)

# ---------------- FLASK ROUTES ----------------

@app.route('/')
def home():
    """Render the search form."""
    return render_template('search.html')

@app.route('/result')
def result():
    """Handle search queries and display results."""
    query = request.args.get('q', '')
    results = search_in_whoosh(query)
    return render_template('result.html', query=query, results=results)

# ---------------- SEARCH FUNCTION ----------------

def search_in_whoosh(query_str: str):
    """
    Search for the query using Whoosh and return a list of results.
    Each result contains URL, title, and a snippet.
    """
    if not query_str:
        return []

    with ix.searcher() as searcher:
        # Create a parser that searches in both 'title' and 'content' fields
        parser = MultifieldParser(["title", "content"], schema=ix.schema)
        query = parser.parse(query_str)
        
        # Perform the search
        whoosh_results = searcher.search(query, limit=30)
        
        # Configure snippet generation
        whoosh_results.fragmenter.charlimit = None  # Remove character limit for snippets

        results = []
        for hit in whoosh_results:
            # Generate snippet from 'content' field
            snippet = hit.highlights("content", top=2, minscore=1)
            if not snippet:
                snippet = "No snippet available."
            results.append({
                "url": hit['url'],
                "title": hit['title'],
                "snippet": snippet
            })

    return results

if __name__ == "__main__":
    # Run the Flask app
    app.run(debug=True)