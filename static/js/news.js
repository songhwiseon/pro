async function fetchNews(category, elementId) {
    try {
        const response = await fetch(`/api/news/news/${category}`);
        const newsList = await response.json();
        const newsContainer = document.getElementById(elementId);

        newsContainer.innerHTML = newsList.map(news => `
            <li><a href="${news.link}" target="_blank">${news.title}</a></li>
        `).join("");
    } catch (error) {
        console.error(`${category} 뉴스 로딩 실패`, error);
        document.getElementById(elementId).innerHTML = "<li>뉴스를 불러올 수 없습니다.</li>";
    }
}

// 각 뉴스 카테고리 불러오기
fetchNews("철강", "steel-news");
fetchNews("반도체", "semi-news");
fetchNews("자동차", "car-news");
fetchNews("정치", "politics-news");
fetchNews("경제", "economy-news");
