import functools

from flask import render_template, redirect, url_for, flash, request, jsonify, g
from flask_login import login_user, login_required, logout_user, current_user

from app.user import user as user_blueprint
from app.user.util import get_redirect_target, send_email
from app.user.forms import LoginForm, RegistrationForm
from app.models import User, Role
from app import db
from app.user import auth


@user_blueprint.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(email=form.email.data).first() 
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(get_redirect_target() or url_for("home.homepage"))
        flash("Invalid username or password.")
    return render_template("user/login.html", form=form)


@user_blueprint.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(get_redirect_target() or url_for("home.homepage"))


@user_blueprint.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data, name=form.name.data,
            password=form.password.data
        )
        if not user.role and not user.role_id:
            user.role = db.session.query(Role).filter_by(name="User").one()
        db.session.add(user)
        db.session.commit()
        token = user.generate_token()
        send_email(
            user.email, "Confirm Your Account",
            "user/email/confirm", user=user, token=token
        )
        flash("A confirmation email has been sent to you by email.")
        return redirect(url_for("user.login"))
    return render_template("user/register.html", form=form)


@user_blueprint.route("/confirm/<token>")
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for("home.homepage"))
    if current_user.confirm(token):
        flash("You have confirmed your account. Thanks!")
    else:
        flash("The confirmation link is invalid or has expired.")
    return redirect(url_for("home.homepage"))


@user_blueprint.before_app_request
def before_request():
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint[:5] != "user.":
        return redirect(url_for("user.unconfirmed"))


@user_blueprint.route("/unconfirmed")
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect("home.homepage")
    return render_template("user/unconfirmed.html")


@user_blueprint.route("/confirm")
@login_required
def resend_confirmation():
    token = current_user.generate_token()
    send_email(current_user.email, "Confirm Your Account", 
               "user/email/confirm", user=current_user, token=token)
    flash("A new confirmation email has been sent to you by email.")
    return redirect(url_for("home.homepage"))
    

@user_blueprint.route("/token")
@auth.login_required
def get_token():
    token = g.user.generate_token()
    return jsonify({"token": token.decode("ascii")})