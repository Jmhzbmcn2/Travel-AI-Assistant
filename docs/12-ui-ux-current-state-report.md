# Travel AI Agent — Báo cáo hiện trạng UI/UX & API (cho redesign)

Ngày lập: 2026-08-31
Nguồn: trạng thái repo hiện tại `C:\Users\VUDUYLINH\PycharmProjects\Travel AI Agent`
Mục đích: tài liệu bàn giao cho chuyên gia thiết kế để redesign lại UI/UX.

Kèm theo báo cáo này:
- `docs/ui-redesign/current-ui-mock.html` — mock tĩnh (HTML/CSS thuần) mô phỏng đúng UI hiện tại với dữ liệu mẫu. Mở trực tiếp bằng trình duyệt, không cần chạy backend.

---

## 0. TL;DR cho designer

- Sản phẩm là **công cụ hỗ trợ ra quyết định chuyến đi**, không phải chatbot cảm hứng. User đã có ý tưởng (TikTok/Google), cần biết: đi được không, đủ tiền không, lịch trình có hợp lý không, chọn phương án nào, cắt gì nếu quá dày, rủi ro gì, làm gì tiếp theo.
- UI hiện tại là **layout 3 cột cố định trên desktop**: Sidebar (lịch sử) · Khung chat (command surface) · Decision Workspace (kết quả có cấu trúc).
- Chat là nơi ra lệnh; **Workspace bên phải là nơi sản phẩm tạo ra giá trị** (kế hoạch, chi phí, lịch trình, rủi ro, hành động).
- Toàn bộ chữ trong UI là **tiếng Việt**. Font: Plus Jakarta Sans (tiêu đề) + Inter (nội dung).
- Màu thương hiệu hiện tại: **đỏ `#dc2626`** làm màu nhấn chính (primary) — đây là điểm cần cân nhắc lại khi redesign (đỏ thường mang nghĩa cảnh báo/lỗi, xung đột với các badge trạng thái).
- Có sẵn **light theme duy nhất**, chưa có dark mode. Có sẵn `@media print` để "In PDF".
- Không có màn hình đăng nhập/onboarding trong UI (backend có auth nhưng `get_current_user()` đang bypass, trả về `demo_user_123`).

---

## 1. Kiến trúc frontend

| Hạng mục | Chi tiết |
|---|---|
| Framework | React 19 + Vite 7 |
| Routing | Không có router. `App.jsx` render thẳng `ChatPage`. 1 màn hình duy nhất. |
| State | `useState`/`useRef` cục bộ trong `ChatPage.jsx`. Không dùng Redux/Zustand/Context. |
| Styling | 1 file CSS toàn cục `frontend/src/index.css` (~1750 dòng), dùng CSS variables. Không CSS Modules, không Tailwind, không styled-components. |
| Data fetching | `fetch` thuần trong `frontend/src/services/api.js`. Streaming qua SSE đọc tay từ `ReadableStream`. |
| Markdown | Tự parse bằng regex trong `ChatBubble.jsx` (`formatMarkdown`), render qua `dangerouslySetInnerHTML`. Không dùng thư viện markdown. |
| Icon | **Không có bộ icon**. Mọi "icon" hiện là text ("Xe", "Bus", "Đi bộ", "...", "AI", "Bạn"). |
| Ảnh / hình | Không có. Không có ảnh địa điểm, không có bản đồ nhúng, chỉ có link "Mở Maps". |
| Responsive | 4 breakpoint: `1180px`, `960px` (ẩn sidebar, chuyển dọc), `640px` (1 cột), `print`. |
| Build/serve | `npm run dev` (cổng 5173), proxy `/api` → `http://localhost:8000`. |

### ⚠️ Lưu ý kỹ thuật quan trọng
`frontend/src/App.jsx` hiện đang chứa một dòng lỗi cú pháp cố ý (`<<<SYNTAX_ERROR_CRASH_VITE_RED_OVERLAY>>>` ở dòng 4) khiến app **không build/chạy được**. Đây là lý do mock phải dựng tĩnh bằng HTML. Cần xoá dòng này để app chạy lại (ngoài phạm vi task redesign, nhưng nên xử lý sớm).

### Cây component

```
App
└─ ChatPage                     (frontend/src/pages/ChatPage.jsx) — toàn bộ state & orchestration
   ├─ Sidebar                    lịch sử phiên, tạo phiên mới, đổi tên, xoá
   ├─ main.main-shell
   │  ├─ section.command-panel   (khung chat)
   │  │  ├─ header.command-header  tiêu đề + nút "Thu gọn workspace"
   │  │  ├─ div.messages-container
   │  │  │  ├─ WelcomeScreen (inline)   màn hình chào + 3 gợi ý bấm nhanh
   │  │  │  ├─ ChatBubble (user / assistant)
   │  │  │  ├─ InterruptBubble          thẻ xác nhận kế hoạch (HITL)
   │  │  │  └─ TypingIndicator          3 chấm nhảy + text trạng thái node
   │  │  └─ ChatInput               textarea auto-grow + nút "Gửi"
   │  └─ TripWorkspace           (aside.decision-canvas) — có thể thu gọn
   │     ├─ header.decision-header
   │     │  ├─ kicker "Decision workspace" + tiêu đề "Chuyến đi {điểm đến}"
   │     │  ├─ decision-status-card    pill trạng thái + badge độ phủ dữ liệu
   │     │  └─ trip-meta-grid          4 ô: Thời lượng / Số người / Ngân sách / Dự kiến
   │     ├─ div.decision-scroll
   │     │  ├─ workspace-skeleton      shimmer khi loading
   │     │  ├─ workspace-error         hộp lỗi đỏ
   │     │  ├─ PlanEditor              form sửa kế hoạch (2 cột)
   │     │  ├─ workspace-empty         trạng thái chưa có kế hoạch
   │     │  ├─ plan-section            "Bản nháp kế hoạch" (dl) + nút "Chỉnh sửa"
   │     │  ├─ missing-section         "Còn thiếu để xác nhận" (nền vàng)
   │     │  ├─ blocking-reasons-section "Lý do chưa thể khuyến nghị" (nền vàng)
   │     │  ├─ evidence-summary-section "Tại sao cần chỉnh sửa?" (nền vàng)
   │     │  ├─ OptionComparison        3 thẻ: Tiết kiệm / Cân bằng / Thoải mái
   │     │  ├─ CostBreakdownPanel      tổng chi phí + /người + badge ngân sách + chi tiết 6 khoản
   │     │  ├─ ItineraryTimeline       lịch trình theo ngày → PlaceCard + RouteLegCard + TrustBadge
   │     │  └─ RiskPanel               nhóm rủi ro Cao/TB/Thấp + toggle "Giả định"
   │     └─ footer.decision-actions    "Xuất Markdown" · "In PDF" · "Mở trang đặt chỗ"
```

---

## 2. Các màn hình / trạng thái UI (state inventory)

Chỉ có 1 route, nhưng UI có nhiều trạng thái. Designer nên thiết kế cho từng trạng thái:

### 2.1 Khung chat (cột giữa)
| Trạng thái | Khi nào | Hiện tại trông như thế nào |
|---|---|---|
| **Welcome / rỗng** | `messages.length === 0` và không streaming | Tiêu đề lớn "Biến ý tưởng du lịch thành kế hoạch có thể đi" + đoạn mô tả + 3 nút gợi ý (Đà Nẵng / Phú Quốc / Thái Lan) căn giữa theo chiều dọc |
| **Hội thoại** | có tin nhắn | Bong bóng user (căn phải, nền xám) và assistant (căn trái, nền hồng nhạt) + avatar tròn text "Bạn"/"AI" |
| **Đang stream text** | đang nhận chunk SSE | Bong bóng assistant cập nhật dần |
| **Đang xử lý (chưa có text)** | agent đang chạy node | `TypingIndicator`: 3 chấm + text theo node ("Trợ lý Khách sạn đang tìm kiếm phòng...", v.v. — xem §5) |
| **Chờ xác nhận (HITL/interrupt)** | graph interrupt | `InterruptBubble`: bong bóng assistant + thẻ "Xác nhận bản nháp kế hoạch?" với 2 nút [Xác nhận] [Chỉnh sửa]. *Ghi chú: flow MVP hiện tại thường không trigger interrupt.* |
| **Lỗi** | SSE trả `error` | Thêm 1 bong bóng assistant nội dung "Lỗi: ..." |

### 2.2 Decision Workspace (cột phải)
| Trạng thái | Khi nào |
|---|---|
| **Ẩn/thu gọn** | `isWorkspaceCollapsed` — cột trượt ra (width 0, translateX). Trên mobile: `display:none` |
| **Rỗng** (`workspace-empty`) | Chưa có `plan` — hộp "Bắt đầu bằng một yêu cầu chuyến đi" + bullet gợi ý |
| **Loading** | `workspace-skeleton` shimmer 3 dòng |
| **Có bản nháp kế hoạch, chưa có quyết định** | Hiện `plan-section` + có thể có `missing-section` (thiếu trường) |
| **Đang sửa kế hoạch** | `PlanEditor` thay chỗ `plan-section` |
| **Có quyết định — insufficient_data** | pill đỏ "Chưa đủ dữ liệu" + `blocking-reasons-section` + OptionComparison ở chế độ "bản nháp" (không có badge Khuyến nghị) |
| **Có quyết định — needs_revision** | pill vàng "Cần chỉnh sửa" + `evidence-summary-section` |
| **Có quyết định — recommended** | pill xanh "Có thể khuyến nghị" + 1 thẻ option có viền đỏ + badge "Khuyến nghị"; footer hiện nút "Mở trang đặt chỗ" |
| **Lỗi workspace** | hộp `workspace-error` đỏ |

### 2.3 Trạng thái badge trải khắp workspace (designer cần hệ thống hoá)
- **Decision status:** `recommended` (xanh) · `needs_revision` (vàng) · `insufficient_data` (đỏ)
- **Coverage status:** `verified` "Dữ liệu xác minh" · `draft_only` "Bản nháp" · `estimated` · `unsupported` "Chưa hỗ trợ"
- **Trust badge (từng địa điểm / chặng đường):** `verified` "Đã xác thực" · `estimated` "Ước tính" · `unverified` "Chưa kiểm chứng" · `fixture` "Dữ liệu test" · `missing` "Thiếu dữ liệu"
- **Budget status:** `under_budget` "Dưới ngân sách" · `near_limit` "Gần hết" · `slightly_over` "Hơi vượt" · `over_budget` "Vượt ngân sách" · `unknown` "Chưa rõ"
- **Risk severity:** `high` "Cao" (đỏ) · `medium` "Trung bình" (vàng) · `low` "Thấp" (xanh)
- **Feasibility status (option):** "Khả thi" · "Khả thi có điều kiện" · "Cần chỉnh sửa" · "Không đủ dữ liệu"

> Vấn đề: 5 nhóm badge dùng chung 3 màu (xanh/vàng/đỏ) + primary cũng là đỏ → khó phân biệt ý nghĩa, dễ nhiễu thị giác. Đây là ưu tiên số 1 khi redesign.

---

## 3. Design tokens hiện tại (từ `index.css`)

### Màu
| Token | Giá trị | Dùng cho |
|---|---|---|
| `--surface-page` | `#f2f6f4` | nền toàn trang (xanh xám rất nhạt) |
| `--surface` | `#ffffff` | nền panel/thẻ |
| `--surface-soft` | `#f7faf8` | nền header, sidebar, thẻ phụ |
| `--surface-muted` | `#edf3f0` | nền hover, bong bóng user |
| `--surface-danger/warning/success/info` | `#fff1f2` / `#fff8e6` / `#eefaf2` / `#eef5ff` | nền badge/hộp trạng thái |
| `--text` | `#18201e` | chữ chính |
| `--text-muted` | `#596662` | chữ phụ |
| `--text-subtle` | `#74817d` | nhãn nhỏ, uppercase |
| `--border` | `#d9e2df` | viền mặc định |
| `--border-strong` | `#b7c4c0` | viền hover |
| `--primary` | `#dc2626` | **màu nhấn chính (đỏ)** — nút chính, link, avatar AI, viền option khuyến nghị, kicker |
| `--primary-hover` | `#b91c1c` | |
| `--primary-soft` | `#fff1f2` | nền bong bóng assistant, nút gợi ý welcome |
| `--warning` | `#9a5b0a` | chữ vàng |
| `--success` | `#13753b` | chữ xanh |
| `--danger` | `#bf1d2d` | chữ đỏ (gần trùng primary) |
| `--info` | `#1e4f9a` | chữ xanh dương (khuyến nghị rủi ro) |

### Bo góc
`--radius-control: 6px` (nút, input) · `--radius-panel: 8px` (thẻ, panel) · `--radius-pill: 999px` (badge, avatar) · bong bóng chat dùng `16px` cố định.

### Bóng đổ
`--shadow-sm: 0 1px 2px rgb(24 32 30 / 0.06)` · `--shadow-md: 0 12px 30px rgb(24 32 30 / 0.08)`

### Kích thước layout
`--sidebar-width: 260px` · `--workspace-width: clamp(360px, 32vw, 500px)` · cột chat: `minmax(460px, 1fr)`

### Typography
- Font tiêu đề: `'Plus Jakarta Sans'` (600/700/800), font nội dung: `Inter` (400–700) — nạp từ Google Fonts.
- Cỡ chữ dao động 10px–15px cho nội dung, tiêu đề welcome `clamp(28px, 4vw, 44px)`, tiêu đề workspace 22px.
- Font-weight rất nặng: hầu hết label/nút dùng **800**. Cảm giác tổng thể "đậm và đặc".

### Animation
- `bounce` (typing dots), `shimmer` (skeleton), transition 140ms cho hover.
- Tôn trọng `prefers-reduced-motion`.

---

## 4. Luồng tương tác chính

```
1. User mở app → Welcome screen (chat) + Workspace rỗng
2. User gõ yêu cầu (hoặc bấm 1 gợi ý) → POST /api/v1/chat/stream (SSE)
   - Nhận event `session` → set sessionId
   - Nhận nhiều event `status` → TypingIndicator đổi text theo node
   - Nhận nhiều event `chunk` → stream text vào bong bóng assistant
   - Có thể nhận `interrupt` → hiện InterruptBubble
   - Nhận `done` → chốt tin nhắn
3. Sau mỗi lượt: GET /api/v1/trips/{sid} → cập nhật toàn bộ Workspace
   + GET /api/v1/sessions → cập nhật sidebar
4. User có thể:
   - "Chỉnh sửa" kế hoạch → PlanEditor → PATCH /api/v1/trips/{sid}/plan
   - Bấm "Tối ưu ngày" / "Thay địa điểm" trên timeline → POST /api/v1/trips/{sid}/actions
     → kết quả thành công thì thêm 1 bong bóng assistant + reload workspace
   - "Xác nhận" trên InterruptBubble → POST /api/v1/chat/stream/resume (SSE, tương tự bước 2)
   - "Xuất Markdown" → mở GET /api/v1/trips/{sid}/export.md
   - "In PDF" → window.print() (CSS @media print ẩn sidebar + chat, chỉ in workspace)
5. Sidebar: chọn phiên cũ → GET /api/v1/sessions/{sid} (messages) + GET /api/v1/trips/{sid}
   đổi tên → PATCH /api/v1/sessions/{sid} ; xoá → DELETE /api/v1/sessions/{sid}
```

Điểm đáng chú ý về UX:
- **Không có optimistic full-page loading**; workspace reload hoàn toàn sau mỗi hành động (có skeleton).
- **Không có toast/notification system**; mọi phản hồi hành động được nhồi vào luồng chat dưới dạng bong bóng assistant hoặc hộp lỗi trong workspace.
- **Không có empty-state minh hoạ**, chỉ có text.
- **Nút "Thu gọn workspace" xuất hiện 2 chỗ** (header chat + header workspace) — trùng lặp.
- Sidebar khi chưa có phiên nào sẽ hiện 2 mục mẫu tĩnh ("Đà Nẵng 4N3Đ", "Phú Quốc 3N2Đ") không bấm được.
- Trên mobile (<960px) sidebar bị **ẩn hoàn toàn**, không có cách mở lại (không có hamburger).

---

## 5. Text trạng thái theo node agent (hiển thị trong TypingIndicator)

Từ `chat.py` `NODE_STATUS_MAP`:

| Node | Text hiển thị |
|---|---|
| `classify_intent` | Đang phân tích ý định... |
| `chitchat` | Đang chuẩn bị câu trả lời... |
| `follow_up` | Đang liên kết lịch trình... |
| `out_of_scope` | Đang kiểm tra phạm vi câu hỏi... |
| `planner` | Đang phác thảo kế hoạch chuyến đi... |
| `supervisor` | Trưởng nhóm đang phân chia công việc... |
| `flight_agent` | Trợ lý Chuyến bay đang tìm kiếm vé... |
| `hotel_agent` | Trợ lý Khách sạn đang tìm kiếm phòng... |
| `weather_agent` | Trợ lý Thời tiết đang xem dự báo... |
| `info_agent` | Trợ lý Thông tin đang tra cứu địa điểm... |
| `decision` | Đang phân tích rủi ro ngân sách... |
| `respond` | Đang hoàn thiện câu trả lời... |

Đây là cơ hội UX tốt: có thể hình dung "đội ngũ trợ lý đang làm việc" bằng đồ hoạ thay vì 3 chấm.

---

## 6. API endpoints

Base URL: cùng origin, prefix `/api/v1`. Dev: frontend proxy `/api` → `http://localhost:8000`.
Auth: **hiện bypass** — `get_current_user()` luôn trả `demo_user_123`. Không cần header token. (Có rate limit token-bucket theo IP: 100 token, hồi 2/s; vượt → 429.)

### 6.1 Chat — `/api/v1/chat`
| Method | Path | Body | Trả về | Ghi chú |
|---|---|---|---|---|
| POST | `/api/v1/chat` | `{message, session_id?}` | `{response, session_id, type, interrupt_data?}` | đồng bộ, không stream |
| POST | `/api/v1/chat/resume` | `{session_id, response: str\|dict = "ok"}` | như trên | 409 nếu không có interrupt đang chờ |
| **POST** | **`/api/v1/chat/stream`** | `{message, session_id?}` | **SSE** `text/event-stream` | endpoint chính FE dùng |
| POST | `/api/v1/chat/stream/resume` | `{session_id, response}` | SSE | 409 nếu không có interrupt |

**Định dạng SSE** (`data: {json}\n\n`), các `type`:
- `{type:"session", session_id}` — đầu stream
- `{type:"status", content}` — text trạng thái node (xem §5)
- `{type:"chunk", content}` — 1 mẩu text trả lời (~12 ký tự/mẩu, delay 30ms)
- `{type:"interrupt", content, data?}` — cần user xác nhận
- `{type:"done"}` — kết thúc
- `{type:"error", content}` — lỗi

### 6.2 Sessions — `/api/v1/sessions`
| Method | Path | Trả về |
|---|---|---|
| GET | `/api/v1/sessions` | `[{session_id, title, message_count}]` |
| GET | `/api/v1/sessions/{id}` | `{messages: [{role, content}]}` (404 nếu không có) |
| DELETE | `/api/v1/sessions/{id}` | `{status:"deleted"}` |
| PATCH | `/api/v1/sessions/{id}` | body `{title}` → `{session_id, title, message_count}` |
| GET | `/api/v1/sessions/{id}/usage` | tổng token/cost (chưa dùng trong UI) |

### 6.3 Trips / Workspace — `/api/v1/trips`
| Method | Path | Body | Trả về |
|---|---|---|---|
| GET | `/api/v1/trips/{id}` | — | `TripWorkspaceResponse` |
| PATCH | `/api/v1/trips/{id}/plan` | `TripPlanPatch` (mọi field optional) | `TripWorkspaceResponse` |
| GET | `/api/v1/trips/{id}/decision` | — | `TripWorkspaceResponse` |
| POST | `/api/v1/trips/{id}/decision/feedback` | `{action:"accepted"\|"rejected", reason?}` | `{status:"recorded"}` (chưa dùng trong UI) |
| POST | `/api/v1/trips/{id}/actions` | `{action:"optimize_day"\|"replace_place", target_day?, target_place_id?}` | `TripActionResponse` |
| GET | `/api/v1/trips/{id}/export.md` | — | `text/plain` (markdown) |

### 6.4 Auth — `/api/v1/auth` (chưa có UI)
`POST /register` · `POST /login` · `POST /refresh` · `POST /logout` — JWT access token + refresh cookie.

### 6.5 Khác
`GET /api/v1/health` → `{status:"ok"}` · `GET /api/v1/analytics/summary` → `{event_type: count}`

---

## 7. Data models chính (để designer biết field nào có sẵn)

### `TripWorkspaceResponse`
```
session_id: str
status: "empty" | "draft" | "decided" | "awaiting_confirmation" | ...
missing_fields: string[]          // vd ["destination","budget","preferences","days_or_date_range","comfort_level"]
plan: TripPlan | null
decision: DecisionOutput | null
metadata: object
```

### `TripPlan`
```
origin, destination: str
departure_date, return_date: date
days (1–30), nights, travelers (1–20)
budget_total, budget_per_person: number
currency: "VND"
comfort_level: "budget" | "medium" | "comfortable"
priority: "cheapest" | "less_travel" | "comfortable"
preferences: string[]
trip_type, goal: str
must_have, avoid, special_requirements, steps: string[]
```

### `DecisionOutput`
```
decision_status: "recommended" | "needs_revision" | "insufficient_data"
coverage_status: "draft_only" | "verified" | "estimated" | "unsupported"
confidence: "high" | "medium" | "low" | "insufficient"
budget_status: "under_budget" | "near_limit" | "slightly_over" | "over_budget" | "unknown"
total_cost, total_cost_per_person, budget_delta: number
feasibility_score, comfort_score, value_score: number (0–1, hiện chưa hiển thị dạng %)
cost_breakdown: {flights, hotels, food, local_transport, tickets, buffer}
recommended_option: "cheapest" | "balanced" | "comfortable" | null
options: RankedOption[]
itinerary: ItineraryDay[]
risks: Risk[]
assumptions: string[]
blocking_reasons: string[]
why_recommended: string[]
booking_links: string[]
data_freshness: {khoản: ISO datetime}
```

### `RankedOption`
```
id: "cheapest" | "balanced" | "comfortable"
total_cost: number
feasibility_status, comfort_status: str
cost_breakdown: {...}
tradeoffs: string[]        // hiển thị dạng chip
reasons: string[]          // bullet list
```

### `ItineraryDay` → `ItineraryItem` (PlaceCard) & `ItineraryLeg` (RouteLegCard)
```
day: int, date: date, title: str
items: [{ place_id, title, category, area, estimated_visit_minutes,
          estimated_cost, maps_url, confidence }]
route_legs: [{ from_label, to_label, mode:"driving"|"transit"|"walking",
               distance_km, duration_minutes, confidence, directions_url }]
travel_minutes: int
evidence: [{ rule, observed_value, recommendation }]   // hộp cảnh báo vàng trong ngày
```

### `Risk`
```
type: str
severity: "low" | "medium" | "high"
message: str
recommendation: str
target_day, target_place_id: optional
```

---

## 8. Đánh giá UX & danh sách vấn đề cần redesign xử lý

### Nghiêm trọng / ưu tiên cao
1. **Hệ thống màu trạng thái bị quá tải.** primary = đỏ, đồng thời đỏ = lỗi/rủi ro cao/vượt ngân sách. 5 họ badge chia nhau 3 màu. → Cần: đổi màu thương hiệu sang màu trung tính hơn (xanh dương/teal), tách bảng màu semantic riêng, thêm icon phân biệt.
2. **Workspace quá tải thông tin, không có phân cấp.** Khi có decision đầy đủ, cột phải là 1 chuỗi ~6 section xếp dọc dài, đều nhau về trọng số thị giác. Không có "câu trả lời 1 dòng" ở trên cùng (kiểu: *"Chuyến đi khả thi, ~9,8 triệu, dưới ngân sách 200k — nên đi phương án Cân bằng"*).
3. **Không có visual cho địa điểm & bản đồ.** PlaceCard chỉ có text + link "Mở Maps". Không ảnh, không map, không cụm địa điểm trên bản đồ. Đây là sản phẩm du lịch — thiếu hình ảnh là điểm yếu lớn.
4. **"Icon" là chữ.** "Xe"/"Bus"/"Đi bộ"/"..." /"AI"/"Bạn". Cần bộ icon thật.
5. **Feedback hành động lẫn vào chat.** Bấm "Tối ưu ngày" → kết quả nằm ở bong bóng chat phía xa, user đang nhìn workspace không thấy. Cần inline feedback / diff view (schema `TripActionResponse` đã có `before_summary`/`after_summary` nhưng UI không dùng).
6. **Mobile hỏng về mặt tính năng.** Sidebar biến mất không lối vào; workspace + chat xếp dọc rất dài; không tối ưu cho việc lập kế hoạch trên điện thoại (dù target user là người Việt đi du lịch — rất nhiều dùng mobile).

### Trung bình
7. **Scoring 0–1 không được hiển thị** (feasibility/comfort/value). UX plan cũ ghi chú "khả thi 100%, thoải mái 55%" gây hiểu nhầm — designer nên quyết định cách thể hiện (hoặc bỏ, hoặc diễn giải bằng chữ).
8. **Nút trùng lặp** ("Thu gọn workspace" x2).
9. **Welcome screen** chỉ có text + 3 nút; thiếu định vị sản phẩm, thiếu ví dụ kết quả, thiếu giải thích "tôi khác chatbot ở đâu".
10. **`missing_fields` / `blocking_reasons` / `evidence`** đều là hộp nền vàng giống nhau, xếp cạnh nhau → user không phân biệt "tôi cần nhập gì" vs "hệ thống chưa chắc chắn gì".
11. **Không có trạng thái đăng nhập / hồ sơ / nhiều thiết bị.** Sidebar "Gần đây" nhưng không có tìm kiếm, nhóm theo ngày, hay phân biệt phiên nháp/đã chốt.
12. **Chat markdown parser tự viết** — dễ vỡ layout với nội dung phức tạp (bảng, link, nested list).
13. **`InterruptBubble` / HITL** hiện gần như không dùng trong flow MVP nhưng vẫn chiếm chỗ trong thiết kế — cần làm rõ có giữ hay không.
14. **Export chỉ có Markdown thô** (~10 dòng). "Trang đặt chỗ" chỉ là link ngoài. Không có bản chia sẻ đẹp.

### Điểm mạnh nên giữ
- Mô hình **chat = ra lệnh, workspace = kết quả có cấu trúc** rõ ràng, đúng định vị sản phẩm.
- Có **trust/confidence layer** ở cấp dữ liệu (verified/estimated/fixture/missing) — hiếm sản phẩm có; cần làm nổi bật hơn chứ đừng bỏ.
- **Timeline theo ngày + route leg giữa các điểm** là cấu trúc tốt cho "route sanity".
- Có sẵn **print stylesheet**.
- Bảng phân cấp trạng thái quyết định (insufficient → needs_revision → recommended) là logic sản phẩm tốt.

---

## 9. Gợi ý hướng redesign (để designer tham khảo, không bắt buộc)

- **Tái phân cấp cột phải:** trên cùng là "verdict card" (1 câu kết luận + độ tin cậy + CTA chính), rồi mới đến chi tiết có thể mở rộng (accordion).
- **Bảng màu mới:** primary trung tính (không đỏ). Semantic: success/warning/danger/info riêng, dùng cùng icon set.
- **Bộ icon:** chọn 1 bộ (Lucide/Phospher...) cho mode di chuyển, category địa điểm, trạng thái.
- **Place card có ảnh + mini-map** (hoặc ít nhất placeholder khi thiếu dữ liệu — gắn với trust badge "chưa xác minh").
- **Diff view cho hành động** (optimize_day / replace_place): hiện "trước → sau" ngay tại chỗ.
- **Onboarding/welcome:** 1 màn hình giải thích giá trị + ví dụ kết quả thật (screenshot workspace).
- **Mobile:** layout tab (Chat ↔ Kế hoạch), sidebar thành drawer, place card gọn.
- **Trực quan hoá "đội trợ lý"** thay cho typing dots, dựa trên `NODE_STATUS_MAP`.
- **Dark mode** (hiện chưa có).
- Cân nhắc **màn hình đăng nhập** khi backend auth được bật.

---

## 10. Cách dùng mock kèm theo

`docs/ui-redesign/current-ui-mock.html`:
- Mở bằng trình duyệt (double-click). Không cần Node/Python/backend.
- CSS lấy gần như nguyên văn từ `frontend/src/index.css` → **phản ánh trung thực UI hiện tại**.
- Có thanh chuyển trạng thái ở đầu trang: **Trạng thái đầy đủ** / **Màn hình chào** / **Đang xử lý** / **Workspace rỗng**.
- Dữ liệu là mẫu tĩnh (chuyến Đà Nẵng 4N3Đ, 2 người, 12 triệu).
- Designer có thể chỉnh trực tiếp file này hoặc export sang Figma qua ảnh chụp / công cụ html-to-figma.
