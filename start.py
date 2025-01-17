# start.py

from flask import Flask, render_template, request
from whoosh import index
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.spelling import Corrector
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
    results, suggestions = search_in_whoosh(query)
    return render_template('result.html', query=query, results=results, suggestions=suggestions)

# ---------------- SEARCH FUNCTION ----------------

def add_fuzzy(query_str: str, max_edits: int = 2) -> str:
    """
    Add fuzzy operator (~) to each term in the query string.

    Args:
        query_str (str): Original query string.
        max_edits (int): Maximum edit distance for fuzzy search.

    Returns:
        str: Modified query string with fuzzy operators.
    """
    # Split the query string into terms
    terms = query_str.strip().split()
    # Add '~' with the maximum edit distance to each term
    fuzzy_terms = [f"{term}~{max_edits}" for term in terms]
    # Join back into a single query string
    return ' '.join(fuzzy_terms)

def search_in_whoosh(query_str: str, max_edits: int = 2):
    """
    Search for the query using Whoosh with fuzzy search and return a list of results.
    Each result contains URL, title, and a snippet.

    Args:
        query_str (str): The search query input by the user.
        max_edits (int): Maximum edit distance for fuzzy search.

    Returns:
        tuple: (results, suggestions)
    """
    if not query_str:
        return [], []

    # Add fuzziness to the query
    fuzzy_query_str = add_fuzzy(query_str, max_edits)
    logging.info(f"Fuzzy Query: {fuzzy_query_str}")

    with ix.searcher() as searcher:
        # Create a parser that searches in both 'title' and 'content' fields using OrGroup
        parser = MultifieldParser(["title", "content"], schema=ix.schema, group=OrGroup)
        # Parse the modified query with fuzzy operators
        try:
            query = parser.parse(fuzzy_query_str)
        except Exception as e:
            logging.error(f"Error parsing query: {e}")
            return [], []

        # Perform the search
        whoosh_results = searcher.search(query, limit=30)
        logging.info(f"Number of results found: {len(whoosh_results)}")

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

        # If no results found, generate suggestions
        if not results:
            suggestions = generate_suggestions(searcher, query_str)
            return [], suggestions

    return results, []

def generate_suggestions(searcher, query_str, max_suggestions=5):
    """
    Generate suggestions for misspelled queries.

    Args:
        searcher: Whoosh searcher object.
        query_str (str): Original query string.
        max_suggestions (int): Maximum number of suggestions to return.

    Returns:
        list: A list of suggested query strings.
    """
    # Obtain the corrector for the 'content' field
    corrector = searcher.corrector("content")
    terms = query_str.strip().split()
    suggestions = set()
    for term in terms:
        corrected = corrector.suggest(term)
        for c in corrected:
            suggestions.add(c)
    return list(suggestions)[:max_suggestions]

if __name__ == "__main__":
    # Run the Flask app
    app.run(debug=True)