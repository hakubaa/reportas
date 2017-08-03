from datetime import date

from wtforms import fields, validators
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from werkzeug.utils import secure_filename

from app import db
from db.models import Company


class LanguageMixin(object):

    language = fields.SelectField(
        "Language", choices=[("PL", "PL")], default="PL"
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
        "Timestamp", format="%Y-%m-%d", validators=[validators.optional()]
    )

    def get_file(self):
        return self.file.data

    def get_filename(self):
        return self.file.data.filename


class DirectInputForm(LanguageMixin, FlaskForm):
    content = fields.TextAreaField("Content", [validators.DataRequired()])
    company = QuerySelectField(
        query_factory=lambda: db.session.query(Company).all(),
        get_label=lambda item: item.name, get_pk=lambda item: item.id
    )
    report_timerange = fields.SelectField(
        "Timerange", default="12",
        choices=[("3", "3"), ("6", "6"), ("9", "9"), ("12", "12")],
    )
    report_timestamp = fields.DateField(
        "Timestamp", format="%Y-%m-%d", validators=[validators.optional()]
    )
