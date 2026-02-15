# ✈️ AI Travel Deal Hunter

Agentic chatbot tìm kiếm vé máy bay và khách sạn giá tốt nhất — xây dựng bằng **LangGraph** + **Gemini** + **FastAPI** + **React**.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent-blueviolet)

---

## 🏗️ Kiến trúc

```
User ──► Parser Node ──► [đủ info?]
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
              Search Node        Ask User Node
                    │                 │
                    ▼              (loop back)
              Ranker Node
                    │
                    ▼
             Response Node ──► AI trả lời
```

| Layer | Công nghệ |
|-------|-----------|
| LLM | Google Gemini 2.0 Flash |
| Agent Framework | LangGraph (StateGraph) |
| Flight Search | SerpAPI (Google Flights) |
| Hotel Search | Makcorps API |
| Backend | FastAPI + SSE Streaming |
| Frontend | React + Vite |

---

## 📁 Cấu trúc dự án

```
Travel AI Agent/
├── api.py                  # FastAPI server (SSE streaming + sessions)
├── main.py                 # CLI chatbot
├── .env                    # API keys (không commit)
├── config/
│   ├── settings.py         # Env vars & LLM config
│   ├── constants.py        # Node names, IATA codes
│   └── prompts.py          # Prompt templates
├── src/
│   ├── graphs/
│   │   └── main_graph.py   # LangGraph pipeline
│   ├── nodes/
│   │   ├── parser_node.py  # Parse user request → JSON
│   │   ├── search_node.py  # Search flights & hotels
│   │   ├── ranker_node.py  # LLM rank kết quả
│   │   ├── response_node.py# Format response
│   │   └── ask_user_node.py# Hỏi thêm thông tin
│   ├── edges/
│   │   └── routing_edges.py# Conditional routing
│   ├── tools/
│   │   ├── flight_search.py# SerpAPI wrapper
│   │   └── hotel_search.py # Makcorps wrapper
│   ├── services/
│   │   └── llm_service.py  # Gemini LLM client
│   └── state/
│       └── agent_state.py  # AgentState TypedDict
├── frontend/               # React Web UI
│   ├── src/
│   │   ├── pages/ChatPage.jsx
│   │   ├── components/
│   │   │   ├── ChatBubble.jsx
│   │   │   ├── ChatInput.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── TypingIndicator.jsx
│   │   └── services/api.js
│   └── vite.config.js
└── tests/
```

---

## 🚀 Cài đặt & Chạy

### 1. Clone & cài dependencies

```bash
git clone <repo-url>
cd "Travel AI Agent"

# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### 2. Cấu hình `.env`

```env
GEMINI_API_KEY=your_gemini_api_key
SERPAPI_API_KEY=your_serpapi_key
MAKCORPS_API_KEY=your_makcorps_key   # tùy chọn
```

### 3. Chạy

```bash
# Terminal 1 — Backend
uvicorn api:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Mở **http://localhost:5173** 🎉

### CLI mode (không cần frontend)

```bash
python main.py
```

---

## 🔌 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `POST` | `/api/chat` | Chat đồng bộ |
| `POST` | `/api/chat/stream` | Chat streaming (SSE) |
| `GET` | `/api/sessions` | Danh sách sessions |
| `GET` | `/api/sessions/{id}` | Lịch sử hội thoại |
| `DELETE` | `/api/sessions/{id}` | Xóa session |
| `GET` | `/api/health` | Health check |

---

## 💬 Ví dụ sử dụng

```
Bạn: Tìm vé máy bay từ Hà Nội đi Đà Nẵng ngày 20/3, budget 3 triệu
AI:  🔍 Đang tìm kiếm vé máy bay HAN → DAD...
     ✈️ Top 3 vé rẻ nhất:
     1. VietJet Air — 1,200,000 VND (bay thẳng, 1h20)
     2. Bamboo Airways — 1,450,000 VND (bay thẳng, 1h25)
     ...
```

---

## 📄 License

MIT
