# Sử dụng hình ảnh Python chính thức, gọn nhẹ
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép file danh sách thư viện vào trước để tận dụng cache
COPY requirements.txt .

# Cài đặt các thư viện cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn còn lại vào container
COPY . .

# Mở cổng 5000 (Cổng mặc định của Flask)
EXPOSE 5000

# Lệnh khởi chạy ứng dụng bằng Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]