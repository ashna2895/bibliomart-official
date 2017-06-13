from flask import (Flask, request, render_template, url_for, redirect, flash, session, g,
 send_file, abort, make_response)
from flask_login import LoginManager
from flask_login import login_user , logout_user , current_user , login_required
from werkzeug import generate_password_hash, check_password_hash
from flask_seasurf import SeaSurf #for csrf protection
import os
import datetime
import requests as req
app = Flask(__name__)

app.config.from_object('config')

from models import User, Category, Book, Image, Cart, CartBook
from models import db

db.init_app(app)
csrf = SeaSurf(app)
#cross site request forgery

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    return User.query.get(id)

@app.before_request
def before_request():
    g.user = current_user

@app.route('/about')
def aboutus():
    return render_template("aboutus.html",page="about")

@app.route('/contact')
def contactus():
    if current_user.is_authenticated:
        cart = g.user.cart.first()
        if not cart:
            cart = Cart(g.user.id)
    else:
        cart=None
    return render_template("contactus.html",page="contact", cart=cart)

@app.route('/admin/books')
def admin_view_books():
    books = Book.query.all()
    return render_template("admin-view-books.html", page="admin_view_books", books=books)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        cart = g.user.cart.first()
        if not cart:
            cart = Cart(g.user.id)
    else:
        cart=None

    if request.method == 'GET':
        if g.user is not None and g.user.is_authenticated:
            return redirect(url_for('index'))
        return render_template('login.html',page="login", cart=cart)

    elif request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user:
            if not user.verified:
                return render_template('pendingverification.html')
            if check_password_hash(user.pwdhash, password):
                user.authenticated = True
                db.session.commit()
                login_user(user)
                return redirect(url_for('index'))
            flash('Username or Password is invalid' , 'warning')
            return render_template("login.html",page="login",cart=cart)
        else:
            flash('Username or Password is invalid' , 'warning')
            return render_template("login.html",page="login", cart=cart)

@app.route('/logout')
@login_required
def logout():
    g.user.authenticated = False
    db.session.commit()
    logout_user()
    flash('Logged out successfully.' , 'success')
    return redirect(url_for('login'))


@app.route('/register',methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        cart = g.user.cart.first()
        if not cart:
            cart = Cart(g.user.id)
    else:
        cart=None
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))

    error = False
    if request.method == 'GET':
        return render_template('register.html',page="register", cart=cart)

    elif request.method == 'POST':
        app.logger.info(repr(request.form))
        name = request.form['name']
        email = request.form['email']
        mobilenumber = request.form['mobilenumber']

        password = request.form['password']
        passwordconfirm = request.form['password-confirm']

        user = User.query.filter_by(email=email).first()
        if user:

            error = True
            flash('Email already registered','warning')

        if password != passwordconfirm:
            error = True
            flash("Passwords don't match",'warning')
        if len(mobilenumber) != 10 or not mobilenumber.isdigit():
            error = True
            flash("Mobile number is invalid",'warning')

        #app.logger.info("Error = ", str(error))
        if error:
            return render_template(
                'register.html',page="register",retry=True,
                oldform = request.form
            )
        else:
            newuser = User(name,email,password,mobilenumber,'customer')

            newuser.authenticated = True
            db.session.add(newuser)
            db.session.commit()
            return render_template('pendingverification.html')


@app.route('/admin/add-book', methods = ['GET', 'POST'])
@login_required
def add_book():
    """ Creates a new book. The POST request is sent from the client's browser by ajax
    using XMLHttpRequest."""
    if g.user.is_admin:
        if request.method == 'GET':
            categories = Category.query.all()
            return render_template('add_book.html', page="admin_add_book", categories=categories)
        elif request.method == 'POST':
            app.logger.info(repr(request.form))
            title = request.form['title']
            author = request.form['author']
            price = request.form['price']
            description = request.form['description']
            category_id = request.form['category']
            newbook = Book(title, author, description, price, category_id)
            db.session.add(newbook)
            db.session.commit()

            book_id =newbook.id

            if not os.path.isdir(app.config['IMAGE_FOLDER']):
                try:
                    os.makedirs(app.config['IMAGE_FOLDER'])
                except:
                    app.logger.info("Couldn't create directory")
                    return "Couldn't create directory"

            for idx,f in enumerate(request.files.getlist("file")):
                app.logger.info(repr(f.content_type))
                if f.__dict__['filename'] == '':
                    continue
                filename = "img%d_%s"%(book_id,f.__dict__['filename'])
                if f.content_type[:5] == 'image':
                    filetype = 'image'
                    f.save(os.path.join(app.config['IMAGE_FOLDER'], filename))

                newfile = Image(filename, filetype, book_id)
                db.session.add(newfile)
                db.session.commit()

            flash('Book added successfully' , 'success')
            return "ok"


@app.route('/admin/add_category', methods = ['GET', 'POST'])
@login_required
def add_category():
    """ Creates a new category. The POST request is sent from the client's browser by ajax
    using XMLHttpRequest."""
    if request.method == 'POST':
        app.logger.info(repr(request.form))
        name = request.form['name']
        newcategory = Category(name)
        db.session.add(newcategory)
        db.session.commit()

        flash('Category added successfully' , 'success')
    add_category = Category.query.all()
    return render_template('add_category.html',page="category")

@app.route('/admin/confirmed_orders')
@login_required
def admin_confirmed_orders():
    return render_template("admin-confirmed-orders.html", page="admin_confirmed_orders")

@app.route('/admin/verify',methods=['GET','POST'])
@login_required
def admin_verify():
    if g.user.is_admin:
        if request.method == 'POST':
            app.logger.info(request.form)
            formtype = request.form['formtype']
            user_id = request.form['userid']
            user = User.query.get(user_id)
            if formtype == 'approve':
                user.verified = True
                db.session.add(user)
            elif formtype == 'reject':
                if user.verified == False:
                    db.session.delete(user)
            db.session.commit()
            return redirect(url_for('admin_verify'))

        categories = Category.query.all()
        unverifiedusers = User.query.filter_by(verified=False).order_by(User.id.desc()).all()
        users = User.query.all()
        return render_template(
            'admin-verify.html', unverifiedusers = unverifiedusers,
            categories=categories,page="admin_user_verify"
        )

@app.route('/user/edit',methods=['GET','POST'])
@login_required
def edituser():
    categories = Category.query.all()
    users = User.query.all()

    error = False
    if request.method == 'GET':
        return render_template('edituser.html',page="edituser", categories=categories,users=users)

    elif request.method == 'POST':
        app.logger.info(repr(request.form))
        edittype = request.form['edittype']
        if edittype == 'changepassword':
            oldpassword = request.form['old-password']
            newpassword = request.form['new-password']
            passwordconfirm = request.form['password-confirm']
            if newpassword != passwordconfirm:
                error = True
                flash("Passwords don't match",'warning')

            if not check_password_hash(g.user.pwdhash, oldpassword):
                error = True
                flash("Current Password is invalid",'warning')
            if error:
                return render_template(
                    'edituser.html',page="edituser",categories=categories,
                    users=users
                )
            else:
                g.user.pwdhash = generate_password_hash(newpassword)
                db.session.commit()
                flash("Password changed succesfully.",'success')
                return render_template(
                    'edituser.html',page="edituser",categories=categories,
                    users=users
                )

        elif edittype == 'userdetails':
            usrname = request.form['name']
            mobno = request.form['mobilenumber']
            password = request.form['password']
            if len(mobno) != 10 or not mobno.isdigit():
                error = True
                flash("Mobile number is invalid",'warning')
            if not check_password_hash(g.user.pwdhash, password):
                error = True
                flash("Password is invalid",'warning')
            if error:
                return render_template(
                    'edituser.html',page="edituser",categories=categories,
                    users=users
                )
            else:
                g.user.name = usrname
                g.user.mobilenumber = mobno
                db.session.commit()
                flash("Details changed succesfully.",'success')
                return render_template(
                    'edituser.html',page="edituser",categories=categories,
                    users=users
                )

@app.route('/')
def index():
    books = Book.query.all()
    if current_user.is_authenticated:
        cart = g.user.cart.first()
        if not cart:
            cart = Cart(g.user.id)
    else:
        cart=None
    return render_template("index.html",page="home",books=books, cart=cart)

@app.route('/404')
def error_404():
    categories = Category.query.all()
    if current_user.is_authenticated:
        cart = g.user.cart.first()
        if not cart:
            cart = Cart(g.user.id)
    else:
        cart=None
    return render_template("404.html",page="404",categories=categories)

@app.route('/book/<book_id>', methods = ['GET', 'POST'])
def book_page(book_id):
    book = Book.query.get(book_id)
    categories = Category.query.all()
    if current_user.is_authenticated:
        cart = g.user.cart.first()
        if not cart:
            cart = Cart(g.user.id)
    else:
        cart=None
    return render_template('product.html',page="individual book pages", categories=categories, book=book, cart=cart)

@app.route('/books', methods = ['GET', 'POST'])
@app.route('/books/<category>', methods = ['GET', 'POST'])
def product_list_page(category=''):
    categories = Category.query.all()
    if current_user.is_authenticated:
        cart = g.user.cart.first()
        if not cart:
            cart = Cart(g.user.id)
    else:
        cart=None
    if category:
        selected_category = Category.query.filter_by(name=category)
        if not selected_category:
            return redirect(urlfor('error_404'))
        else:
            books = Book.query.filter(Book.category.has(name=category)).all()
    else:
        books = Book.query.all()
    page = category.capitalize()
    return render_template('products_list.html',page=page, categories=categories, books=books, cart=cart)

@app.route('/cart', methods = ['GET', 'POST'])
def cart():
    if request.method == 'GET':
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        cart = g.user.cart.first()
        if not cart:
            cart = Cart(g.user.id)
        categories = Category.query.all()
        return render_template('cart.html',page="cart", categories=categories, cart=cart)
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return make_response("Login")
        book_id = request.form['book_id']
        book = Book.query.get(book_id)
        cart = g.user.cart.first()
        if not cart:
            cart = Cart(g.user.id)
            db.session.add(cart)
            db.session.commit()
        cart.add_book(book)
        db.session.commit()
        resp = make_response("Book added to cart")
        return resp


@app.route('/test/<template>')
def test(template):
    """ Route for quickly testing templates under development"""
    return render_template(template+'.html')

if __name__ == '__main__':
    app.run()
