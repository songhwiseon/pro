$(document).ready(function() {
    $('#loginForm').on('submit', function(e) {
        e.preventDefault();
        
        const id = $('#id').val();
        const pw = $('#pw').val();
        
        $.ajax({
            type: 'POST',
            url: '/api/login/login',
            contentType: 'application/json',
            data: JSON.stringify({
                id: id,
                pw: pw
            }),
            success: function(response) {
                if (response.success) {
                    alert('로그인 성공');
                    // 저장된 리다이렉트 URL 확인
                    const redirectUrl = localStorage.getItem('redirectUrl');
                    if (redirectUrl) {
                        localStorage.removeItem('redirectUrl'); // 사용 후 삭제
                        window.location.href = redirectUrl;
                    } else {
                        window.location.href = '/';
                    }
                } else {
                    alert('관리자 계정이 아닙니다.');
                }
            },
            error: function() {
                alert('로그인 처리 중 오류가 발생했습니다.');
            }
        });
    });
});



// 로그인 상태 확인
document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/loginck/check-login')
        .then(response => response.json())
        .then(data => {
            const userNameElement = document.getElementById('user-name');
            const loginButton = document.getElementById('login-btn');
            const logoutButton = document.getElementById('logout-btn');
            
            if (data.isLoggedIn) {
                userNameElement.textContent = data.nickname + '님';
                userNameElement.style.display = 'inline';
                loginButton.style.display = 'none';
                logoutButton.style.display = 'inline';
            } else {
                userNameElement.style.display = 'none';
                loginButton.style.display = 'inline';
                logoutButton.style.display = 'none';
            }
        });
});


// 로그아웃 처리 함수
function handleLogout() {
    fetch('/api/loginck/logout', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/';
        }
    });
}

// 로그인 체크 및 페이지 리다이렉트 함수
function checkLoginAndRedirect(targetUrl) {
    fetch('/api/loginck/check-login')
        .then(response => response.json())
        .then(data => {
            if (data.isLoggedIn) {
                window.location.href = targetUrl;
            } else {
                alert('로그인 후 사용해주세요.');
                // 현재 페이지 URL을 로컬 스토리지에 저장
                localStorage.setItem('redirectUrl', targetUrl);
                window.location.href = '/login';
            }
        });
}
