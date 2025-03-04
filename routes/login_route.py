from flask import Blueprint, request, jsonify, session
from db import get_db_connection
import pymysql

login_route = Blueprint('login', __name__)


@login_route.route('/login', methods=['POST'])
def login_process():
    data = request.get_json()
    input_id = data.get('id')
    input_pw = data.get('pw')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = "SELECT * FROM register_info WHERE rgst_id = %s AND rgst_pw = %s"
        cursor.execute(sql, (input_id, input_pw))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            session['user_id'] = input_id
            session['logged_in'] = True
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'message': '아이디 또는 비밀번호가 올바르지 않습니다.'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    

