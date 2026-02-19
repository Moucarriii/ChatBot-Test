import os
import json
import uuid
from datetime import datetime, timezone

import streamlit as st
from openai import OpenAI

# Optional local support: reads .env only when running locally
# Streamlit Cloud will ignore .env and you will use st.secrets instead
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# -------------------- Settings --------------------
MODEL = "gpt-4.1-mini"

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "chat_logs.jsonl")

SYSTEM_PROMPT = (
    "You are a helpful assistant. "
    "Keep answers clear and structured. "
    "If you are unsure, say you are unsure."
)
# -------------------------------------------------


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_log_dir() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)


def append_log(record: dict) -> None:
    """
    Appends one JSON record per line (JSONL).
    Note: On Streamlit Cloud, filesystem writes may not persist long-term.
    """
    ensure_log_dir()
    record = {"ts_utc": utc_now_iso(), **record}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def get_api_key() -> str | None:
    # 1) Streamlit Cloud secrets (recommended for deployment)
    api_key = None
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        api_key = None

    # 2) Fallback to environment variable (local .env -> os.environ)
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")

    return api_key


st.set_page_config(page_title="Chatbot", layout="centered")
st.title("Chatbot")

api_key = get_api_key()
if not api_key:
    st.error(
        "OPENAI_API_KEY not found.\n\n"
        "For local: create a .env file with OPENAI_API_KEY=sk-...\n"
        "For Streamlit Cloud: add OPENAI_API_KEY in the Secrets settings."
    )
    st.stop()

client = OpenAI(api_key=api_key)

# Session id: new for each visitor session (no long-term memory)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Initialize chat with system prompt once
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

with st.sidebar:
    st.caption("Model")
    st.code(MODEL)

    st.caption("Server log file (local dev)")
    st.code(LOG_FILE)

    if st.button("Clear current screen chat"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()

# Render messages except system (we do not show system prompt)
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_text = st.chat_input("Type your message...")
if user_text:
    # Show + store user message
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.write(user_text)

    # Log user message
    append_log({
        "session_id": st.session_state.session_id,
        "role": "user",
        "content": user_text,
    })

    # Call OpenAI
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=st.session_state.messages,
                )
                reply = resp.choices[0].message.content
            except Exception as e:
                reply = f"Error: {e}"

        st.write(reply)

    # Show + store assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Log assistant reply
    append_log({
        "session_id": st.session_state.session_id,
        "role": "assistant",
        "content": reply,
    })
