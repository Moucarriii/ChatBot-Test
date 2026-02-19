import os
import json
import uuid
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Config ----------
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    st.error("OPENAI_API_KEY not found. Check your .env file.")
    st.stop()

client = OpenAI(api_key=API_KEY)

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "chat_logs.jsonl")
MODEL = "gpt-4.1-mini"
# ---------------------------


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def append_log(record: dict):
    ensure_log_dir()
    record = {"ts_utc": utc_now_iso(), **record}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


st.set_page_config(page_title="Chatbot", layout="centered")
st.title("Chatbot")

# New visitor session id (fresh each time, no long-term memory)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Chat history for UI only (this is NOT persistent memory)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Optional: show where logs are written
with st.sidebar:
    st.caption("Server log file path:")
    st.code(LOG_FILE)
    if st.button("Clear current screen chat"):
        st.session_state.messages = []
        st.rerun()

# Render chat on screen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input
user_text = st.chat_input("Type your message...")
if user_text:
    # Display + store in current session
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.write(user_text)

    # Log user message to disk (persistent)
    append_log({
        "session_id": st.session_state.session_id,
        "role": "user",
        "content": user_text,
    })

    # Get assistant reply
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            resp = client.chat.completions.create(
                model=MODEL,
                messages=st.session_state.messages,
            )
            reply = resp.choices[0].message.content
        st.write(reply)

    # Display + store in current session
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Log assistant reply to disk (persistent)
    append_log({
        "session_id": st.session_state.session_id,
        "role": "assistant",
        "content": reply,
    })
