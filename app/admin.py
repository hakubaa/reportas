from flask_admin.contrib.sqla import ModelView

from app import admin_, db
from db.models import Company


class MyView(ModelView):
    pass


admin_.add_view(MyView(Company, db.session))