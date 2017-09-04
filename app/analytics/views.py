from flask import render_template
from flask_login import login_required

from app.analytics import analytics
from app.models import Permission
from app.decorators import permission_required


@analytics.route("/")
@login_required
def index():
    return render_template("analytics/index.html")