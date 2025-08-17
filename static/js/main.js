document.addEventListener('DOMContentLoaded', function() {
  const startBtn = document.querySelector('.start-btn');
  if (startBtn) {
    startBtn.addEventListener('click', function() {
      const token = localStorage.getItem('access_token');
      if (token) {
        window.location.href = '/mypage_edit';
      } else {
        alert('로그인이 필요합니다.');
        window.location.href = '/login';
      }
    });
  }
}); 