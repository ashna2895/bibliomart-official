from werkzeug import generate_password_hash
import datetime, uuid

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):

    __tablename__ = "user"
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique = True)
    mobilenumber = db.Column(db.String, nullable=False)
    pwdhash = db.Column(db.String, nullable=False)
    registered_on = db.Column(db.DateTime)
    authenticated = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default = False)
    verified = db.Column(db.Boolean, default = False)
    user_role = db.Column(db.String, nullable=False)

    def __init__(self, name, email, password, mobilenumber, role):
        self.id = uuid.uuid4().hex
        self.name = name
        self.email = email
        self.mobilenumber = mobilenumber
        self.pwdhash = generate_password_hash(password)
        self.registered_on = datetime.datetime.utcnow()
        self.user_role = role


    def is_active(self):
        return True

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

    def __repr__(self):
        return '<id: %r - email: %r - role:%r>' %(self.id, self.email, self.user_role)



class Category(db.Model):
    """The database model for Category"""
    __tablename__ = "category"
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)

    def __init__(self, name):
        self.id = uuid.uuid4().hex
        self.name = name

    def  __repr__(self):
        return '<Category- id: %r - name: %r ->'%(self.id, self.name)

class CartBook(db.Model):
    __tablename__ = 'cart_book'
    id = db.Column(db.String, primary_key=True)
    cart_id = db.Column(db.String, db.ForeignKey('cart.id'), primary_key=True)
    book_id = db.Column(db.String, db.ForeignKey('book.id'), primary_key=True)

    cart = db.relationship("Cart", backref=db.backref("cart_books", cascade="all, delete-orphan" ))
    book = db.relationship("Book", backref=db.backref("cart_books", cascade="all, delete-orphan" ))

    def __init__(self, cart, book):
        self.id = uuid.uuid4().hex
        self.cart = cart
        self.book =  book

    def __repr__(self):
        return '<CartBook {}>'.format(self.cart.user.name+" "+self.book.title)

class OrderBook(db.Model):
    __tablename__ = 'order_book'
    id = db.Column(db.String, primary_key=True)
    order_id = db.Column(db.String, db.ForeignKey('order.id'), primary_key=True)
    book_id = db.Column(db.String, db.ForeignKey('book.id'), primary_key=True)

    order = db.relationship("Order", backref=db.backref("order_books", cascade="all, delete-orphan" ))
    book = db.relationship("Book", backref=db.backref("order_books", cascade="all, delete-orphan" ))

    def __init__(self, order, book):
        self.id = uuid.uuid4().hex
        self.order = order
        self.book =  book

    def __repr__(self):
        return '<OrderBook {}>'.format(self.order.user.name+" "+self.book.title)


class Book(db.Model):
    """The database model for Books"""
    __tablename__ = "book"

    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime)
    category_id = db.Column(db.String, db.ForeignKey('category.id'))
    category = db.relationship('Category',backref=db.backref('book', lazy='dynamic'))
    images = db.relationship('Image', backref='book', lazy='dynamic')
    carts = db.relationship("Cart", secondary="cart_book", viewonly=True)
    orders = db.relationship("Order", secondary="order_book", viewonly=True)
    # is_sold = db.Column(db.Boolean, default = False)

    def __init__(self, title, author, description, price, category_id):
        self.id = uuid.uuid4().hex
        self.title = title
        self.author = author
        self.description = description
        self.price = price
        self.category_id = category_id
        self.date_added = datetime.datetime.utcnow()

    def  __repr__(self):
        return '<id: %r - title: %r ->'%(self.id, self.title)



class Image(db.Model):
    """The database model for Images"""
    __tablename__ = "image"
    id = db.Column(db.String, primary_key=True)
    filename = db.Column(db.String, nullable=False)
    filetype = db.Column(db.String, nullable=False)
    book_id = db.Column(db.String, db.ForeignKey('book.id'))
    timestamp = db.Column(db.DateTime)

    def __init__(self, filename, filetype, book_id):
        self.id = uuid.uuid4().hex
        self.filename = filename
        self.filetype = filetype
        self.timestamp = datetime.datetime.utcnow()
        self.book_id = book_id

    def __repr__(self):
        return '<id: %r - filename: %r - filetype: %r>'%(self.id, self.filename, self.filetype)

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.String,  primary_key=True, unique=True)
    user_id = db.Column(db.String,db.ForeignKey('user.id'))
    total_price = db.Column(db.Float, default=0)
    book_count = db.Column(db.Integer, default=0)
    shipping_charge = db.Column(db.Float, default=0)

    books = db.relationship("Book", secondary="cart_book", viewonly=True)
    user = db.relationship('User',backref=db.backref('cart', lazy='dynamic'))

    def add_book(self, book):
        self.cart_books.append(CartBook(cart=self, book=book))
        self.total_price += book.price
        self.book_count += 1

    def remove_book(self, book):
        self.cart_books = [cb for cb in self.cart_books if cb.book_id != book.id]
        self.total_price -= book.price
        self.book_count -= 1

    def __init__(self, user_id):
        self.id = uuid.uuid4().hex
        self.user_id = user_id

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.String,  primary_key=True, unique=True)
    user_id = db.Column(db.String,db.ForeignKey('user.id'))
    total_price = db.Column(db.Float, default=0)
    book_count = db.Column(db.Integer, default=0)
    shipping_name = db.Column(db.String)
    shipping_address = db.Column(db.String)
    shipping_city = db.Column(db.String)
    shipping_state = db.Column(db.String)
    shipping_pincode = db.Column(db.String)
    shipping_landmark = db.Column(db.String)
    shipping_phone = db.Column(db.String)

    is_approved = db.Column(db.Boolean, default = False)
    is_cancelled = db.Column(db.Boolean, default = False)

    books = db.relationship("Book", secondary="order_book", viewonly=True)
    user = db.relationship('User',backref=db.backref('order', lazy='dynamic'))

    def add_book(self, book):
        self.order_books.append(OrderBook(order=self, book=book))
        self.total_price += book.price
        self.book_count += 1

    def remove_book(self, book):
        self.order_books = [cb for cb in self.order_books if cb.book_id != book.id]
        self.total_price -= book.price
        self.book_count -= 1

    def __init__(self, user_id,shipping_name,shipping_address,shipping_state,
        shipping_city,shipping_pincode,shipping_landmark,shipping_phone):
        self.id = uuid.uuid4().hex
        self.user_id = user_id
        self.shipping_name = shipping_name
        self.shipping_address = shipping_address
        self.shipping_state = shipping_state
        self.shipping_city = shipping_city
        self.shipping_pincode = shipping_pincode
        self.shipping_landmark = shipping_landmark
        self.shipping_phone = shipping_phone
