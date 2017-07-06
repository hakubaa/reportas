from flask import render_template

from app.home import home

@home.route("/")
def homepage():
    """
    Render the homepage template on the / route
    """
    return render_template("home/index.html")
