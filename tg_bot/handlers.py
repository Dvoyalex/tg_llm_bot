import os
from dotenv import load_dotenv

import requests
import json
import time

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
# LLM REQUEST
# =========================
def ask_llm(messages):
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for current information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ],
        "tool_choice": "auto",
        "max_completion_tokens": 500,
    }

    try:
        r = requests.post(LLM_BASE_URL, headers=headers, json=payload, timeout=20)
        r.raise_for_status()

        data = r.json()

        if "choices" not in data or not data["choices"]:
            return None, "Empty LLM response."

        message = data["choices"][0]["message"]
        print(message)
        return message, None

    except requests.exceptions.Timeout:
        return None, "LLM request timed out."
    except requests.exceptions.RequestException as e:
        return None, f"LLM request error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected LLM error: {str(e)}"
   

# =========================
# TOOL HANDLER
# =========================
def handle_tool_call(message, messages):
    tool_calls = message.get("tool_calls")

    if not tool_calls:
        return message.get("content")

    for call in tool_calls:
        print("*tool use")
        print(call)
        if call.get("function", {}).get("name") == "web_search":
            try:
                args = json.loads(call["function"]["arguments"])
                query = args.get("query", "")
                print(query)

                if not query:
                    result = "Invalid query."
                else:
                    result = web_search(query)

            except Exception as e:
                result = f"Tool parsing error: {str(e)}"

            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": result
            })

    # second LLM call with tool result
    time.sleep(2)
    second_msg, err = ask_llm(messages)
    time.sleep(2)

    if err:
        print(err)
        return err

    if not second_msg or not second_msg.get("content"):
        return "Empty response after tool execution."

    return second_msg["content"]


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