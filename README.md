

# 🎬 Movie Recommendation Agent
> **Tired of scrolling endlessly through your Movies folder or streaming platforms? Let the Agent choose for you.**
> **Spend less time browsing and more time watching.**
> 
An AI-powered movie recommendation assistant built with **OpenAI Tool Calling**, **Structured Outputs (Pydantic)**, and **Streamlit**. 

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![OpenAI](https://img.shields.io/badge/AI-OpenAI_Tools-412991.svg)](https://platform.openai.com/)

**How does it work?** You are prompted for a type of movie you would like to watch (e.g., "A classic action movie from the 80s"). The agent gets a recommendation from OpenAI then check your local movie collection first. If no matching title is found in your personal library, it searched the web and retrieve a direct streaming link from a legitimate platform.

---

## ✨ Features

* **Local-First Search:** Prioritizes movies already available in your local `movie_library.json` using structured filtering by title, genre, and cast.
* **Web Search Fallback:** Automatically queries the web for streaming, rental, or purchase links (e.g., JustWatch, Prime Video, Apple TV) when a requested movie isn't in your library.
* **Guaranteed Structured Output:** Uses OpenAI's `beta.chat.completions.parse` with **Pydantic v2** to ensure every response strictly adheres to a predictable schema (`RecommendationResponse`).
* **Interactive Streamlit UI:** Features a browsable sidebar of your local library, one-click example prompt presets, clean metadata cards, and an expandable raw JSON inspector.

---

## 🏗️ Project Structure

```text
├── agent.py              # Core AI agent, Pydantic schemas, tool definitions, and OpenAI logic
├── app.py                # Streamlit web application frontend
├── movie_library.json    # Local JSON database of available movies
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites

* Python 3.10 or higher
* An [OpenAI API Key](https://platform.openai.com/)

### 2. Installation

Clone the repository and install the required packages:

```bash
git clone https://github.com/yourusername/movie-recommendation-agent.git
cd movie-recommendation-agent
pip install openai pydantic streamlit
```

*(Optional)* Create a `requirements.txt` with:
```text
openai>=1.40.0
pydantic>=2.0.0
streamlit>=1.35.0
```

### 3. Set Your OpenAI API Key

Export your API key as an environment variable:

**macOS / Linux:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY="your-api-key-here"
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

### 4. Configure Your Local Library

Ensure `movie_library.json` exists in the root directory alongside `agent.py`. It supports either a top-level list or a dictionary containing a `"movies"` key:

```json
[
  {
    "title": "Die Hard",
    "year": 1988,
    "genre": "action",
    "rating": 8.2,
    "audience": "adults",
    "director": "John McTiernan",
    "lead_actors": ["Bruce Willis", "Alan Rickman"],
    "synopsis": "An NYPD officer tries to save his wife and several others taken hostage by German terrorists during a Christmas party."
  }
]
```

### 5. Run the Application

Launch the Streamlit interface:

```bash
streamlit run app.py
```

---

## 🧠 How It Works

1. **User Input:** The user submits a natural language movie request in the Streamlit UI.
2. **Tool Call 1 (`lookup_movie_in_library`):** The agent is instructed via system prompt to always search `movie_library.json` first.
3. **Decision Branch:**
   * **Match Found:** The agent selects the best fit from your local library and sets `source="In Movie Library"`.
   * **No Match (`no_matches`):** The agent chooses a fitting real-world movie and triggers **Tool Call 2 (`find_streaming_link_for_movie`)**, which queries OpenAI's search-enabled model to locate a legal streaming URL, setting `source="External link"`.
4. **Structured Parsing:** The final conversation state is parsed directly into the `RecommendationResponse` Pydantic model and rendered cleanly in the UI.

---

## 🛠️ Customization

* **Genres & Ratings:** You can expand the allowed `Literal` genres or adjust validation constraints directly in the `Movie` model inside `agent.py`.
* **Models:** `agent.py` uses `gpt-4o` for tool orchestration and structured parsing, paired with `gpt-5-search-api` for web search. You can swap these models in `agent.py` as needed.
