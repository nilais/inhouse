from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    IntegerField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class JoinRoomForm(FlaskForm):
    identifier = StringField()
    room_id = IntegerField('Join a room with the following ID:', validators=[DataRequired()])
    submit = SubmitField('Join')

class CreateRoomForm(FlaskForm):
    identifier = StringField()
    room_id = IntegerField('Create a room with the following ID:', validators=[DataRequired()])
    submit  = SubmitField('Create')

class EditProfileForm(FlaskForm):
    preferences = StringField('preferences', validators=[Length(min=5,max=5)])
    submit  = SubmitField('Submit')
