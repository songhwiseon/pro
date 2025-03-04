$(document).ready(function () {
    const BELT = $(".belt");
    
    const SETTINGS = {
        beltSpeed: 30,
        loadInterval: 5000,
        startPosition: -800,
        endPosition: window.innerWidth + 1000
    };

    const processedImages = new Set();
    let lastImageLoadedTime = Date.now();

    const LOG_SETTINGS = {
        maxLogItems: 5,
        logContainer: '#log-list'
    };

    const INACTIVITY_TIMEOUT = 60000;

    function loadAndAnimateImage() {
        fetch('/api/images/images', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
            .then(res => res.ok ? res.json() : Promise.reject('HTTP 오류'))
            .then(data => {
                if (data.status === 'success' && !processedImages.has(data.plt_number)) {
                    const $img = $(`<img src="${data.image}" />`);
                    $img.data('plt_number', data.plt_number);
                    $img.css({
                        position: "absolute",
                        transform: `translateX(${SETTINGS.startPosition}px)`,
                        transition: `transform ${SETTINGS.beltSpeed}s linear`
                    });

                    BELT.append($img);
                    animateImage($img);

                    processedImages.add(data.plt_number);
                    lastImageLoadedTime = Date.now();

                    setTimeout(() => {
                        processedImages.delete(data.plt_number);
                    }, SETTINGS.beltSpeed * 1000 * 2);
                }
            })
            .catch(() => setTimeout(loadAndAnimateImage, 1000));
    }

    function detectInactivity() {
        let inactivityInterval;
    
        document.addEventListener("visibilitychange", () => {
            if (document.visibilityState === "hidden") {
                console.log("페이지 비활성화: 스레드 종료");
                stopThreads();
                clearInterval(inactivityInterval);
            } else if (document.visibilityState === "visible") {
                console.log("페이지 활성화: 스레드 시작");
                monitorInactivity();
            }
        });
    
        function monitorInactivity() {
            inactivityInterval = setInterval(() => {
                const currentTime = Date.now();
                if (currentTime - lastImageLoadedTime > INACTIVITY_TIMEOUT) {
                    console.warn("비활성화 감지: 스레드 종료");
                    stopThreads();
                    clearInterval(inactivityInterval);
                }
            }, 5000);
        }
    
        monitorInactivity();
    }
    
    // 애니메이션 처리
    function animateImage($img) {
        requestAnimationFrame(() => {
            $img.css("transform", `translateX(${SETTINGS.endPosition}px)`);
        });

        $img.on('transitionend', function () {
            processImage($img);
        });
    }

    function detectPosition() {
        const detectionZone = document.querySelector('.detection-zone');
        const zoneLeft = detectionZone.getBoundingClientRect().left;
        const zoneRight = detectionZone.getBoundingClientRect().right;
    
        function checkPositions() {
            $('.belt img').each(function () {
                const $img = $(this);
                const imgRect = this.getBoundingClientRect();
    
                if (imgRect.left <= zoneRight && imgRect.right >= zoneLeft && !$img.data('processed')) {
                    processImage($img);
                    $img.data('processed', true);
                }
    
                if (imgRect.left > zoneRight && $img.data('processed')) {
                    setTimeout(() => {
                        $img.fadeOut(1000, function () {
                            $(this).remove();
                        });
                    }, 2000);
                }
            });
            requestAnimationFrame(checkPositions);
        }
        requestAnimationFrame(checkPositions);
    }    

    async function addLog(type, message, pltNumber) {
        const logItem = document.createElement('li');
        logItem.className = type === 'warning' ? 'defect' : '';
        logItem.innerHTML = `
            <span class="log-time">[${new Date().toLocaleString('ko-KR')}]</span>
            <span class="log-plt">[PLT: ${pltNumber}]</span>
            ${message}`;

        const logList = document.getElementById('log-list');
        logList.insertBefore(logItem, logList.firstChild);

        while (logList.children.length > LOG_SETTINGS.maxLogItems) {
            logList.removeChild(logList.lastChild);
        }

        try {
            await fetch('/api/logs/logs', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    timestamp: new Date().toISOString(),
                    message: message,
                    pltNumber: pltNumber
                })
            });
        } catch (error) {
            console.error('Kafka 로그 전송 실패:', error);
        }
    }

    // 이미지 처리
    async function processImage($img) {
        const pltNumber = $img.data('plt_number');
        try {
            $img.addClass('processing');

            const res = await fetch('http://5gears.iptime.org:8001/predict/', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ 
                    image_base64: getBase64Data($img.attr('src')),
                    plt_number: pltNumber
                }),
            });

            const result = await res.json();

            // 검사 결과 반영
            updateImageWithResult($img, result, pltNumber);
        } catch (error) {
            console.error('Error during image processing:', error);
            addLog('error', `검사 실패`, pltNumber);
            $img.removeClass('processing');
        }
    }

    function getBase64Data(src) {
        if (src.includes('base64,')) {
            return src.split('base64,')[1];
        }
        throw new Error('Invalid image source format');
    }

    function updateImageWithResult($img, result, pltNumber) {
        requestAnimationFrame(async () => {
            $img.attr('src', `data:image/png;base64,${result.annotated_image}`)
                .removeClass('processing');

            const defect = result.predictions.find(p => p.label === 'Defect');
            if (defect) {
                addLog('warning', '불량품', pltNumber);
                Swal.fire({
                    icon: "warning",
                    title: "불량품 감지!",
                    text: `파이프 번호: ${pltNumber}`,
                    confirmButtonText: "확인",
                    timer: 2000,
                    timerProgressBar: true,
                    customClass: { timerProgressBar: "timer-bar" }
                });

                try {
                    await fetch('/api/slack', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            image_base64: result.annotated_image,
                            label: defect.label,
                            confidence: defect.confidence,
                        }),
                    });
                } catch (slackError) {
                    console.error('Error sending Slack notification:', slackError);
                }
            } else {
                addLog('info', '정상품', pltNumber);
            }
        });
    }
    
    function stopThreads() {
        fetch('/api/images/stop_threads', { method: 'POST' })
            .then(res => {
                if (res.ok) {
                    console.log('스레드가 성공적으로 종료되었습니다.');
                } else {
                    console.error('스레드 종료 실패');
                }
            })
            .catch(err => console.error('스레드 종료 중 오류:', err));
    }

    loadAndAnimateImage();
    setInterval(loadAndAnimateImage, SETTINGS.loadInterval);
    detectPosition();
    detectInactivity();
});