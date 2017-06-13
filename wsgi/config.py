import os
#basedir = os.path.abspath(os.path.dirname(__file__))
basedir = os.environ['OPENSHIFT_DATA_DIR']


DATABASE = 'site.db'
DEBUG = True
DATABASE_PATH = os.path.join(basedir, DATABASE)
#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE_PATH
SQLALCHEMY_DATABASE_URI = os.environ['OPENSHIFT_POSTGRESQL_DB_URL'] + '/bibliomart'
SECRET_KEY = "this is some kind of secret"
DATA_FOLDER = os.environ['OPENSHIFT_DATA_DIR']
IMAGE_FOLDER = os.environ['OPENSHIFT_DATA_DIR'] + 'files/images'
DOC_FOLDER = os.environ['OPENSHIFT_DATA_DIR'] + 'files/docs'
