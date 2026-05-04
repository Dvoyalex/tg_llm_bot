import os
from dotenv import load_dotenv

from telebot import TeleBot
from telebot.types import Message, CallbackQuery

import handlers
import llm

load_dotenv()

TG_API_KEY = os.getenv("AGENTIOS_API_KEY")
tg_bot = TeleBot(TG_API_KEY)

users = {}
start_message = [
    {"role": "system", "content": "You are a helpful assistant. Use web_search to get current information when needed."}
]


@tg_bot.message_handler(commands=["start"])
def welcome(message: Message):
    chat_id = message.chat.id
    users.setdefault(chat_id, {"messages": start_message})
    tg_bot.send_message(chat_id,"Добро пожаловать! Что вас интересует?")

@tg_bot.message_handler(func=lambda m: True)
def chat(message: Message):
    chat_id = message.chat.id
    users.setdefault(chat_id, {"messages": start_message})
    messages = users.get(chat_id, {}).get("messages")
    messages.append({"role": "user", "content": message.text})
    response, err = llm.ask_llm(messages)
    
    try:
        if not err:
            messages.append(response)
            reply = llm.handle_tool_call(response, messages)
            tg_bot.send_message(chat_id, reply, parse_mode="markdown")
        else:
            tg_bot.send_message(chat_id, f"{err}")
            messages.append({"role": "assistant", "content": err})

    except Exception as e:
        tg_bot.send_message(chat_id, f"{e}")

    for i in messages:
        print(i, "\n-#########################")

if __name__ == '__main__':
    print('Bot is running!')
    tg_bot.infinity_polling()