# Progress

## 2026-06-21

Last Updated: 2026-06-21
Active feature: harness-state-lifecycle

### Current State

The repo already had a product-native harness through `AGENTS.md`, `docs/`, `checklists/`, `decisions/`, `prompts/`, and `.agents/skills/`. The missing state and lifecycle layer expected by `harness-creator` has now been added.

### What changed

- Added `feature_list.json` for active feature state, done criteria, dependencies, evidence, and next step.
- Added `progress.md` for append-only work history and Verification Evidence.
- Added `session-handoff.md` for restartable session handoff.
- Added root verification entrypoints `init.ps1` and `init.sh`.
- Updated `AGENTS.md` with Startup Workflow, Scope Rules, Verification Commands, Definition of Done, and End of Session procedure.

### Verification Evidence

- `node C:\Users\VUDUYLINH\.codex\skills\harness-creator\scripts\validate-harness.mjs --target "C:\Users\VUDUYLINH\PycharmProjects\Travel AI Agent"` passed with Overall `100/100`; all five subsystems passed.
- `.\init.ps1 -SkipFrontend` passed; it ran Python compile through `.agents/skills/validation-demo/scripts/check_project.ps1`.
- `bash ./init.sh --skip-frontend` passed; it ran Python compile through the shell wrapper.
- Full frontend lint/build was not run in this handoff because the worktree already had unrelated modified frontend files before this harness task.

### Blockers

- None for the harness layer.

### Next

Pick the next product feature only after the user selects or defines it. For future work, keep `feature_list.json`, `progress.md`, and `session-handoff.md` current at session boundaries.

## 2026-06-26

Last Updated: 2026-06-26
Active feature: simplify-agent-flow

### Current State

The simplify-agent-flow feature is complete. All done criteria are satisfied and successfully verified.

### What changed

- **Backend Graph**: Removed `human_confirm` and `reflect` nodes from `main_graph.py`, allowing the travel planner to flow directly to supervisor, and supervisor to route to decision and respond nodes.
- **FastAPI API**:
  - Removed `reflect` from `NODE_STATUS_MAP` in `chat.py`.
  - Updated `_persist_processed` to save draft plans and decided trips without intermediating through the `awaiting_confirmation` status.
  - Added 409 Conflict check in `resume_chat` and `stream_resume` endpoints if no pending interrupt exists.
  - Fixed `owner_id` context propagation bug in the synchronous `/api/v1/chat` endpoint.
  - Added exception stack trace printing to streaming endpoints for cleaner troubleshooting.
  - Sanitized `comfort_level` and collection fields in `trip_plan_from_graph_plan` to default gracefully rather than triggering Pydantic validation errors.
- **Frontend (React)**:
  - Removed the always-disabled plan confirmation button from `TripWorkspace.jsx`.
  - Allowed `ChatInput` to be enabled even during planner missing fields query/drafting, only disabling it during active streaming.
- **Smoke Tests**:
  - Updated `smoke_test_api.py` (TC5 asserts no interrupt, TC7 asserts 409 Conflict guard on resume).

### Verification Evidence

- **Compilation**: Run `python -m compileall src main.py` successfully compiled all Python files.
- **Frontend Build**: Run `npm run lint` and `npm run build` in the `frontend` directory successfully completed with zero errors and produced production-ready client bundles.
- **API Smoke Tests**: Run the full API suite locally, validating health check, sessions list, chitchat stream (with Vietnamese encoding fix), out-of-scope check, full travel flow drafting/response, trip workspace inspection, usage endpoint, markdown export, and resume conflict guard. All 10 scenarios passed successfully.

### Blockers

- None.

### Next

Await user instructions for the next active feature or task.


## 2026-06-27

Last Updated: 2026-06-27
Active feature: pm-current-status-report

### Current State

Generated a PM-ready current-state report for Travel AI Agent based on the current repo state, product docs, active feature state, progress log, session handoff, backend/frontend maps, and selected live code paths.

### What changed

- Added `docs/11-current-status-report-for-pm.md`.
- Updated `feature_list.json` with the completed report artifact feature.

### Verification Evidence

- `python -m compileall src main.py` passed.
- `python -m pytest tests/test_decision_engine.py tests/test_itinerary_builder.py tests/test_coverage_gate.py tests/test_auth.py -q` passed with 22 tests; pytest emitted cache permission warnings only.

### Blockers

- None for the report.
- Workspace still contains many modified/untracked files, so the report explicitly distinguishes current local state from clean release readiness.

### Next

PM should review the report and choose the next active feature. Recommended next feature: Route Sanity Checker UX.


## 2026-09-06

Last Updated: 2026-09-06
Active feature: lean-backend-graph

### Current State

Backend graph tinh gọn từ 12 node → 5: `classify_intent → {chitchat | planner} → {END | decision} → respond → END`. Hoàn tất, verify đầy đủ.

### What changed

- **Xoá** (−1065 dòng, 9 file): `agents/{supervisor,flight_agent,hotel_agent,weather_agent,info_agent,reflection}.py`, `nodes/{follow_up_node,out_of_scope_node}.py`, `api/utils/plan_builder.py`. Lý do: supervisor replan không bao giờ chạy; 4 agent chỉ là wrapper 1 dòng gọi gateway; reflection không được import; follow_up trùng planner; out_of_scope trùng chitchat.
- **`nodes/decision_node.py`**: `async def`; gọi `fetch_flights` ‖ `fetch_hotels` bằng `asyncio.to_thread` + `asyncio.gather`; giữ places/routes/weather/reviews như cũ; ghi normalized options (`flight_options`, `hotel_options`, `place_options`, `route_segments`, `weather_forecasts`, `review_summaries`) vào state.
- **`agents/response_agent.py`**: viết lại thành template deterministic từ `DecisionOutput` + `TripPlan`, bỏ LLM và `RESPONSE_AGENT_PROMPT`. Nhánh theo `decision_status` (recommended / needs_revision / insufficient_data).
- **`agents/planner_agent.py`**: return `plan.model_dump(mode="json")` trực tiếp; bỏ `_default_steps` và lớp convert; `_trip_plan_from_state` dùng `TripPlan.model_validate`.
- **`state/agent_state.py`**: cắt ~12 field chết (`user_request`, `search_type`, `flight_results`, `hotel_results`, `ranked_deals`, `needs_revision`, `revision_count`, `plan_modifications`, `agents_to_retry`, `reflection_issues`, `suggested_fixes`, `next_agent`, `reasoning`, `completed_agents`, `weather_info`, `search_info`, `current_step_index`); thêm 6 field normalized options.
- **`api/services/trip_service.py`**: xoá `trip_plan_from_graph_plan` / `graph_plan_from_trip_plan`; thêm `to_iata()` public.
- **`api/services/chat_service.py`**: bỏ nhánh interrupt trong `process_graph_result`.
- **`api/routers/chat.py`**: `NODE_STATUS_MAP` còn 5 node; `_persist_processed` dùng `TripPlan.model_validate`.
- **`api/routers/trips.py`**: `patch_trip_plan` dùng `plan.model_dump(mode="json")`; endpoint `actions` giờ chạy đúng vì state có options (bug fix).
- **`config/prompts.py`**: xoá 7 prompt chết; giữ classify/chitchat/planner + `build_missing_fields_question`.
- **`main.py`**: compile graph với `MemorySaver` trước khi invoke.
- **Tests**: `test_decision_node.py` chuyển async + TripPlan dump; thêm `test_response_template.py` (thay `test_response_agent_contract.py`); thêm `test_graph_flow.py`.

### Verification Evidence

- `python -m compileall src main.py` — pass.
- `python -m pytest tests/ -q` (bỏ `smoke_test_api.py`) — **60 passed**.
- `.\init.ps1` — Python compile + frontend `eslint .` + `vite build` (41 modules, 226.94 kB) pass.
- Manual E2E (uvicorn port 8012, `PYTHONUTF8=1`):
  - Chitchat → LLM reply. Out-of-scope → câu từ chối cố định, 0 LLM.
  - Travel (Hà Nội→Đà Nẵng, 25tr) → status [classify, planner, decision, respond], no error, `decision_status=recommended`, verdict template "**Khả thi** · 7.239.375₫ · dưới ngân sách · Tiết kiệm" + itinerary + route legs.
  - Travel không origin → `insufficient_data` "Không có dữ liệu chuyến bay" (coverage gate đúng).
  - `POST /trips/{sid}/actions` optimize_day + replace_place → 200, logic thật, `no_action` hợp lệ.

### Blockers

- `print()` tiếng Việt trong `classify_intent_node` crash trên stdout cp1252 (Windows). Workaround: `PYTHONUTF8=1`. Bug có sẵn, không do đợt này.
- `fetch_routes` còn loop tuần tự theo ngày — điểm chậm còn lại.

### Next

Commit. Rồi UI redesign (verdict-first, 2 pane) — xem plan `.claude/plans/oke-gi-l-n-plan-starry-cupcake.md` phần "Ngoài phạm vi".


## 2026-09-06 (2)

Last Updated: 2026-09-06
Active feature: ui-redesign-verdict-first

### Current State

Frontend áp dụng bản redesign "Lộ trình" (Claude Design canvas do user gửi): 2 pane, verdict-first workspace, palette teal, dark mode. Hoàn tất, build + lint pass, verify bằng screenshot.

### What changed

- **Design system** (`index.css`): viết lại — token light + dark (`:root` / `@media prefers-color-scheme` / `:root[data-theme="dark"]`), primary teal `#125f5c` (bỏ đỏ `#dc2626`), clay accent, semantic ok/warn/dgr/info. Font Be Vietnam Pro + JetBrains Mono (số) + Material Symbols Rounded (icon). CSS 1747 dòng → ~130 (phần lớn style chuyển thành inline trong component, khớp cách canvas gốc).
- **`index.html`**: nạp 3 Google Font, favicon 🧭, title/description mới.
- **Component 11 → 6**: mới `ChatPane.jsx`, `Workspace.jsx`, `lib/ui.jsx` (Icon), `lib/format.js` (money + formatMarkdown). Viết lại `Sidebar.jsx` (drawer), `PlanEditor.jsx` (restyle). Xoá `ChatBubble`, `ChatInput`, `TypingIndicator`, `TripWorkspace`, `OptionComparison`, `CostBreakdownPanel`, `ItineraryTimeline`, `RiskPanel`.
- **`ChatPage.jsx`**: shell 2 pane + sidebar drawer + mobile tabs (`Trò chuyện | Kế hoạch`, breakpoint 860px) + theme toggle (localStorage, `?theme=` param) + `?session=` param để mở phiên trực tiếp. Bỏ interrupt/HITL (`resumeChat`, `InterruptBubble`). State `wsTab`/`editingPlan` lift lên ChatPage (tránh setState-in-effect).
- **`Workspace.jsx`**: VerdictCard (strip màu theo `decision_status`, thanh confidence, verdict 1 câu, 3 mini-stat, CTA) + tabs Tổng quan / Lịch trình / Chi phí / Rủi ro. Place card có icon category + trust badge; route leg chip + confidence dot; day evidence; cost stacked bar; risk nhóm theo severity + blocking_reasons. 2 thang badge (trust + severity) thay vì 5 họ.
- **`agents/response_agent.py`**: rút gọn message chat còn ~4 dòng (verdict + 2 điểm chính + trỏ sang workspace). Bỏ dump full itinerary/cost/risk vào chat (đã có ở workspace). Xoá `_itinerary_lines`, `_cost_lines`.
- **Tests**: `test_response_template.py` cập nhật (message ngắn, ≤6 dòng).

### Verification Evidence

- `npm run lint` — pass (0 lỗi). `npm run build` — pass (37 modules, CSS 4.51 kB, JS 249 kB).
- `python -m pytest tests/ -q` (bỏ smoke) — **60 passed**.
- `python -m compileall src` — pass.
- Screenshot (Chrome headless, vite dev):
  - Desktop 1440 light — welcome + empty workspace: OK. Decided session (`?session=`): VerdictCard "Có thể đặt chỗ" + "Đi được với 5.292.025₫ theo phương án Tiết kiệm", 3 mini-stat, tabs, 3 option card (Tiết kiệm có viền teal + ⭐ Khuyến nghị): OK.
  - Desktop 1440 dark (`?theme=dark`) — welcome: OK, mint accent + clay tiles, contrast tốt.
  - Mobile: overflow đo bằng CDP iframe (ép width 320/375/414) → `scrollWidth == clientWidth`, không element nào tràn. (Screenshot headless trực tiếp bị méo do `vw` tính theo screen 1920 chứ không theo window — artifact của headless, không phải bug layout.)

### Blockers

- Dark mode + mobile chỉ verify gián tiếp (CDP đo overflow + 1 screenshot dark desktop). Nên mở trình duyệt thật kiểm tra nhanh khi có dịp.
- Nội dung `why_recommended` từ `decision/engine.py` vẫn dùng id tiếng Anh + số có dấu phẩy ("cheapest", "5,292,025 VND"). UI hiện đúng nhưng xấu — sửa ở engine sau.
- `booking_links` rỗng khi provider không trả URL → footer "Chưa sẵn sàng đặt chỗ" dù `decision_status=recommended`. Chấp nhận được.
- `frontend/src/services/api.js` còn export `resumeChat` (không dùng) — dọn sau.

### Next

Commit. Kiểm tra trên trình duyệt thật (dark + mobile). Rồi: what-if ngân sách, verified place identity end-to-end, xoá endpoint resume.


## 2026-09-06 (3)

Last Updated: 2026-09-06
Active feature: repo-tidy

### What changed

- **Root dọn sạch**: `12_week_plan.md` `SPEC.md` `TRAVEL_AGENT_IMPROVEMENT_PLAN.md` `benchmark_report.md` → `docs/`. Xoá `_append_forecast.py` (migration script đã chạy), `seed_sid.txt`. Root .md giờ chỉ còn `AGENTS.md` `README.md` `progress.md` `session-handoff.md`.
- **Docker**: xoá `Dockerfile` cũ (hỏng — `CMD uvicorn main:app` nhưng `main.py` là REPL; `pip install .` từ pyproject không có dep). `Dockerfile.backend` → `Dockerfile` (bản đúng, dùng `requirements.txt`, `--app-dir src`). `docker-compose.yml build: .` giờ trỏ đúng.
- **`src/travel_ai_agent/agents/` → gộp vào `nodes/`**: `planner_agent.py` → `nodes/planner_node.py`, `response_agent.py` → `nodes/respond_node.py`. `nodes/` giờ đủ 5 node `*_node.py`. Xoá `agents/`. 3 import site cập nhật.
- **`src/travel_ai_agent/services/` → `core/`**: bỏ trùng tên với `api/services/`. `guardrails.py` + `llm_service.py`. 6 import site cập nhật (sed).
- **`.gitignore`**: thêm `run-logs/` `seed_sid.txt` `data/*.sqlite`. Xoá 198 file `data/test-*.sqlite` khỏi disk. `git rm --cached seed_sid.txt`.
- **Docs**: viết lại `README.md` (layout tree + Backend Flow theo graph 5-node) và `.agents/skills/backend/references/backend-map.md`.
- **Giữ nguyên** (convention LangGraph, churn cao): `edges/` `graphs/` `state/` mỗi cái 1 file — không gộp. `src/travel_ai_agent/` là tên package, không đổi thành `backend/`.

### Verification Evidence

- `python -m compileall src main.py` — pass.
- `python -m pytest tests/ -q` (bỏ smoke) — **60 passed**.
- `.\init.ps1` — Python compile + frontend eslint + vite build (`✓ built`) pass.

### Next

Commit tất cả (backend lean + UI redesign + repo tidy). Rồi feature mới.
