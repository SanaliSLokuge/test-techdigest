import streamlit as st
import os
import feedparser
import requests
from educhain import Educhain, LLMConfig
from langchain_community.chat_models import ChatOpenRouter

# Setup OpenRouter Key
OPENROUTER_KEY = "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"
os.environ["OPENROUTER_API_KEY"] = OPENROUTER_KEY

# Initialize OpenRouter model
chat_model = ChatOpenRouter(
    model="mistral/mistral-7b-instruct",  # Or "meta-llama/llama-3-8b-instruct"
    openrouter_api_key=OPENROUTER_KEY
)

# Educhain config
llm_config = LLMConfig(custom_model=chat_model)
educhain_client = Educhain(llm_config)

# Summarization (uses OpenRouter via requests)
def generate_summary(text):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral/mistral-7b-instruct",
        "messages": [{"role": "user", "content": f"Summarize this:\n{text}"}],
        "temperature": 0.3
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        st.warning("Summary failed.")
        return ""

# Fetch RSS
def get_latest_news(url, max_items=3):
    return feedparser.parse(url).entries[:max_items]

# Flashcards
def generate_flashcards(text, num=3):
    try:
        result = educhain_client.qna_engine.generate_questions(topic=text, num=num)
        if hasattr(result, "questions"):
            return result.questions
        else:
            return []
    except Exception as e:
        st.warning(f"Educhain error: {e}")
        return []

# --- Streamlit UI ---
st.set_page_config(page_title="TechDigest AI")
st.title("🧠 TechDigest AI (Free with OpenRouter + Educhain)")

url = st.text_input("RSS Feed URL", value="https://techcrunch.com/feed/")
count = st.slider("Number of Articles", 1, 10, 3)

if st.button("Fetch & Generate"):
    with st.spinner("Loading..."):
        articles = get_latest_news(url, count)
        for idx, article in enumerate(articles, 1):
            st.subheader(f"{idx}. {article.title}")
            summary = generate_summary(article.summary)
            st.markdown(f"**Summary:** {summary}")
            cards = generate_flashcards(summary)
            if cards:
                st.markdown("**Flashcards:**")
                for card in cards:
                    st.markdown(f"- **Q:** {card.question}")
                    for opt in card.options:
                        st.markdown(f"  - {opt}")
                    st.markdown(f"**Answer:** {card.answer}")
            st.divider()
