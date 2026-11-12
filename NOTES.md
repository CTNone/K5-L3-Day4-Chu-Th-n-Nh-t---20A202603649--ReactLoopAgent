# Ghi chú phân tích · Day 04

Họ và tên: Chu Thân Nhất

MSSV: 20A202603649

## 1. Case được chọn

- ID case: E5.
- Câu trả lời ở lần chạy trước ghi nhận incident Copilot Mission Control là đã resolved, không suy luận từ `components` rỗng rằng mọi dịch vụ chắc chắn không bị ảnh hưởng, và dẫn URL nguồn.
- Điểm trong báo cáo cũ: 88/100. Đây là kết quả lưu sẵn; không được tái lập bằng lượt chạy Dots hiện tại.
- Ở lần eval baseline Dots hiện có, E5 được 100/100. Case được chọn để phân tích dựa trên lần chạy cũ và nhận xét Judge trước đó; không diễn giải 88 thành điểm của eval hiện tại.

## 2. Bằng chứng trong trace

Trace E5 trong `eval_before.json` cho thấy `get_status` trả `components: []`, `overall.indicator: none`, đồng thời có incident `tc28c0wzrnpz` về Copilot Mission Control với trạng thái `resolved`. Tool result có nguồn `https://www.githubstatus.com`. Điều này chứng minh danh sách component khớp rỗng không đồng nghĩa không có incident lịch sử.

Judge cũ nhận xét câu trả lời đúng hướng nhưng nên ngắn hơn, nêu rõ rằng không tìm thấy incident active không đủ để khẳng định không có ảnh hưởng, và trích nguồn trực tiếp. Trace này là bằng chứng từ báo cáo trước; không trình bày nó như trace mới của Dots.

## 3. Bài 1–2 và thay đổi ở Bài 4

- Agent loop khởi tạo system/user messages, gọi provider tối đa `max_steps`, giữ nguyên assistant message, thực thi mọi tool call và trả kết quả với đúng `tool_call_id`.
- JSON arguments không hợp lệ được gửi lại như observation `INVALID_ARGUMENTS`; lỗi tool được đưa về model. Lỗi provider, output bị cắt và finish reason bất thường trả trạng thái `error`; hết bước trả `max_steps`.
- Trace ghi tool name, arguments, result và usage.
- Cải tiến Bài 4: thêm Evidence Gate. Sau khi `get_incident_details` thành công, agent yêu cầu câu trả lời nhắc URL incident đã quan sát; nếu hết budget thì không báo `completed`. System prompt cũng yêu cầu câu trả lời ngắn gọn, dựa trên evidence và nêu giới hạn snapshot.
- Baseline trong eval hiện tại dùng cùng agent loop với prompt ban đầu và Evidence Gate tắt. Commit gốc trong repo là khung bài chưa implement, nên không thể chạy trực tiếp làm baseline. Đây là ablation có ghi nhận, không phải khẳng định đã chạy đúng nội dung khung Git.

## 4. Bài 3 và 5: kết quả eval

Model agent: `dots-studio/dots-3-note-preview:free`; snapshot và dataset: core E1–H8; `max_steps`: 8. Chi phí model hiển thị $0.

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---:|---:|
| Case đã chấm | 13/22 | 11/22 |
| Điểm tổng | Chưa có (`null`) | Chưa có (`null`) |
| Trung bình tạm | 99.69/100 | 99.36/100 |
| Model calls và judge calls trong case đã chấm | 45 | 45 |
| Token đã báo cáo trong case đã chấm | 85,532 | 83,525 |

Các điểm `eval_before` đã chấm: E1–E6 100, A1–A5 100, A6 96, A7 100. Các điểm `eval_after`: E1 95, E2–E3 100, E4 99, E5–E6 100, A1 99, A2–A5 100. Trung bình tạm không phải điểm eval tổng; 9 case baseline và 11 case after vẫn chưa chấm.

OpenRouter trả `free-models-per-day` khi hết hạn mức. Case A4 của `eval_after` được judge bởi `openrouter/free` sau khi Dots judge trả HTTP 400; các case khác dùng Dots. Vì vậy kết quả after không hoàn toàn đồng nhất về judge. Không sửa dataset, fixtures, scenarios hoặc grading để làm case pass; không dùng tài khoản/key khác để vượt hạn mức free.

## 5. Giới hạn và tình trạng nộp

- Điểm judge là ước lượng; đọc `expected`, trace và lý do chấm trước khi diễn giải.
- Snapshot chỉ bao gồm tối đa 50 incident gần nhất tại thời điểm chụp; tìm kiếm rỗng không chứng minh incident không tồn tại.
- Hiện **chưa đủ điều kiện hoàn tất eval theo checklist nộp bài** vì cả hai báo cáo có điểm tổng `null`, và `eval_after` có một judge dự phòng. Cần bổ sung các case thiếu khi quota được cấp lại, dùng cùng model/judge cho mỗi lượt, rồi kiểm tra lại 22/22 trước khi ghi điểm tổng.
- Kiểm tra offline: `python -m unittest discover -s tests -q` — 37 tests passed.
