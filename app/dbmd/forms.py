# app/admin/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms_sqlalchemy.orm import model_form

import db.models as models
from app import db


class UniqueInDb():

    def __init__(self, model, session, name=None, message=None):
        self.model = model
        self.session = session
        self.message = message
        self.name = name

    def __call__(self, form, field):
        if hasattr(form, "edit_mode") and form.edit_mode:
            return None
            
        field_name = self.name or field.name
        field_value = field.data

        obj = self.session.query(self.model).filter(
                  getattr(self.model, field_name) == field_value
              ).first()
        if obj:
            msg = self.message or "{} is not unique".format(field_name)
            raise ValidationError(msg) 


class LevelFormValidationMixin(object):
    formvalidator = HiddenField()

    def validate_formvalidator(form, field=None):
        return form.validate_form()

    def validate_form(form):
        return None


class CompanyForm(LevelFormValidationMixin, FlaskForm):
    '''Form to add or edit a company'''

    def __init__(self, *args, edit_mode=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.edit_mode = edit_mode

    isin = StringField(
        "Isin", 
        validators=[DataRequired(), UniqueInDb(models.Company, db.session)]
    )
    name = StringField(
        "Name", 
        validators=[DataRequired(), UniqueInDb(models.Company, db.session)]
    )
    fullname = StringField("Full Name")
    ticker = StringField("Ticker")
    district = StringField("District")
    webpage = StringField("Webpage")
    email = StringField("Email(s)")
    address = StringField("Address")
    debut = StringField("Debut")
    fax = StringField("Fax")
    telephone = StringField("Telephone")
    sector = StringField("Secotr")
    submit = SubmitField("Submit")


class RecordTypeForm(FlaskForm):
    '''Form to add or edit type of record'''
    
    name = StringField(
        "Name", 
        validators=[DataRequired(), UniqueInDb(models.RecordType, db.session)]
    )
    statement = SelectField(
        "Statement", validators=[DataRequired()],
        choices=[("nls", "NLS"), ("bls", "BLS"), ("cfs", "CFS")]
    )


class RecordTypeReprForm(FlaskForm):
    '''Form to add or edit representation of record type'''
    
    lang = StringField("Language", validators=[DataRequired()])
    value = StringField("Value", validators=[DataRequired()])

    rtype = QuerySelectField(
        validators=[DataRequired()],
        query_factory=lambda: db.session.query(models.RecordType),
        get_label="name"
    )
	
