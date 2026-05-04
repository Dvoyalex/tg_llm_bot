from dotenv import load_dotenv

import os
import requests
import json

load_dotenv()

# =========================
# CONFIG
# =========================
LLM_API_KEY = os.getenv("OPENROUTER_API_KEY")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")
MODEL = os.getenv("MODEL")
SEARCH_URL = os.getenv("SEARCH_URL")
EXTRACT_URL = os.getenv("EXTRACT_URL")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")


# =========================
# WEB SEARCH TOOL
# =========================
def web_search(query):
    try:
        headers = {
            "Authorization": f"Bearer {SEARCH_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "query": query,
            "max_results": 3,
        }

        r = requests.post(SEARCH_URL, headers=headers, json=data, timeout=20)
        r.raise_for_status()

        data = r.json()
        search_results = []

        for item in data.get("results", []):
            search_results.append(item.get("url"))

        if not search_results:
            return "No search results found."
        

        print("SEARCH RESULTS\n", search_results)


        
        results = web_extraction(search_results, query)[:2500]

        return results

    except requests.exceptions.Timeout:
        return "Search timeout error."
    except requests.exceptions.RequestException as e:
        return f"Search request error: {str(e)}"
    except Exception as e:
        return f"Unexpected search error: {str(e)}"

def web_extraction(search_results, query):
    headers = {
            "Authorization": f"Bearer {SEARCH_API_KEY}",
            "Content-Type": "application/json"
        }
    data = {
            "urls": [i for i in search_results],
            "query": f"{query}",
            "format": "text",
        }
    try:
        r = requests.post(EXTRACT_URL, headers=headers, json=data, timeout=20)
        r.raise_for_status()

        data = r.json()
        results = ""

        for item in data.get("results", []):
            results += item.get("raw_content")
        
        if not results:
            return "No search results found."

        return results
        
    except requests.exceptions.Timeout:
        return "Extract timeout error."
    except requests.exceptions.RequestException as e:
        return f"Extract request error: {str(e)}"
    except Exception as e:
        return f"Unexpected extract error: {str(e)}"