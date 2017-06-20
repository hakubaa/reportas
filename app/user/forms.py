from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    ValidationError
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp
from sqlalchemy import exists

from app.models import User
from app import db


class LoginForm(FlaskForm):
    email = StringField(
        "Email", validators=[DataRequired(), Length(1, 64), Email()]
    )
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Keep me logged in")
    submit = SubmitField("Log In")


class RegistrationForm(FlaskForm):
    email = StringField(
        "Email", validators=[DataRequired(), Length(1, 64), Email()]
    )
    name = StringField(
        "Name",
        validators = [
            DataRequired(), Length(1, 64),
            Regexp("^[A-Za-z][A-Za-z0-9_.]*$", 0,
                   "Usernames must have only letters, "
                   "numbers, dots or underscores")
        ]
    )
    password = PasswordField(
        "Password",
        validators = [
            DataRequired(), EqualTo("password2", message="Passwords must match.")
        ]
    )
    password2 = PasswordField("Confirm password", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self, field):
        (ret, ), = db.session.query(exists().where(User.email == field.data))
        if ret:
            raise ValidationError("Email already registered.")
    
    def validate_name(self, field):
        (ret, ), = db.session.query(exists().where(User.name == field.data))
        if ret:
            raise ValidationError("Username already in use.")