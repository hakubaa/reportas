import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
	SECRET_KEY = os.environ.get("SECRET_KEY") or "#V45VP_eJaGp#vAu_BsK68#ftfW64_"
	FLASKY_ADMIN = os.environ.get("FLASKY_ADMIN")

	@staticmethod
	def init_app(app):
		pass


class DevelopmentConfig(Config):
	DEBUG = True

class TestingConfig(Config):
	TESTING = True


config = {
	"development": DevelopmentConfig,
	"testing": TestingConfig,
	"default": DevelopmentConfig
}