from werkzeug import generate_password_hash
import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):

    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    def __init__(self, name):
        self.name = name

    def  __repr__(self):
        return '<Category- id: %r - name: %r ->'%(self.id, self.name)


class Book(db.Model):
    """The database model for Books"""
    __tablename__ = "book"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',backref=db.backref('book', lazy='dynamic'))
    images = db.relationship('Image', backref='book', lazy='dynamic')
    def __init__(self, title, author, description, price, category_id, ):
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
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, nullable=False)
    filetype = db.Column(db.String, nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    timestamp = db.Column(db.DateTime)

    def __init__(self, filename, filetype, book_id):
        self.filename = filename
        self.filetype = filetype
        self.timestamp = datetime.datetime.utcnow()
        self.book_id = book_id

    def __repr__(self):
        return '<id: %r - filename: %r - filetype: %r>'%(self.id, self.filename, self.filetype)


class ConfirmedOrders(db.Model):
    __tablename__ = "confirmed_orders"
    id = db.Column(db.Integer, primary_key=True)
    bookid = db.Column(db.Integer, db.ForeignKey('book.id'))
    userid = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float)
    paymentid = db.Column(db.Integer)

    def __init__(self, bookid, userid, amount, paymentid):
        self.bookid = bookid
        self.userid = userid
        self.amount = amount
        self.paymentid = paymentid



        #done!
