// 차트 팝업 컴포넌트 관리
export class ChartPopupManager {
  constructor() {
    this.popupOverlay = null;
    this.popupContainer = null;
    this.closeBtn = null;
    this.diaryData = null;
    
    this.init();
  }

  init() {
    this.createPopupElements();
    this.setupEventListeners();
  }

  createPopupElements() {
    // 팝업 오버레이 생성
    this.popupOverlay = document.createElement('div');
    this.popupOverlay.className = 'chart-popup-overlay';
    this.popupOverlay.id = 'chart-popup-overlay';

    // 팝업 컨테이너 생성
    this.popupContainer = document.createElement('div');
    this.popupContainer.className = 'chart-popup-container';
    this.popupContainer.id = 'chart-popup-container';

    // 팝업 헤더 생성
    const header = document.createElement('div');
    header.className = 'chart-popup-header';

    const title = document.createElement('h3');
    title.className = 'chart-popup-title';
    title.textContent = '일일 감정 분석';

    this.closeBtn = document.createElement('button');
    this.closeBtn.className = 'chart-popup-close-btn';
    this.closeBtn.innerHTML = '×';
    this.closeBtn.setAttribute('aria-label', '닫기');

    header.appendChild(title);
    header.appendChild(this.closeBtn);

    // 팝업 콘텐츠 영역 생성
    const content = document.createElement('div');
    content.className = 'chart-popup-content';
    content.id = 'chart-popup-content';

    this.popupContainer.appendChild(header);
    this.popupContainer.appendChild(content);
    this.popupOverlay.appendChild(this.popupContainer);

    // DOM에 추가
    document.body.appendChild(this.popupOverlay);
  }

  setupEventListeners() {
    // 닫기 버튼 클릭
    this.closeBtn.addEventListener('click', () => {
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

  show(diaryData) {
    this.diaryData = diaryData;
    this.renderContent();
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

  renderContent() {
    const content = document.getElementById('chart-popup-content');
    
    if (!this.diaryData) {
      content.innerHTML = '<p>데이터를 불러올 수 없습니다.</p>';
      return;
    }

    const { date_str, emotions, scores, keywords, keyword_descriptions, summary } = this.diaryData;

    // 날짜 표시
    const dateDisplay = this.formatDate(date_str);
    
    // 감정과 점수 매칭
    const emotionItems = emotions.map((emotion, index) => {
      const score = scores[index];
      const scoreText = score >= 0 ? `+${score.toFixed(1)}` : score.toFixed(1);
      return `<span class="chart-popup-emotion-item">${emotion} (${scoreText})</span>`;
    }).join('');

    // 키워드와 설명 매칭
    const keywordItems = keywords.map((keyword, index) => {
      const description = keyword_descriptions[index] || '';
      return `
        <div class="chart-popup-keyword-item">
          <div class="chart-popup-keyword-title">${keyword}</div>
          <div class="chart-popup-keyword-desc">${description}</div>
        </div>
      `;
    }).join('');

    content.innerHTML = `
      <div class="chart-popup-date">${dateDisplay}</div>
      
      <div class="chart-popup-section">
        <div class="chart-popup-section-title"> 감정</div>
        <div class="chart-popup-emotions">
          ${emotionItems}
        </div>
      </div>

      <div class="chart-popup-section">
        <div class="chart-popup-section-title"> 키워드 </div>
        <div class="chart-popup-keywords">
          ${keywordItems}
        </div>
      </div>

      <div class="chart-popup-section">
        <div class="chart-popup-summary">
          <div class="chart-popup-summary-title"> 하루 </div>
          <div class="chart-popup-summary-text">${summary}</div>
        </div>
      </div>
    `;
  }

  formatDate(dateStr) {
    if (!dateStr) return '날짜 정보 없음';
    
    try {
      const date = new Date(dateStr);
      const year = date.getFullYear();
      const month = date.getMonth() + 1;
      const day = date.getDate();
      
      const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
      const weekday = weekdays[date.getDay()];
      
      return `${year}년 ${month}월 ${day}일 (${weekday})`;
    } catch (e) {
      return dateStr;
    }
  }
}

// 차트 팝업 매니저 인스턴스 (모듈 내부에서만)
let chartPopupManager = null;

// 차트 팝업 표시 함수 (외부에서 사용)
export function showChartPopup(diaryData) {
  if (!chartPopupManager) {
    chartPopupManager = new ChartPopupManager();
  }
  chartPopupManager.show(diaryData);
}
