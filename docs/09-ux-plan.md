# Kế hoạch UX: Từ AI-generated Text Thành Decision-ready Travel Plan

## 1. Root Cause Analysis

Output hiện tại chưa đủ tin cậy để user hành động.

### Vấn đề gốc

- **Thông tin quan trọng bị aggregate sai cấp độ:** UI chỉ hiển thị tổng `travel_minutes` theo ngày, trong khi user cần thời gian của từng chặng.
- **Backend đang loại bỏ dữ liệu route chi tiết:** hệ thống tính từng route segment nhưng chỉ giữ tổng thời gian khi tạo itinerary.
- **Độ chính xác giả:** khi thiếu dữ liệu, hệ thống mặc định `20 phút` và `5 km` nhưng không thông báo đây là fallback.
- **Place identity yếu:** chỉ có tên, tọa độ và rating; thiếu địa chỉ, khu vực, provider place ID và trạng thái xác minh.
- **Recommendation không đa dạng:** lịch trình gia đình 4 ngày nhưng gần như chỉ gồm nhà hàng hải sản.
- **Scoring gây hiểu nhầm:** “khả thi 100%”, “thoải mái 55%” tạo cảm giác khoa học nhưng không giải thích được cách tính.
- **Claim mâu thuẫn:** hệ thống nói “độ tin cậy cao” trong khi thừa nhận đang dùng fixture.

### Tác động UX

| Vấn đề | Hậu quả |
|---|---|
| Không biết địa điểm ở đâu | User phải tự tìm kiếm và có thể chọn nhầm địa điểm |
| Chỉ có tổng phút di chuyển | Không phát hiện được chặng route bất hợp lý |
| Không phân biệt live/estimated/fallback | User tin nhầm dữ liệu không chính xác |
| Mọi risk nằm cuối output | User không biết risk ảnh hưởng ngày hoặc địa điểm nào |
| CTA chung chung | User không biết nên thực hiện hành động tiếp theo nào |

---

## 2. Proposed UX Improvements

### P0 — Place Cards Có Identity Rõ Ràng

**Problem solved:** Tên địa điểm mơ hồ và trùng lặp.

**UX proposal:** Mỗi địa điểm phải hiển thị:

- Tên
- Khu vực hoặc địa chỉ rút gọn
- Rating và số lượng review
- Thời gian dự kiến tại điểm
- Trạng thái xác minh
- Nút `Mở trên Google Maps`
- Nút `Thay địa điểm`

**Example:**

> **Nhà hàng Vua Hải Sản**  
> Dương Đông, Phú Quốc · ⭐ 4.3 từ 1.240 đánh giá  
> Dự kiến: 90 phút · Địa điểm đã xác minh  
> `[Mở trên Maps]` `[Thay địa điểm]`

**Complexity:** Medium  
**Priority:** P0

---

### P0 — Route Leg Thay Cho Tổng Phút Mơ Hồ

**Problem solved:** “Di chuyển 38 phút” không giải thích được từ đâu tới đâu.

**UX proposal:** Hiển thị route chip giữa từng place card:

> Khách sạn → Nhà hàng Vua Hải Sản  
> Taxi · 4,3 km · khoảng 12 phút · Route đã xác minh  
> `[Mở chỉ đường]`

Mỗi ngày vẫn có tổng thời gian di chuyển, nhưng đây chỉ là summary phụ.

**Complexity:** High  
**Priority:** P0

---

### P0 — Confidence Theo Từng Dữ Liệu

Không sử dụng một claim chung như “độ tin cậy cao”.

| Trạng thái | Cách hiển thị |
|---|---|
| Provider trả về route/place chính xác | `Đã xác minh` |
| Tính từ tọa độ | `Ước tính theo khoảng cách` |
| Chỉ tìm kiếm theo tên | `Chưa xác minh địa điểm` |
| Fixture/demo | `Dữ liệu demo, không dùng để đặt dịch vụ` |

Không được hiển thị thời gian chính xác như `20 phút` nếu đó là fallback.

**Complexity:** Medium  
**Priority:** P0

---

### P1 — Day Theme Và Geographic Context

Mỗi ngày cần có mục đích rõ ràng:

> **Ngày 2 — Bắc đảo & Grand World**  
> 3 điểm · 7 giờ hoạt động · 52 phút di chuyển  
> Route tương đối tập trung, có một chặng dài 31 phút.

Điều này giúp user hiểu logic lịch trình mà không cần đọc toàn bộ danh sách.

**Complexity:** Medium  
**Priority:** P1

---

### P1 — Recommendation Explainability

Thay:

> cheapest · khả thi 100% · thoải mái 55%

Bằng:

> **Khuyến nghị: Phương án tiết kiệm**  
> Phù hợp vì nằm dưới ngân sách khoảng 9,6 triệu và không có ngày vượt giới hạn hoạt động.  
> Đánh đổi: nhiều bữa ăn tương tự và chưa xác minh route từ khách sạn trong ngày 1.

Ẩn lựa chọn `balanced` nếu chênh lệch chỉ 22.199 VND và không có khác biệt thực tế.

**Complexity:** Low  
**Priority:** P1

---

### P1 — Contextual Risks Và Actions

Risk phải xuất hiện tại nơi bị ảnh hưởng:

> ⚠️ Chặng Grand World → Nhà hàng Xin Chào mất khoảng 40 phút.  
> `[Đổi nhà hàng gần hơn]` `[Giữ nguyên]`

**Complexity:** Medium  
**Priority:** P1

---

### P2 — Whole-day Map Preview

Hiển thị map với pins và route tổng quan theo ngày.

Postpone vì deep links giải quyết phần lớn nhu cầu hành động với effort và API cost thấp hơn.

**Complexity:** High  
**Priority:** P2

---

## 3. Redesigned Output Example

> Lưu ý: Các route và địa chỉ dưới đây phải được tạo từ dữ liệu provider đã xác minh. Không được tự sinh con số chính xác khi thiếu dữ liệu.

### Chuyến Đi Gia Đình Tới Phú Quốc

**4 ngày 3 đêm · 4 người · Ngân sách 25 triệu**

#### Quyết định nhanh

- **Chi phí dự kiến:** 15,4 triệu
- **Còn dư ngân sách:** khoảng 9,6 triệu
- **Route:** Cần kiểm tra lại một chặng quay đầu
- **Độ đầy đủ dữ liệu:** Một số địa điểm chưa được xác minh
- **Khuyến nghị:** Có thể sử dụng để tham khảo, chưa nên đặt dịch vụ ngay

`[Tối ưu lại tuyến đường]` `[Thay đổi ngân sách]`

---

### Ngày 1 — Dương Đông Và Hải Sản

**2 địa điểm · khoảng 3 giờ hoạt động · 38 phút di chuyển**

#### Khách sạn đã chọn

**Khách sạn tại Dương Đông**  
Điểm bắt đầu và kết thúc ngày.

↓ **Taxi · 4,3 km · khoảng 12 phút · Route đã xác minh**  
`[Mở chỉ đường]`

#### Nhà hàng Vua Hải Sản

Dương Đông, Phú Quốc · ⭐ 4.3 từ 1.240 đánh giá  
Dự kiến: 90 phút · Địa điểm đã xác minh

`[Mở trên Google Maps]` `[Thay địa điểm]`

↓ **Taxi · 6,8 km · khoảng 16 phút · Route đã xác minh**  
`[Mở chỉ đường]`

#### Hải sản Động Tôm Hùm

Khu vực trung tâm Dương Đông · Địa chỉ chưa xác minh  
Dự kiến: 90 phút

⚠️ Có nhiều địa điểm trùng tên. Cần xác nhận trước khi sử dụng.

`[Tìm trên Google Maps]` `[Chọn địa điểm chính xác]`

↓ **Về khách sạn · khoảng 10 phút · Ước tính theo khoảng cách**

---

### Ngày 2 — Grand World Và Bắc Đảo

**Cảnh báo:** Hai địa điểm thuộc hai khu vực khác nhau, có thể tạo chặng di chuyển dài.

`[Tối ưu lại ngày 2]` `[Giữ lịch trình]`

---

### Chi Phí

| Hạng mục | Dự kiến |
|---|---:|
| Vé máy bay | 7,2 triệu |
| Khách sạn | 4,1 triệu |
| Ăn uống | 5,6 triệu |
| Di chuyển | 1,2 triệu |
| Dự phòng | 1,4 triệu |

**Tổng:** 15,4 triệu  
**Còn dư:** khoảng 9,6 triệu

Chi phí ăn uống đang dựa trên giả định `350.000 VND/người/ngày`.

---

### Dữ Liệu Và Độ Tin Cậy

- 5/8 địa điểm đã xác minh bằng tọa độ/provider ID.
- 3/8 địa điểm chỉ được match theo tên.
- 6/10 route segment có dữ liệu provider.
- Các route fallback chưa được dùng để đưa ra claim “độ tin cậy cao”.

---

### Hành Động Tiếp Theo

`[Xác minh các địa điểm còn lại]`  
`[Tối ưu tuyến đường]`  
`[Thay nhà hàng trùng lặp]`  
`[Xác nhận kế hoạch]`

---

## 4. Product Differentiation Vs ChatGPT

Google Maps link đơn thuần không tạo moat. ChatGPT cũng có thể sinh link tìm kiếm.

Differentiation có giá trị là:

1. **Verified place identity:** hệ thống biết chính xác địa điểm nào đang được đề xuất.
2. **Route-aware itinerary:** lịch trình được kiểm tra bằng từng route leg, không chỉ được viết hợp lý bằng ngôn ngữ.
3. **Actionable correction:** user có thể thay địa điểm, tối ưu route và xác nhận từng ngày.
4. **Evidence-linked recommendation:** mỗi claim về chi phí, feasibility và route có nguồn dữ liệu tương ứng.
5. **Persistent trip workspace:** user chỉnh sửa và tiếp tục kế hoạch thay vì bắt đầu lại bằng prompt mới.

Moat thực tế nằm ở structured decision engine và workflow chỉnh sửa, không nằm ở văn phong output.

---

## 5. Technical Changes

### Public Data Contract

Mở rộng place model:

```text
address
area
provider_place_id
maps_url
place_match_status
place_match_confidence
```

Thêm `ItineraryLeg`:

```text
from_place_id
from_label
to_place_id
to_label
mode
distance_km
duration_minutes
provider
data_mode
confidence
directions_url
```

Mỗi `ItineraryDay` cần chứa:

```text
route_legs
total_travel_minutes
total_visit_minutes
area_summary
route_status
```

### Google Maps Deep Link Strategy

Ưu tiên theo thứ tự:

1. Provider place ID + tọa độ
2. Tọa độ
3. Tên + destination search fallback

Search fallback phải hiển thị là `Tìm trên Maps`, không phải `Mở địa điểm`.

Route deep link:

```text
https://www.google.com/maps/dir/?api=1
&origin={lat,lng}
&destination={lat,lng}
&travelmode=driving
```

### Reliability Rules

- Không dùng mặc định `20 phút` hoặc `5 km` như dữ liệu thật.
- Thiếu route phải trả về trạng thái `unverified`.
- Route mỗi ngày sử dụng khách sạn làm start/end anchor khi hotel có tọa độ.
- Duplicate place names phải yêu cầu match bằng provider ID hoặc tọa độ.
- Recommendation không được claim “high confidence” khi có fixture hoặc unverified place quan trọng.

---

## 6. Two-sprint Implementation Plan

### Sprint 1 — Trustworthy Place Và Route Foundation

**Goal:** Loại bỏ ambiguity và độ chính xác giả.

**Deliverables**

- Mở rộng place schema với address, area, provider ID và match status.
- Giữ lại route segment chi tiết trong itinerary output.
- Tính route khách sạn → activities → khách sạn.
- Sinh Google Maps place và directions deep links.
- Loại bỏ silent fallback `20 phút`/`5 km`.
- Hiển thị place card và route leg trong structured workspace.
- Hiển thị rõ `verified`, `estimated`, `unverified`, `fixture`.

**Acceptance criteria**

- 100% thời gian di chuyển hiển thị rõ `from → to`.
- 100% địa điểm có deep link hoặc được đánh dấu chưa xác minh.
- Không có route fallback nào được trình bày như dữ liệu provider.
- Không claim “high confidence” khi itinerary chứa fixture hoặc unverified critical data.
- Mobile user có thể mở native Google Maps từ từng place/route.

---

### Sprint 2 — Decision Actions Và Recommendation Trust

**Goal:** Cho phép user sửa và xác nhận kế hoạch thay vì chỉ đọc.

**Deliverables**

- Day summary: khu vực, tổng activity time, tổng travel time, route status.
- Contextual risk gắn với route/place bị ảnh hưởng.
- Actions: thay địa điểm, tối ưu route, làm ngày nhẹ hơn.
- Suppress các option không có khác biệt có ý nghĩa.
- Thay score pseudo-precision bằng explanation và evidence.
- Thêm validation cho duplicate names và route quay đầu.
- Instrument analytics cho Maps clicks, route optimization và place replacement.

**Acceptance criteria**

- User có thể xác định chặng dài nhất trong dưới 10 giây.
- User có thể mở chỉ đường cho bất kỳ chặng nào bằng tối đa hai thao tác.
- User có thể thay một địa điểm mà không phải nhập lại toàn bộ prompt.
- Recommendation explanation nêu rõ ít nhất một lợi ích và một đánh đổi.
- Risks quan trọng xuất hiện ngay tại ngày hoặc địa điểm liên quan.
