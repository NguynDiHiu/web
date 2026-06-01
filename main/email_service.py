from extensions import mail
from flask_mail import Message


def send_order_email(user, product, qty, total_price):
    try:
        msg = Message(
            subject="Xác nhận đơn hàng Laptop",
            recipients=[user.email]
        )

        msg.body = f"""
Xin chào {user.fullname},

Cảm ơn bạn đã đặt hàng tại Shop Laptop.

THÔNG TIN ĐƠN HÀNG

Sản phẩm: {product.name}
Số lượng: {qty}
Tổng tiền: {total_price:,} VNĐ

THÔNG TIN NGƯỜI NHẬN

Họ tên: {user.fullname}
SĐT: {user.phone}
Địa chỉ: {user.address}

Chúng tôi sẽ liên hệ với bạn trong thời gian sớm nhất để xác nhận đơn hàng.

Trân trọng,
SHOP LAPTOP
"""

        mail.send(msg)

        print(f"[EMAIL] Đã gửi email tới {user.email}")

        return True

    except Exception as e:
        print("[EMAIL ERROR]", str(e))
        return False