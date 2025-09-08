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

  showConfirm(message, title = '확인', onConfirm, onCancel) {
    this.popupMessage.textContent = message;
    document.querySelector('.popup-title').textContent = title;
    
    // 확인/취소 버튼 표시
    this.confirmBtn.style.display = 'inline-block';
    this.closeBtn.innerHTML = '&times;'; // X 표시로 변경
    
    // 이벤트 리스너 설정
    const handleConfirm = () => {
      this.hide();
      if (onConfirm) onConfirm();
      this.confirmBtn.removeEventListener('click', handleConfirm);
      this.closeBtn.removeEventListener('click', handleCancel);
    };
    
    const handleCancel = () => {
      this.hide();
      if (onCancel) onCancel();
      this.confirmBtn.removeEventListener('click', handleConfirm);
      this.closeBtn.removeEventListener('click', handleCancel);
    };
    
    this.confirmBtn.addEventListener('click', handleConfirm);
    this.closeBtn.addEventListener('click', handleCancel);
    
    this.popupOverlay.style.display = 'flex';
    this.confirmBtn.focus();
  }

  hide() {
    this.popupOverlay.style.display = 'none';
    
    // 버튼 상태 초기화
    this.closeBtn.innerHTML = '&times;'; // X 표시로 초기화
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