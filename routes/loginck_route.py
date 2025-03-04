from flask import Blueprint, request, jsonify, session
from db import get_db_connection
import pymysql


loginck_route = Blueprint('loginck', __name__)

# 로그인 상태 확인
@loginck_route.route('/check-login', methods=['GET'])
def check_login():
    try:
        is_logged_in = session.get('logged_in', False)
        user_id = session.get('user_id', None)
        
        if is_logged_in and user_id:
            conn = get_db_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # 사용자 정보 조회
            sql = "SELECT nickname FROM register_info WHERE rgst_id = %s"
            cursor.execute(sql, (user_id,))
            user = cursor.fetchone()
            
            if user is None:
                return jsonify({
                    'isLoggedIn': False,
                    'error': '사용자를 찾을 수 없습니다'
                })
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'isLoggedIn': True,
                'nickname': user['nickname']
            })
            
        return jsonify({
            'isLoggedIn': False
        })
            
    except Exception as e:
        return jsonify({
            'isLoggedIn': False,
            'error': str(e)
        })


# 로그아웃
@loginck_route.route('/logout', methods=['POST'])
def logout():
    try:
        # 세션에서 사용자 정보 제거
        session.pop('logged_in', None)
        session.pop('user_id', None)
        
        return jsonify({
            'success': True,
            'message': '로그아웃되었습니다'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500