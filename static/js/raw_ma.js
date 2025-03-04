document.addEventListener('DOMContentLoaded', function() {
    async function fetchCoalChart() {
        const canvasId = 'rawChart';
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        try {
            // 로딩 표시
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.font = '14px Arial';
            ctx.fillStyle = '#666';
            ctx.textAlign = 'center';
            ctx.fillText('석탄 가격 데이터를 불러오는 중...', canvas.width/2, canvas.height/2);

            const response = await fetch('/api/chart/raw', {
                method: 'GET',
                headers: {
                    'Accept': 'image/png',
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const blob = await response.blob();
            const imageUrl = URL.createObjectURL(blob);
            const img = new Image();
            
            img.onload = function() {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
                URL.revokeObjectURL(imageUrl);
            };
            
            img.onerror = function() {
                ctx.font = '14px Arial';
                ctx.fillStyle = 'red';
                ctx.textAlign = 'center';
                ctx.fillText('석탄 가격 차트 로딩 실패', canvas.width/2, canvas.height/2);
                URL.revokeObjectURL(imageUrl);
            };
            
            img.src = imageUrl;

        } catch (error) {
            console.error('석탄 가격 차트 로딩 실패:', error);
            const ctx = canvas.getContext('2d');
            ctx.font = '14px Arial';
            ctx.fillStyle = 'red';
            ctx.textAlign = 'center';
            ctx.fillText(`로딩 실패: ${error.message}`, canvas.width/2, canvas.height/2);
        }
    }

    // 초기 로드
    fetchCoalChart();

    // 15분마다 새로고침
    setInterval(fetchCoalChart, 900000);
});