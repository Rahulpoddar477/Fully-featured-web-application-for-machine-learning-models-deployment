import os
import secrets
from PIL import Image
from flask import Flask, render_template, url_for, flash, redirect, request
from top import app, db, bcrypt , login_manager, mail
from top.forms import RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm, SpamvsHamForm, VGG16ImageClassificaion
from flask_login import login_user, current_user, logout_user, login_required
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.models import load_model
import pickle
from flask_login import UserMixin
from flask_mail import Message


model = VGG16()

class Useraut():
    def __init__(self,username,email,password,image_file,_id):
        self.email = email
        self.username = username
        self.password = password
        self.image_file = image_file
        self._id = _id

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.email

    @login_manager.user_loader
    def load_user(email):
        user = db.user.find_one({"email": email})
        if not user:
            return None
        return Useraut(user['username'],user['email'],user['password'],user['image_file'],user['_id'])

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'email': self.email}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            email = s.loads(token)['email']
        except:
            return None
        return db.user.find_one({'email': email })



@app.route("/home")
@login_required
def home():
    return render_template('home.html')



@app.route("/about")
@login_required
def about():
    return render_template('about.html', title='About')



@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        db.user.insert({'username':form.username.data, 'email': form.email.data, 'password': hashed_password, 'image_file': 'default.jpg'})
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/",methods=['GET', 'POST'])
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.user.find_one({'email': form.email.data })
        if user and bcrypt.check_password_hash(user['password'], form.password.data):
            login_user(Useraut(user['username'],user['email'],user['password'],user['image_file'],user['_id']), remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.user.update({ '_id' : current_user._id },{'$set':{'username':current_user.username , 'email':current_user.email,'image_file':current_user.image_file}})
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


def send_reset_email(user):
    token = Useraut(user['username'],user['email'],user['password'],user['image_file'],user['_id']).get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user['email']])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = db.user.find_one({'email': form.email.data })
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)



@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = Useraut.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        db.user.update({ 'username': user['username']},{'$set':{'password': hashed_password}})
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@app.route("/spamvsham", methods=['GET', 'POST'])
@login_required
def spamvsham():
    form = SpamvsHamForm()
    if form.validate_on_submit():
        with open('model_pickle','rb') as f:
            model = pickle.load(f)
        pred = model.predict([form.mailsubject.data])
        if pred[0] == 'ham':
            flash(f'This is predicted as {pred[0]} mail!', 'success')
        elif pred[0] == 'spam':
            flash(f'This is predicted as {pred[0]} mail!', 'danger')
        db.user.update({ 'username': current_user.username},{'$push':{'mails': form.mailsubject.data }})
    return render_template('spamvsham.html', title='Spam vs Ham', form=form)

@app.route("/vgg16_image_classification", methods=['GET', 'POST'])
@login_required
def vgg16_image_classification():
    form = VGG16ImageClassificaion()
    if form.validate_on_submit():
        if form.picture.data:
            img = Image.open(form.picture.data)
            imgarr = img_to_array(img.resize((224,224)))
            imgres = imgarr.reshape(1,imgarr.shape[0],imgarr.shape[1],imgarr.shape[2])
            imgpre = preprocess_input(imgres)
            y_pred = model.predict(imgpre,batch_size=64)
            label = decode_predictions(y_pred,top=1)
            picture_file = save_picture(form.picture.data)
            image_file = url_for('static', filename='profile_pics/' + picture_file)
            flash(f'This is predicted as {label[0][0][1]} with {round(label[0][0][2]*100,2)}% confidence!', 'success')
            return render_template('vgg16classification.html', title='VGG16 Image classification', form=form, image_file = image_file)
    return render_template('vgg16classification.html', title='VGG16 Image classification', form=form)
