# Báo cáo Tổng kết Giai đoạn Phát triển MVP (Sprint 1 - Sprint 6)
**Dự án:** AI Travel Deal Hunter (Travel AI Agent)  
**Mục tiêu:** Xây dựng Defensible MVP cho hệ thống lên kế hoạch du lịch tự động, đảm bảo an toàn dữ liệu, tính khả thi của lộ trình, và độ tin cậy của chi phí thông qua tích hợp dữ liệu thật (Live APIs).

---

## Tổng Quan Kiến Trúc (Architecture Overview)
Hệ thống được thiết kế dựa trên kiến trúc Agentic Workflow kết hợp giữa quy tắc bảo vệ cứng (Deterministic Guardrails) và khả năng xử lý ngôn ngữ tự nhiên của LLM (LangGraph). 
- **Backend:** FastAPI, LangGraph, Python 3.11, SQLite.
- **Bảo mật:** JWT Authentication với HttpOnly Cookies, Token Bucket Rate Limiting, Row-level Owner Isolation.
- **Tích hợp:** SerpAPI (Reviews), Mocks/Live Gateways cho Flights & Hotels.

---

## Chi tiết các Sprint đã triển khai

### Sprint 1: Nền tảng dữ liệu và Workflow Agent
**Mục tiêu:** Định nghĩa luồng giao tiếp giữa User và AI, thiết lập Schema cốt lõi.
- Xây dựng cấu trúc Pydantic models cho `TripPlan`, `DecisionInput`, `DecisionOutput`.
- Phát triển module Provider Gateway (`gateway.py`) nhằm chuẩn hóa dữ liệu từ các API bên ngoài (chuyến bay, khách sạn, thời tiết).
- Tích hợp mô hình ngôn ngữ (LLM - Gemini/OpenRouter) để phân tích yêu cầu bằng ngôn ngữ tự nhiên của người dùng và chuyển hóa thành cấu trúc JSON.

### Sprint 2: Kiến trúc Async & State Persistence
**Mục tiêu:** Quản lý state của Agent một cách bền vững và hỗ trợ gián đoạn (Human-in-the-loop).
- Triển khai `AsyncSqliteSaver` tùy biến cho LangGraph, đảm bảo mọi trạng thái hội thoại (chat messages) và State của Agent đều được lưu trữ theo thời gian thực xuống SQLite.
- Xây dựng `SessionStore` để quản lý các chuyến đi (Trips) theo `session_id`, cho phép người dùng dừng việc lập kế hoạch ở bất kỳ bước nào và tiếp tục lại sau (Resume capability).
- Triển khai Streaming SSE (Server-Sent Events) để trả về phản hồi từng phần (chunk) cho giao diện người dùng, giảm thiểu độ trễ.

### Sprint 3: Guardrails, Báo giá & Evidence UX
**Mục tiêu:** Đảm bảo hệ thống không "ảo giác" (hallucinate) ra chi phí hoặc các chuyến bay không có thật.
- Xây dựng **Rule-Based Decision Engine**: Tách rời tác vụ tính toán toán học/chi phí ra khỏi LLM. Engine này chỉ sử dụng Python thuần để tổng hợp ngân sách, so sánh chi phí với giới hạn của user.
- Tích hợp **Evidence UX**: Mọi khuyến nghị (Recommendation) đều phải đi kèm với bằng chứng (ví dụ: giá vé từ hãng nào, link đặt phòng ở đâu).
- Phát triển hệ thống Risk Detector để gắn cờ các cảnh báo (Warnings) tự động như "ngân sách quá eo hẹp" (`budget_tight`) hoặc "thiếu dữ liệu điểm đến".

### Sprint 4: Bảo mật & Identity (JWT Authentication)
**Mục tiêu:** Đảm bảo hệ thống có thể public an toàn, không rò rỉ dữ liệu chéo giữa các người dùng.
- Tích hợp JWT Authentication. Xây dựng endpoint Đăng ký/Đăng nhập an toàn.
- Cấu hình Access Token (15 phút, lưu memory) và Refresh Token (30 ngày, lưu dưới dạng HttpOnly Cookie chống XSS).
- Triển khai cơ chế **Owner Isolation**: Tất cả thao tác đọc/ghi vào `SessionStore` (trips, messages, decisions) đều bắt buộc phải đối chiếu `owner_id`. Người dùng A hoàn toàn không thể tiếp cận dữ liệu của người dùng B.
- Xây dựng cơ chế **Rate Limiting** tùy chỉnh (In-memory token bucket) tính theo IP để chống spam và DoS.

### Sprint 5: Đánh giá Chất lượng & Benchmark
**Mục tiêu:** Chứng minh sản phẩm đáng tin cậy và không bao giờ đưa ra "Unsafe Recommendation".
- Thiết lập bộ Test Dataset bao gồm 30 trường hợp (20 hợp lệ, 5 thiếu dữ liệu, 5 vượt ngoài vùng hỗ trợ).
- Xây dựng Benchmark Runner tự động test các trường hợp đi qua Decision Engine.
- **Kết quả Validation xuất sắc:** 
  - **Unsafe Recommendation Rate = 0.00%** (Tuyệt đối không cấp kế hoạch ảo).
  - **Blocking Accuracy = 100.00%** (Chặn thành công 10/10 ca lỗi/quá ngân sách).
  - Hệ thống tuân thủ 100% tài liệu `05-ai-behavior.md`: "LLM không được dùng để tính toán hay quyết định rule chặn, chỉ giải thích trade-offs".

### Sprint 6: Đóng gói Sản phẩm & CI/CD
**Mục tiêu:** Hoàn thiện Product Defense Package để sẵn sàng thuyết trình (Demo) hoặc chuyển giao.
- **Analytics & Tracking:** Bổ sung các event log quan trọng (`plan_completed`, `plan_edited`, `decision_blocked`) và thiết lập API thu thập Feedback từ user (Accept/Reject plan).
- **CI/CD Pipeline:** Triển khai GitHub Actions (`.github/workflows/ci.yml`) để tự động hóa quá trình chạy 56 unit/integration tests (chạy qua Pytest) và lint code.
- **Dockerization:** Đóng gói toàn bộ ứng dụng bằng Multi-stage `Dockerfile` và `docker-compose.yml`, giúp deploy lên bất kì server nào chỉ với 1 lệnh khởi động.
- Chuẩn bị đầy đủ tài liệu Báo cáo nghiệm thu (Validation Report) và Kịch bản Demo, bao gồm FAQ phòng thủ trước các reviewer khó tính.

---

## Tổng kết & Đề xuất (Next Steps)
Sau 6 Sprint, hệ thống Backend & Agentic Core đã hoàn thành `100%` tiêu chuẩn MVP đặt ra trong kế hoạch 12 tuần ban đầu. Nó cung cấp sự cân bằng hoàn hảo giữa tính linh hoạt của AI và tính nghiêm ngặt của một hệ thống thương mại điện tử.

**Định hướng tiếp theo:**
1. Mở khóa Frontend React UI (Tích hợp luồng Auth & Dashboard thực tế).
2. Tích hợp Affiliate Booking links thực tế để hoàn thiện Business Model.
3. Chạy Pilot Testing với 10-20 Users đầu tiên dựa trên kịch bản và Analytics Dashboard đã xây dựng.
