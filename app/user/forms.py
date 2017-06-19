from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Email, Length


class LoginForm(FlaskForm):
    email = StringField(
        "Email", validators=[Required(), Length(1, 64), Email()]
    )
    password = PasswordField("Password", validators=[Required()])
    remember_me = BooleanField("Keep me logged in")
    submit = SubmitField("Log In")

    # def validate(self):
    #     initial_validation = super(RegisterForm, self).validate()
    #     if not initial_validation:
    #         return False
    #     user = User.query.filter_by(email=self.email.data).first()
    #     if user:
    #         self.email.errors.append("Email already registered")
    #         return False
    #     return True