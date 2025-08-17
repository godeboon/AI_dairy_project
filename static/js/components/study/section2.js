console.log('📚 study/section.js 로드됨');

// 전역 함수로 만들어서 언제든지 호출 가능하게
window.checkStudyNotificationStatus = function() {
  console.log('�� study/section.js - 알림 상태 확인');
  
  const notificationStatus = window.globalNotificationManager.checkNotificationStatus('study');
  console.log('📊 알림 상태:', notificationStatus);

  if (!notificationStatus.hasAnyNotification) {
    console.log('�� 활성 알림 없음 - 기본 비활성화 상태로 시작');
    
    // 모니터 비활성화
    const studyOverlayMonitor = document.querySelector('.study-overlay-monitor');
    if (studyOverlayMonitor) {
      studyOverlayMonitor.style.display = 'none';
    }
    
    const blinkElement = document.querySelector('.blink-study-overlay-monitor');
    if (blinkElement) {
      blinkElement.classList.remove('blink');
    }
    
    // 퀘스트 비활성화
    deactivateDiaryQuest();
  } else {
    console.log('✅ 활성 알림 있음 - 이벤트 리스너가 처리할 예정');
  }
};

// 페이지 로드 시 실행 
window.checkStudyNotificationStatus();




// 전역 이벤트 리스너 설정
setupStudyGlobalEventListeners();

// 전역 이벤트 리스너 설정 함수
function setupStudyGlobalEventListeners() {
  // 일기 생성 가능 알림 이벤트 수신
  document.addEventListener('diary_available', function(event) {
    const data = event.detail;
    console.log('📨 study/section.js에서 일기 생성 가능 알림 수신:', data);
    
    // 우선순위별 처리
    if (data.priority === 'high') {
      // AI 생성 버튼 클릭 - 애니메이션 없이
      // showStudyOverlayMonitor();
      activateDiaryQuest();
    } else {
      // Celery 알림 - blink 애니메이션 사용
      showStudyOverlayBlink();
      activateDiaryQuest();
    }
  });

  // 일기 생성 불가능 알림 이벤트 수신
  document.addEventListener('diary_unavailable', function(event) {
    const data = event.detail;
    console.log('📨 study/section.js에서 일기 생성 불가능 알림 수신:', data);
    console.log('🔍 diary_unavailable 이벤트 상세:', {
      priority: data.priority,
      reason: data.reason,
      message: data.message
    });
    
    // blink 애니메이션 제거
    const blinkElement = document.querySelector('.blink-study-overlay-monitor');
    console.log('🎯 blink 요소 검색 결과:', blinkElement);
    
    if (blinkElement) {
      console.log('✨ blink 클래스 제거 시작');
      blinkElement.classList.remove('blink');
      console.log('✅ blink 클래스 제거 완료');
    } else {
      console.warn('⚠️ .blink-study-overlay-monitor 요소를 찾을 수 없습니다');
    }
    
    // 퀘스트 비활성화
    deactivateDiaryQuest();
  });
}
  
  // // 기본 overlay 표시 (애니메이션 없음)
  // function showStudyOverlayMonitor() {
  //   const studyOverlayMonitor = document.querySelector('.study-overlay-monitor');
  //   if (studyOverlayMonitor) {
  //     console.log('✨ 기본 overlay 표시 (애니메이션 없음)');
  //     studyOverlayMonitor.style.display = 'block';
  //   }
  // }
  
  // blink 애니메이션 효과
  function showStudyOverlayBlink() {
    const studyOverlayBlink = document.querySelector('.blink-study-overlay-monitor');
    console.log('🎯 .blink-study-overlay-monitor 요소:', studyOverlayBlink);
    
    if (studyOverlayBlink) {
      console.log('✨ 일기 생성 모니터 반짝임 시작');
      
      // 기존 blink 클래스 제거 (이전 애니메이션 중단)
      studyOverlayBlink.classList.remove('blink');
      
      // 강제로 리플로우 발생시켜 애니메이션 재시작
      studyOverlayBlink.offsetHeight;
      
      // blink 클래스 추가 (무한 반복)
      studyOverlayBlink.classList.add('blink');
    } else {
      console.warn('⚠️ .blink-study-overlay-monitor 요소를 찾을 수 없습니다');
      console.log('🔍 현재 main-content 내용:', document.getElementById('main-content')?.innerHTML?.substring(0, 200));
    }
  }
  
  // 일기 작성 퀘스트 활성화
  function activateDiaryQuest() {
    const diaryQuest = document.querySelector('.quest-box:first-child'); // 첫 번째 퀘스트 (일기 작성)
    if (diaryQuest) {
      // locked 클래스 제거
      diaryQuest.classList.remove('locked');
      
      // 전체 박스 활성화 스타일 추가
      diaryQuest.classList.add('diary-active');
      
      // 버튼 활성화
      const questButton = diaryQuest.querySelector('.quest-action');
      if (questButton) {
        questButton.disabled = false;
        questButton.classList.add('active');
        questButton.textContent = 'ai로 일기 작성하기';
      }
      
      console.log('✅ 일기 작성 퀘스트 활성화');
    } else {
      console.warn('⚠️ 일기 작성 퀘스트를 찾을 수 없습니다');
    }
  }
  
  // 일기 작성 퀘스트 비활성화
  function deactivateDiaryQuest() {
    const diaryQuest = document.querySelector('.quest-box:first-child');
    if (diaryQuest) {
      // locked 클래스 추가
      diaryQuest.classList.add('locked');
      
      // 전체 박스 비활성화 스타일 제거
      diaryQuest.classList.remove('diary-active');
      
      // 버튼 비활성화
      const questButton = diaryQuest.querySelector('.quest-action');
      if (questButton) {
        questButton.disabled = true;
        questButton.classList.remove('active');
        questButton.textContent = '준비 중';
      }
      
      console.log('❌ 일기 작성 퀘스트 비활성화');
    }
  }
  
  // 일기 작성 버튼 클릭 이벤트
  document.addEventListener('click', function(e) {
    if (e.target.classList.contains('diary-write-btn')) {
      console.log('📝 일기 작성 버튼 클릭됨');
      // 일기 생성 페이지로 전환
      loadDiaryGenerateSection();
    }
  });
  
  // 일기 생성 섹션 로드 함수
  function loadDiaryGenerateSection() {
    console.log('📄 일기 생성 섹션 로드 시작');
    // mypage_edit.js의 전역 함수 호출
    window.switchToDiaryGenerateTab();
  }