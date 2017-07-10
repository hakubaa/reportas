from flask_admin import Admin

from app.dbmd.base import AdminIndexView


dbmd = Admin(
    index_view=AdminIndexView(
        template="admin/index.html",
        url="/dbmd"
    ),
    template_mode="bootstrap3"
)

from app.dbmd import views