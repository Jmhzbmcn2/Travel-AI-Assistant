# Travel AI Agent Improvement Plan

## 1. Muc tieu

Nang cap du an tu mot multi-agent chatbot goi API thanh mot AI travel planning workspace co:

- State quan ly chuyen di ro rang
- UI tuong tac thay vi chi chat text
- Persistent memory
- Agent actions co confirmation
- Guardrails kiem soat chi phi va cau hoi ngoai pham vi
- Test coverage va production polish

Muc tieu la giup du an noi bat hon trong mat nha tuyen dung, the hien tu duy full-stack, agentic workflow va kha nang xay dung san pham AI co the van hanh thuc te.

## 2. Danh gia hien tai

Diem uoc luong hien tai: **6.5 - 7/10**

Diem manh:

- Co FastAPI backend
- Co React frontend
- Co SSE streaming
- Co LangGraph multi-agent
- Co planner, supervisor, tool agents
- Co HITL confirmation
- Co Docker
- Co README mo ta kien truc

Diem con thieu:

- UI van chu yeu la chatbot
- Memory chi la in-memory
- Chua co database that
- Chua co trip object persistent
- Chua co workflow tuong tac nhu chon ve/chon khach san/chinh itinerary
- Chua co mock booking/calendar/export
- Chua co guardrails kiem soat chi phi
- Chua co test coverage
- Error handling va logging con don gian
- Chua co demo story manh cho nha tuyen dung

Neu cai thien day du theo plan nay, diem ky vong: **8.5 - 9/10**.

## 3. Huong nang cap chinh

### 3.1. Bien chatbot thanh travel planning workspace

Thay vi chi tra loi text, he thong nen quan ly mot `Trip` hoac `TripPlan` co cau truc.

Vi du:

```json
{
  "trip_id": "trip_123",
  "destination": "Da Nang",
  "origin": "Ho Chi Minh City",
  "start_date": "2026-06-10",
  "end_date": "2026-06-13",
  "travelers": 2,
  "budget": 8000000,
  "selected_flight": null,
  "selected_hotel": null,
  "itinerary": [],
  "status": "draft"
}
```

Agent khong chi tra loi ma con cap nhat trang thai chuyen di.

### 3.2. Structured output cho agent

Response cua backend nen co ca text va structured payload de frontend render UI.

Vi du:

```json
{
  "type": "trip_plan",
  "message": "Minh da tao ke hoach so bo cho chuyen di Da Nang.",
  "data": {
    "trip": {},
    "flight_options": [],
    "hotel_options": [],
    "itinerary": []
  },
  "actions": [
    {
      "type": "select_flight",
      "label": "Chon chuyen bay nay"
    },
    {
      "type": "optimize_budget",
      "label": "Toi uu ngan sach"
    }
  ]
}
```

Các response type de xuat:

- `chat_message`
- `trip_plan`
- `flight_options`
- `hotel_options`
- `itinerary`
- `confirmation`
- `error`

### 3.3. Frontend tuong tac

Frontend nen chuyen tu chat-only sang workspace co:

- Flight cards
- Hotel cards
- Itinerary timeline
- Budget panel
- Action buttons
- Confirmation modal hoac confirmation card
- Sidebar danh sach trip/session

Các hanh dong UI nen co:

- `Chon chuyen bay`
- `Chon khach san`
- `Tim re hon`
- `Doi gio bay`
- `Lam lich trinh nhe hon`
- `Toi uu ngan sach`
- `Xuat lich trinh`
- `Tao lich calendar`

### 3.4. Persistent memory

Hien du an co `MemorySaver` va `SessionStore`, nhung deu la in-memory. Can them database.

V1 nen dung SQLite de de demo. Sau do co the nang len PostgreSQL.

Can luu:

- Sessions
- Messages
- Trips
- Selected flight/hotel
- Itinerary
- User preferences
- Tool usage/cost metadata

User preference memory nen gom:

- `preferred_budget`
- `preferred_hotel_star`
- `flight_time_preference`
- `travel_style`
- `food_preferences`
- `past_destinations`

### 3.5. Agent actions va confirmation flow

Agent nen co kha nang thuc hien action, nhung cac action quan trong phai qua confirmation.

Các action nen co:

- `create_trip_plan`
- `search_flights`
- `select_flight`
- `search_hotels`
- `select_hotel`
- `create_itinerary`
- `update_itinerary_item`
- `optimize_budget`
- `create_calendar_event`
- `export_itinerary`
- `mock_booking`
- `send_email_summary`

Flow mau:

```text
User: Len chuyen di Da Nang 3 ngay cho 2 nguoi.

Agent:
- Tao trip plan
- Tim ve may bay
- Tim khach san
- Tao lich trinh so bo

User bam: Chon chuyen bay 2

Agent:
- Luu selected_flight
- Cap nhat ngan sach con lai
- Goi y chon khach san phu hop

User bam: Xac nhan booking mock

Agent:
- Tao ma booking gia
- Xuat itinerary
- Tao calendar file
```

### 3.6. Mock booking, calendar va export

Neu chua co real booking API, dung mock booking.

Thong tin mock booking:

```json
{
  "booking_id": "MOCK-HOTEL-9382",
  "status": "confirmed",
  "provider": "mock",
  "created_at": "2026-05-15T10:00:00"
}
```

Tinh nang export nen co:

- Export Markdown
- Export PDF neu co thoi gian
- Export `.ics` calendar file

### 3.7. Cost & Scope Guardrails

Day la tinh nang quan trong de the hien tu duy production.

Can them lop guardrail truoc khi chay workflow nang.

Intent categories:

- `travel`: cho chay planner/tools
- `follow_up`: xu ly neu lien quan trip/session hien tai
- `chitchat`: tra loi ngan, khong goi external tool
- `out_of_scope`: tu choi nhe, khong goi planner/search/tool
- `abuse_or_spam`: canh bao hoac rate limit

Vi du phan hoi out-of-scope:

```text
Minh la tro ly du lich, minh co the giup ban len lich trinh, tim ve, khach san, thoi tiet va thong tin diem den.
```

Can them:

- Tool budget theo session
- Rate limit theo session/IP
- Cache ket qua external API
- Logging ly do bi block
- Estimated cost tracking

Tool budget vi du:

```json
{
  "session_id": "abc",
  "tool_calls": {
    "flight_search": 2,
    "hotel_search": 1,
    "weather": 1,
    "search": 2
  },
  "llm_calls": 8,
  "cost_limit_reached": false
}
```

Cache key vi du:

```text
flight_search:HCM:DAD:2026-06-10:2
hotel_search:DAD:2026-06-10:2026-06-13:2
weather:DAD:2026-06-10
```

TTL de xuat:

- Flight/hotel: 10-30 phut
- Weather: 1-3 gio
- Travel info/search: 24 gio

### 3.8. Error handling va observability

Can bo sung:

- Structured error response
- Timeout cho external API
- Retry nhe cho API search
- Logging co `session_id`, `trip_id`, `agent_name`
- Tool call status: `pending`, `success`, `failed`
- Fallback khi thieu API key

Log nen co dang:

```text
[GUARDRAIL] blocked out_of_scope session=abc reason=non_travel_question
[COST] session=abc tool=flight_search count=3
[TOOL] trip=trip_123 agent=hotel_agent status=success latency_ms=1200
```

### 3.9. Test coverage

Can them test backend va frontend.

Backend tests:

- Out-of-scope question khong goi planner/tool
- Travel intent duoc route vao planner
- Follow-up chi chay khi co session/trip phu hop
- Tool budget vuot gioi han thi bi chan hoac yeu cau confirm
- Cache hit khong goi lai external API
- Trip selection cap nhat dung selected flight/hotel
- Export itinerary tao output dung
- Session/trip persistence hoat dong sau restart app

Frontend checks/tests:

- Render flight cards
- Render hotel cards
- Render itinerary timeline
- Action button gui dung payload
- Confirmation flow hoat dong
- Chat streaming khong bi vo UI

### 3.10. README va demo polish

README nen bo sung:

- Demo screenshots hoac GIF
- Sample prompts
- Architecture diagram ro hon
- Section: `What makes this agentic?`
- Section: `Cost & Scope Guardrails`
- Section: `Key Technical Decisions`
- Section: `Known Limitations`
- Section: `Future Improvements`

Nen co demo story ro rang:

```text
1. User tao chuyen di Da Nang 3 ngay
2. Agent tao plan
3. User chon flight/hotel bang card
4. Agent cap nhat budget
5. User yeu cau lam lich trinh nhe hon
6. Agent sua itinerary
7. User xac nhan export
8. App tao itinerary file/calendar/mock booking
9. User hoi cau ngoai pham vi
10. Guardrail chan khong goi tool
```

## 4. API de xuat

### Trip APIs

```http
POST /api/v1/trips
GET /api/v1/trips/{trip_id}
PATCH /api/v1/trips/{trip_id}
POST /api/v1/trips/{trip_id}/actions
POST /api/v1/trips/{trip_id}/confirm
POST /api/v1/trips/{trip_id}/export
```

### Chat response mo rong

Van giu chat API hien tai de tuong thich, nhung response nen them structured payload.

```json
{
  "response": "Minh da tao ke hoach so bo.",
  "session_id": "abc",
  "type": "trip_plan",
  "structured": {
    "trip": {},
    "actions": []
  },
  "interrupt_data": null
}
```

### Action payload

```json
{
  "action": "select_hotel",
  "trip_id": "trip_123",
  "payload": {
    "hotel_id": "hotel_2"
  }
}
```

## 5. Thu tu uu tien trien khai

### Phase 1: Core state & structured response

- Tao `Trip` model/schema
- Luu trip vao SQLite
- Chuan hoa response co `type`, `data`, `actions`
- Frontend render itinerary co ban

### Phase 2: Interactive UI

- Flight cards
- Hotel cards
- Itinerary timeline
- Budget panel
- Action buttons

### Phase 3: Agent actions

- Select flight
- Select hotel
- Update itinerary
- Optimize budget
- Confirmation flow

### Phase 4: Guardrails

- Scope gate
- Out-of-scope refusal
- Tool budget
- Cache external API
- Rate limit
- Logging

### Phase 5: Export & mock booking

- Mock booking
- Export Markdown/PDF
- Calendar `.ics`
- Optional email summary

### Phase 6: Tests & polish

- Backend tests
- Frontend checks
- README screenshots/GIF
- Docker/deploy cleanup
- `.env.example`

## 6. Diem ky vong

Hien tai: **6.5 - 7/10**

Sau khi cai thien mot phan:

- Structured trip object + UI cards: **7.5 - 8/10**
- Them persistent memory + action workflow: **8 - 8.5/10**
- Them guardrails + tests + demo polish: **8.5 - 9/10**

Muon dat vung **9+**, can co it nhat:

- Interactive trip workspace
- Persistent trip state
- Agent actions co confirmation
- Cost/scope guardrails
- Test coverage du tot
- Demo story ro rang

## 7. Assumptions

- V1 chua can real booking API.
- Mock booking du de demo workflow end-to-end.
- SQLite la lua chon mac dinh cho persistence vi de setup.
- Frontend tiep tuc dung React/Vite hien tai.
- LangGraph multi-agent van duoc giu.
- Muc tieu chinh la nang cap chat luong portfolio/interview, khong phai commercial production ngay lap tuc.
