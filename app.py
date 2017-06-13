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

from models import User, Category, Book, Image, Cart, CartBook, Order
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
    return render_template("contactus.html",page="contact")

@app.route('/admin/books')
def admin_view_books():
    books = Book.query.all()
    return render_template("admin-view-books.html", page="admin_view_books", books=books)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if g.user is not None and g.user.is_authenticated:
            return redirect(url_for('index'))
        return render_template('login.html',page="login")

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
            return render_template("login.html",page="login")
        else:
            flash('Username or Password is invalid' , 'warning')
            return render_template("login.html",page="login")

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
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))

    error = False
    if request.method == 'GET':
        return render_template('register.html',page="register")

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
                filename = "img%s_%s"%(book_id,f.__dict__['filename'])
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
    categories = Category.query.all()
    return render_template('add_category.html',page="category",categories=categories)

@app.route('/admin/approve_orders',methods=['GET','POST'])
@login_required
def admin_approve_orders():
    if g.user.is_admin:
        if request.method == 'POST':
            formtype = request.form['formtype']
            order_id = request.form['orderId']
            order = Order.query.get(order_id)
            if formtype == 'approve':
                order.is_approved = True
            elif formtype == 'cancel':
                order.is_cancelled = True
            db.session.add(order)
            db.session.commit()
            return redirect(url_for('admin_approve_orders'))

        unapproved_orders = Order.query.filter_by(is_approved=False, is_cancelled=False).all()
        cancelled_orders = Order.query.filter_by(is_cancelled=True).all()
        approved_orders = Order.query.filter_by(is_approved=True).all()
        return render_template(
            "admin-approve-orders.html", page="admin_approve_orders",
            approved_orders=approved_orders,unapproved_orders=unapproved_orders,
            cancelled_orders=cancelled_orders
        )

@app.route('/admin/verify',methods=['GET','POST'])
@login_required
def admin_verify():
    if g.user.is_admin:
        if request.method == 'POST':
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

        unverifiedusers = User.query.filter_by(verified=False).order_by(User.id.desc()).all()
        verifiedusers = User.query.filter_by(verified=True).order_by(User.id.desc()).all()
        return render_template(
            'admin-verify.html', unverifiedusers = unverifiedusers,
            page="admin_user_verify",verifiedusers=verifiedusers
        )

@app.route('/admin/delete_books', methods=['GET','POST'])
@login_required
def admin_delete_books():
    if g.user.is_admin:
        books = Book.query.all()
        if request.method == 'POST':
            formtype = request.form['formtype']
            book_id = request.form['bookid']
            book = Book.query.get(book_id)
            if formtype == 'reject':
                db.session.delete(book)
            db.session.commit()
            return redirect(url_for('admin_delete_books'))
        flash('Book deleted successfully' , 'success')
        return render_template('admin-delete-books.html', page="admin-delete-books",books=books)

@app.route('/admin/delete_categories', methods=['GET','POST'])
@login_required
def admin_delete_categories():
    if g.user.is_admin:
        categories = Category.query.all()
        if request.method == 'POST':
            formtype = request.form['formtype']
            category_id = request.form['categoryid']
            category = Category.query.get(category_id)
            if formtype == 'reject':
                db.session.delete(category)
            db.session.commit()
            return redirect(url_for('admin_delete_categories'))
        flash('Category deleted successfully' , 'success')
        return render_template('admin-delete-categories.html', page="admin-delete-categories",categories=categories)


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
        if request.form['type'] == 'AddBook':
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
        if request.form['type'] == 'RemoveBook':
            book_id = request.form['book_id']
            book = Book.query.get(book_id)
            cart = g.user.cart.first()
            cart.remove_book(book)
            db.session.commit()
            resp = make_response("Book removed from cart")
        return resp

@app.route('/orders')
def orders():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    cart = g.user.cart.first()
    if not cart:
        cart = Cart(g.user.id)
    orders = g.user.order.all()
    categories = Category.query.all()
    return render_template("orders.html",page="orders", orders=orders, cart=cart, categories=categories)

@app.route('/checkout', methods = ['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        form_data = request.form
        cart = g.user.cart.first()
        if not cart or cart.book_count<1:
            resp = make_response("Cart Empty")
        order = Order(g.user.id, form_data['name'], form_data['address'],
            form_data['state'], form_data['city'], form_data['pincode'],
            form_data['landmark'], form_data['phone'])
        db.session.add(order)
        db.session.commit()
        for cb in cart.cart_books:
            order.add_book(cb.book)
        db.session.delete(cart)
        db.session.commit()
        return redirect(url_for('orders'))

    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    cart = g.user.cart.first()
    if not cart:
        return redirect(url_for('cart'))
    categories = Category.query.all()
    return render_template("checkout.html",page="checkout", cart=cart, categories=categories)

@app.route('/search/<search_text>')
def search(search_text):
    search_text = search_text.replace('+','%')
    categories = Category.query.all()
    books = Book.query.filter(Book.title.like('%'+search_text+'%')).all()
    if current_user.is_authenticated:
        cart = g.user.cart.first()
        if not cart:
            cart = Cart(g.user.id)
    else:
        cart=None
    return render_template('search_results.html', search_text = search_text.replace('%','+'), books=books, categories=categories, cart=cart)





@app.route('/test/<template>')
def test(template):
    """ Route for quickly testing templates under development"""
    return render_template(template+'.html')

if __name__ == '__main__':
    app.run()
