console.log('📚 study/section2.js 로드됨');



// 전역 함수로 만들어서 언제든지 호출 가능하게
window.checkStudyNotificationStatus = function() {
  console.log('   study/section.js - 알림 상태 확인');
  
  const notificationStatus = window.globalNotificationManager.checkNotificationStatus('study');
  const encourageStatus = window.globalNotificationManager.checkNotificationStatus('study_encourage');
  const sevenDayReportStatus = window.globalNotificationManager.checkNotificationStatus('study_chart');
  
  console.log('📊 diary 알림 상태:', notificationStatus);
  console.log(' encourage 알림 상태:', encourageStatus);
  console.log('📊 seven day report 알림 상태:', sevenDayReportStatus);

  // diary 알림이 없으면 diary 퀘스트 비활성화 처리
  if (!notificationStatus.hasAnyNotification) {
    console.log('✅ diary 활성 알림 없음 - diary 퀘스트 비활성화 상태로 시작');
  }
  
  // encourage 알림이 없으면 encourage 퀘스트 비활성화 처리
  if (!encourageStatus.hasAnyNotification) {
    console.log('✅ encourage 활성 알림 없음 - encourage 퀘스트 비활성화 상태로 시작');
  }
  
  // seven day report 알림이 없으면 seven day report 퀘스트 비활성화 처리
  if (!sevenDayReportStatus.hasAnyNotification) {
    console.log('✅ seven day report 활성 알림 없음 - seven day report 퀘스트 비활성화 상태로 시작');
  }
  
  // 하나의 퀘스트 클릭 이벤트 리스너로 모든 퀘스트 처리
  setupDisabledQuestClickListeners();
};

// 비활성화된 퀘스트 클릭 이벤트 리스너 설정
function setupDisabledQuestClickListeners() {
  document.addEventListener('click', function(e) {
    if (e.target.classList.contains('quest-action') && e.target.classList.contains('disabled')) {
      console.log('🖱️ 비활성화된 퀘스트 버튼 클릭됨:', e.target.getAttribute('data-quest-type'));
      
      const questType = e.target.getAttribute('data-quest-type');
      
      // 첫 번째 버튼(diary) 처리
      if (questType === 'diary') {
        handleDisabledDiaryQuestClick();
      } else if (questType === 'end') { // 응원 퀘스트
        handleDisabledEncourageQuestClick();
      } else if (questType === 'chart') { // seven day report 퀘스트
        handleDisabledSevenDayReportQuestClick();
      }
    }
  });
}




// 전역 이벤트 리스너 설정
setupStudyGlobalEventListeners();

// 페이지 로드 시 실행 
window.checkStudyNotificationStatus();


// 비활성화된 일기 퀘스트 클릭 처리
async function handleDisabledDiaryQuestClick() {
  console.log('�� 비활성화된 일기 퀘스트 클릭됨 - 조건 체크 시작');
  
  try {
    // 조건 체크 API 호출
    const response = await fetch('/study/diary/check-condition', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    const result = await response.json();
    console.log('📊 일기 조건 체크 결과:', result);
    
    // 팝업으로 결과 표시
    if (window.popupManager) {
      window.popupManager.show(result.reason, result.available ? '알림' : '안내');
    } else {
      alert(result.reason);
    }
    
  } catch (error) {
    console.error('❌ 일기 조건 체크 실패:', error);
    if (window.popupManager) {
      window.popupManager.show('일기 생성 조건 확인 중 오류가 발생했습니다.', '오류');
    } else {
      alert('일기 생성 조건 확인 중 오류가 발생했습니다.');
    }
  }
}

// 응원 퀘스트 비활성화 클릭 처리
async function handleDisabledEncourageQuestClick() {
  try {
    const response = await fetch('/study/encourage/check-condition', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    const result = await response.json();
    console.log('📊 응원원 조건 체크 결과:', result);
    
    // 팝업으로 결과 표시
    if (window.popupManager) {
      window.popupManager.show(result.reason, '안내');
    } else {
      alert(result.reason);
    }
    
  } catch (error) {
    console.error('❌ 응원 메시지 조건 체크 실패:', error);
  }
}

// seven day report 퀘스트 비활성화 클릭 처리
async function handleDisabledSevenDayReportQuestClick() {
  console.log('📊 비활성화된 seven day report 퀘스트 클릭됨 - 로컬스토리지 확인');
  
  try {
    // 로컬스토리지에서 기존 데이터 확인
    const existingData = localStorage.getItem('seven_day_report_data');
    
    if (!existingData) {
      // analysis_id가 없으면 데이터 부족 메시지
      console.log('❌ seven day report 데이터 없음 - 데이터 부족 메시지 표시');
      
      if (window.popupManager) {
        window.popupManager.show('일주일 차트 생성하기엔 데이터가 부족합니다.', '안내');
      } else {
        alert('일주일 차트 생성하기엔 데이터가 부족합니다.');
      }
    } else {
      // analysis_id가 있으면 기존 차트 확인 메시지
      try {
        const data = JSON.parse(existingData);
        const startDate = data.week_start_date;
        const endDate = data.week_end_date;
        
        console.log('✅ 기존 seven day report 데이터 발견:', { startDate, endDate });
        
        if (window.popupManager) {
          // 예/아니요 버튼이 있는 커스텀 팝업
          window.popupManager.showConfirm(
            `이미 완성된 ${startDate} ~ ${endDate} 차트가 있습니다. 확인하시겠습니까?`,
            '기존 차트 확인',
            function() {
              // 예 버튼 클릭 시 처리
              console.log('✅ 사용자가 예를 선택함 - 화면 전환 예정');
              // TODO: 화면 전환 로직 (주석 처리)
              loadSevenDayReportSection();
            },
            function() {
              // 아니요 버튼 클릭 시 처리
              console.log('❌ 사용자가 아니요를 선택함 - 팝업 닫기');
              // 팝업은 자동으로 닫힘
            }
          );
        } else {
          // popupManager가 없으면 기본 confirm 사용
          const confirmed = confirm(`이미 완성된 ${startDate} ~ ${endDate} 차트가 있습니다. 확인하시겠습니까?`);
          if (confirmed) {
            console.log('✅ 사용자가 예를 선택함 - 화면 전환 예정');
            // TODO: 화면 전환 로직 (주석 처리)
            loadSevenDayReportSection();
          } else {
            console.log('❌ 사용자가 아니요를 선택함');
          }
        }
      } catch (error) {
        console.error('❌ 기존 데이터 파싱 실패:', error);
        if (window.popupManager) {
          window.popupManager.show('일주일 차트 생성하기엔 데이터가 부족합니다.', '안내');
        } else {
          alert('일주일 차트 생성하기엔 데이터가 부족합니다.');
        }
      }
    }
  } catch (error) {
    console.error('❌ seven day report 조건 체크 실패:', error);
    if (window.popupManager) {
      window.popupManager.show('일주일 차트 조건 확인 중 오류가 발생했습니다.', '오류');
    } else {
      alert('일주일 차트 조건 확인 중 오류가 발생했습니다.');
    }
  }
}




// 전역 이벤트 리스너 설정 함수
function setupStudyGlobalEventListeners() {
  // 일기 생성 가능 알림 이벤트 수신
  document.addEventListener('diary_available', function(event) {
    const data = event.detail;
    console.log('📨 study/section.js에서 일기 생성 가능 알림 수신:', data);
    
    // 우선순위별 처리
    if (data.priority === 'high') {
      activateDiaryQuest();
    } else {
      showStudyOverlayBlink();
      activateDiaryQuest();
    }
  });

  // 일기 생성 불가능 알림 이벤트 수신
  document.addEventListener('diary_unavailable', function(event) {
    const data = event.detail;
    console.log('📨 study/section.js에서 일기 생성 불가능 알림 수신:', data);
    
    // blink 애니메이션 제거
    const blinkElement = document.querySelector('.blink-study-overlay-monitor');
    if (blinkElement) {
      blinkElement.classList.remove('blink');
    }
    
    // 퀘스트 비활성화
    deactivateDiaryQuest();
  });

  // 응원 메시지 가능 알림 이벤트 수신
  document.addEventListener('encourage_available', function(event) {
    const data = event.detail;
    console.log(' study/section.js에서 응원 메시지 알림 수신:', data);
    
    // 편지 반짝임 효과 활성화 + 표시
    showLetterGlow();
    // 응원 퀘스트 활성화
    activateEncourageQuest();
  });

  // 응원 메시지 불가능 알림 이벤트 수신
  document.addEventListener('encourage_unavailable', function(event) {
    const data = event.detail;
    console.log('📨 study/section.js에서 응원 메시지 불가능 알림 수신:', data);
    
    // 편지 반짝임 효과 제거
    hideLetterGlow();
    // 응원 퀘스트 비활성화
    deactivateEncourageQuest();
  });

  // seven day report 알림 이벤트 수신
  document.addEventListener('seven_day_report', function(event) {
    const data = event.detail;
    console.log('📊 study/section.js에서 seven day report 알림 수신:', data);
    
    // seven day report 퀘스트 활성화
    activateSevenDayReportQuest();
  });
}

// blink 애니메이션 효과
function showStudyOverlayBlink() {
  const studyOverlayBlink = document.querySelector('.blink-study-overlay-monitor');
  if (studyOverlayBlink) {
    console.log('✨ 일기 생성 모니터 반짝임 시작');
    
    // 기존 blink 클래스 제거 (이전 애니메이션 중단)
    studyOverlayBlink.classList.remove('blink');
    
    // 강제로 리플로우 발생시켜 애니메이션 재시작
    studyOverlayBlink.offsetHeight;
    
    // blink 클래스 추가 (무한 반복)
    studyOverlayBlink.classList.add('blink');
    
    // 클릭 이벤트 리스너 추가
    studyOverlayBlink.onclick = function() {
      console.log('✨ 반짝이는 모니터 클릭됨 - AI 일기 자동 생성 시작');
      loadDiaryGenerateSection();
    };
  }
}

// 일기 작성 퀘스트 활성화
function activateDiaryQuest() {
  const diaryQuest = document.querySelector('[data-quest-id="diary-quest"]');
  if (diaryQuest) {
    // locked 클래스 제거
    diaryQuest.classList.remove('locked');
    
    // 기존 active 클래스 제거 (이전 애니메이션 중단)
    diaryQuest.classList.remove('active');
    
    // 강제로 리플로우 발생시켜 애니메이션 재시작
    diaryQuest.offsetHeight;
    
    // active 클래스 추가 (무한 반복 애니메이션 시작)
    diaryQuest.classList.add('active');
    
    // 버튼 활성화
    const questButton = diaryQuest.querySelector('.quest-action');
    if (questButton) {
      questButton.disabled = false;
      questButton.classList.remove('disabled');
      questButton.classList.add('active');
      questButton.textContent = 'AI로 일기 작성하기';
      
      // 활성화 상태에서의 클릭 이벤트 설정
      questButton.onclick = function() {
        console.log('✅ 활성화된 일기 퀘스트 클릭 - 페이지 이동');
        loadDiaryGenerateSection();
      };
    }
    
    console.log('✅ 일기 작성 퀘스트 활성화 - quest-glow 애니메이션 시작');
  } else {
    console.warn('⚠️ diary-quest 요소를 찾을 수 없습니다');
  }
}

// 일기 작성 퀘스트 비활성화
function deactivateDiaryQuest() {
  const diaryQuest = document.querySelector('[data-quest-id="diary-quest"]');
  if (diaryQuest) {
    // locked 클래스 추가
    diaryQuest.classList.add('locked');
    
    // 전체 박스 비활성화 스타일 제거
    diaryQuest.classList.remove('active');
    
    // 버튼 비활성화
    const questButton = diaryQuest.querySelector('.quest-action');
    if (questButton) {
      questButton.disabled = false;
      questButton.classList.add('disabled');
      questButton.classList.remove('active');
      questButton.textContent = '준비 중';
      
      // 비활성화 상태에서의 클릭 이벤트 설정
      questButton.onclick = function() {
        console.log('❌ 비활성화된 일기 퀘스트 클릭 - 조건 체크');
        handleDisabledDiaryQuestClick();
      };
    }
    
    console.log('❌ 일기 작성 퀘스트 비활성화');
  }
}







// 기존의 중복된 클릭 이벤트 리스너 제거 - 이제 activateDiaryQuest/deactivateDiaryQuest에서 직접 처리

// 편지 표시 함수 (반짝임 효과 포함)
function showLetterGlow() {
  const letterOverlay = document.querySelector('.letter-overlay-glow');
  if (letterOverlay) {
    letterOverlay.style.display = 'block'; // 편지 표시
    // CSS의 애니메이션은 이미 적용되어 있음 (letter-overlay-glow 클래스)
    
    // 편지 클릭 이벤트 리스너 추가
    letterOverlay.onclick = function() {
      console.log('💌 반짝이는 편지 클릭됨 - 응원 메시지 자동 생성 시작');
      loadEncourageSection();
    };
  }
}

// 편지 숨김 함수
function hideLetterGlow() {
  const letterOverlay = document.querySelector('.letter-overlay-glow');
  if (letterOverlay) {
    letterOverlay.style.display = 'none'; // 편지 숨김
  }
}

// 응원 퀘스트 활성화 (기존 일기 퀘스트와 비슷한 구조)
function activateEncourageQuest() {
  const encourageQuest = document.querySelector('[data-quest-id="end-quest"]');
  if (encourageQuest) {
    // locked 클래스 제거
    encourageQuest.classList.remove('locked');
    
    // 기존 active 클래스 제거 (이전 애니메이션 중단)
    encourageQuest.classList.remove('active');
    
    // 강제로 리플로우 발생시켜 애니메이션 재시작
    encourageQuest.offsetHeight;
    
    // active 클래스 추가 (무한 반복 애니메이션 시작)
    encourageQuest.classList.add('active');
    
    // 버튼 활성화
    const questButton = encourageQuest.querySelector('.quest-action');
    if (questButton) {
      questButton.disabled = false;
      questButton.classList.remove('disabled');
      questButton.classList.add('active');
      questButton.textContent = '응원 메시지 보기';
      
      // 활성화 상태에서의 클릭 이벤트 설정
      questButton.onclick = function() {
        console.log('✅ 활성화된 응원 퀘스트 클릭 - 페이지 이동');
        loadEncourageSection();
      };
    }
    
    console.log('✅ 응원 퀘스트 활성화 - quest-glow 애니메이션 시작');
  } else {
    console.warn('⚠️ end-quest 요소를 찾을 수 없습니다');
  }
}

// 응원 퀘스트 비활성화
function deactivateEncourageQuest() {
  const encourageQuest = document.querySelector('[data-quest-id="end-quest"]');
  if (encourageQuest) {
    // locked 클래스 추가
    encourageQuest.classList.add('locked');
    
    // 전체 박스 비활성화 스타일 제거
    encourageQuest.classList.remove('active');
    
    // 버튼 비활성화
    const questButton = encourageQuest.querySelector('.quest-action');
    if (questButton) {
      questButton.disabled = false;
      questButton.classList.add('disabled');
      questButton.classList.remove('active');
      questButton.textContent = '준비 중';
      
      // 비활성화 상태에서의 클릭 이벤트 설정
      questButton.onclick = function() {
        console.log('❌ 비활성화된 응원 퀘스트 클릭 - 조건 체크');
        handleDisabledEncourageQuestClick();
      };
    }
    
    console.log('❌ 응원 퀘스트 비활성화');
  }
}

// 일기 생성 섹션 로드 함수
function loadDiaryGenerateSection() {
    console.log('📄 일기 생성 섹션 로드 시작');
    
    // 1. mypage_edit.js의 switchToDiaryGenerateTab 함수 호출
    if (window.switchToDiaryGenerateTab) {
        console.log('🔄 일기 생성 페이지로 이동 시작');
        window.switchToDiaryGenerateTab();
        
        // 2. 페이지 로드 후 AI 탭 활성화 (sub_diary_generate.js 로드 대기)
        setTimeout(() => {
            if (window.activateAITabAndGenerate) {
                console.log('✅ AI 탭 활성화 + 자동 생성 실행');
                window.activateAITabAndGenerate();
            } else {
                console.error('❌ activateAITabAndGenerate 함수를 찾을 수 없습니다');
            }
        }, 500); // sub_diary_generate.js 로드 시간 고려
    } else {
        console.error('❌ switchToDiaryGenerateTab 함수를 찾을 수 없습니다');
    }
}

// 응원 섹션 로드 함수
function loadEncourageSection() {
    console.log('💌 응원 섹션 로드 시작');
    
    // 1. mypage_edit.js의 switchToEncourageTab 함수 호출
    if (window.switchToEncourageTab) {
        console.log('🔄 응원 페이지로 이동 시작');
        window.switchToEncourageTab();
        
        // 2. 페이지 로드 후 응원 버튼 클릭 (encourage.js 로드 대기)
        setTimeout(() => {
            if (window.handleEncourageClick) {
                console.log('✅ 응원 버튼 자동 클릭 실행');
                window.handleEncourageClick();
            } else {
                console.error('❌ handleEncourageClick 함수를 찾을 수 없습니다');
            }
        }, 500); // encourage.js 로드 시간 고려
    } else {
        console.error('❌ switchToEncourageTab 함수를 찾을 수 없습니다');
    }
}

// seven day report 퀘스트 활성화
function activateSevenDayReportQuest() {
  const sevenDayReportQuest = document.querySelector('[data-quest-id="chart-quest"]');
  if (sevenDayReportQuest) {
    // locked 클래스 제거
    sevenDayReportQuest.classList.remove('locked');
    
    // 기존 active 클래스 제거 (이전 애니메이션 중단)
    sevenDayReportQuest.classList.remove('active');
    
    // 강제로 리플로우 발생시켜 애니메이션 재시작
    sevenDayReportQuest.offsetHeight;
    
    // active 클래스 추가 (무한 반복 애니메이션 시작)
    sevenDayReportQuest.classList.add('active');
    
    // 버튼 활성화
    const questButton = sevenDayReportQuest.querySelector('.quest-action');
    if (questButton) {
      questButton.disabled = false;
      questButton.classList.remove('disabled');
      questButton.classList.add('active');
      questButton.textContent = '확인하기';
      
      // 활성화 상태에서의 클릭 이벤트 설정
      questButton.onclick = function() {
        console.log('✅ 활성화된 seven day report 퀘스트 클릭 - 페이지 이동');
        loadSevenDayReportSection();
      };
    }
    
    console.log('✅ seven day report 퀘스트 활성화 - quest-glow 애니메이션 시작');
  } else {
    console.warn('⚠️ chart-quest 요소를 찾을 수 없습니다');
  }
}

// seven day report 섹션 로드 함수
function loadSevenDayReportSection() {
  console.log('📊 seven day report 섹션 로드 시작');
  
  // mypage_edit.js의 일주일 차트 서브탭으로 이동
  if (window.switchToSevenChartTab) {
    console.log('🔄 일주일 차트 페이지로 이동 시작');
    window.switchToSevenChartTab();
  } else {
    console.error('❌ switchToSevenChartTab 함수를 찾을 수 없습니다');
  }
}
