console.log('🚀 space/section.js 로드 시작');

// 카드 클릭 이벤트 리스너 등록
const spaceCards = document.querySelectorAll('.space-card');
console.log('🎯 찾은 카드 개수:', spaceCards.length);

spaceCards.forEach((card, index) => {
  console.log(`🎴 카드 ${index + 1} 이벤트 리스너 등록`);
  card.addEventListener('click', function() {
    const cardTitle = this.querySelector('.space-card-title').textContent.trim();
    console.log('🖱️ 카드 클릭됨:', cardTitle);
    
    // 카드 제목에 따라 해당 메인 탭으로 이동
    switch(cardTitle) {
      case '대화하기':
        navigateToTab('chatting');
        break;
      case '서재':
        navigateToTab('study');
        break;
      case '텃밭':
        navigateToTab('garden');
        break;
      case '리포트':
        navigateToTab('constellation');
        break;
      default:
        console.log('알 수 없는 카드:', cardTitle);
    }
  });
});

// 메인 탭으로 이동하는 함수
function navigateToTab(tabName) {
  console.log(`🔍 ${tabName} 탭 찾는 중...`);
  // 해당 메인 탭 요소 찾기
  const targetTab = document.querySelector(`[data-tab="${tabName}"]`);
  
  if (targetTab) {
    console.log(`✅ ${tabName} 탭 찾음, 클릭 트리거`);
    // 메인 탭 클릭 이벤트 트리거
    targetTab.click();
    console.log(`${tabName} 탭으로 이동 완료`);
  } else {
    console.error(`❌ ${tabName} 탭을 찾을 수 없습니다.`);
  }
}