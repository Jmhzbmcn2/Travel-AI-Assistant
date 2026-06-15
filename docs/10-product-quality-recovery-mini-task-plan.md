# Product Quality Recovery Mini-task Plan

## Delivery Rules

- Mục tiêu: nâng sản phẩm từ decision-support prototype thành defensible MVP cho chuyến đi nội địa ngắn ngày.
- Capacity mặc định: 1 developer, 2 sprint, 2 tuần mỗi sprint, khoảng 20 developer-days.
- Sprint 1 ưu tiên trust, route truth và evidence presentation.
- Sprint 2 ưu tiên itinerary realism và actionability.
- Không làm cosmetic polish trước khi hoàn thành các task P0.
- Mỗi task chỉ được hoàn thành khi code, automated tests và acceptance criteria tương ứng đều pass.
- Không được gọi kế hoạch là `verified` hoặc `recommended` nếu còn fixture hoặc unverified critical data.

---

## Sprint 1: Trust And Route Truth

### Sprint Goal

Ngăn recommendation sai do fixture hoặc false precision; đảm bảo mọi địa điểm và thời gian di chuyển user nhìn thấy đều có nguồn dữ liệu và confidence rõ ràng.

### Sprint Definition Of Done

- Fixture không thể tạo recommendation.
- Không còn route fallback `20 phút` hoặc `5 km`.
- Mọi travel duration hiển thị rõ `from -> to` và confidence.
- Hotel anchor được tính hoặc được đánh dấu chưa xác minh.
- Chat response và structured workspace không mâu thuẫn.

### S1-01 - Ngăn Fixture Bị Gắn Nhãn Live

**Priority:** P0  
**Estimate:** 0.5 ngày  
**Dependencies:** Không có

#### Checklist

- [ ] Sửa `_fixture_flights()` để luôn trả `data_mode="fixture"`.
- [ ] Sửa `_fixture_hotels()` để luôn trả `data_mode="fixture"`.
- [ ] Kiểm tra fixture places, routes, reviews và weather luôn giữ `fixture`.
- [ ] Tìm toàn repo các nhánh có thể chuyển fixture thành live.
- [ ] Thêm regression test với `DEMO_MODE=True`.
- [ ] Xác nhận fixture decision không tạo recommendation hoặc booking links.

#### Acceptance Criteria

- [ ] Không fixture record nào serialize thành `live`.
- [ ] Fixture flight, hotel, place hoặc route chặn recommendation.
- [ ] Fixture decision không có `why_recommended` hoặc `booking_links`.

### S1-02 - Nâng Cấp Coverage Gate

**Priority:** P0  
**Estimate:** 1 ngày  
**Dependencies:** S1-01

#### Checklist

- [ ] Thêm coverage status `estimated`.
- [ ] Kiểm tra mọi itinerary place có stable identity.
- [ ] Kiểm tra confidence của mọi route leg.
- [ ] Block recommendation khi có fixture critical data.
- [ ] Block recommendation khi có unverified place trong itinerary.
- [ ] Hạ coverage xuống `estimated` khi route dùng Haversine.
- [ ] Thêm blocking reason cụ thể cho từng loại dữ liệu thiếu.
- [ ] Cập nhật decision engine sử dụng coverage mới.
- [ ] Bổ sung coverage gate tests.

#### Acceptance Criteria

- [ ] GPS fallback không tạo `coverage_status="verified"`.
- [ ] Chỉ verified critical data mới tạo `recommended_option`.
- [ ] Blocking reason chỉ rõ dữ liệu nào chưa đủ.

### S1-03 - Cho Phép Route Không Có Duration

**Priority:** P0  
**Estimate:** 0.5 ngày  
**Dependencies:** S1-02

#### Checklist

- [ ] Đổi `ItineraryLeg.distance_km` thành `float | None`.
- [ ] Đổi `ItineraryLeg.duration_minutes` thành `int | None`.
- [ ] Chuẩn hóa confidence thành `verified`, `estimated`, `unverified`.
- [ ] Giữ default phù hợp để đọc persisted decisions cũ.
- [ ] Thêm serialization và backward-compatibility tests.

#### Acceptance Criteria

- [ ] Missing route serialize được mà không cần số giả.
- [ ] Persisted decision cũ vẫn đọc được.

### S1-04 - Xóa Silent Route Fallback

**Priority:** P0  
**Estimate:** 1 ngày  
**Dependencies:** S1-03

#### Checklist

- [ ] Xóa fallback `5 km`.
- [ ] Xóa fallback `20 phút`.
- [ ] Provider route trả confidence `verified`.
- [ ] Haversine route trả confidence `estimated`.
- [ ] Thiếu coordinates trả confidence `unverified`.
- [ ] Không cộng unverified duration vào tổng travel time.
- [ ] Thêm warning cho ngày có unverified route.
- [ ] Thêm verified, estimated và unverified leg counts vào day summary.
- [ ] Bổ sung route resolution tests.

#### Acceptance Criteria

- [ ] Không tạo số phút hoặc km khi thiếu evidence.
- [ ] Ngày có unverified leg không thể có feasibility tối đa.
- [ ] Tổng travel time không bao gồm unverified legs.

### S1-05 - Tách Itinerary Ordering Và Route Fetching

**Priority:** P0  
**Estimate:** 1.5 ngày  
**Dependencies:** S1-04

#### Checklist

- [ ] Tách logic thành bước build itinerary order và enrich routes.
- [ ] Tạo route pairs từ itinerary order thực tế.
- [ ] Deduplicate route pairs.
- [ ] Fetch routes sau khi xác định itinerary order.
- [ ] Cache routes bằng provider IDs hoặc coordinates.
- [ ] Không cache bằng positional IDs như `place_1`.
- [ ] Fallback sang estimated hoặc unverified khi provider fail.
- [ ] Cập nhật `decision_node`.
- [ ] Thêm tests kiểm tra route pair order.

#### Acceptance Criteria

- [ ] Mỗi fetched route được sử dụng trong itinerary.
- [ ] Không fetch route dư thừa.
- [ ] Route leg order khớp itinerary item order.
- [ ] Provider failure không làm decision node crash.

### S1-06 - Thêm Hotel Anchor

**Priority:** P0  
**Estimate:** 1 ngày  
**Dependencies:** S1-05

#### Checklist

- [ ] Mở rộng `HotelOption` với lat, lng, provider place ID và Maps URL.
- [ ] Normalize hotel coordinates khi provider cung cấp.
- [ ] Chọn hotel của option đang đánh giá làm anchor.
- [ ] Tạo hotel -> first place leg.
- [ ] Tạo last place -> hotel leg.
- [ ] Tạo unverified anchor legs nếu hotel thiếu coordinates.
- [ ] Tính lại tổng travel time.
- [ ] Thêm hotel-anchor tests.

#### Acceptance Criteria

- [ ] Ngày có hotel coordinates luôn có start/end legs.
- [ ] Thiếu hotel coordinates tạo warning rõ ràng.
- [ ] Tổng travel time bao gồm các anchor legs có evidence.

### S1-07 - Hoàn Thiện Place Identity

**Priority:** P0  
**Estimate:** 0.75 ngày  
**Dependencies:** S1-02

#### Checklist

- [ ] Normalize address và area/neighborhood.
- [ ] Giữ provider place ID.
- [ ] Sinh Maps link từ provider ID hoặc coordinates.
- [ ] Thêm destination vào search-only Maps fallback.
- [ ] Phân biệt verified, coordinate-only, search-only và fixture place.
- [ ] Thêm duplicate-name detection.
- [ ] Bổ sung provider normalization tests.

#### Acceptance Criteria

- [ ] Mỗi place có stable identity hoặc được đánh dấu unverified.
- [ ] Search-only place không được gọi là verified.
- [ ] Duplicate names tạo warning.

### S1-08 - Render Place Cards Và Route Legs

**Priority:** P0  
**Estimate:** 2 ngày  
**Dependencies:** S1-06, S1-07

#### Checklist

- [ ] Tạo component `PlaceCard`.
- [ ] Tạo component `RouteLegCard`.
- [ ] Tạo component `TrustBadge`.
- [ ] Place card hiển thị address/area, rating, review count và visit duration.
- [ ] Place card hiển thị verification status và Maps action.
- [ ] Route card hiển thị from/to, mode, distance, duration và confidence.
- [ ] Route card có directions link khi đủ coordinates.
- [ ] Search-only place dùng label `Tìm trên Maps`.
- [ ] Unverified route không hiển thị số phút hoặc km.
- [ ] Cập nhật mobile layout và print mode.

#### Acceptance Criteria

- [ ] Không còn standalone text `Di chuyển X phút`.
- [ ] Mọi displayed duration có from/to và confidence.
- [ ] User phân biệt được verified, estimated, unverified và fixture.
- [ ] Layout hoạt động ở chiều rộng 375px.

### S1-09 - Đồng Bộ Text Response Với Structured Workspace

**Priority:** P0  
**Estimate:** 0.5 ngày  
**Dependencies:** S1-08

#### Checklist

- [ ] Bắt buộc response agent sử dụng từng route leg.
- [ ] Không cho LLM tự tổng hợp lại route duration.
- [ ] Không gọi plan là `đã xác minh` nếu coverage không verified.
- [ ] Không tạo recommendation text nếu decision chưa recommended.
- [ ] Resolve internal hotel IDs thành tên khách sạn.
- [ ] Thêm response contract tests.

#### Acceptance Criteria

- [ ] Chat text và workspace không mâu thuẫn.
- [ ] Không internal ID xuất hiện trong output.
- [ ] Fixture hoặc estimated plan được gọi rõ là bản tham khảo.

### S1-10 - Sprint 1 Release Gate

**Priority:** P0  
**Estimate:** 1.25 ngày  
**Dependencies:** S1-01 đến S1-09

#### Automated Validation

- [ ] Fixture leakage regression tests pass.
- [ ] Coverage gate tests pass.
- [ ] Route fallback và route ordering tests pass.
- [ ] Hotel anchor và place identity tests pass.
- [ ] Response contract tests pass.
- [ ] Full backend tests pass.
- [ ] `python -m compileall src main.py` pass.
- [ ] Frontend lint và build pass.

#### Manual Validation

- [ ] Mở verified place link.
- [ ] Mở search-only place link.
- [ ] Mở directions link.
- [ ] Kiểm tra missing route và provider failure.
- [ ] Kiểm tra fixture-only trip.
- [ ] Kiểm tra mobile workspace.

---

## Sprint 2: Realistic And Actionable Itinerary

### Sprint Goal

Tạo itinerary có thể đi ngoài đời, phù hợp với trip context và cho phép user sửa trực tiếp các vấn đề được phát hiện.

### Sprint Definition Of Done

- Family itinerary không bị độc chiếm bởi một category.
- Recommendation không dùng pseudo-precision.
- Risks gắn với đúng day, place hoặc route.
- User có thể optimize route và replace place trực tiếp.
- Không hiển thị duplicate options không có trade-off thực tế.

### S2-01 - Phân Loại Place Categories

**Priority:** P0  
**Estimate:** 0.75 ngày  
**Dependencies:** Sprint 1 hoàn tất

#### Checklist

- [ ] Chuẩn hóa provider categories thành internal categories.
- [ ] Hỗ trợ food, attraction, beach/nature, culture, shopping, nightlife và rest/flexible.
- [ ] Xử lý unknown category.
- [ ] Thêm category normalization tests.

#### Acceptance Criteria

- [ ] Mọi place có internal category hợp lệ.
- [ ] Unknown category không bị mặc định thành food.

### S2-02 - Thêm Itinerary Composition Rules

**Priority:** P0  
**Estimate:** 1.5 ngày  
**Dependencies:** S2-01

#### Checklist

- [ ] Giới hạn tối đa hai food places mỗi ngày.
- [ ] Không đặt hai food places liên tiếp.
- [ ] Mỗi ngày đầy đủ có ít nhất một non-food activity.
- [ ] Preference chỉ tăng ranking, không độc chiếm itinerary.
- [ ] Cho phép override khi user yêu cầu food tour.
- [ ] Trả warning hoặc blocking reason khi provider thiếu diversity.
- [ ] Thêm composition evidence vào itinerary day.
- [ ] Thêm tests cho trip ưu tiên hải sản.

#### Acceptance Criteria

- [ ] Family trip bốn ngày không thể gồm hoàn toàn nhà hàng.
- [ ] Thiếu place diversity được thông báo rõ.
- [ ] Food-tour request vẫn hoạt động đúng.

### S2-03 - Thêm Family Suitability Rules

**Priority:** P0  
**Estimate:** 1 ngày  
**Dependencies:** S2-02

#### Checklist

- [ ] Thêm assumption khi chưa biết tuổi trẻ em.
- [ ] Giới hạn activity load cho family trip.
- [ ] Thêm rest buffer giữa các hoạt động dài.
- [ ] Hạn chế late-night activities.
- [ ] Cảnh báo route leg dài và ngày thiếu thời gian nghỉ.
- [ ] Thêm family suitability tests.

#### Acceptance Criteria

- [ ] Family trip ảnh hưởng trực tiếp tới itinerary logic.
- [ ] Không claim phù hợp gia đình nếu family rules fail.
- [ ] Output nêu rõ assumption về trẻ em.

### S2-04 - Thay Pseudo-precision Bằng Explainable Status

**Priority:** P0  
**Estimate:** 1 ngày  
**Dependencies:** S2-03

#### Checklist

- [ ] Giữ numeric score chỉ để ranking nội bộ.
- [ ] Map feasibility thành `Khả thi`, `Khả thi có điều kiện`, `Cần chỉnh sửa`, `Không đủ dữ liệu`.
- [ ] Map comfort thành categorical explanation.
- [ ] Tạo evidence summary cho recommendation.
- [ ] Recommendation bắt buộc có benefit, trade-off và unresolved risk.
- [ ] Xóa percentage khỏi frontend và chat response.
- [ ] Thêm mapping tests.

#### Acceptance Criteria

- [ ] User-facing output không còn feasibility hoặc comfort percentage.
- [ ] Recommendation giải thích được lý do lựa chọn.
- [ ] Recommendation không che giấu unresolved risks.

### S2-05 - Gắn Risk Với Đúng Context

**Priority:** P1  
**Estimate:** 1 ngày  
**Dependencies:** S2-04

#### Checklist

- [ ] Mở rộng `Risk` với day, place và route identifiers.
- [ ] Gắn route risk với route leg.
- [ ] Gắn place risk với place card.
- [ ] Gắn dense-day risk với day header.
- [ ] Resolve hotel ID thành tên khách sạn.
- [ ] Thêm suggested action cho actionable risks.
- [ ] Giữ RiskPanel làm summary.
- [ ] Thêm risk serialization tests.

#### Acceptance Criteria

- [ ] Không internal ID xuất hiện với user.
- [ ] User biết risk ảnh hưởng phần nào.
- [ ] Mỗi actionable risk có action phù hợp.

### S2-06 - Tạo Trip Action API Contract

**Priority:** P1  
**Estimate:** 0.75 ngày  
**Dependencies:** S2-05

#### Checklist

- [ ] Tạo endpoint `POST /api/v1/trips/{session_id}/actions`.
- [ ] Tạo typed request schema.
- [ ] Hỗ trợ `optimize_day`.
- [ ] Hỗ trợ `replace_place`.
- [ ] Validate owner, day và stable place identity.
- [ ] Trả structured API errors.
- [ ] Ghi action analytics events.
- [ ] Thêm authorization tests.

#### Acceptance Criteria

- [ ] Invalid action trả HTTP 422.
- [ ] Trip không thuộc owner trả 404.
- [ ] Action failure không làm mất decision hiện tại.

### S2-07 - Implement Optimize-day

**Priority:** P1  
**Estimate:** 1 ngày  
**Dependencies:** S2-06

#### Checklist

- [ ] Lấy places của ngày cần optimize.
- [ ] Dùng hotel làm start/end anchor.
- [ ] Sắp xếp deterministic nearest-neighbor.
- [ ] Fetch affected route pairs.
- [ ] So sánh route trước và sau.
- [ ] Chỉ apply nếu giảm travel time hoặc unverified legs.
- [ ] Rebuild và persist decision.
- [ ] Trả before/after summary.
- [ ] Thêm idempotency và does-not-worsen-route tests.

#### Acceptance Criteria

- [ ] Optimize không làm route tệ hơn.
- [ ] Không ảnh hưởng ngày khác.
- [ ] Gọi lại action trên route tối ưu không thay đổi kết quả.

### S2-08 - Implement Replace-place

**Priority:** P1  
**Estimate:** 1.5 ngày  
**Dependencies:** S2-06

#### Checklist

- [ ] Xác định category của place cần thay.
- [ ] Fetch alternatives cùng category và relevant area.
- [ ] Loại bỏ unverified alternatives, duplicate provider IDs và excluded places.
- [ ] Rank theo distance, rating và review count.
- [ ] Replace candidate tốt nhất.
- [ ] Re-fetch affected routes.
- [ ] Rebuild và persist decision.
- [ ] Giữ decision cũ nếu không có candidate.
- [ ] Thêm replacement tests.

#### Acceptance Criteria

- [ ] Không replace bằng unverified place.
- [ ] Không tạo duplicate place.
- [ ] Failed replacement không làm mất plan cũ.
- [ ] Response giải thích lý do chọn replacement.

### S2-09 - Thêm Frontend Action Controls

**Priority:** P1  
**Estimate:** 1 ngày  
**Dependencies:** S2-07, S2-08

#### Checklist

- [ ] Thêm API client `executeTripAction`.
- [ ] Thêm nút `Tối ưu ngày này`.
- [ ] Thêm nút `Thay địa điểm`.
- [ ] Thêm loading state và disable duplicate clicks.
- [ ] Hiển thị contextual errors.
- [ ] Update workspace từ action response.
- [ ] Hiển thị before/after result.
- [ ] Ẩn buttons trong print mode.

#### Acceptance Criteria

- [ ] User thực hiện action trong tối đa hai thao tác.
- [ ] Workspace cập nhật không cần reload.
- [ ] Failed action không làm mất dữ liệu đang hiển thị.

### S2-10 - Xóa Meaningless Options

**Priority:** P1  
**Estimate:** 0.5 ngày  
**Dependencies:** S2-04

#### Checklist

- [ ] Chỉ giữ option khi cost difference ít nhất 3%, comfort category khác, feasibility status khác hoặc có trade-off thực tế.
- [ ] Không hiển thị `rẻ hơn 0%`.
- [ ] Nếu chỉ có một meaningful option, chỉ hiển thị một option.
- [ ] Thêm equivalent-option tests.

#### Acceptance Criteria

- [ ] Không hiển thị duplicate options.
- [ ] Mỗi option có ít nhất một trade-off thực sự.

### S2-11 - Sprint 2 Release Gate

**Priority:** P0  
**Estimate:** 1 ngày  
**Dependencies:** S2-01 đến S2-10

#### Automated Validation

- [ ] Category mapping, composition và family suitability tests pass.
- [ ] Explainable status và contextual risk tests pass.
- [ ] Action authorization, optimize-day và replace-place tests pass.
- [ ] Option suppression tests pass.
- [ ] Full backend tests pass.
- [ ] Frontend lint và build pass.

#### Manual Validation

- [ ] Phú Quốc family trip ưu tiên hải sản.
- [ ] Provider chỉ trả về restaurants.
- [ ] Missing hotel coordinates hoặc route provider.
- [ ] Fixture weather với live critical data.
- [ ] Optimize route có backtracking.
- [ ] Replace unverified place.
- [ ] Reload session sau action.
- [ ] Mobile action flow.

---

## Daily Execution Schedule

### Sprint 1

| Day | Tasks |
|---:|---|
| 1 | S1-01, bắt đầu S1-02 |
| 2 | Hoàn thành S1-02, S1-03 |
| 3 | S1-04 |
| 4-5 | S1-05 |
| 6 | S1-06 |
| 7 | S1-07, bắt đầu S1-08 |
| 8-9 | Hoàn thành S1-08, S1-09 |
| 10 | S1-10 release gate |

### Sprint 2

| Day | Tasks |
|---:|---|
| 1 | S2-01, bắt đầu S2-02 |
| 2 | Hoàn thành S2-02 |
| 3 | S2-03 |
| 4 | S2-04 |
| 5 | S2-05, bắt đầu S2-06 |
| 6 | Hoàn thành S2-06, S2-07 |
| 7-8 | S2-08 |
| 9 | S2-09, S2-10 |
| 10 | S2-11 release gate |

---

## Scope Cut Order

Nếu bị trễ, cắt theo thứ tự:

1. Analytics chi tiết cho actions.
2. Before/after visual summary.
3. Contextual risks trên frontend, nhưng vẫn giữ risk summary.
4. `replace_place` action.

Không được cắt:

- Fixture leakage fix.
- Coverage gate.
- Xóa false route precision.
- Route generation order.
- Route-leg presentation.
- Itinerary diversity rules.
- Explainable feasibility.
- Regression tests.

---

## Final Completion Criteria

Recovery plan chỉ hoàn thành khi:

- [ ] Fixture không thể tạo recommendation.
- [ ] Không có precise route duration thiếu evidence.
- [ ] Mọi duration hiển thị from/to và confidence.
- [ ] Hotel anchor được tính hoặc đánh dấu missing.
- [ ] Family itinerary không chỉ gồm một category.
- [ ] Recommendation không dùng pseudo-precision.
- [ ] User có thể optimize route trực tiếp.
- [ ] Không internal ID xuất hiện trong output.
- [ ] Full backend tests pass.
- [ ] Frontend lint và build pass.
- [ ] Tất cả manual release scenarios pass.
