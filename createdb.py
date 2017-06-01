from app import app
from models import db
db.init_app(app)

with app.app_context():
    db.drop_all()
    db.create_all()
    db.session.commit()

#add sample entries
from app import User, Category
with app.app_context():
    u = User("ashna","ashna@bibliomart.com","password","9995903767","admin")
    u.is_admin = True
    u.verified = True
    db.session.add(u)

    c = Category("Fiction")
    db.session.add(c)
    c1 = Category("Biography")
    db.session.add(c1)
    c2 = Category("Drama")
    db.session.add(c2)
    c3 = Category("Non-Fiction")
    db.session.add(c3)
    c4 = Category("Educational")
    db.session.add(c4)

    db.session.commit()

#It's used to create database entries we initially need like the admin account and categories
