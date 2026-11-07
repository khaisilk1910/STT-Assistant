# STT Assistant 1.18.0 — Rà soát Home Assistant 2026.11 / Marketplace

Ngày rà soát: 07/11/2026. Đầu vào: mã nguồn trong `STT-Assistant-main.zip` của người dùng. Đây là báo cáo thay đổi **mã nguồn**, không phải chứng chỉ đã chạy thành công trên một máy Home Assistant thực tế.

## Nền tảng và giới hạn tương thích

- Home Assistant **2026.11.0** (phát hành 04/11/2026) tích hợp HACS trực tiếp dưới tên **Settings > Marketplace**. Không cài HACS độc lập trên HA 2026.11+. Các repository tùy chỉnh vẫn dùng `hacs.json`, cấu trúc `custom_components/<domain>` và bước kiểm tra HACS action.
- Duy trì mức yêu cầu tối thiểu **Home Assistant 2026.10.0** để người dùng 2026.10 vẫn có thể cài qua HACS cũ. `pyproject.toml` yêu cầu **Python >= 3.14.2**.
- Đây là **Conversation Agent xử lý câu nói sau STT**, không phải thành phần xử lý tín hiệu âm thanh/STT hay wake-word.

## Thay đổi trong mã nguồn 1.18.0

1. **Config Flow / Options Flow** — `config_flow.py`: loại bỏ việc truyền/giữ `ConfigEntry` qua hàm khởi tạo `OptionsFlow`; dùng `self.config_entry` ở bước hiển thị cấu hình, đúng mô hình Home Assistant mới. Giữ `step_id` rõ ràng cho từng form và xử lý submit mà không đọc entry không cần thiết.
2. **Khởi động nhẹ** — `__init__.py`, `runtime.py`: bước setup chỉ tạo runtime, đăng ký lắng nghe và forward Conversation platform; không quét metadata entity/area/floor và không xây chỉ mục trong `async_setup_entry`. Chỉ nạp registry lúc warmup sau khi HA khởi động (trễ 15 giây) hoặc khi cần xử lý lệnh sớm. Warmup từng ngôn ngữ tuần tự. Giữ cơ chế hủy timers/tasks và xóa cache khi unload.
3. **Tính nhất quán của registry** — `runtime.py`: khi cập nhật registry, cache và fingerprint được tính từ snapshot trước khi công bố. Nếu xây registry index lỗi, trạng thái `registry_initialized` vẫn `False` để lần sau nạp lại; tránh ghi nhận nhầm trạng thái dữ liệu đã sẵn sàng.
4. **Diagnostics chuẩn của Home Assistant** — `diagnostics.py`: thêm `async_get_config_entry_diagnostics` để người dùng tải báo cáo từ menu config entry. Dữ liệu chỉ là số đếm, cấu hình ngưỡng, chỉ số thời gian, số lượng index, trạng thái lỗi (boolean), không xuất câu nói, hotword, ID agent, request ID, trace ID, tên thiết bị hay thông báo exception chưa kiểm soát. Endpoint chỉ đọc RAM, không khởi chạy index build hoặc I/O.
5. **Nhật ký dễ khoanh vùng** — `__init__.py`: thêm `setup_ms` vào log thiết lập, cải thiện dấu vết khi không thể đọc Assist pipeline hay nạp registry. Giữ log route, thời gian, mã request ngẫu nhiên, cảnh báo request chậm của phiên bản trước.
6. **Marketplace/HACS metadata** — `manifest.json`: thêm category hợp lệ `ai_voice.voice_assistants`, đồng bộ `version = 1.18.0`. `hacs.json` giữ khai báo phiên bản HA và tương thích HACS cũ, bỏ khóa README lỗi thời. `pyproject.toml` và package nội bộ trong `uv.lock` được đồng bộ bản phát hành. `README.md` và `README.en.md` hướng dẫn Marketplace 2026.11+ và HACS legacy.
7. **Kiểm thử hồi quy** — thêm test riêng cho diagnostics không rò dữ liệu; test để bảo đảm registry chỉ được đọc khi cần và retry được sau lỗi; cập nhật test Options Flow và metadata.

## Kết quả kiểm tra tại môi trường đóng gói

| Hạng mục | Kết quả |
| --- | --- |
| Kiểm tra cú pháp `python -m compileall -q custom_components/stt_assistant tests` | **PASS** (Python 3.13.5, chỉ xác minh cú pháp) |
| Nhóm pytest **không cần Home Assistant**: metadata, brand/README, telemetry, translations, validator, validator compatibility | **172 passed**, 0 failed (Python 3.13.5) |
| `uv run --locked tools/validate.py` (entry point bắt buộc của dự án) | **BLOCKED**, không được đánh dấu PASS: môi trường không có Python 3.14 và không phân giải DNS để tải Python/phụ thuộc |
| Pytest phụ thuộc HA, Ruff/Ty/Pyright/hassfest/HACS action, benchmark, startup time, voice pipeline end-to-end trên HA 2026.11 | **CHƯA CHẠY ĐƯỢC** tại môi trường này |

Không tuyên bố rằng bản phát hành đã chạy toàn bộ test hoặc vượt qua chứng nhận tương thích trên HA thực tế. Các nhánh tiếp cận cấu trúc nội bộ Assist pipeline vẫn có rủi ro khi Home Assistant thay đổi API; cần kiểm tra với bản phát hành mới.

## Việc phải làm trước khi phát hành Marketplace

1. Đẩy mã nguồn đầy đủ của archive lên repository công khai `https://github.com/khaisilk1910/STT-Assistant`, bảo đảm ở **root repository** có `hacs.json`, `README.md`, và `custom_components/stt_assistant/manifest.json`. Khi kiểm tra 07/11/2026, trang GitHub trả về trạng thái **repository empty**. File ZIP trong máy **không tự xuất hiện trên Marketplace**.
2. Tạo release/tag **1.18.0** (phải khớp manifest). Xem báo cáo GitHub Actions **Hassfest & HACS Validation** và **CI** sau khi push.
3. Trên môi trường có Python >= 3.14.2 và dependency đầy đủ: chạy `uv sync --locked --all-groups`, `uv run --locked tools/validate.py` và các bài test `tests/test_config_flow.py`, `tests/test_diagnostics_download.py`, `tests/test_init.py`, `tests/test_runtime.py`.
4. Dùng một instance HA 2026.11.0 thử nghiệm; sao lưu trước khi nâng cấp. Thử Config Flow, Options, diagnostics, xử lý câu lệnh Việt/Anh, tên entity thay đổi, fallback, nhiều yêu cầu đồng thời, reload/unload và ít nhất một lần HA restart. Đo startup/CPU/RAM và so sánh với bản trước.
5. Vào **Settings > Marketplace > Add from link**, thêm URL GitHub nếu chưa có trong catalog; thử cài đặt và cập nhật qua Marketplace. Đối với HA 2026.10, thử HACS độc lập.

## Thu thập log khi phát sinh lỗi

Trong `configuration.yaml` (nếu đã có `logger:` thì chỉ thêm `logs`):

```yaml
logger:
  default: warning
  logs:
    custom_components.stt_assistant: debug
```

Sau khi chẩn đoán, giảm xuống `info` để tránh ghi log quá nhiều. Tải **Diagnostics** từ config entry ở **Settings > Devices & services**. Không chia sẻ file log hoặc ảnh chụp cấu hình chưa kiểm tra thông tin nhạy cảm.

## Tài liệu đối chiếu chính thức

- https://www.home-assistant.io/blog/2026/11/04/release-202611/
- https://contributors.home-assistant.io/marketplace/how-it-works/
- https://contributors.home-assistant.io/marketplace/guides/integrations/
- https://contributors.home-assistant.io/core/integrations/options-flow/
- https://contributors.home-assistant.io/core/integrations/diagnostics/
- https://contributors.home-assistant.io/blog/2026/10/23/flow-results-require-step-id/
- https://contributors.home-assistant.io/blog/2026/10/23/config-entry-methods-return-none/
