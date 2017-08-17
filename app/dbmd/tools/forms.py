from datetime import date

from wtforms import fields, validators
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from werkzeug.utils import secure_filename

from app import db
from db.models import Company, FinancialStatementSchema


class LanguageMixin(object):

    language = fields.SelectField(
        "Language", choices=[("PL", "PL")], default="PL"
    )


class ReportTimerangeMixin(object):
    report_timerange = fields.SelectField(
        "Timerange", default="12",
        choices=[("3", "3"), ("6", "6"), ("9", "9"), ("12", "12")],
    )
    report_timestamp = fields.DateField(
        "Timestamp", format="%Y-%m", validators=[validators.optional()]
    )


class CompanyMixin(object):
    company = QuerySelectField(
        query_factory=lambda: db.session.query(Company).all(),
        get_label=lambda item: item.name, get_pk=lambda item: item.id
    ) 


class ReportUploaderForm(LanguageMixin, FlaskForm):
    file = FileField(validators=[
        FileRequired("No file selected"),
        FileAllowed(["pdf"], "Not allowed extension")
    ])
    company = QuerySelectField(
        query_factory=lambda: db.session.query(Company).all(),
        get_label=lambda item: item.name, get_pk=lambda item: item.id,
        blank_text="(detect automatically)", allow_blank=True
    )
    report_timerange = fields.SelectField(
        "Timerange", default="",
        choices=[
            ("", "(detect automatically)"), ("3", "3"), ("6", "6"), 
            ("9", "9"), ("12", "12")
        ],
    )
    report_timestamp = fields.DateField(
        "Timestamp", format="%Y-%m", validators=[validators.optional()]
    )

    def get_file(self):
        return self.file.data

    def get_filename(self):
        return self.file.data.filename


class DirectInputForm(
    CompanyMixin, ReportTimerangeMixin, LanguageMixin, FlaskForm
):
    content = fields.TextAreaField("Content", [validators.DataRequired()])


class BatchUploaderForm(
    CompanyMixin, ReportTimerangeMixin, LanguageMixin, FlaskForm
):
    fschema = QuerySelectField(
        query_factory=lambda: db.session.query(FinancialStatementSchema).all(),
        get_label=lambda item: item.default_repr.value, 
        get_pk=lambda item: item.id,
        validators = [validators.DataRequired()]
    ) 