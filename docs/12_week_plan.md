# Kế Hoạch 12 Tuần: Travel AI Agent → Defensible MVP

## Summary

**Mục tiêu:** Public MVP có thể tiếp nhận yêu cầu tự do, nhưng chỉ đưa recommendation khi chuyến đi đạt verified coverage.

**Nguồn lực:** 1 developer, 12 tuần, 10–20 người dùng test.

**Verified coverage v1:**

- Chuyến nội địa Việt Nam, một điểm đến.
- 2–5 ngày, 1–4 người, VND.
- Có live flight, hotel và route data hợp lệ.
- Không có fixture trong dữ liệu critical.
- Input ngoài coverage chỉ nhận draft, không đưa recommendation.

**Definition of Success:**

- Fixture/missing critical data không bao giờ tạo recommendation.
- User khác không thể truy cập trip của nhau.
- Test, lint và build chạy bằng một CI command.
- Có benchmark 30 cases và kết quả test với ít nhất 10 người dùng.

## Public API And Type Changes

- Thêm `CoverageStatus`: `verified | draft_only | unsupported`.
- Thêm `DecisionStatus`: `recommended | needs_revision | insufficient_data`.
- Thêm `DecisionConfidence`: `high | medium | insufficient`.
- `DecisionOutput.recommended_option` chuyển thành optional.
- Thêm `evidence`, `blocking_reasons`, `rule_version`, `data_freshness`.
- Thêm auth endpoints:
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/auth/me`
- Mọi chat/session/trip endpoint, trừ health và auth, yêu cầu authenticated user.

---

## Sprint 1 — Trust Contract Và Validation Baseline

**Goal:** Dừng việc tạo recommendation không đáng tin.

### Mini Steps

- **S1.1:** Thêm `DEMO_MODE=false` và provider fixture policy vào settings.
- **S1.2:** Thêm coverage/confidence/status fields vào domain schemas.
- **S1.3:** Viết `evaluate_coverage(DecisionInput)` kiểm tra phạm vi và dữ liệu critical.
- **S1.4:** Sửa `build_decision()`:
  - Fixture/missing flight, hotel hoặc route → `insufficient_data`.
  - Không tạo `recommended_option` hoặc booking links.
- **S1.5:** Fixture chỉ được provider trả về khi `DEMO_MODE=true`.
- **S1.6:** Thay UI “Khả thi X%” bằng `Khả thi`, `Cần chỉnh sửa`, `Không đủ dữ liệu`.
- **S1.7:** Hiển thị blocking reasons và data mode trên workspace.
- **S1.8:** Sửa test API `FakeGraph.aupdate_state`.
- **S1.9:** Thêm pytest config để tự nhận package `src` và dùng cache/temp hợp lệ.
- **S1.10:** Đồng bộ README, SPEC và roadmap bằng trạng thái `implemented`, `validated`, `planned`.

**Definition of Done**

- 100% test case fixture/missing critical data bị chặn recommendation.
- Test hiện tại chạy bằng một command và không còn lỗi collection.
- UI không còn phần trăm feasibility chưa validate.

---

## Sprint 2 — Provider Và Cost Reliability

**Goal:** Cost breakdown đúng với trip plan và có provenance rõ ràng.

### Mini Steps

- **S2.1:** Mở rộng flight search nhận cả `outbound_date` và `return_date`.
- **S2.2:** Thêm `price_scope`: `round_trip_per_traveler | one_way_per_traveler`.
- **S2.3:** Chặn verified recommendation nếu trip cần khứ hồi nhưng chỉ có one-way price.
- **S2.4:** Sửa hotel checkout dùng `return_date` hoặc `nights`, không dùng `days`.
- **S2.5:** Tách cost rules thành versioned configuration:
  - Per-person cost.
  - Per-day cost.
  - Per-night cost.
  - Fixed trip cost.
- **S2.6:** Gắn `provider`, `retrieved_at`, `data_mode`, `assumptions` vào mọi cost input.
- **S2.7:** Thay silent `except Exception` bằng structured provider error logging.
- **S2.8:** Thêm timeout và tối đa một retry cho provider calls.
- **S2.9:** Viết 10 golden cost scenarios: solo/couple/group, 2–5 ngày, one-way/round-trip, missing data.
- **S2.10:** Hiển thị cost assumptions và thời điểm lấy giá trên frontend.

**Definition of Done**

- Golden cost tests pass 100%.
- Không có round-trip recommendation sử dụng one-way cost.
- Người dùng nhìn thấy nguồn và thời điểm lấy giá.

---

## Sprint 3 — Rule-Based Feasibility Và Evidence UX

**Goal:** Mọi kết luận feasibility đều giải thích được.

### Mini Steps

- **S3.1:** Thêm `estimated_visit_minutes` vào itinerary item output.
- **S3.2:** Tính daily load gồm visit, route, meal và rest buffer.
- **S3.3:** Đặt rule v1:
  - Comfortable: tối đa 8 giờ hoạt động/ngày.
  - Medium: tối đa 10 giờ/ngày.
  - Budget: tối đa 11 giờ/ngày.
  - Travel time trên 180 phút/ngày → warning.
- **S3.4:** Dùng giờ đến/chuyến bay đi để giảm available time ngày đầu/cuối.
- **S3.5:** Weather thiếu hoặc ngoài forecast window chỉ tạo assumption, không giả forecast.
- **S3.6:** Tạo `DecisionEvidence` chứa rule, observed value, threshold và recommendation.
- **S3.7:** Cho người dùng chọn priority: `cheapest`, `less_travel`, `comfortable`.
- **S3.8:** Thay trọng số bí mật bằng weight preset công khai theo priority.
- **S3.9:** Thêm evidence panel và “Tại sao cần chỉnh sửa?” trên frontend.
- **S3.10:** Viết tests cho dense schedule, flight-time conflict, route overload và missing weather.

**Definition of Done**

- Mỗi warning có rule và evidence.
- Không hiển thị percentage score.
- Cùng input và priority luôn tạo cùng decision.

---

## Sprint 4 — JWT Authentication Và Ownership

**Goal:** Public MVP không làm lộ trip/session giữa người dùng.

### Mini Steps

- **S4.1:** Thêm dependencies `PyJWT` và `pwdlib[argon2]`.
- **S4.2:** Tạo migration runner với bảng `schema_migrations`.
- **S4.3:** Tạo bảng `users` và `refresh_tokens`.
- **S4.4:** Thêm `owner_id` vào sessions, trips, decisions và usage events.
- **S4.5:** Implement email/password register và login.
- **S4.6:** Access token hết hạn sau 15 phút.
- **S4.7:** Refresh token hết hạn sau 30 ngày, lưu hash và hỗ trợ revoke.
- **S4.8:** Refresh token dùng HttpOnly cookie; frontend giữ access token trong memory.
- **S4.9:** Thêm authorization dependency cho chat/session/trip endpoints.
- **S4.10:** Rate limit theo user và IP, không theo client-provided session ID.
- **S4.11:** Không trả raw exception cho client.
- **S4.12:** Viết tests: unauthorized, expired token, cross-user read/edit/delete, logout revoke.

**Definition of Done**

- User A không thể đọc, sửa, resume, export hoặc xóa dữ liệu User B.
- Health và auth endpoints vẫn public.
- Auth/security tests pass.

---

## Sprint 5 — Benchmark Và User Validation

**Goal:** Có evidence recommendation thực sự hữu ích.

### Mini Steps

- **S5.1:** Tạo benchmark dataset 30 cases:
  - 20 verified domestic cases.
  - 5 insufficient-data cases.
  - 5 unsupported/out-of-coverage cases.
- **S5.2:** Mỗi case có expected coverage, decision status, cost formula và warning labels.
- **S5.3:** Tạo benchmark runner xuất JSON/Markdown report.
- **S5.4:** Đo unsafe recommendation rate và warning precision.
- **S5.5:** Chuẩn bị interview script tập trung vào planning pain và trust.
- **S5.6:** Phỏng vấn 5 người trước moderated test.
- **S5.7:** Chạy usability test với 10–20 người:
  - Tạo trip.
  - Sửa plan.
  - Đọc evidence.
  - Chấp nhận hoặc reject recommendation.
- **S5.8:** Thu thập rejection reason bằng structured options.
- **S5.9:** So sánh thời gian tạo usable plan với ChatGPT/manual baseline.
- **S5.10:** Fix tối đa ba vấn đề có tần suất hoặc severity cao nhất.

**Definition of Done**

- Unsafe recommendation rate: `0%`.
- Insufficient-data blocking accuracy: `100%`.
- Warning precision theo human labels: mục tiêu `>=80%`.
- Ít nhất `70%` người test đánh giá evidence hữu ích.

---

## Sprint 6 — Public Demo Và Defense Package

**Goal:** Có MVP, case study và tài liệu đủ bảo vệ trước reviewer.

### Mini Steps

- **S6.1:** Thêm analytics events: plan completed, edit, decision blocked, recommendation accepted/rejected, next-action click.
- **S6.2:** Thêm usage summary nội bộ, không xây full admin dashboard.
- **S6.3:** Hoàn thiện loading, empty, provider failure và insufficient-data states.
- **S6.4:** Thêm ba case studies:
  - Verified recommendation.
  - Dense itinerary cần chỉnh sửa.
  - Provider failure bị chặn recommendation.
- **S6.5:** Thêm CI chạy compile, pytest, frontend lint và build.
- **S6.6:** Cập nhật Docker/env setup cho auth secrets và demo mode.
- **S6.7:** Viết product validation report gồm benchmark, user findings, limitations và next steps.
- **S6.8:** Chuẩn bị demo script và tough-reviewer Q&A.
- **S6.9:** Public deploy và chạy security/smoke checklist.
- **S6.10:** Đóng băng feature, chỉ sửa blocker trong tuần cuối.

**Definition of Done**

- Public demo yêu cầu auth và không lộ dữ liệu.
- CI xanh.
- Có benchmark report, user-validation report và ba demo cases.

---

## Priority Backlog

### P0 — Hoàn thành trong Sprint 1–4

- Confidence/coverage gate.
- Loại bỏ production fixture fallback.
- Cost và feasibility correctness.
- Auth/ownership.
- Test/CI baseline.

### P1 — Hoàn thành trong Sprint 5–6

- Benchmark.
- User validation.
- Evidence UX.
- Analytics và defense package.

### P2 — Postpone

- Affiliate integration.
- Shareable public trip links.
- PDF đẹp.
- Preference memory.
- Agency handoff.

## What Not To Build Trong 12 Tuần

- Full booking/payment.
- Multi-city optimization.
- Visa hoặc accessibility recommendation.
- Group voting/split bill.
- Mobile app.
- Agency dashboard.
- Review sentiment AI.
- Thêm agent mới.
- Recommend outbound trip khi chưa có verified coverage.

## Test Plan

- Unit: coverage gate, cost rules, feasibility rules, priority presets.
- Integration: provider failure, stale data, one-way-only data, auth ownership.
- API: chat/HITL vẫn giữ `thread_id=session_id`; SSE event types không bị phá.
- Frontend: verified, needs-revision, insufficient-data và auth-expired states.
- Benchmark: 30 fixed cases chạy lại sau mọi thay đổi Decision Engine.
- Security: cross-user access, revoked refresh token, raw-error leakage.
- Release gate: compile, pytest, lint, build, benchmark và smoke test đều pass.

## Assumptions

- Một developer triển khai tuần tự trong 12 tuần.
- Auth dùng email/password JWT.
- Có thể tuyển 10–20 người dùng test.
- Sản phẩm nhận input tự do nhưng chỉ recommend khi đạt verified coverage.
- SQLite tiếp tục dùng cho MVP; PostgreSQL và horizontal scaling bị hoãn.
- Existing SSE contract và LangGraph HITL flow được giữ nguyên.
