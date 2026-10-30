<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="custom_components/stt_assistant/brand/dark_logo.png">
  <img src="custom_components/stt_assistant/brand/logo.png" alt="STT Assistant" width="480">
</picture>

### Sửa câu lệnh giọng nói trước khi Home Assistant xử lý

**🇻🇳 [Tiếng Việt](README.md) · 🇬🇧 [English](README.en.md)**

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-%E2%89%A5%202026.10-blue)](https://www.home-assistant.io/)
[![GitHub](https://img.shields.io/badge/GitHub-STT--Assistant-181717?logo=github)](https://github.com/khaisilk1910/STT-Assistant)
[![License](https://img.shields.io/github/license/khaisilk1910/STT-Assistant)](LICENSE)

[![Thêm vào HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=khaisilk1910&repository=STT-Assistant&category=integration)

**[Tải bản phát hành](https://github.com/khaisilk1910/STT-Assistant/releases) · [Báo lỗi / Góp ý](https://github.com/khaisilk1910/STT-Assistant/issues)**

</div>

> [!NOTE]
> Đây là **tích hợp cộng đồng**, không phải thành phần chính thức của Home Assistant và chưa được xác nhận kiểm thử đầy đủ trên Home Assistant thực tế. Repository GitHub cần có mã nguồn trước khi HACS có thể tải tích hợp. Nút bên trên mở trang repository trong HACS, **không tự động cài đặt**.

## STT Assistant là gì?

**STT Assistant** là **Conversation Agent** cho Home Assistant Assist. Khi STT đã chuyển giọng nói thành văn bản, tích hợp giúp chuẩn hóa và tìm câu lệnh gần đúng (kể cả lỗi từ, thay đổi trật tự từ hay tên thiết bị), sau đó sử dụng luồng xử lý intent của Home Assistant.

**Không phải** engine STT nhận âm thanh, wake word hay TTS; các bước này vẫn do Assist Pipeline đảm nhiệm.

## ✨ Tính năng

- **Sửa/chuẩn hóa câu lệnh sau STT:** kết hợp fuzzy matching, BM25, so khớp ký tự và ngữ cảnh intent.
- **Hỗ trợ nhiều ngôn ngữ**, tên và bí danh entity, khu vực, tầng và câu lệnh tùy chỉnh.
- **Hạn chế thực thi nhầm:** kiểm tra ngưỡng tin cậy và xác minh intent trước khi thực thi; chuyển agent dự phòng khi không chắc chắn.
- **Fallback & hotword tùy chỉnh:** chuyển câu hỏi mở đến Conversation Agent khác (nếu được cấu hình).
- **Khởi động nhẹ:** trì hoãn warmup chỉ mục và xử lý tác vụ nền; yêu cầu đầu tiên có thể chậm hơn.
- **Log & diagnostics:** mã theo dõi từng yêu cầu, nhánh xử lý, thời gian xử lý, P50/P95 và các action kiểm thử/làm mới chỉ mục.
- **Xử lý cục bộ:** không tự gửi dữ liệu đến dịch vụ ngoài; agent dự phòng có thể sử dụng cloud tùy cấu hình của bạn.

## 📥 Cài đặt

### Cách 1 — HACS (khuyên dùng)

[![Thêm STT Assistant vào HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=khaisilk1910&repository=STT-Assistant&category=integration)

1. Cài [HACS](https://www.hacs.xyz/) nếu chưa có.
2. Bấm nút trên. Nếu không mở được, vào **HACS → ⋮ → Custom repositories** và thêm:
   - **Repository:** `https://github.com/khaisilk1910/STT-Assistant`
   - **Type / Category:** `Integration`
3. Mở STT Assistant trong HACS và chọn **Download**.
4. **Khởi động lại Home Assistant.**

> [!IMPORTANT]
> HACS chỉ có thể tải sau khi repository đã có mã nguồn hợp lệ. Đây là **custom repository**; không có nghĩa tích hợp đã được duyệt vào kho HACS mặc định.

### Cách 2 — Cài thủ công

1. Lấy mã nguồn từ [Releases](https://github.com/khaisilk1910/STT-Assistant/releases) hoặc tệp ZIP của dự án.
2. Sao chép **nguyên thư mục** `custom_components/stt_assistant` vào thư mục cấu hình Home Assistant:

   ```text
   config/
   └── custom_components/
       └── stt_assistant/
           ├── __init__.py
           ├── manifest.json
           └── brand/
   ```

3. **Khởi động lại Home Assistant.** Không cần sao chép toàn bộ tests/tài liệu vào `custom_components`.

### Kích hoạt trong Assist

1. Vào **Settings → Devices & services → Add integration**, tìm **STT Assistant**.
2. Chọn **Fallback Conversation Agent** và giữ ngưỡng tin cậy mặc định khi bắt đầu.
3. Vào **Settings → Voice assistants**, mở Assist Pipeline đang dùng và chọn **STT Assistant** làm *Conversation Agent*.
4. Thử câu đơn giản rồi thử một câu STT sai từ; kiểm tra log/diagnostics nếu kết quả chưa đúng.

**Lưu ý:** Chỉ cài tích hợp nhưng chưa chọn trong Assist Pipeline thì STT Assistant sẽ **không xử lý câu lệnh**.

## 🪵 Log và sửa lỗi

Có thể bật/tắt **Enable debug logging** ở trang tích hợp trong **Devices & services**; hoặc cấu hình `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.stt_assistant: info  # đổi thành debug khi cần điều tra
```

Nếu đã có `logger:`, **gộp** dòng `custom_components.stt_assistant` vào khối đang dùng, không tạo khối `logger:` thứ hai. Log INFO cho biết nhánh xử lý và thời gian; DEBUG hiển thị thời gian từng giai đoạn. Xem thêm [hướng dẫn logging](LOGGING_STT_ASSISTANT.vi.md) và [chẩn đoán/kiểm thử](RELEASE_VALIDATION.vi.md).

## ⚠️ Rủi ro & khuyến cáo

- **Thực thi sai intent:** tương đồng văn bản không bảo đảm đúng ý; kiểm tra kỹ các câu **bật/tắt, khóa/mở khóa**, tên thiết bị gần giống. Dùng ngưỡng mặc định trước, không hạ ngưỡng tùy tiện.
- **Hiệu năng:** xây chỉ mục lần đầu có thể tăng CPU/RAM và khiến lệnh đầu tiên chậm; hiệu quả phụ thuộc cấu hình, số entity và máy chủ.
- **Tương thích:** bản mã nguồn 1.17.0 khai báo **Home Assistant ≥ 2026.10.0**, nhưng chưa được chứng nhận end-to-end trên hệ thống thật. Sao lưu trước khi cài và kiểm thử trên instance phụ nếu có.
- **Nâng cấp từ tên cũ:** domain mới `stt_assistant` **không tự chuyển cấu hình** của `assist_canonicalizer`. Xem [hướng dẫn chuyển đổi](MIGRATION_STT_ASSISTANT.vi.md); **không sửa trực tiếp** `.storage`.
- **Riêng tư:** tích hợp không chủ động log transcript ở INFO/DEBUG mới, nhưng agent khác và Home Assistant có thể ghi dữ liệu nhạy cảm. Kiểm tra log trước khi chia sẻ; cân nhắc cloud fallback.
- **Không thay thế STT engine:** nếu engine nhận sai hoàn toàn câu nói, tích hợp có thể không khôi phục được ý định đúng.

## 📚 Tài liệu & hỗ trợ

[Logging](LOGGING_STT_ASSISTANT.vi.md) · [Chuyển đổi domain](MIGRATION_STT_ASSISTANT.vi.md) · [Giới hạn kiểm thử](RELEASE_VALIDATION.vi.md) · [Brand assets](BRANDING.md) · [GitHub Issues](https://github.com/khaisilk1910/STT-Assistant/issues)

**Dự án:** [github.com/khaisilk1910/STT-Assistant](https://github.com/khaisilk1910/STT-Assistant) · **Giấy phép:** [LICENSE](LICENSE)
