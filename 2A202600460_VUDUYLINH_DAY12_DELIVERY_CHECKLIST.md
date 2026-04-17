#  Delivery Checklist — Day 12 Lab Submission

> **Student Name:** Vũ Duy Linh 
> **Student ID:** 2A202600460 
> **Date:** 17/04/2026

---

##  Submission Requirements

Submit a **GitHub repository** containing:

### 1. Mission Answers (40 points)

Create a file `MISSION_ANSWERS.md` with your answers to all exercises:

```markdown
# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Hardcode thông tin nhạy cảm như API_KEY, REDIS_URL trong code, nếu đẩy code này lên GitHub thì người khác có thể lấy được API_KEY, REDIS_URL
2. Không có hệ thống quản lý cấu hình, các thiết lập như DEBUG, MAX_TOKENS bị hardcode cúng trong code thay vì đọc từ env hay config file, nếu muốn thay đổi thì phải đổi từng file và redeploy
3. Sử dụng print() thay vì logging chuẩn, và log luôn cả secret: Ứng dụng dùng hàm print để in ra các sự kiện, không có level (INFO, ERROR, WARN) và không dễ dàng để xuất ra file hay theo dõi trên cloud. Nguy hiểm hơn là in thẳng cả OPENAI_API_KEY ra màn hình console, tạo lỗ hổng bảo mật rò rỉ secret qua file log.
4. Thiếu API Health Check: Không có bất kỳ API nào (như /health hay /ping) để kiểm tra trạng thái sống còn của ứng dụng. Do đó, các nền tảng Cloud (như Docker, Kubernetes, Railway, Render,...) sẽ không thể biết được app có đang chạy ổn định hay đã bị crash/treo để tự động restart.
...

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config  | ...     | ...        | ...            |
...

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: Là "nền móng" ban đầu chứa hệ điều hành và các môi trường cần thiết để chạy ứng dụng (ví dụ: `FROM python:3.11`).
2. Working directory: Là thư mục làm việc mặc định bên trong container (ví dụ: `WORKDIR /app`).
3. Tại sao COPY requirements.txt trước?: Để tối ưu hóa Docker Layer Cache. Thư viện ít thay đổi, copy trước giúp dùng lại cache, không phải cài lại từ đầu mỗi khi code đổi, giúp build cực nhanh.
4. CMD vs ENTRYPOINT khác nhau thế nào?: `CMD` là lệnh mặc định dễ dàng bị ghi đè khi chạy container, còn `ENTRYPOINT` là lệnh cố định bắt buộc phải chạy và rất khó bị ghi đè.

### Exercise 2.3: Image size comparison
- Develop: [1.66] GB
- Production: [236.44] MB
- Difference: [~86.1]% (giảm khoảng 86.1% so với bản Develop)

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://linhvd-production.up.railway.app/
- Screenshot: screenshot\VuDuyLinh_railway_sc.png

## Part 4: API Security

### Exercise 4.1-4.3: Test results
**Exercise 4.1: API Key authentication**
- **API key được check ở đâu?** Được check trong Dependency `verify_api_key`, gắn vào endpoint `/ask` thông qua `Depends(verify_api_key)`.
- **Điều gì xảy ra nếu sai key?** Trả về mã lỗi `403 Forbidden` với thông báo "Invalid API key." (nếu thiếu hẳn thì trả về `401 Unauthorized`).
- **Làm sao rotate key?** Thay đổi biến môi trường `AGENT_API_KEY`, platform sẽ tự redeploy, sau đó cung cấp key mới cho phía Client.
- **Test Output:** 
  ```json
  // Gọi thiếu key (hoặc dùng curl -d '{"question":"Hello"}' sai định dạng parameter)
  {"detail":"Missing API key. Include header: X-API-Key: <your-key>"}
  
  // Gọi đúng key
  {"question":"Hello","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận."}
  ```

**Exercise 4.2: JWT authentication (Advanced)**
- **Luồng hoạt động (Flow):** Gửi username/password tới `/token` để lấy JWT. Cung cấp mã JWT đó trong header `Authorization: Bearer <token>` ở mỗi request `/ask`.
- **Test Output:**
  ```json
  // Gọi /auth/token thành công:
  {"access_token": "eyJhb...<token>...", "token_type": "bearer", "expires_in_minutes": 60, "hint": "Include in header: Authorization: Bearer eyJhb..."}
  
  // Gọi /ask với token:
  {"question":"Test 1","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","usage":{"requests_remaining":9,"budget_remaining_usd":0.000018}}
  ```

**Exercise 4.3: Rate limiting**
- **Algorithm nào được dùng?** Thuật toán Sliding Window Counter.
- **Limit là bao nhiêu requests/minute?** Role `user` là 10 requests/phút. Role `admin` là 100 requests/phút.
- **Làm sao bypass limit cho admin?** Dựa trên `role` giải mã được từ JWT token, code sẽ tự động trỏ tham chiếu limiter sang `rate_limiter_admin`.
- **Test Output:** (Sau request thứ 10 thành công, request thứ 11 trả về 429)
  ```json
  // Request 10
  {"question":"Test 10","answer":"Tôi là AI agent...","usage":{"requests_remaining":0,"budget_remaining_usd":0.000179}}
  
  // Request 11 & 12 (Bị chặn)
  {"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":57}}
  ```

### Exercise 4.4: Cost guard implementation
**Phương pháp thực hiện (Approach):**
- **Cơ chế lưu trữ:** Dùng Redis để theo dõi chi phí một cách cực nhanh và phân tán (phù hợp khi scale nhiều server).
- **Cách thiết kế Key:** Mỗi user trong mỗi tháng sẽ có một key riêng biệt định dạng `budget:{user_id}:{YYYY-MM}`.
- **Luồng xử lý (Logic):**
  1. Mỗi khi user gửi request, ta dự tính chi phí `estimated_cost` và lấy tổng chi phí đã tiêu trong tháng qua `r.get(key)`.
  2. Nếu `current_cost + estimated_cost > 10` ($10), hàm trả về `False` để block request.
  3. Nếu hợp lệ, ta cộng chi phí vào Redis bằng lệnh `r.incrbyfloat()` và thiết lập thời gian hết hạn (TTL) bằng lệnh `r.expire()` là 32 ngày (32 * 24 * 3600 giây).
- **Tại sao lại dùng `expire` 32 ngày?** Giúp Redis tự động dọn dẹp các dữ liệu chi phí của các tháng cũ (vì mỗi tháng dùng 1 key mới), qua đó tối ưu bộ nhớ.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
**Exercise 5.1: Health checks**
- Liveness probe (`/health`): Trả về 200 OK đơn giản để báo cho platform (Kubernetes/Railway) biết process của container vẫn đang chạy.
- Readiness probe (`/ready`): Kiểm tra kết nối tới các external services (như ping Redis, test Database). Nếu bị đứt kết nối hoặc đang bận khởi động, trả về 503 để Load Balancer không điều hướng traffic vào.

**Exercise 5.2: Graceful shutdown**
- Sử dụng thư viện `signal` để bắt tín hiệu `SIGTERM`.
- Thay vì tắt ngay lập tức, server sẽ ngừng nhận request mới, nhưng cho phép các in-flight requests (đang xử lý dở) được chạy cho tới khi hoàn thành (hoặc hết timeout), sau đó đóng kết nối database/Redis an toàn rồi mới `exit`. 
- **Kết quả test:** Khi gửi request xử lý tốn thời gian rồi lập tức gõ lệnh `kill -TERM`, log server hiển thị tiến trình đang chờ request xử lý xong rồi mới thực sự tắt.

**Exercise 5.3: Stateless design**
- Chuyển toàn bộ state (ví dụ lịch sử chat `conversation_history`) ra khỏi bộ nhớ (RAM/dict) của Python và lưu vào hệ thống ngoài (Redis).
- Lợi ích: Khi scale ra nhiều instance (mỗi instance có memory riêng), user gọi request vào bất kỳ instance nào đều đọc/ghi được lịch sử đúng từ Redis.

**Exercise 5.4: Load balancing**
- Sử dụng Docker Compose với Nginx làm Load Balancer. Khi chạy `docker compose up --scale agent=3`, 3 container agent sẽ được tạo.
- Nginx đóng vai trò là cửa ngõ nhận traffic ở port 80/443 rồi phân phối đều theo thuật toán Round-Robin tới 3 instance. Nếu 1 instance "chết", Nginx sẽ tự route sang 2 instance còn lại.
- **Kết quả test:** Gửi 10 request liên tục, kết quả sinh ra log phân bổ rõ ràng ra 3 instance khác nhau (round-robin):
  ```log
  production-agent-3  | {"time":"2026-04-17 09:42:24","level":"INFO","msg":"{"event": "request", "q_len": 9}"}
  production-agent-2  | {"time":"2026-04-17 09:42:24","level":"INFO","msg":"{"event": "request", "q_len": 9}"}
  production-agent-1  | {"time":"2026-04-17 09:42:24","level":"INFO","msg":"{"event": "request", "q_len": 9}"}
  ```

**Exercise 5.5: Test stateless**
- Mô phỏng môi trường production với file `test_stateless.py`. Dù có 3 instances nhận ngẫu nhiên các request trong 1 phiên chat, nhưng nhờ lưu data tập trung trên Redis nên dữ liệu lịch sử chat hoàn toàn không bị mất, và các instance đều nhận biết được session chung.
- **Kết quả test thực tế:**
  ```text
  ============================================================
  Stateless Scaling Demo
  ============================================================
  Session ID: 3e227d32-2164-4bac-8c72-0650947ae0e0
  
  Request 1: [instance-26dad5]
    Q: What is Docker?
  Request 2: [instance-70e688]
    Q: Why do we need containers?
  Request 3: [instance-65297c]
    Q: What is Kubernetes?
  
  ------------------------------------------------------------
  Total requests: 5
  Instances used: {'instance-65297c', 'instance-26dad5', 'instance-70e688'}
  ✅ All requests served despite different instances!
  
  --- Conversation History ---
  Total messages: 10
  ✅ Session history preserved across all instances via Redis!
  ```
```

---

### Lab 06 Complete (60 points)
##  Submission
**Submit your GitHub repository URL:**
```
https://github.com/Jmhzbmcn2/Travel-AI-Assistant
```

**Submit your deployed service URL:**
```
https://travel-ai-assistant-1.onrender.com/
```

**Deadline:** 17/4/2026

---

##  Quick Tips

1.  Test your public URL from a different device
2.  Make sure repository is public or instructor has access
3.  Include screenshots of working deployment
4.  Write clear commit messages
5.  Test all commands in DEPLOYMENT.md work
6.  No secrets in code or commit history

---

##  Need Help?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [CODE_LAB.md](CODE_LAB.md)
- Ask in office hours
- Post in discussion forum

---

**Good luck! **
