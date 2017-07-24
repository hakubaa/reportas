from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed


class ReportUploaderForm(FlaskForm):
    file = FileField(validators=[
        FileRequired("No file selected"),
        FileAllowed(["pdf"], "Not allowed extension")
    ])
