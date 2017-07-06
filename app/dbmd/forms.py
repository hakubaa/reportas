# app/admin/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.ext.sqlalchemy.orm import model_form

import db.models as models


# CompanyForm = model_form(models.Company)


class CompanyForm(FlaskForm):
    """
    Form for admin to add or edit a department
    """
    name = StringField("Name", validators=[DataRequired()])
    isin = StringField("Isin", validators=[DataRequired()])

    submit = SubmitField("Submit")



#     name = Column(String, nullable=False)
#     isin = Column(String, unique=True, nullable=False)
#     ticker = Column(String)
#     fullname = Column(String)
#     district = Column(String)
#     webpage = Column(String)
#     email = Column(String)
#     address = Column(String)
#     debut = Column(DateTime)
#     fax = Column(String)
#     telephone = Column(String)
#     sector = Column(String)
