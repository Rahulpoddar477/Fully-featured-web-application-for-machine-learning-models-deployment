from flask import Flask
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from flask_login import LoginManager
from flask_mail import Mail

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'rahulpoddarofficial12@gmail.com'
app.config['MAIL_PASSWORD'] = '*****'
mail = Mail(app)

client = MongoClient("mongodb://db:27017")
#client = MongoClient("mongodb://localhost:27017")
db = client.users
user = db["user"]


from top import routes
