# 🧠 FeedbackAI — AI-Powered Feedback Summarizer & Recommendation Engine

**FeedbackAI** is a simple, modern, functional full-stack web application that converts large volumes of unstructured text feedback (reviews, comments, survey responses) into structured intelligence, aspect-based sentiment breakdowns, and prioritized, actionable recommendations.

---

## 🌟 Key Features

1. **Social Media & Video Link Analysis (100% Free)**:
   - **YouTube Videos**: Paste any video link (`youtube.com/watch?v=...`) to analyze viewer retention, pacing complaints, and follow-up topics.
   - **YouTube Shorts**: Paste any Short link (`youtube.com/shorts/...`) for hook retention, viral factors, and replayability analysis.
   - **YouTube Channels**: Paste any channel handle (`youtube.com/@handle`) for macro-community sentiment, audience personas, and content gaps.
   - **Reddit Threads**: Paste any Reddit discussion (`reddit.com/r/.../comments/...`) to extract community debates, top counter-arguments, and consensus.
   - **Live URL Inspector**: Previews thumbnail, title, author, and comment counts before running analysis.
2. **Flexible Multimodal Feedback Input**:
   - **Direct Text Input**: Paste reviews, Instagram/YouTube comments, or survey answers.
   - **File Upload**: Upload `.csv` (with automatic feedback column detection) or `.txt` files.
   - **1-Click Sample Datasets**: Instant test datasets for social links, headphone reviews, and student feedback.
3. **Context & Goal Adaptation**:
   - Adapts analysis to the specific feedback source (Instagram, App Store, Product Reviews, Customer Support, Student Evaluations, Employee Surveys, etc.).
   - Prioritizes recommendations toward your objective (Improve Content, Fix Product Quality, Boost CSAT, Reduce Churn, Enhance Teaching).
3. **Structured AI Analysis**:
   - **Overall Sentiment**: Positive, Negative, Neutral, or Mixed with exact percentage distributions.
   - **Emotional Spectrum**: Intensity percentages for Delight, Frustration, Confusion, Excitement, Satisfaction, and Disappointment.
   - **Aspect-Based Sentiment**: Quantitative sentiment scores across dimensions (UI/UX, Speed, Content Depth, Customer Service) with supporting verbatim quotes.
   - **Recurring Themes**: Categorized by urgency level (Low, Medium, High, Critical) with mention frequency and expandable quotes.
   - **Voice-of-Customer Deep Dive**: Categorized lists of common complaints, recurring questions, user suggestions, and feature requests.
   - **Actionable Prioritized Recommendations**: Ranked with rationale grounded directly in customer quotes, projected impact, and effort level (Quick Wins vs. Strategic Projects).
4. **Export & History**:
   - Download complete **JSON** analysis payload.
   - Download structured **CSV** report summary.
   - Print or save as clean **PDF**.
   - Analysis history modal to switch between past runs or review historical trends.
5. **Zero-Config Smart Fallback**:
   - If an `OPENAI_API_KEY` is provided, FeedbackAI connects directly to OpenAI's frontier models with strict JSON schema outputs.
   - If no API key is provided, FeedbackAI seamlessly activates its built-in intelligent heuristic engine, allowing full local testing out of the box!

---

## 🛠️ Architecture & Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Lucide Icons, Vite
- **Backend**: Python 3.9+, FastAPI, SQLAlchemy, Pydantic v2
- **Database**: SQLite (default, zero configuration needed) or PostgreSQL (via `DATABASE_URL`)
- **AI/LLM**: OpenAI API (`gpt-4o-mini` / `gpt-4o`) with structured JSON schema outputs and offline smart heuristic fallback

---

## 🚀 Quick Start (Run Locally)

### 1. Prerequisites
- **Node.js** (v18+ recommended)
- **Python** (v3.9+ recommended)

---

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Set your OpenAI API key in .env for live LLM mode
# If omitted, it will automatically run in Smart Heuristic Simulation mode!
# OPENAI_API_KEY=sk-...

# (Optional) Set your YouTube Data API v3 key for real YouTube comment fetching
# Free tier gives 10,000 units/day (up to 1,000,000 comments/day) from Google Cloud Console
# YOUTUBE_API_KEY=AIzaSy...

# Run the FastAPI server
python run.py
```
> The backend server starts at **`http://localhost:8000`**  
> Interactive OpenAPI documentation: **`http://localhost:8000/docs`**

---

### 3. Frontend Setup

In a separate terminal:

```bash
cd frontend

# Install npm dependencies
npm install

# Start the Vite development server
npm run dev
```
> The frontend application starts at **`http://localhost:5173`**

---

## 🐳 Docker Deployment (Optional)

Run the entire application in isolated containers with Docker Compose:

```bash
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

---

## 📂 Project Structure

```
summariser/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py         # REST endpoints (analysis, export, history)
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic environment configuration
│   │   │   └── database.py       # Async SQLAlchemy session & engine
│   │   ├── models/
│   │   │   └── analysis.py       # Database models
│   │   ├── schemas/
│   │   │   └── analysis.py       # Pydantic validation & LLM schemas
│   │   ├── services/
│   │   │   ├── file_parser.py    # Robust CSV & TXT parsing engine
│   │   │   └── llm_analyzer.py   # LLM structured prompt & fallback analyzer
│   │   └── main.py               # FastAPI application setup & CORS
│   ├── .env.example              # Environment variables template
│   ├── requirements.txt          # Python dependencies
│   ├── run.py                    # One-command server runner
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.tsx            # Header & mode status badge
│   │   │   ├── FeedbackInput.tsx     # Context selectors, sample data & uploader
│   │   │   ├── Dashboard.tsx         # Results dashboard & exports
│   │   │   ├── SentimentChart.tsx    # Sentiment & emotion distribution
│   │   │   ├── ThemeCard.tsx         # Recurring theme cards with quotes
│   │   │   ├── RecommendationCard.tsx# Prioritized action cards
│   │   │   └── HistoryModal.tsx      # Past analysis manager
│   │   ├── App.tsx                   # Main state & workflow controller
│   │   ├── api.ts                    # Backend API client
│   │   └── types.ts                  # TypeScript interfaces
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🔒 Security & Best Practices

- **Grounded AI**: System prompts mandate citing verbatim excerpts and prevent fabricating numbers.
- **Environment Isolation**: API credentials are kept securely on the backend in `.env`.
- **Sanitized Parsing**: Input file sizes and character limits are validated with clear error handling.
- **Fail-Safe Operation**: If external network or LLM rate limits hit, the backend falls back gracefully.

---

## 📄 License
MIT License. Built for turning raw customer feedback into high-impact action.
