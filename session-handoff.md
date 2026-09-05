# Session Handoff

Last Updated: 2026-09-06
Current Objective: Repo tidy (`repo-tidy`) — hoàn tất. Trong phiên đã làm: lean backend graph + UI redesign + repo tidy.

## Current Goal

3 việc lớn xong, chưa commit. Bước tiếp: commit chọn lọc, kiểm tra dark/mobile trên trình duyệt thật, rồi feature mới.

## Repo tidy (2026-09-06)

- 4 planning doc → `docs/`. Xoá `_append_forecast.py`, `seed_sid.txt`, 198 file `data/test-*.sqlite`.
- Docker: xoá `Dockerfile` cũ (hỏng), `Dockerfile.backend` → `Dockerfile`.
- `src/travel_ai_agent/agents/` → gộp vào `nodes/` (`planner_node.py`, `respond_node.py`). Xoá `agents/`.
- `src/travel_ai_agent/services/` → `core/` (bỏ trùng tên `api/services/`).
- `.gitignore` + `README.md` + `backend-map.md` cập nhật.
- Giữ nguyên: `src/travel_ai_agent/` (tên package, đúng — không đổi thành `backend/`); `edges/graphs/state` mỗi cái 1 file (convention LangGraph).
- Verify: `compileall` + `pytest` 60 passed + `init.ps1` pass.

## UI redesign (2026-09-06)

## UI redesign (2026-09-06)

Áp bản "Lộ trình" từ Claude Design canvas (`Thiết kế lại UI du lịch.zip`). 2 pane, verdict-first, palette teal, dark mode.

- **Component 11 → 6**: `ChatPane.jsx` + `Workspace.jsx` (mới), `Sidebar.jsx` (drawer) + `PlanEditor.jsx` (restyle), `lib/ui.jsx` (Icon) + `lib/format.js` (money/markdown). Xoá ChatBubble/ChatInput/TypingIndicator/TripWorkspace/OptionComparison/CostBreakdownPanel/ItineraryTimeline/RiskPanel.
- **`index.css`** viết lại: token light+dark theo pattern chuẩn, primary teal `#125f5c`, clay accent, semantic ok/warn/dgr/info. Style component phần lớn inline (khớp canvas gốc).
- **`index.html`**: 3 Google Font (Be Vietnam Pro, JetBrains Mono, Material Symbols Rounded).
- **`ChatPage.jsx`**: shell 2 pane + drawer + mobile tabs (860px) + theme toggle (localStorage + `?theme=`) + `?session=` param. Bỏ HITL/interrupt.
- **`Workspace.jsx`**: VerdictCard + 4 tab (Tổng quan/Lịch trình/Chi phí/Rủi ro). 2 thang badge thay 5.
- **`agents/response_agent.py`**: message chat rút còn ~4 dòng (verdict + trỏ workspace), không dump itinerary/cost/risk.

Verify: `npm run lint` + `npm run build` pass · `pytest tests/ -q` 60 passed · screenshot desktop light (welcome + decided workspace) + dark + CDP đo mobile không tràn (320/375/414).

## Lean backend graph (2026-09-06, phần trước)

## Current State

Graph còn 5 node: `classify_intent → {chitchat | planner} → {END | decision} → respond → END`.

- Xoá `supervisor`, 4 agent node (`flight/hotel/weather/info`), `reflection`, `follow_up`, `out_of_scope`, `plan_builder`. Tổng −1065 / +418 dòng, 9 file xoá.
- `decision_node` giờ `async`: gọi `fetch_flights` ‖ `fetch_hotels` (`asyncio.to_thread` + `gather`), rồi places/routes/weather/reviews như cũ. Ghi normalized options vào state (`flight_options`, `hotel_options`, `place_options`, `route_segments`, `weather_forecasts`, `review_summaries`).
- `response_agent` = template deterministic từ `DecisionOutput` + `TripPlan`, **không LLM**. → 1 LLM call/chuyến (chỉ planner; classify chỉ gọi LLM khi keyword không match).
- `state["plan"]` = `TripPlan.model_dump(mode="json")` trực tiếp. Xoá lớp convert `trip_plan_from_graph_plan` / `graph_plan_from_trip_plan`; thay bằng `to_iata()` trong `trip_service.py`.
- `AgentState` cắt ~12 field chết.
- Bug fix kèm theo: `POST /trips/{id}/actions` trước đây chạy với options rỗng (không node nào ghi `flight_options`... vào state). Giờ `decision_node` ghi → actions chạy đúng logic.
- `main.py` REPL: compile graph với `MemorySaver` trước khi `.invoke`.

## Files Touched

- `graphs/main_graph.py`, `edges/routing_edges.py`, `state/agent_state.py`
- `nodes/decision_node.py`, `nodes/chitchat_node.py`
- `agents/planner_agent.py`, `agents/response_agent.py`
- `api/services/trip_service.py`, `api/services/chat_service.py`
- `api/routers/chat.py`, `api/routers/trips.py`
- `config/prompts.py`, `main.py`
- Xoá: `agents/{supervisor,flight_agent,hotel_agent,weather_agent,info_agent,reflection}.py`, `nodes/{follow_up_node,out_of_scope_node}.py`, `api/utils/plan_builder.py`
- Tests: `test_decision_node.py` (async), `test_response_template.py` (mới, thay `test_response_agent_contract.py`), `test_graph_flow.py` (mới)

## Last Verified (2026-09-06)

- `python -m compileall src main.py` — pass.
- `python -m pytest tests/ -q` (bỏ smoke) — **60 passed**.
- `.\init.ps1` — Python compile + frontend `eslint` + `vite build` pass.
- Manual (uvicorn port 8012, `PYTHONUTF8=1`):
  - `/health` ok.
  - Chitchat → LLM reply. Out-of-scope ("viết code...") → câu từ chối cố định, không LLM.
  - Travel "Hà Nội → Đà Nẵng 3 ngày, 25tr" → 4 status (classify/planner/decision/respond), không error, `decision_status=recommended`, template verdict "**Khả thi** · 7.239.375₫ · dưới ngân sách · Tiết kiệm" + lịch trình + route leg + cảnh báo.
  - Travel không có origin → `insufficient_data` ("Không có dữ liệu chuyến bay") — đúng coverage gate.
  - `POST /trips/{sid}/actions` `optimize_day` / `replace_place` → 200, chạy logic thật, trả `no_action` hợp lệ (không còn crash/empty).

## Known Blockers

- `print()` tiếng Việt trong `classify_intent_node` crash khi stdout là cp1252 (Windows console mặc định). Chạy uvicorn với `PYTHONUTF8=1` để tránh. Bug có sẵn từ trước, không do đợt này. Nên bỏ các `print` debug hoặc ép UTF-8 khi khởi động.
- `why_recommended` từ `decision/engine.py` vẫn dùng id tiếng Anh ("cheapest"/"balanced") và số có dấu phẩy — cosmetic, engine không đụng đợt này.
- `fetch_routes` trong `decision_node` vẫn loop tuần tự từng ngày — điểm chậm còn lại, để tối ưu sau.
- Workspace repo còn nhiều file modified/untracked từ trước; cần commit/snapshot sạch trước khi bàn giao.

## Recommended Next Step

1. Commit đợt backend này.
2. UI redesign: verdict-first workspace, 2 pane, gộp badge còn 2 thang, component 10→6. Xem `docs/feature-report` (artifact) mục 06.
3. Sau đó: What-if ngân sách, verified place identity end-to-end.

## Next Session

Đọc `AGENTS.md`, `feature_list.json`, file này, entry mới nhất trong `progress.md`, và plan `.claude/plans/oke-gi-l-n-plan-starry-cupcake.md`.
