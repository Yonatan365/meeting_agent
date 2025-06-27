# app.py – Streamlit chat UI for the YAML-Calendar agent
#
# Run:
#   pip install streamlit openai openai-agents-python pyyaml python-dotenv
#   streamlit run app.py
#
import asyncio
import streamlit as st
from dotenv import load_dotenv
from agents import Runner
from calendar_bot import scheduler   # your Agent object with tools

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="Calendar Bot", layout="wide")
st.title("📅 Yonatan's Calendar Bot")

# ── initialise session state ─────────────────────────────────────────
if "conversation" not in st.session_state:
    st.session_state.conversation = []   # full history (incl. tool calls)
if "display" not in st.session_state:
    st.session_state.display = []        # UI-only (user & assistant turns)

# ── render existing messages ────────────────────────────────────────
for msg in st.session_state.display:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── input box ───────────────────────────────────────────────────────
if prompt := st.chat_input("Type here…"):
    # 1) store user turn
    user_turn = {"role": "user", "content": prompt}
    st.session_state.conversation.append(user_turn)
    st.session_state.display.append(user_turn)
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2) call the agent in its own event loop
    async def call_agent(conv):
        return await Runner.run(scheduler, conv)

    result = asyncio.run(call_agent(st.session_state.conversation))

    # 3) persist full result history & UI reply
    st.session_state.conversation = result.to_input_list()
    assistant_turn = {"role": "assistant", "content": result.final_output}
    st.session_state.display.append(assistant_turn)

    # 4) show assistant reply
    with st.chat_message("assistant"):
        st.markdown(result.final_output)
