from flask import Blueprint, jsonify
from kafka import KafkaConsumer, KafkaProducer
import base64
import time
import json
from queue import Queue
import threading
from threading import Event
from db import get_db_connection

images_route = Blueprint('images_route', __name__)

# Kafka 설정
KAFKA_BROKER = '5gears.iptime.org:9092'
TOPIC_NAME = 'process_topic'
ACK_TOPIC = 'ack_topic'

# Kafka Producer 설정
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

# Kafka Consumer 설정
consumer = KafkaConsumer(
    TOPIC_NAME,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',
    enable_auto_commit=False,
    group_id='image_consumer_group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# ACK Consumer (재사용 가능하도록 전역으로 생성)
ack_consumer = KafkaConsumer(
    ACK_TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    group_id='ack_consumer_group',
    auto_offset_reset='earliest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# 메시지를 저장할 큐 생성 (FIFO)
message_queue = Queue()

# Stop 이벤트
stop_event = Event()

# 이미지 인코딩 함수
def encode_image(image_data):
    return base64.b64encode(image_data).decode('utf-8')

# MySQL에서 이미지를 가져와 Kafka로 전송
def fetch_and_send_images():
    try:
        con = get_db_connection()
        last_acknowledged = None

        while not stop_event.is_set():
            with con.cursor() as cur:
                if last_acknowledged:
                    query = "SELECT img, plt_number FROM plt_img WHERE plt_number > %s ORDER BY plt_number ASC LIMIT 1"
                    cur.execute(query, (last_acknowledged,))
                else:
                    query = "SELECT img, plt_number FROM plt_img ORDER BY plt_number ASC LIMIT 1"
                    cur.execute(query)

                data = cur.fetchone()
                if data:
                    img, plt_number = data
                    encoded_image = encode_image(img)

                    message = {'plt_number': plt_number, 'encoded_image': encoded_image}
                    producer.send(TOPIC_NAME, value=message)
                    producer.flush()
                    print(f"Sent image with plt_number: {plt_number}")

                    ack_timeout = 10
                    start_time = time.time()

                    for ack_message in ack_consumer:
                        if stop_event.is_set():  # Check stop event inside loop
                            break
                        ack_data = ack_message.value
                        if ack_data.get('plt_number') == plt_number and ack_data.get('status') == 'processed':
                            print(f"Received ACK for plt_number: {plt_number}")
                            last_acknowledged = plt_number
                            break

                        if time.time() - start_time > ack_timeout:
                            print(f"ACK timeout for plt_number: {plt_number}")
                            break
                else:
                    print("No new images to process.")
                time.sleep(3)

    except Exception as e:
        print(f"Error in producer thread: {e}")

def consume_kafka_messages():
    """Kafka 메시지를 소비하고 처리 완료 후 ACK 신호를 전송"""
    try:
        for message in consumer:
            if stop_event.is_set():
                break
            data = message.value
            plt_number = data.get('plt_number')
            encoded_image = data.get('encoded_image')

            if encoded_image:
                message_queue.put({
                    "plt_number": plt_number,
                    "encoded_image": f"data:image/png;base64,{encoded_image}"
                })
                print(f"Processed message for plt_number: {plt_number}")

                ack_message = {'status': 'processed', 'plt_number': plt_number}
                producer.send(ACK_TOPIC, value=ack_message)
                producer.flush()
                print(f"Sent ACK for plt_number: {plt_number}")
            consumer.commit()
    except Exception as e:
        print(f"Error in consumer thread: {e}")

@images_route.route('/images', methods=['POST'])
def get_images():
    global stop_event

    # Stop 이벤트 초기화 (스레드를 다시 시작할 수 있도록)
    if stop_event.is_set():
        stop_event.clear()

    # 현재 실행 중인 스레드 확인 및 시작
    active_threads = threading.enumerate()
    thread_names = [t.name for t in active_threads]

    if "fetch_and_send_images" not in thread_names:
        print("Starting fetch_and_send_images thread...")
        threading.Thread(target=fetch_and_send_images, name="fetch_and_send_images", daemon=True).start()

    if "consume_kafka_messages" not in thread_names:
        print("Starting consume_kafka_messages thread...")
        threading.Thread(target=consume_kafka_messages, name="consume_kafka_messages", daemon=True).start()

    timeout = 10
    start_time = time.time()

    while message_queue.empty():
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            return jsonify({'message': 'No images available yet.'}), 404
        
        time.sleep(1)

    print(f"Queue size : {message_queue.qsize()}")
    next_message = message_queue.get()
    return jsonify({
        'status': 'success',
        'plt_number': next_message['plt_number'],
        'image': next_message['encoded_image']
    }), 200

@images_route.route('/stop_threads', methods=['POST'])
def stop_threads():
    global stop_event

    stop_event.set()  # Stop 이벤트 활성화로 스레드 종료 신호 전달
    return jsonify({'message': 'Threads are stopping...'}), 200
