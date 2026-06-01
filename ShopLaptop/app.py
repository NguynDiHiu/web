import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key = 'laptop_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# EMAIL CONFIG (Flask-Mail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'levietphuc2005@gmail.com'
app.config['MAIL_PASSWORD'] = 'qgpb knqn jffs gfqb'
app.config['MAIL_DEFAULT_SENDER'] = 'levietphuc2005@gmail.com'
from extensions import db, mail

db.init_app(app)
mail.init_app(app)
from models import User, Category, Product, Order
def init_db():
    if not os.path.exists('instance/database.db'):
        with app.app_context():
            db.create_all()
            if not User.query.filter_by(email='admin@gmail.com').first():
                admin_user = User(fullname='Administrator', phone='0123456789', email='admin@gmail.com', address='Hanoi', password=generate_password_hash('admin123'), is_admin=True)
                db.session.add(admin_user)
            
            # Tạo danh mục mẫu
            if Category.query.count() == 0:
                c1 = Category(name="Gaming")
                c2 = Category(name="Văn phòng")
                c3 = Category(name="Đồ họa")
                db.session.add_all([c1, c2, c3])
                db.session.commit()
            
            if Product.query.count() == 0:
                p1 = Product(name="MacBook Air M2", category="Văn phòng", price=25990000, stock=15, image="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500", description="Chip M2 siêu mạnh.")
                p2 = Product(name="ASUS ROG Strix G16", category="Gaming", price=34500000, stock=8, image="https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500", description="Quái vật gaming thế hệ mới.")
                db.session.add_all([p1, p2])
            db.session.commit()

#  ROUTES 
@app.route('/')
def index():
    cat = request.args.get('category')
    products = Product.query.filter_by(category=cat).all() if cat else Product.query.all()
    categories = Category.query.all() # Lấy danh mục từ database
    return render_template('index.html', products=products, categories=categories, current_cat=cat)

@app.route('/product/<int:id>')
def detail(id):
    product = Product.query.get_or_404(id)
    return render_template('detail.html', product=product)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email này đã được sử dụng!', 'danger')
            return redirect(url_for('register'))
        new_user = User(fullname=fullname, phone=phone, email=email, address=address, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash('Đăng ký thành công! Hãy đăng nhập.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.fullname
            session['is_admin'] = user.is_admin
            flash(f'Chào mừng {user.fullname}!', 'success')
            return redirect(url_for('index'))
        flash('Email hoặc mật khẩu không chính xác.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất.', 'info')
    return redirect(url_for('index'))

@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user.fullname = request.form['fullname']
        user.phone = request.form['phone']
        user.address = request.form['address']
        db.session.commit()
        session['user_name'] = user.fullname
        flash('Cập nhật thông tin thành công!', 'success')
    return render_template('account.html', user=user)

#  GIỎ HÀNG XỬ LÝ FIX XUNG ĐỘT SESSION 
def get_clean_cart():
    cart = session.get('cart', {})
    if isinstance(cart, list):
        cart = {}
        session['cart'] = cart
    return cart

@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    if 'user_id' not in session:
        flash('Bạn phải đăng nhập để mua hàng!', 'warning')
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(id)
    if product.stock <= 0:
        flash('Sản phẩm này hiện đã hết hàng!', 'danger')
        return redirect(url_for('index'))

    cart = get_clean_cart()
    str_id = str(id)
    
    if str_id in cart:
        if cart[str_id] < product.stock:
            cart[str_id] += 1
        else:
            flash('Số lượng đặt mua đạt giới hạn tồn kho!', 'warning')
            return redirect(url_for('cart'))
    else:
        cart[str_id] = 1
        
    session['cart'] = cart
    flash(f'Đã thêm {product.name} vào giỏ hàng.', 'success')
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    if 'user_id' not in session: return redirect(url_for('login'))
    cart = get_clean_cart()
    cart_items = []
    total_price = 0
    
    for pid_str, quantity in cart.items():
        p = Product.query.get(int(pid_str))
        if p:
            item_total = p.price * quantity
            total_price += item_total
            cart_items.append({'product': p, 'quantity': quantity, 'total': item_total})
            
    return render_template('cart.html', items=cart_items, total_price=total_price)

@app.route('/update_cart/<int:id>/<string:action>')
def update_cart(id, action):
    cart = get_clean_cart()
    str_id = str(id)
    p = Product.query.get_or_404(id)
    
    if str_id in cart:
        if action == 'increase':
            if cart[str_id] < p.stock:
                cart[str_id] += 1
            else:
                flash('Không thể tăng thêm, đã đạt giới hạn tồn kho!', 'warning')
        elif action == 'decrease':
            cart[str_id] -= 1
            if cart[str_id] <= 0:
                cart.pop(str_id)
        session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:id>')
def remove_from_cart(id):
    cart = get_clean_cart()
    cart.pop(str(id), None)
    session['cart'] = cart
    flash('Đã xóa sản phẩm khỏi giỏ hàng.', 'info')
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cart = get_clean_cart()

    if not cart:
        return redirect(url_for('index'))

    for pid_str, qty in cart.items():

        p = Product.query.get(int(pid_str))

        if p and p.stock >= qty:

            p.stock -= qty

            new_order = Order(
                user_id=session['user_id'],
                product_name=p.name,
                quantity=qty,
                price=p.price * qty
            )

            db.session.add(new_order)

    db.session.commit()

    session['cart'] = {}

    flash('Đặt hàng thành công!', 'success')

    return redirect(url_for('account'))
#  TRANG ADMIN (BỔ SUNG THÊM DANH MỤC) 
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('is_admin'): return redirect(url_for('index'))
    if request.method == 'POST':
        # Kiểm tra xem đang gửi form thêm Sản phẩm hay form thêm Danh mục
        if 'add_product' in request.form:
            name = request.form['name']
            category = request.form['category']
            price = int(request.form['price'])
            stock = int(request.form['stock'])
            image = request.form['image']
            description = request.form['description']
            new_prod = Product(name=name, category=category, price=price, stock=stock, image=image, description=description)
            db.session.add(new_prod)
            db.session.commit()
            flash('Thêm sản phẩm thành công!', 'success')
        
        elif 'add_category' in request.form:
            cat_name = request.form['cat_name'].strip()
            if cat_name:
                if Category.query.filter_by(name=cat_name).first():
                    flash('Danh mục này đã tồn tại!', 'danger')
                else:
                    new_cat = Category(name=cat_name)
                    db.session.add(new_cat)
                    db.session.commit()
                    flash('Thêm danh mục mới thành công!', 'success')
            return redirect(url_for('admin'))
        
    products = Product.query.all()
    categories = Category.query.all()
    orders = Order.query.order_by(Order.date_ordered.desc()).all()
    return render_template('admin.html', products=products, categories=categories, orders=orders)

@app.route('/admin/edit/<int:id>', methods=['POST'])
def edit_product(id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    p = Product.query.get_or_404(id)
    p.name = request.form['name']
    p.category = request.form['category']
    p.price = int(request.form['price'])
    p.stock = int(request.form['stock'])
    db.session.commit()
    flash('Cập nhật sản phẩm thành công!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/delete_cat/<int:id>')
def delete_category(id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    c = Category.query.get_or_404(id)
    # Kiểm tra xem có sản phẩm nào thuộc danh mục này không
    if Product.query.filter_by(category=c.name).first():
        flash('Không thể xóa danh mục này vì đang có sản phẩm thuộc danh mục!', 'danger')
    else:
        db.session.delete(c)
        db.session.commit()
        flash('Đã xóa danh mục thành công!', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:id>')
def delete_product(id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    p = Product.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for('admin'))
from chatbot import chatbot_bp
app.register_blueprint(chatbot_bp)
if __name__ == '__main__':
    init_db()
    app.run(debug=True, use_reloader=False)