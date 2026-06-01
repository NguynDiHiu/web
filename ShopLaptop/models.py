from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    products = db.relationship(
        'Product',
        backref='cat_rel',
        lazy=True
    )


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    category = db.Column(
        db.String(50),
        db.ForeignKey('category.name'),
        nullable=False
    )

    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=10)
    image = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Integer, nullable=False)

    date_ordered = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    user = db.relationship(
        'User',
        backref=db.backref('orders', lazy=True)
    )