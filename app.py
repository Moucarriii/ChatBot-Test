import uuid
from supabase import create_client
import streamlit as st
from openai import OpenAI

# -------------------- Settings --------------------
MODEL = "gpt-4.1-mini"

SYSTEM_PROMPT = (
    "You are a helpful assistant. "
    "Keep answers clear and structured. "
    "If you are unsure, say you are unsure."
)
# --------------------------------------------------


def must_get_secret(name: str) -> str:
    value = st.secrets.get(name)
    if not value:
        st.error(
            f"Missing secret: {name}\n\n"
            "Go to Streamlit Cloud -> App settings -> Secrets and add it."
        )
        st.stop()
    return value


st.set_page_config(page_title="Chatbot", layout="centered")
st.title("Chatbot")

# ----- Load secrets (Streamlit Cloud) -----
OPENAI_API_KEY = must_get_secret("OPENAI_API_KEY")
SUPABASE_URL = must_get_secret("SUPABASE_URL")
SUPABASE_SECRET_KEY = must_get_secret("SUPABASE_SECRET_KEY")

# ----- Clients -----
client = OpenAI(api_key=OPENAI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


def append_log(session_id: str, role: str, content: str) -> None:
    """
    Persist logs to Supabase.
    Table expected: public.chat_logs(session_id uuid, role text, content text, ts_utc default now()).
    """
    try:
        supabase.table("chat_logs").insert(
            {"session_id": session_id, "role": role, "content": content}
        ).execute()
    except Exception as e:
        # Do not crash the chat if logging fails
        st.sidebar.warning(f"Logging failed: {e}")


# ----- New visitor session id (fresh each time) -----
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ----- Initialize chat history (screen only) -----
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

with st.sidebar:
    st.caption("Model")
    st.code(MODEL)

    if st.button("Clear current screen chat"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()

# Render chat messages (skip system prompt)
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_text = st.chat_input("Type your message...")
if user_text:
    # Store + show user message
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.write(user_text)

    # Log user message
    append_log(st.session_state.session_id, "user", user_text)

    # Generate assistant reply
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=st.session_state.messages,
                )
                reply = resp.choices[0].message.content
            except Exception as e:
                reply = f"Error calling OpenAI API: {e}"

        st.write(reply)

    # Store + show assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Log assistant reply
    append_log(st.session_state.session_id, "assistant", reply)
