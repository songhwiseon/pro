from flask import Blueprint, request, jsonify
import requests
import base64

slack_route = Blueprint('slack', __name__)

SLACK_TOKEN = ""
SLACK_CHANNEL = "C089X7RJE0Y"
thread_ts = ""

def send_to_slack(image_base64, label, confidence):
    try:
        image_data = base64.b64decode(image_base64)

        # 1. Slack의 files.getUploadURLExternal API를 호출해 업로드 URL과 file_id 받아오기
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {SLACK_TOKEN}'
        }

        data = {
            "filename": "error.png",
            "length": len(image_data)
        }

        headers['Content-Type'] = 'application/x-www-form-urlencoded'

        get_url_response = requests.post(
            url="https://slack.com/api/files.getUploadURLExternal",
            headers=headers,
            data=data
        )
        get_url_result = get_url_response.json()
        
        if not get_url_result.get("ok", False):
            print("업로드 URL을 받지 못했습니다:", get_url_result)
            return

        file_id_info = {
            "file_id": get_url_result.get('file_id'),
            "upload_url": get_url_result.get('upload_url')
        }

        if not file_id_info.get("upload_url"):
            print("업로드 URL이 응답에 없습니다.")
            return

        # Step 2. Slack이 제공한 URL에 파일 데이터를 업로드합니다.
        upload_response = requests.post(
            url=file_id_info.get('upload_url'),
            files={'file': image_data}
        )
        if upload_response.status_code != 200:
            print("파일 업로드에 실패했습니다:", upload_response.text)
            return

        # Step 3. 업로드 완료 후 Slack에 첨부파일 공유 요청을 보냅니다.
        attachment = {
            "files": [{
                "id": file_id_info.get('file_id'),
                "title": "error.png"
            }],
            "channel_id": SLACK_CHANNEL,
            "initial_comment": "불량품 감지!\n라벨: {}\nConfidence: {:.2f}".format(label, confidence)
        }
        if thread_ts:
            attachment["thread_ts"] = thread_ts

        headers['Content-Type'] = 'application/json; charset=utf-8'

        complete_response = requests.post(
            url="https://slack.com/api/files.completeUploadExternal",
            headers=headers,
            json=attachment
        )
        complete_result = complete_response.json()

        if not complete_result.get("ok"):
            print(f"업로드 완료 처리 실패: {complete_result.get('error')}")
        else:
            print("Slack에 파일 업로드 및 공유 성공!")
            print("Slack 응답:", complete_result)

    except Exception as e:
        print(f"Slack 전송 중 오류 발생: {str(e)}")

@slack_route.route('/', methods=['POST'])
def send_slack_notification():
    try:
        data = request.json
        image_base64 = data.get('image_base64')
        label = data.get('label')
        confidence = data.get('confidence')

        if not image_base64 or not label or confidence is None:
            print('no data')
            return jsonify({'error': 'Invalid data'}), 400

        send_to_slack(image_base64, label, confidence)
        return jsonify({'status': 'success'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
