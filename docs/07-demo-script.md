# Demo Script & Q&A

## 1. Demo Flow
Khởi động hệ thống bằng lệnh `docker-compose up -d`.

### Case 1: Verified Recommendation (The Happy Path)
1. **User Input:** "Tôi muốn đi từ Hà Nội đến Đà Nẵng 3 ngày 2 người, ngân sách 12 triệu."
2. **System Action:** Parser dịch ra JSON TripPlan. Agent gọi Live API.
3. **Result:** Trả về "Recommended" option kèm Booking Links.
4. **Highlight:** "Mọi chi phí ước tính ở đây không phải do AI sinh ra, mà được bóc tách từ API thật của hãng hàng không và khách sạn. Sự can thiệp của LLM chỉ nằm ở việc giải thích trade-offs cho dễ hiểu."

### Case 2: Insufficient Data / Missing Route (The Safe Block)
1. **User Input:** "Tôi muốn đi du lịch 10 ngày ở 5 thành phố khác nhau với 5 triệu."
2. **System Action:** Agent gọi API nhưng thiếu chuyến bay rẻ, hoặc budget quá thấp.
3. **Result:** Blocked. `decision_status` = `insufficient_data` hoặc `needs_revision`.
4. **Highlight:** "Đây là điểm cốt lõi của Defensible MVP. Khi không có đủ dữ liệu, AI không được phép đoán mò hay tạo ra một chuyến đi ảo tưởng."

### Case 3: Out-of-Coverage (The Guardrail)
1. **User Input:** "Đi du lịch New York cuối tuần này nhé."
2. **System Action:** Rule engine kiểm tra vị trí.
3. **Result:** Blocked. `decision_status` = `insufficient_data` (ngoài phạm vi).
4. **Highlight:** "Chúng ta khoanh vùng Coverage (Domestic) rất rõ, giảm rủi ro token và rủi ro hallucination cho các vùng chưa có data sources tốt."

---

## 2. Q&A
**Q1: Tại sao không để AI lo toàn bộ luồng Routing?**
A1: Agentic workflow của chúng tôi ưu tiên Deterministic Rules. Routing dựa trên logic code giúp hệ thống có thể dự đoán được (predictable), không bao giờ lọt lỗi nghiêm trọng, và dễ dàng benchmark.

**Q2: Làm sao để ngăn AI bị jailbreak để book vé máy bay giả?**
A2: AI không có tool để book vé máy bay. Quyền hạn của AI chỉ dừng ở việc "đề xuất plan" (Read-only). Hơn nữa, toàn bộ plan phải đi qua Rule Engine (kiểm tra coverage, kiểm tra price match) trước khi trả về. Hệ thống Auth đảm bảo chỉ user hợp lệ mới có thể tương tác.

**Q3: Tốc độ hiện tại có chậm do Agent không?**
A3: Rất nhanh. LLM chỉ được dùng để phân tích intent (lần 1) và giải thích quyết định (lần 2). Các việc tìm kiếm, so sánh giá, tổng hợp route hoàn toàn xử lý bằng Python Native.
