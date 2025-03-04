from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import json
import os

def get_car_price_data():
    current_time = datetime.now()
    data_file = 'car_price_data.json'
    
    # 현재 시간이 오전 10시가 아니고, 저장된 데이터가 있다면 저장된 데이터 사용
    if not (current_time.hour == 10 and current_time.minute < 5) and os.path.exists(data_file):
        with open(data_file, 'r') as f:
            saved_data = json.load(f)
            return saved_data['dates'], saved_data['values']
    
    # 크롤링 실행
    driver = webdriver.Chrome()
    driver.get('https://tradingeconomics.com/united-states/used-car-prices-mom')

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "highcharts-series"))
    )

    ten_year_button = driver.find_element(By.CSS_SELECTOR, "a[data-span_str='10Y']")
    ten_year_button.click()
    time.sleep(3)

    MoM_chart_data = driver.execute_script("""
        return Highcharts.charts[0].series[0].data.map(point => {
            return { x: point.category, y: point.y };
        });
    """)

    MoM_dates = [datetime.utcfromtimestamp(int(point['x']) // 1000).strftime('%Y-%m-%d') for point in MoM_chart_data]
    MoM_values = [point['y'] for point in MoM_chart_data]

    driver.quit()
    
    # 크롤링한 데이터 저장
    with open(data_file, 'w') as f:
        json.dump({
            'dates': MoM_dates,
            'values': MoM_values,
            'last_update': current_time.strftime('%Y-%m-%d %H:%M:%S')
        }, f)
    
    return MoM_dates, MoM_values