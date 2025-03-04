from flask import Blueprint, jsonify
from news import get_news

news_route = Blueprint('news', __name__)

@news_route.route('/news/<category>')   
def get_news_data(category):
    try:
        news_list = get_news(category)
        return jsonify(news_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500




