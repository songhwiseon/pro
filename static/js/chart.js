document.addEventListener('DOMContentLoaded', function() {
    // 초기 로드
    fetchAll();

    // 15분마다 새로고침
    setInterval(function(){
        fetchAll();
    }, 900000);
});

async function fetchAll() {
    await fetchRawChart('coal', 'coalChart');
    await fetchRawChart('iron', 'ironChart');
    await fetchRawChart('aluminum', 'aluminumChart');
    await fetchCarChart();
}

// 원자재 가격 차트
async function fetchRawChart(commodity, canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = '14px Arial';
    ctx.fillStyle = '#666';
    ctx.textAlign = 'center';
    ctx.fillText(`${commodity.toUpperCase()} 가격 데이터를 불러오는 중...`, canvas.width / 2, canvas.height / 2);

    try {
        const response = await fetch(`/api/chart/raw/${commodity}`, { method: 'GET', headers: { 'Accept': 'image/png' } });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const blob = await response.blob();
        const imageBitmap = await createImageBitmap(blob);

        // 📌 Canvas 크기를 이미지 크기에 맞게 조정
        canvas.width = imageBitmap.width;
        canvas.height = imageBitmap.height;
        ctx.drawImage(imageBitmap, 0, 0);   //0,0 위치에 이미지 그리기

    } catch (error) {
        console.error(`${commodity.toUpperCase()} 가격 차트 로딩 실패:`, error);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'red';
        ctx.fillText(`${commodity.toUpperCase()} 가격 차트 로딩 실패`, canvas.width / 2, canvas.height / 2);
    }
}

// 자동차 가격 차트
async function fetchCarChart() {
    const canvasId = 'priceChart';
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    try {
        // 로딩 표시
        ctx.clearRect(0, 0, canvas.width, canvas.height);  // 기존 내용 삭제
        ctx.font = '14px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('자동차 가격 데이터를 불러오는 중...', canvas.width / 2, canvas.height / 2);

        const response = await fetch('/api/chart/chart', {
            method: 'GET',
            headers: {
                'Accept': 'image/png',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const blob = await response.blob();
        const imageBitmap = await createImageBitmap(blob);  // createImageBitmap으로 동기화

        canvas.width = imageBitmap.width;  // 이미지 크기로 캔버스 크기 변경
        canvas.height = imageBitmap.height;
        ctx.drawImage(imageBitmap, 0, 0);  // 이미지 그리기

    } catch (error) {
        console.error('자동차 가격 차트 로딩 실패:', error);
        ctx.clearRect(0, 0, canvas.width, canvas.height);  // 실패 시 기존 내용 삭제
        ctx.font = '14px Arial';
        ctx.fillStyle = 'red';
        ctx.textAlign = 'center';
        ctx.fillText('자동차 가격 차트 로딩 실패', canvas.width / 2, canvas.height / 2);
    }
}


