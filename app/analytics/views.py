from flask import render_template
from flask_login import login_required

from app.analytics import analytics
from app.models import Permission
from app.decorators import permission_required


@analytics.route("/")
@login_required
def index():
    return render_template("analytics/index.html")



        # exp_data = [
        #     {
        #         "timestamp": date(2015, 12, 31),
        #         "data": [
        #             {"position": 0, "record": records[1], "rtype": fa},
        #             {"position": 2, "record": records[0], "rtype": ta},
        #             {"position": 1, "record": None, "rtype": ca}
        #         ]
        #     }
        # ]