from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user

from app.user import user as user_blueprint
from app.user.util import get_redirect_target
from app.user.forms import LoginForm
from app.models import User
from app import db


@user_blueprint.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(email=form.email.data).first() 
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(get_redirect_target() or url_for("main.index"))
        flash("Invalid username or password.")
    return render_template("user/login.html", form=form)


@user_blueprint.route("/logout", methods=["GET"])
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(get_redirect_target() or url_for("main.index"))