# VN30 Trading Bot - Hướng Dẫn Sử Dụng (Cập Nhật Sponsor Edition)

## 📋 Tổng Quan
Bot phân tích tự động các cổ phiếu VN30 và gửi báo cáo vào nhóm Telegram mỗi giờ.
**Phiên bản này đã được cấu hình tối ưu cho tài khoản VNStock Sponsor (Premium).**

---

## 🚀 Cách Chạy (Khuyên Dùng)

### ✅ Cách 1: Chạy Tự Động (Best Practice)
Sử dụng file **`Start_Bot_Complete.bat`** - Bot sẽ tự làm tất cả:
1. Cập nhật danh sách VN30 mới nhất.
2. Tải dữ liệu lịch sử **365 ngày** (để tính toán chỉ báo chính xác).
3. Khởi động chế độ Lập lịch (Scheduler) chạy mỗi 60 phút.

Chỉ cần double-click vào file:
```bash
Start_Bot_Complete.bat
```

### ⏩ Cách 2: Chỉ Cập Nhật Dữ Liệu
Nếu bạn muốn cập nhật dữ liệu mà không chạy bot ngay:
```bash
Update_Data.bat
```
*(Lệnh này sẽ tải 365 ngày dữ liệu, đảm bảo đủ cho phân tích kỹ thuật)*

### 🛠️ Cách 3: Chạy Bot (Không cập nhật)
Nếu dữ liệu đã mới, bạn có thể chạy bot ngay:
```bash
Start_Bot.bat
```

---

## ⚙️ Cấu Hình Môi Trường & API Key

### 1. Môi Trường Ảo (Virtual Environment)
Bot hiện tại được cấu hình để **BẮT BUỘC** chạy trên môi trường ảo tại:
`C:\Users\84378\.venv`

Các file `.bat` đã được lập trình để tự động tìm và sử dụng đúng phiên bản Python trong thư mục này. Bạn **không cần** phải kích hoạt thủ công.

### 2. VNStock API Key (Sponsor)
API Key được lưu trong file `.env`. Bot sẽ tự động nạp và đăng ký với server khi khởi động.
```bash
VNSTOCK_API_KEY=vnstock_xxxxxxxxxxxxxxxxxxxxxxxx
```
*(Bạn không cần nhập key vào code, bot sẽ tự xử lý)*

---

## 🔧 Xử Lý Sự Cố (Troubleshooting)

### ❓ Lỗi: "No high-conviction setups found"
- **Nguyên nhân:** Có thể do dữ liệu lịch sử quá ngắn (dưới 30 ngày) khiến các chỉ báo (RSI, MA) không tính được.
- **Khắc phục:** Chạy lại **`Update_Data.bat`** để tải đủ 365 ngày dữ liệu.

### ❓ Cảnh báo màu đỏ: "DeprecationWarning: asyncio..."
- **Nguyên nhân:** Đây là cảnh báo kỹ thuật của thư viện Python trên Windows, **KHÔNG ẢNH HƯỞNG** đến hoạt động của bot.
- **Trạng thái:** Đã được ẩn trong phiên bản mới nhất để màn hình sạch sẽ hơn.

### ❓ Lỗi thiếu thư viện (ModuleNotFoundError)
- Nếu gặp lỗi này, hãy đảm bảo bạn đang chạy bằng các file `.bat` cung cấp sẵn, vì chúng trỏ đúng vào môi trường `.venv` đã cài đủ thư viện.

---

## 📝 Các Lệnh Thủ Công (Dành cho Dev)

Nếu bạn muốn gõ lệnh thủ công trong Terminal (CMD/PowerShell), hãy dùng đường dẫn tuyệt đối tới Python của venv:

| Mục Đích | Lệnh (Copy & Paste) |
|----------|---------------------|
| Cập nhật VN30 | `"C:\Users\84378\.venv\Scripts\python.exe" -m src.app.cli.main update-universe` |
| Tải Data 365 ngày | `"C:\Users\84378\.venv\Scripts\python.exe" -m src.app.cli.main backfill-ohlcv --days 365` |
| Chạy Scheduler | `"C:\Users\84378\.venv\Scripts\python.exe" -m src.app.cli.main schedule` |
| Test Telegram | `"C:\Users\84378\.venv\Scripts\python.exe" -m src.app.cli.main test-telegram` |

