import requests
from bs4 import BeautifulSoup

# 🔹 네이버 뉴스 URL 목록
NEWS_URLS = {
    "철강": "https://search.naver.com/search.naver?where=news&ie=utf8&sm=nws_hty&query=%EC%B2%A0%EA%B0%95",
    "반도체": "https://search.naver.com/search.naver?where=news&ie=utf8&sm=nws_hty&query=%EB%B0%98%EB%8F%84%EC%B2%B4",
    "자동차": "https://search.naver.com/search.naver?where=news&ie=utf8&sm=nws_hty&query=%EC%9E%90%EB%8F%99%EC%B0%A8",
    "정치": "https://news.naver.com/section/100",
    "경제": "https://news.naver.com/section/101"
}

def get_news(category):
    """ 주제별 최신 뉴스 10개 크롤링 """
    if category not in NEWS_URLS:
        return []

    url = NEWS_URLS[category]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    news_list = []

    if category in ["철강", "반도체", "자동차"]:
        # 🔹 네이버 검색 뉴스 결과에서 가져오기
        items = soup.select(".news_area .news_tit")[:10]  # 최대 10개 가져오기
        for item in items:
            title = item.text.strip()
            link = item["href"]
            news_list.append({"title": title, "link": link})

    elif category in ["정치", "경제"]:
        # 🔹 네이버 뉴스 페이지 헤드라인 뉴스 가져오기
        items = soup.select(".sa_text_strong")[:10]  # 최대 10개
        for item in items:
            title = item.text.strip()
            link = item.find_parent("a")["href"]
            news_list.append({"title": title, "link": link})

    return news_list


# print(get_news("철강"),'끝')
# print(get_news("반도체"),'끝')
# print(get_news("정치"),'끝')
# print(get_news("경제"),'끝')
# print(get_news("자동차"),'끝')

