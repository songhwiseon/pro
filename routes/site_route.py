from flask import render_template,request,jsonify,Blueprint

site_route = Blueprint('site', __name__)

@site_route.route("/")
def home():
    return render_template("front.html")

@site_route.route("/pipe")
def pipe():
    return render_template("pipe.html")

@site_route.route("/news")
def news():
    return render_template("news.html")

@site_route.route("/login")
def login_page():
    return render_template("login.html")