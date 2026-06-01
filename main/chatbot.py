import os
from flask import Blueprint, request, jsonify, session
from groq import Groq
from email_service import send_order_email
chatbot_bp = Blueprint('chatbot', __name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
groq_client = Groq(api_key=GROQ_API_KEY)


@chatbot_bp.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    from extensions import db
    from models import User, Product, Order

    user_msg = request.json.get('message', '').strip()

    if not user_msg:
        return jsonify({
            'reply': 'Vui lòng nhập nội dung cần tư vấn.'
        })

    user_msg_lower = user_msg.lower()
    user_id = session.get('user_id')

    if 'bot_state' not in session:
        session['bot_state'] = {
            'status': 'idle',
            'product_id': None,
            'quantity': 0
        }

    state = session['bot_state']

    
    # NHẬP SỐ LƯỢNG
    
    if state['status'] == 'waiting_quantity':

        if not user_msg.isdigit() or int(user_msg) <= 0:
            return jsonify({
                'reply': '⚠️ Vui lòng nhập số lượng là số nguyên dương.'
            })

        qty = int(user_msg)

        p = db.session.get(Product, state['product_id'])

        if not p:
            session['bot_state'] = {
                'status': 'idle',
                'product_id': None,
                'quantity': 0
            }

            return jsonify({
                'reply': '⚠️ Sản phẩm không tồn tại hoặc đã bị xóa.'
            })

        if qty > p.stock:
            return jsonify({
                'reply': f'❌ Không đủ hàng. Hiện kho chỉ còn {p.stock} máy.'
            })

        state['quantity'] = qty
        state['status'] = 'waiting_confirm'
        session['bot_state'] = state

        user_info = db.session.get(User, user_id)

        total_price = p.price * qty

        return jsonify({
            'reply':
            f'📋 HÓA ĐƠN ĐẶT HÀNG\n\n'
            f'💻 Sản phẩm: {p.name}\n'
            f'🔢 Số lượng: {qty}\n'
            f'💰 Tổng tiền: {total_price:,} đ\n\n'
            f'👤 Người nhận: {user_info.fullname}\n'
            f'📞 Điện thoại: {user_info.phone}\n'
            f'📍 Địa chỉ: {user_info.address}\n\n'
            f'👉 Nhắn "XÁC NHẬN" để đặt hàng.'
        })

    
    # XÁC NHẬN ĐƠN
    
    if state['status'] == 'waiting_confirm':

        if (
            'xác nhận' in user_msg_lower
            or user_msg_lower == 'ok'
            or user_msg_lower == 'mua'
        ):

            if not user_id:
                session['bot_state'] = {
                    'status': 'idle',
                    'product_id': None,
                    'quantity': 0
                }

                return jsonify({
                    'reply': '⚠️ Phiên đăng nhập đã hết hạn.'
                })

            p = db.session.get(Product, state['product_id'])
            qty = state['quantity']

            if not p or p.stock < qty:

                session['bot_state'] = {
                    'status': 'idle',
                    'product_id': None,
                    'quantity': 0
                }

                return jsonify({
                    'reply': '❌ Tồn kho đã thay đổi.'
                })

            p.stock -= qty

            total_price = p.price * qty

            new_order = Order(
                user_id=user_id,
                product_name=p.name,
                quantity=qty,
                price=total_price
            )

            db.session.add(new_order)
            db.session.commit()
            user = db.session.get(User, user_id)

            send_order_email(
                 user=user,
                 product=p,
                 qty=qty,
                 total_price=total_price
            )
            session['bot_state'] = {
                'status': 'idle',
                'product_id': None,
                'quantity': 0
            }

            return jsonify({
                'reply':
                f'🎉 Đặt hàng thành công!\n\n'
                f'📦 {p.name}\n'
                f'🔢 Số lượng: {qty}\n'
                f'💰 Tổng tiền: {total_price:,} đ'
            })

        session['bot_state'] = {
            'status': 'idle',
            'product_id': None,
            'quantity': 0
        }

        return jsonify({
            'reply': '❌ Đã hủy quy trình đặt hàng.'
        })

    
    # KÍCH HOẠT MUA HÀNG
    
    if 'mua' in user_msg_lower or 'đặt' in user_msg_lower:

        if not user_id:
            return jsonify({
                'reply': '⚠️ Bạn cần đăng nhập trước khi mua hàng.'
            })

        products = Product.query.all()

        for p in products:

            if p.name.lower() in user_msg_lower:

                if p.stock <= 0:
                    return jsonify({
                        'reply': f'❌ {p.name} hiện đã hết hàng.'
                    })

                session['bot_state'] = {
                    'status': 'waiting_quantity',
                    'product_id': p.id,
                    'quantity': 0
                }

                return jsonify({
                    'reply':
                    f'🛒 Đã chọn {p.name}\n\n'
                    f'👉 Vui lòng nhập số lượng muốn mua.'
                })

        return jsonify({
            'reply':
            '🤔 Bạn muốn mua mẫu nào?\nVí dụ: Mua MacBook Air M2'
        })

    
    # AI TƯ VẤN
    
    try:

        all_prods = Product.query.all()

        store_context = ""

        for p in all_prods:
            store_context += (
                f"- {p.name} | "
                f"Loại: {p.category} | "
                f"Giá: {p.price:,} đ | "
                f"Tồn kho: {p.stock} | "
                f"Mô tả: {p.description}\n"
            )

        system_instruction = f"""
Bạn là trợ lý bán laptop.

Dữ liệu sản phẩm:

{store_context}

Quy tắc:
1. Chỉ tư vấn dựa trên dữ liệu trên.
2. Trả lời ngắn gọn bằng tiếng Việt.
3. Nếu khách muốn mua hàng hãy hướng dẫn:
   Mua [Tên sản phẩm]
4. Không tự bịa sản phẩm.
"""

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.4,
            messages=[
                {
                    "role": "system",
                    "content": system_instruction
                },
                {
                    "role": "user",
                    "content": user_msg
                }
            ]
        )

        return jsonify({
            'reply': completion.choices[0].message.content
        })

    except Exception as e:

        print("CHATBOT ERROR:", str(e))

        return jsonify({
            'reply':
            'Xin lỗi, chatbot đang tạm thời gặp sự cố. '
            'Bạn vẫn có thể mua hàng bằng cú pháp: Mua [Tên sản phẩm]'
        })