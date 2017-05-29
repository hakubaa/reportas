import datetime

from app import db


class File(db.Model):
	__tablename__ = "files"

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(), unique=True)
	timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

	def __repr__(self):
		return "<File %r>" % self.name


