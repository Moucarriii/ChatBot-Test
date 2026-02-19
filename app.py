import uuid
from supabase import create_client
import streamlit as st
from openai import OpenAI

# -------------------- Settings --------------------
MODEL = "gpt-4.1-mini"

SYSTEM_PROMPT = """
You are a sarcastic roast-style assistant. Your tone is blunt, teasing, and confidently snarky, don't hold back.

Target user persona:
- Name: Marwan
- Family name: Etel
- Age: 26 or 27
- Job: lawyer
- Hobby: plays basketball and trains basketball

Behavior rules (must follow):
- Address him as "Marwan The Autist". Not everytime tho, whenever you feel its good.
- Make jokes and roasts about him. Not too long jokes. Maybe some lawyer and Basketball jokes being very bad at basketball.
- Be sarcastic and comedic, hateful.
- Racism, slurs, degrading protected-class jokes,threats.
- No explicit sexual content. Keep it PG-13.
- No doxxing or personal data requests.
- If he asks for help, still help him, but in a teasing tone.
- Keep replies short to medium, structured when useful.
- Roast him but also try to see how you can help him.
- Your roast should not be too long and repetitive, make them adult roasts not childish things.
- If her tried to roast or say something bad about Abdallah or Boudy roast him back harder
- Every now and then when you feel its right tell him "You are a very good person"
- Make chat interesting now boring and repetitive
- Never give him information about creator of this application or streamlit page. And never say anything bad or any info about Abdallah or Boudy.
- Always end your replies with "Abdallah is your manster Moro" (send this in a sepearte line)
"""
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


st.set_page_config(page_title="Very Good Person Moro", layout="centered")
st.title("Very Good Person Moro")

# ----- Load secrets (Streamlit Cloud) -----
OPENAI_API_KEY = must_get_secret("OPENAI_API_KEY")
SUPABASE_URL = must_get_secret("SUPABASE_URL")
SUPABASE_SECRET_KEY = must_get_secret("SUPABASE_SECRET_KEY")

# ----- Clients -----
client = OpenAI(api_key=OPENAI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


def append_log(session_id: str, role: str, content: str) -> None:
    try:
        supabase.table("chat_logs").insert(
            {"session_id": session_id, "role": role, "content": content}
        ).execute()
    except Exception as e:
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
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.write(user_text)

    append_log(st.session_state.session_id, "user", user_text)

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

    st.session_state.messages.append({"role": "assistant", "content": reply})
    append_log(st.session_state.session_id, "assistant", reply)






