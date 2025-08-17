// 팝업 컴포넌트 관리
class PopupManager {
  constructor() {
    this.popupOverlay = document.getElementById('popup-overlay');
    this.popupMessage = document.getElementById('popup-message');
    this.closeBtn = document.getElementById('popup-close-btn');
    this.confirmBtn = document.getElementById('popup-confirm-btn');
    
    this.setupEventListeners();
  }

  setupEventListeners() {
    // 닫기 버튼 클릭
    this.closeBtn.addEventListener('click', () => {
      this.hide();
    });

    // 확인 버튼 클릭
    this.confirmBtn.addEventListener('click', () => {
      this.hide();
    });

    // 배경 클릭 시 닫기
    this.popupOverlay.addEventListener('click', (e) => {
      if (e.target === this.popupOverlay) {
        this.hide();
      }
    });

    // ESC 키로 닫기
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isVisible()) {
        this.hide();
      }
    });
  }

  show(message, title = '알림') {
    this.popupMessage.textContent = message;
    document.querySelector('.popup-title').textContent = title;
    this.popupOverlay.style.display = 'flex';
    
    // 포커스 트랩
    this.closeBtn.focus();
  }

  hide() {
    this.popupOverlay.style.display = 'none';
  }

  isVisible() {
    return this.popupOverlay.style.display === 'flex';
  }
}

// 전역 팝업 매니저 인스턴스
window.popupManager = new PopupManager();

// 팝업 표시 함수 (외부에서 사용)
function showPopup(message, title = '알림') {
  window.popupManager.show(message, title);
} 