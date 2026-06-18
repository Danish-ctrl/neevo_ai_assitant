import urllib.request
import urllib.parse
import re

def web_search(query: str) -> str:
    """Searches DuckDuckGo HTML and securely extracts the top result snippets."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        
        # Spoof a standard web browser so websites don't reject the connection
        req = urllib.request.Request(
            url, 
            data=None, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')

        # Extract search snippets
        snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
        
        if not snippets:
            return "No relevant information found on the web."

        # Clean up HTML tags from the text
        clean_snippets = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets]
        
        # Combine the top 3 results into a single context block
        return " ".join(clean_snippets[:3])
        
    except Exception as e:
        return f"Web search connection failed: {e}"