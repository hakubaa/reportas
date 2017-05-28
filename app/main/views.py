from app.main import main

@main.route("/", methods=["GET"])
def index():
	return "<h1>REPORTAS</h1>"