from dotenv import load_dotenv

import os
import requests
import json
import time

import handlers

load_dotenv()


LLM_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("MODEL")


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
        # print(message)
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
        # print(call)
        if call.get("function", {}).get("name") == "web_search":
            try:
                args = json.loads(call["function"]["arguments"])
                query = args.get("query", "")
                print(query)

                if not query:
                    result = "Invalid query."
                else:
                    result = handlers.web_search(query)

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

    messages.append(second_msg)
    return second_msg["content"]