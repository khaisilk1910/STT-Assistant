# Nhật ký và chẩn đoán STT Assistant 1.17.0

STT Assistant là **Conversation Agent xử lý câu đã được STT tạo ra**. Tích hợp không nhận và không ghi âm trực tiếp, không thay thế bộ nhận dạng giọng nói của Assist Pipeline. Wake word, audio, STT engine, TTS engine do Home Assistant quản lý. Phần log dưới đây chỉ bao phủ phần xử lý văn bản và chuyển tiếp agent của STT Assistant.

## Bật nhật ký trong Home Assistant

**Cách 1 — giao diện:** Settings → Devices & services → STT Assistant → Menu (dấu ba chấm) → **Enable debug logging**. Thử lại một câu gây lỗi, sau đó bấm **Disable debug logging** để tải log. Đừng bật DEBUG liên tục khi đã xử lý xong.

**Cách 2 — cấu hình lâu dài:** Thêm đoạn sau vào `configuration.yaml` nếu cần theo dõi cả hoạt động bình thường; sau đó khởi động lại Home Assistant:

```yaml
logger:
  default: warning
  logs:
    custom_components.stt_assistant: info
```

Để phân tích từng giai đoạn và lấy traceback khi lỗi, đổi `info` thành `debug`. Không cần bật DEBUG cho `homeassistant.components.conversation`, `assist_pipeline` hoặc các cloud agent trừ khi bạn chấp nhận khả năng transcript/audio metadata xuất hiện trong các log đó. Đừng thêm nhiều khối `logger:` trùng nhau: hãy gộp vào cấu hình logger hiện có.

Xem log ở Settings → System → Logs → **Show raw logs** (log INFO/DEBUG có thể không xuất hiện trong danh sách lỗi cô đọng). Lọc từ khóa `stt_assistant` hoặc `request=`.

## Các log quan trọng

| Đầu mục | Khi nào xuất hiện | Ý nghĩa |
|---|---|---|
| `services registered` | Khi tích hợp được nạp | Đã đăng ký action chuẩn Home Assistant, không tạo chỉ mục |
| `entry initialized` | Config Entry thiết lập thành công | Conversation Agent sẵn sàng, lịch warmup trễ 15 giây |
| `Background index warmup started` | Sau khi HA khởi động | Bắt đầu chuẩn bị chỉ mục các ngôn ngữ, tuần tự |
| `Index warmup completed` | Sau khi nạp/xây chỉ mục | `language`, `source`, `candidates`, `elapsed_ms` |
| `request=... route=... status=... elapsed_ms=...` | Mỗi yêu cầu (INFO) | Đường xử lý và độ trễ đầu-cuối của Conversation Agent |
| `phase=... elapsed_ms=...` | Khi DEBUG | Thời gian theo giai đoạn |
| `Index warmup failed`, `Ranking failed`, `unexpected...` | Khi có lỗi | Có dấu vết để chẩn đoán; DEBUG có traceback |
| `unloaded` | Khi gỡ tải | Đã dừng tác vụ và giải phóng runtime |

### Các giá trị route thường gặp

- `local_intent_shortcut`: Trúng ý định Home Assistant trong nhánh local-intent shortcut.
- `canonical_success`: Chuẩn hóa được câu và thực thi thành công.
- `canonical_recovered`: Thành công sau một ứng viên phục hồi.
- `hotword_fallback`: Phát hiện hotword tùy chỉnh rồi chuyển agent dự phòng.
- `fallback_no_index`: Không lấy/xây được chỉ mục, chuyển nguyên câu đến agent dự phòng.
- `fallback_low_confidence`: Điểm tin cậy chưa đủ, không cưỡng ép thực thi.
- `fallback_preflight_rejected`: Ứng viên chưa được trình phân tích ý định Home Assistant xác nhận.
- `fallback_ranking_error` / `fallback_candidate_exception`: Có lỗi xử lý, dùng fallback để hạn chế thất bại.
- `fallback_execution_failed`: Thực thi ứng viên không thành công, dùng fallback.
- `unhandled_exception`: Lỗi chưa xử lý; trả thông báo chung cho người dùng.

**Ví dụ log minh họa (không lấy từ thiết bị thực):**

```text
INFO  [custom_components.stt_assistant] STT Assistant entry initialized; conversation agent ready, warmup scheduled 15s after Home Assistant startup
INFO  [custom_components.stt_assistant] Index warmup completed language=vi source=rebuild candidates=1280 elapsed_ms=820.6
INFO  [custom_components.stt_assistant.observability] request=2a7e91c0 language=vi route=canonical_success status=ok elapsed_ms=46.3
DEBUG [custom_components.stt_assistant.observability] request=2a7e91c0 phases_ms={'index_acquisition': 0.1, 'candidate_ranking': 12.7} details={'ranking_cache_hit': False}
```

## Thống kê tại action diagnostics

Đi tới Developer tools → Actions, chọn `stt_assistant.diagnostics`, bật trả kết quả (response) và xem:

- `last_trace_id`: mã yêu cầu gần nhất để đối chiếu log; **không phải** conversation ID.
- `request_metrics.requests`, `failures`, `slow_requests`: các bộ đếm từ lúc nạp tích hợp.
- `request_metrics.routes`: số lượt đi theo từng nhánh.
- `request_metrics.recent_sample_size`, `recent_p50_ms`, `recent_p95_ms`: phân bố độ trễ của **tối đa 100 yêu cầu gần nhất**. Mốc cảnh báo chậm mặc định: 2000 ms.
- `cached_indexes`, `pending_rebuild_languages`, `confidence_gate`, `last_fallback_reason`, `execution_result`: tình trạng tìm kiếm và lựa chọn đường xử lý.

**Lưu ý:** `last_*` là snapshot chung của yêu cầu gần nhất, có thể bị thay thế khi hai thiết bị nói cùng lúc. Để theo dõi từng yêu cầu đồng thời, sử dụng mã `request=` trong log. Chỉ số tốc độ là của lớp Conversation Agent, không gồm STT/TTS/acoustic pipeline. Bộ đếm và 100 mẫu gần nhất chỉ ở RAM và được reset khi reload/restart.

## Bảo mật và xử lý sự cố

- Log mới ở mức INFO/DEBUG **không chủ động ghi bản chép lời**, âm thanh, tên thiết bị hay `conversation_id`; `request=` là mã ngẫu nhiên ngắn cho một lần gọi. Một số log do Home Assistant hoặc agent khác phát sinh vẫn có thể chứa dữ liệu riêng tư.
- Tránh chia sẻ nguyên file log trước khi kiểm tra và che token, ID, transcript và nội dung lời nói từ các tích hợp khác.
- Nếu báo `fallback_no_index`, kiểm tra log warmup và gọi `stt_assistant.rebuild_index` với ngôn ngữ `vi`.
- Nếu báo `fallback_low_confidence`, dùng `stt_assistant.test_match` với câu có lỗi STT để xem các điểm số và kiểm tra `min_confidence` / `min_margin`.
- Nếu `canonical_success` nhưng thiết bị làm sai hành động, **không giảm ngưỡng tùy tiện**: kiểm tra tên entity và nội dung preflight trước tiên; lưu câu lệnh trong bộ test offline, đặc biệt các câu có phủ định.
- Nếu `elapsed_ms` lớn, xem `phases_ms`: `index_acquisition` lớn thường là build lần đầu; `candidate_ranking` lớn là truy hồi; `candidate_preflight` lớn thường do HassIL; `fallback_agent` lớn là do agent khác (có thể là LLM mạng).

Tham khảo tài liệu chính thức: [Home Assistant — Debug logs](https://www.home-assistant.io/docs/configuration/troubleshooting/#debug-logs-and-diagnostics) và [Logger](https://www.home-assistant.io/integrations/logger/).
