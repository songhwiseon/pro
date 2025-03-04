from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import json
import os

# 📌 원자재 URL 설정
COMMODITIES = {
    "coal": "https://tradingeconomics.com/commodity/coal",
    "iron": "https://tradingeconomics.com/commodity/iron-ore",
    "aluminum": "https://tradingeconomics.com/commodity/aluminum"
}

DATA_FILE = "raw_price_data.json"

def get_raw_price_data():
    """3개 원자재 가격 데이터를 한 번에 크롤링 후 JSON 파일 저장"""
    
    current_time = datetime.now()

    # 10시 이전이면 기존 데이터 활용
    if not (current_time.hour == 10 and current_time.minute < 5) and os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            saved_data = json.load(f)
            return saved_data  # JSON 데이터 전체 반환

    # 크롬 드라이버 설정
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # GUI 없이 실행
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    raw_data = {}  # 전체 데이터를 저장할 딕셔너리

    try:
        for commodity, url in COMMODITIES.items():
            driver.get(url)

            # 5Y 버튼 클릭
            five_year_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-span='5y']"))
            )
            driver.execute_script("arguments[0].click();", five_year_button)
            time.sleep(3)

            # 🔹 Highcharts 데이터 추출
            chart_data = driver.execute_script("""
                return Highcharts.charts[0].series[0].data.map(point => {
                    return { x: point.category, y: point.y };
                });
            """)

            # 🔹 데이터 변환
            dates, values = [], []
            for point in chart_data:
                unix_timestamp = int(point['x']) // 1000
                readable_date = datetime.fromtimestamp(unix_timestamp).strftime('%Y-%m-%d')
                dates.append(readable_date)
                values.append(point['y'])

            raw_data[commodity] = {
                "dates": dates,
                "values": values
            }

        # 🔹 크롤링한 데이터 저장
        raw_data["last_update"] = current_time.strftime('%Y-%m-%d %H:%M:%S')

        with open(DATA_FILE, 'w') as f:
            json.dump(raw_data, f)

        return raw_data

    except Exception as e:
        print(f"❌ 데이터 추출 중 오류 발생: {e}")
        if os.path.exists(DATA_FILE):  # 기존 데이터가 있으면 반환
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        raise e

    finally:
        driver.quit()

def get_price_data(commodity):
    """ 특정 원자재 가격 데이터를 JSON에서 가져오는 함수 """
    with open("raw_price_data.json", "r") as f:
        raw_data = json.load(f)

    # JSON 데이터 구조 확인
    if "coal_values" not in raw_data or "iron_values" not in raw_data or "alum_values" not in raw_data:
        print("❌ JSON 데이터 구조가 예상과 다릅니다!")
        return [], []

    if commodity == "coal":
        values = raw_data["coal_values"]
    elif commodity == "iron":
        values = raw_data["iron_values"]
    elif commodity == "aluminum":
        values = raw_data["alum_values"]
    else:
        print(f"❌ {commodity} 데이터가 JSON에 없음!")
        return [], []

    dates = raw_data["dates"]

    # 🚀 **데이터 길이 조정**
    min_length = min(len(dates), len(values))
    dates = dates[:min_length]  # 필요하면 데이터 길이를 맞춤
    values = values[:min_length]

    return dates, values

