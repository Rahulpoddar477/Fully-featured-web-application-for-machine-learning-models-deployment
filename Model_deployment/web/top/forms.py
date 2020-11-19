from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from flask_wtf.file import FileField, FileAllowed
from top import db
from flask_login import current_user
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(),Length(min=6, max=30)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    def validate_username(self, username):
        user = db.user.find_one({'username': username.data })
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = db.user.find_one({'email': email.data })
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = db.user.find_one({'username': username.data })
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = db.user.find_one({'email': email.data })
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')

class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = db.user.find_one({'email': email.data })
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


class SpamvsHamForm(FlaskForm):
    mailsubject = StringField('Mail Subject',validators=[DataRequired(),Length(min = 1,max = 750)])
    submit = SubmitField('Predict')

class VGG16ImageClassificaion(FlaskForm):
    picture = FileField('Just upload an image and see what this model is predicting it to be!!', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Predict')
