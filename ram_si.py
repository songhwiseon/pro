from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 데이터베이스 연결 정보
DB_CONFIG = {
    "host": "192.168.0.163",
    "user": "analysis_user",
    "password": "andong1234",
    "database": "analysis",
    "port": 3306
}

# SQLAlchemy 엔진 생성
engine = create_engine('mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(**DB_CONFIG))

# 1️⃣ 실리콘 가격 데이터 가져오기 (ods_one 테이블에서 실리콘만 필터링)
silicon_query = """
SELECT one_date AS date, one_price AS silicon_price
FROM ods_one
WHERE one_name = '규소'
"""
silicon_df = pd.read_sql(silicon_query, engine)

# 2️⃣ 램 가격 데이터 가져오기 (ods_ram 테이블)
ram_query = """
SELECT ram_date AS date, ram_name, ram_price
FROM ods_ram
"""
ram_df = pd.read_sql(ram_query, engine)

# 날짜 변환 (시간 제거)
silicon_df['date'] = pd.to_datetime(silicon_df['date']).dt.to_period('M')  # 년-월 형식
ram_df['date'] = pd.to_datetime(ram_df['date']).dt.to_period('M')  # 년-월 형식

# 3️⃣ 램 데이터 변환 (ram_name별 가격을 컬럼으로 변환)
ram_pivot_df = ram_df.pivot(index="date", columns="ram_name", values="ram_price").reset_index()

# 4️⃣ 실리콘 주간 데이터를 월간 평균으로 변환
silicon_df = silicon_df.groupby("date").mean().reset_index()

# 5️⃣ 데이터 병합 (램 가격 데이터와 실리콘 월 평균 가격)
merged_df = pd.merge(ram_pivot_df, silicon_df, on='date', how='inner')

# 데이터 확인
print("실리콘 데이터 샘플:")
print(silicon_df.head())
print("\nRAM 데이터 샘플:")
print(ram_pivot_df.head())
print("\n병합된 데이터 샘플:")
print(merged_df.head())

# 그래프 설정
fig, ax1 = plt.subplots(figsize=(12, 6))
sns.set_style("whitegrid")

# x축 변환 (년도-월 포맷)
merged_df['date'] = merged_df['date'].astype(str)

# 첫 번째 y축 (실리콘 가격, USD)
ax1.set_xlabel("Date")
ax1.set_ylabel("Silicon Price (USD)", color="black")
ax1.plot(merged_df['date'], merged_df['silicon_price'], label="Silicon Price (USD)", color="black", linestyle="dashed", linewidth=2)
ax1.tick_params(axis='y', labelcolor="black")

# 두 번째 y축 (램 가격, 원)
ax2 = ax1.twinx()
ax2.set_ylabel("RAM Price (KRW)", color="blue")

# 각 램 제품의 가격을 두 번째 y축에 플롯
ram_columns = [col for col in merged_df.columns if col not in ["date", "silicon_price"]]
for ram in ram_columns:
    ax2.plot(merged_df['date'], merged_df[ram], label=ram, linewidth=1.5)

ax2.tick_params(axis='y', labelcolor="blue")

# 범례 추가
fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
plt.title("Silicon Price (USD) vs RAM Prices (KRW)")
plt.xticks(rotation=45)

# x축 라벨을 YYYY-MM 형식으로만 표시
ax1.set_xticklabels(merged_df['date'], rotation=45)

plt.tight_layout()
plt.show()
