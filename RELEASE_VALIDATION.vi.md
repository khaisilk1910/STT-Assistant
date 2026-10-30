# STT Assistant 1.17.0 — Rà soát Conversation / Voice / Logging (30/10/2026)

## Phạm vi và cơ sở đối chiếu

- Đối chiếu API Home Assistant **2026.10.0** từ mã nguồn chính thức: `homeassistant/components/conversation/entity.py`, `conversation/agent_manager.py`, `assist_pipeline/pipeline.py`, `assist_pipeline/run.py`. Conversation Agent nhận văn bản **sau** khi Assist Pipeline STT hoàn tất; nó **không phải** engine STT hay wake-word/audio/TTS provider.
- Đối chiếu tài liệu chính thức `developers.home-assistant.io/docs/dev_101_services/`: service action phải đăng ký trong `async_setup` để sẵn có khi entry chưa tải.
- Đối chiếu hướng dẫn logs trong `home-assistant.io/docs/configuration/troubleshooting/` và `home-assistant.io/integrations/logger/`.

## Đã chỉnh sửa trong phiên bản 1.17.0

1. Đăng ký các action `stt_assistant.*` ở `async_setup` thay vì `async_setup_entry`; việc tháo entry không xóa service khỏi vòng đời tích hợp. Không thêm gánh nặng xây chỉ mục vào `async_setup`.
2. Thêm **mã trace ngẫu nhiên cho từng yêu cầu**, tách biệt `conversation_id`, bảo đảm không lẫn khi nhiều thiết bị gửi lệnh đồng thời nhờ `contextvars`.
3. Log ở mức INFO cho thiết lập/tải lại/gỡ tải, đăng ký service, warmup và **một dòng tóm tắt mỗi yêu cầu** (ngôn ngữ, route, thời gian, trạng thái). Log DEBUG cho các giai đoạn và thông tin xếp hạng không chứa câu nhận dạng. WARNING cho lỗi và yêu cầu chậm **>= 2000 ms**.
4. Đo thời gian các giai đoạn: local-intent shortcut, index, ranking, preflight, execution, recovery và fallback.
5. Thêm thống kê tổng số request, failure, slow request, phân phối route, và P50/P95 của tối đa **100 yêu cầu gần nhất**. Truy cập qua action `stt_assistant.diagnostics` (trường `request_metrics`) và `last_trace_id`.
6. Dùng mã loại lỗi ở log chuẩn và thông báo an toàn cho người dùng (không lộ trực tiếp exception/chuỗi từ bản chép lời). Traceback chỉ xuất hiện khi bật DEBUG.
7. Chặn fallback tới `self.entity_id` nhằm giảm nguy cơ vòng lặp agent. Lưu luồng fallback nguyên câu khi local intent bị từ chối.
8. Cập nhật tài liệu `LOGGING_STT_ASSISTANT.vi.md`, `LOGGING_STT_ASSISTANT.md` với hướng dẫn bật log trong UI và YAML.

## Kết quả kiểm tra có thể tái lập tại môi trường hiện tại

- `python3 -m compileall -q custom_components tests tools`: **đạt** với Python 3.13.5 (kiểm tra cú pháp; runtime yêu cầu Python 3.14.2+).
- `pytest -q -o addopts='' tests/test_project_metadata.py tests/test_validate.py tests/test_validate_compatibility.py tests/test_observability_standalone.py`: **156 passed**; bao gồm 4 bài mới kiểm tra telemetry, log an toàn, tác vụ đồng thời và phần trăm độ trễ.
- Parse JSON translations, manifest, HACS, TOML, kiểm tra domain và phiên bản: **đạt**.
- Cả bản mã nguồn và bản cài đặt được đóng gói riêng, loại `__pycache__`, `.pyc`.

## Giới hạn cần minh bạch

- Không cài `homeassistant` trong môi trường kiểm tra và chỉ có Python 3.13.5, vì vậy **không thể chạy bộ pytest phụ thuộc Home Assistant**; thử `tests/test_conversation.py tests/test_init.py` dừng ở import với `ModuleNotFoundError: homeassistant`. Các thay đổi vòng đời dịch vụ và các nhánh Conversation Agent vì vậy **chưa được xác nhận trực tiếp trên HA 2026.10**.
- Không chạy được end-to-end wake word → STT → conversation → TTS, không có thiết bị microphone, không đo P50/P95 chính thức trên hệ thống thật và không kiểm định tỉ lệ sửa đúng từ tiếng Việt. Không tuyên bố đây là bản production-certified hoặc nhanh/chính xác nhất.
- Một nhánh local-intent shortcut hiện cần quan sát trạng thái pipeline bằng cấu trúc nội bộ `_pipeline_runs` của Home Assistant. Đây **không phải API công khai bảo đảm ổn định**. Nhánh có xử lý fallback khi không truy cập được nhưng phải được kiểm tra lại sau từng lần cập nhật HA.
- `last_*` diagnostics trước đây dùng snapshot chung và có thể bị request khác ghi đè. Hãy dùng ID `request=` trong log cho các yêu cầu đồng thời.
- Repository `https://github.com/khaisilk1910/STT-Assistant` đã được kiểm tra tồn tại ngày 30/10/2026 nhưng **đang trống** tại thời điểm kiểm tra. Cần tải mã nguồn lên GitHub trước khi cài đặt qua HACS; sự tồn tại của repo không đồng nghĩa bản tích hợp đã vượt qua kiểm thử Home Assistant.

## Kịch bản xác minh trước khi đưa vào Home Assistant chính

1. Sao lưu HA, thử trên instance dự phòng với Home Assistant **2026.10.0+ / Python 3.14.2+**; chạy toàn bộ pytest, Ruff, hassfest, thử UI Config Flow/Options/Diagnostics, thử unload và reload.
2. Chọn STT Assistant làm Conversation Agent trong Assist Pipeline, bật logging theo `LOGGING_STT_ASSISTANT.vi.md`.
3. Chạy câu bật/tắt thiết bị đúng; câu STT sai 1-2 từ; câu tên thiết bị gần giống; câu phủ định; nhiều lệnh liên tiếp; hai thiết bị nói đồng thời; test fallback là agent local/LLM; lỗi cloud agent/mất mạng.
4. So sánh thời gian khởi động HA và chi phí CPU/RAM của index warmup, phân tích `request_metrics.recent_p50_ms` và `recent_p95_ms` sau ít nhất 100 request, kiểm tra rằng không có lệnh sai nguy hiểm.
5. Kiểm tra log trước khi chia sẻ vì Home Assistant hoặc cloud agent khác có thể tự ghi nội dung lời nói của người dùng.
