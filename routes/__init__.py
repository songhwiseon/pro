from .site_route import site_route
from .login_route import login_route
from .loginck_route import loginck_route
from .images_route import images_route
from .kafka_route import kafka_route
from .chart_route import chart_route
from .news_route import news_route
from .slack_route import slack_route

blueprints = [
   (site_route,"/"),
   (login_route,"/api/login"),
   (loginck_route,"/api/loginck"),
   (images_route,"/api/images"),
   (kafka_route,"/api/logs"),
   (news_route,"/api/news"),
   (chart_route,"/api/chart"),
   (slack_route,"/api/slack")
]

def register_blueprints(app):
    app.secret_key = 'your-secret-key-here'
    for blueprint,prefix in blueprints:
        app.register_blueprint(blueprint,url_prefix=prefix)