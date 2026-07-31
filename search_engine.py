import requests

class SearXNGProvider:
    def __init__(self, endpoint="http://localhost:8888"):
        self.endpoint = endpoint

    def search(self, query):
        params = {"q": query, "format": "json"}
        try:
            response = requests.get(f"{self.endpoint}/search", params=params, timeout=10)
            response.raise_for_status()
            results = response.json().get("results", [])
            
            context = "Web Search Results:\n"
            for res in results[:5]:  # Top 5 results to save context
                context += f"- {res.get('title')}: {res.get('content')}\n"
            return context
        except Exception:
            return "Web Search Failed or Unavailable."