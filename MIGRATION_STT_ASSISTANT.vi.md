# Chuyển từ tên tích hợp cũ sang STT Assistant

**Lưu ý:** Domain hiện tại là `stt_assistant`. Do Home Assistant lưu domain trong config entry, việc đổi thư mục **không tự di chuyển cấu hình**.

1. Sao lưu toàn bộ cấu hình Home Assistant, nhất là `configuration.yaml`, `.storage` và automation.
2. Ghi lại các tùy chọn tích hợp cũ: fallback agent, min confidence, min margin và hotword.
3. Vào **Cài đặt → Thiết bị & dịch vụ**, xóa tích hợp cũ bằng giao diện. Sau đó tắt Home Assistant.
4. Xóa thư mục custom component cũ, chép thư mục `custom_components/stt_assistant` vào `config/custom_components/`.
5. Khởi động lại, chọn **Thêm tích hợp → STT Assistant** và điền lại các tùy chọn đã lưu.
6. Mở **Cài đặt → Trợ lý giọng nói**, chọn STT Assistant làm Conversation Agent cho pipeline mong muốn.
7. Cập nhật mọi action/automation cũ sang service `stt_assistant.*`.

**Không sửa trực tiếp** `.storage/core.config_entries`: thao tác sai có thể làm hỏng đăng ký tích hợp.

Khởi động: chỉ mục được làm nóng sau khi Home Assistant chạy khoảng 15 giây; yêu cầu đầu tiên trước khi làm nóng có thể chậm hơn. Dữ liệu chỉ mục ở namespace domain mới sẽ được tạo lại.
