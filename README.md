# 🎓 RBS Nigeria — Executive Master in Data Science AI Advisor

An intelligent chatbot that answers questions about the **Executive Master in Data Science Management** at Rome Business School Nigeria, and compares it with the Italy campus.

Built with LangChain Agent + Pinecone + Google Gemini Pro + Streamlit.

---

## What It Does

- Answers any question about the RBS Nigeria programme
- Compares Nigeria and Italy campuses side by side
- Searches live web for latest RBS news
- Shows its reasoning, which tools it used and why
- Cites the source of every answer

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent & Tools | LangChain + LangGraph |
| LLM | Google Gemini Pro |
| Vector Database | Pinecone |
| Embeddings | Google text-embedding-004 |
| Web Scraping | Playwright |
| Web Search | DuckDuckGo (no API key needed) |
| UI | Streamlit |

---

## Project Structure

```
rbs-agent/
├── app.py                  # Streamlit chat interface
├── build_index.py          # One-time setup: scrape → embed → upload
├── requirements.txt
├── .env                    # Your API keys (never commit this)
├── data/
│   ├── raw/                # Scraped website content
│   └── pdfs/               # Optional PDF brochures
└── src/
    ├── scraper.py          # Scrapes both RBS websites
    ├── loader.py           # Chunks documents for embedding
    ├── embedder.py         # Uploads vectors to Pinecone
    ├── tools.py            # 8 specialised agent tools
    ├── agent.py            # LangGraph ReAct agent
    └── scheduler.py        # Weekly auto re-index
```

---

## The 8 Agent Tools

The agent picks the right tool based on the question — it does not always do the same thing.

| Tool | Used For |
|------|---------|
| `rbs_programme_search` | General programme questions |
| `rbs_compare_campuses` | Nigeria vs Italy comparisons |
| `rbs_fee_lookup` | Fees, costs, payment plans |
| `rbs_admission_checker` | How to apply, eligibility |
| `rbs_curriculum_lookup` | Modules, subjects, syllabus |
| `rbs_career_outcomes` | Jobs, alumni, career support |
| `rbs_web_search` | Latest news and updates |
| `general_knowledge` | Background concepts |

---

## Quickstart

**1. Clone and set up**
```bash
git clone https://github.com/yourusername/rbs-agent.git
cd rbs-agent
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

**2. Add your API keys — create a `.env` file**
```
GOOGLE_API_KEY=your_gemini_key_here
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_INDEX_NAME=rbs-chatbot
```

> Get Gemini key free at [aistudio.google.com](https://aistudio.google.com/app/apikey)  
> Get Pinecone key free at [app.pinecone.io](https://app.pinecone.io)  
> Create Pinecone index with **dimension=768**, **metric=cosine**

**3. Build the knowledge base (run once)**
```bash
python build_index.py
```

**4. Launch**
```bash
streamlit run app.py
```

App opens at `http://localhost:8501`

> If scraping is blocked (403 error), run `python manual_builder.py` instead and follow the prompts.

---

## Deploy Free to Streamlit Cloud

1. Push to GitHub (`.env` is gitignored — safe to push)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select your repo
3. Add your API keys under **Advanced settings → Secrets**
4. Deploy — live public URL in ~3 minutes

---

## Sources

- [RBS Nigeria](https://romebusinessschool.ng/executive-master-in-data-science/)
- [RBS Italy](https://romebusinessschool.com/master-in-data-science-executive/)
