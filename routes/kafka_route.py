from flask import Blueprint, request, jsonify
from kafka import KafkaProducer, KafkaConsumer
import json
from datetime import datetime
import pytz
from db import get_db_connection
from db import get_db_connection2
import pymysql
import base64

kafka_route = Blueprint('kafka', __name__)

# Kafka 프로듀서 설정
KAFKA_BOOTSTRAP_SERVERS = '5gears.iptime.org:9092'  # Kafka 서버 주소
KAFKA_TOPIC_LOGS = 'logs'        # 로그용 토픽
KAFKA_TOPIC_IMAGES = 'kafka-img'    # 이미지용 토픽

tz = pytz.timezone('Asia/Seoul')

try:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    log_consumer = KafkaConsumer(
            KAFKA_TOPIC_LOGS,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='log_db_group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
    
    image_consumer = KafkaConsumer(
            KAFKA_TOPIC_IMAGES,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='analysis_db_group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

except Exception as e:
    print(f"Kafka 연결 실패: {str(e)}")
    producer = None

def decode_image(encoded_image):
    """Base64로 인코딩된 이미지 데이터를 디코딩하여 원래 이미지 바이트로 복원"""
    decoded_image = base64.b64decode(encoded_image.encode('utf-8'))
    return decoded_image

# 이미지
def save_to_db_analysis(data):
    """Kafka 데이터를 analysis_info 테이블에 저장 (log_time = 분석된 시각 그대로)"""
    try:
        conn = get_db_connection2()
        with conn.cursor() as cursor:
            # Kafka에서 받은 timestamp를 한국 시간(KST)으로 변환
            if 'timestamp' in data and data['timestamp']:
                try:
                    # ISO 8601 형식 파싱 (UTC 기준으로 KST 변환)
                    original_timestamp = datetime.strptime(data['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    original_timestamp = original_timestamp.replace(tzinfo=pytz.UTC).astimezone(tz)
                    log_time = original_timestamp.strftime('%Y-%m-%d %H:%M:%S')  # YYYY-MM-DD HH:MM:SS
                except ValueError:
                    print(f"Invalid timestamp format: {data['timestamp']}")
                    return
            else:
                log_time = None

            # 디코드된 이미지 데이터를 BLOB으로 저장하기 위해 변환
            image_data = decode_image(data['image'])
           
           
            query = "INSERT INTO plt_image_analysis (plt_number, img, log_time, ctgr) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (data['pltNumber'],  pymysql.Binary(image_data), log_time, data['message']))
            conn.commit()

        print(f"plt_image_analysis 저장 완료: {data['pltNumber']} | log_time: {log_time}")
    
    except Exception as e:
        print(f"plt_image_analysis 저장 오류: {e}")
    
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

# 로그
def save_to_db_log(data):
    """Kafka 데이터를 log_info 테이블에 저장 (log_time = 분석된 시각 그대로)"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Kafka에서 받은 timestamp를 한국 시간(KST)으로 변환
            if 'timestamp' in data and data['timestamp']:
                try:
                    """ kafka timestamp 문자열을 파싱하여 datatime 객체로 변환 -> UTC 시간을 한국 표준시(KST)로 변경 -> 변환된 시간을 YYY-MM-DD- HH:MM:SS 포맷의 문자열로 저장"""
                    # ISO 8601 형식 파싱 (UTC 기준으로 KST 변환)
                    original_timestamp = datetime.strptime(data['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    # UTC 타임존 설정 및 변환
                    original_timestamp = original_timestamp.replace(tzinfo=pytz.UTC).astimezone(tz)
                    # 시간 문자열 포맷 지정
                    log_time = original_timestamp.strftime('%Y-%m-%d %H:%M:%S')  # YYYY-MM-DD HH:MM:SS
                except ValueError:
                    print(f"Invalid timestamp format: {data['timestamp']}")
                    return
            else:
                log_time = None

            query = "INSERT INTO log_info (plt_number, log_time, ctgr) VALUES (%s, %s, %s)"
            cursor.execute(query, (data['pltNumber'], log_time, data['message']))
            conn.commit()

        print(f"log_info 저장 완료: {data['pltNumber']} | log_time: {log_time}")
    
    except Exception as e:
        print(f"log_info 저장 오류: {e}")
    
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()
        
# 로그 전송
@kafka_route.route('/logs', methods=['POST'])
def send_log_to_kafka():
    try:
        if not producer: 
            return jsonify({
                'status': 'error',
                'message': 'Kafka 서버에 연결할 수 없습니다.'
            }), 500

        log_data = request.json
        log_data['server_timestamp'] = datetime.now().isoformat()
        
        future = producer.send(
            topic=KAFKA_TOPIC_LOGS,
            key=log_data['pltNumber'],
            value=log_data
        )
        future.get(timeout=10)
        
        for message in log_consumer:
            data = message.value
            save_to_db_log(data)

        return jsonify({
            'status': 'success',
            'message': '로그가 성공적으로 전송되었습니다.'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'로그 전송 실패: {str(e)}'
        }), 500

# 이미지 전송
@kafka_route.route('/kafka-ig', methods=['POST'])
def send_image_to_kafka():
    try:
        if not producer:
            return jsonify({
                'status': 'error',
                'message': 'Kafka 서버에 연결할 수 없습니다.'
            }), 500

        image_data = request.json
        image_data['server_timestamp'] = datetime.now().isoformat()
        
        future = producer.send(
            topic=KAFKA_TOPIC_IMAGES,
            key=image_data['pltNumber'],
            value=image_data
        )
        future.get(timeout=10)
        
        for message in image_consumer:
            data = message.value
            save_to_db_analysis(data)
        
        return jsonify({
            'status': 'success',
            'message': '이미지가 성공적으로 전송되었습니다.'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'이미지 전송 실패: {str(e)}'
        }), 500