import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
	SECRET_KEY = os.environ.get("SECRET_KEY") or "#V45VP_eJaGp#vAu_BsK68#ftfW64_"
	FLASKY_ADMIN = os.environ.get("FLASKY_ADMIN")
	SQLALCHEMY_COMMIT_ON_TEARDOWN = True
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	ALLOWED_EXTENSIONS = set(["txt", "pdf"])
	MAX_CONTENT_LENGTH = 10 * 1024 * 1024 # 5 MB
	DEBUG_TB_ENABLED = False

	MAIL_SERVER = "smtp.gmail.com"
	MAIL_PORT = 465
	MAIL_USE_SSL = True
	MAIL_USE_TLS = False
	MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
	MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

	@staticmethod
	def init_app(app):
		pass


class DevelopmentConfig(Config):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = (
		os.environ.get('DEV_DATABASE_URL') 
		or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
	)
	UPLOAD_FOLDER = os.path.join(basedir, "uploads_dev")
	DEBUG_TB_PROFILER_ENABLED = True


class TestingConfig(Config):
	TESTING = True
	SQLALCHEMY_DATABASE_URI = (
		os.environ.get('DEV_DATABASE_URL') 
		or "sqlite:///:memory:"
		or 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
	)
	UPLOAD_FOLDER = os.path.join(basedir, "uploads_test")
	WTF_CSRF_ENABLED = False
	

config = {
	"development": DevelopmentConfig,
	"testing": TestingConfig,
	"default": DevelopmentConfig
}