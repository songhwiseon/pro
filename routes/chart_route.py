import matplotlib
matplotlib.use('Agg')  # Flask 서버 환경에서 사용하기 위해 백엔드를 'Agg'로 설정
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from chart import get_car_price_data
from raw_ma import get_price_data
from flask import Blueprint, send_file, jsonify
import io
import os

chart_route = Blueprint('chart', __name__)

# 자동차 가격 차트
@chart_route.route('/chart')
def show_chart():
    try:
        # 데이터 가져오기
        MoM_dates, MoM_values = get_car_price_data()
        
        # 데이터가 없는 경우 에러 처리
        if not MoM_dates or not MoM_values:
            return jsonify({'error': '데이터를 가져올 수 없습니다.'}), 500

        # 새로운 figure 생성
        plt.figure(figsize=(12, 6))
        
        # 데이터 플로팅
        plt.plot(pd.to_datetime(MoM_dates), MoM_values, 
                marker="o", 
                linestyle="-", 
                color="b", 
                label="Change Rate (%)")
        
        # 그래프 스타일 설정
        plt.title("Used Car Prices MoM Change", fontsize=16)
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Change Rate (%)", fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()

        # 이미지로 변환
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
        img.seek(0)
        plt.close()

        return send_file(
            img,
            mimetype='image/png',
            as_attachment=False
        )
        
    except Exception as e:
        plt.close()
        return jsonify({'error': str(e)}), 500
    

# 원자재 가격 차트
@chart_route.route('/raw/<commodity_type>')
def show_raw(commodity_type):
    try:
        print(f"🔹 원자재 유형: {commodity_type}")

        # 📌 유효한 원자재인지 확인
        if commodity_type not in ["coal", "iron", "aluminum"]:
            return jsonify({'error': '잘못된 원자재 유형입니다.'}), 400

        # 📌 원자재 가격 데이터 가져오기
        dates, values = get_price_data(commodity_type)

        # 데이터가 없거나 길이가 다를 경우 예외 처리
        if not dates or not values or len(dates) != len(values):
            print(f"⚠️ {commodity_type} 데이터가 없거나 길이가 맞지 않습니다!")
            return jsonify({'error': f'{commodity_type} 데이터가 없습니다.'}), 500

        print(f"✅ {commodity_type} 데이터 로드 성공! 데이터 개수: {len(dates)}개")

        # 🔹 Pandas 데이터 변환
        df = pd.DataFrame({'date': pd.to_datetime(dates), 'value': values})
        df.sort_values('date', inplace=True)

        # 🔹 차트 설정
        color_map = {'coal': 'g', 'iron': 'r', 'aluminum': 'b'}
        plt.figure(figsize=(12, 6))
        plt.plot(df['date'], df['value'], marker="o", markersize=4, linestyle="-", color=color_map[commodity_type])

        plt.title(f"{commodity_type.capitalize()} Price History", fontsize=16, pad=20)
        plt.xlabel("Date", fontsize=12, labelpad=10)
        plt.ylabel("Price (USD)", fontsize=12, labelpad=10)
        plt.xticks(rotation=45)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend([commodity_type.capitalize()], loc='upper right')

        # 🔹 이미지를 메모리에 저장하여 반환
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=100, bbox_inches='tight', pad_inches=0.2)
        img.seek(0)
        plt.close()

        print(f"📢 {commodity_type} 그래프 생성 완료!")
        return send_file(img, mimetype='image/png', max_age=0)

    except Exception as e:
        print(f"❌ 서버 오류 발생: {str(e)}")  # 터미널에서 확인 가능
        return jsonify({'error': f'서버 오류: {str(e)}'}), 500

