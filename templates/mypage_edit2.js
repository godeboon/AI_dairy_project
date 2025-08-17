document.addEventListener('DOMContentLoaded', function() {
  // WebSocket 연결 관리
  let ws = null;
  let userId = null;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 10;
  const reconnectDelay = 3000; // 3초

  // 사용자 ID 가져오기 (localStorage에서)
  function getCurrentUserId() {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      console.error('❌ access_token이 없습니다');
      return null;
    }
    
    try {
      // JWT 토큰에서 user_id 추출
      const payload = JSON.parse(atob(accessToken.split('.')[1]));
      console.log('✅ 사용자 ID 추출:', payload.user_id);
      return payload.user_id;
    } catch (error) {
      console.error('❌ 토큰 파싱 실패:', error);
      return null;
    }
  }

  // WebSocket 연결 상태 확인
  function isWebSocketConnected() {
    return ws && ws.readyState === WebSocket.OPEN;
  }

  // WebSocket 연결
  function connectWebSocket() {
    userId = getCurrentUserId();
    if (!userId) {
      console.error('❌ 사용자 ID를 가져올 수 없어 WebSocket 연결을 건너뜁니다');
      return;
    }

    // 기존 연결이 있으면 닫기
    if (ws) {
      ws.close();
    }

    console.log(`🔗 WebSocket 연결 시도: user_id=${userId}`);
    ws = new WebSocket(`ws://localhost:8000/ws/${userId}`);
    
    ws.onopen = function() {
      console.log('✅ WebSocket 연결됨');
      reconnectAttempts = 0; // 연결 성공 시 재시도 횟수 초기화
    };
    
    ws.onmessage = function(event) {
      const data = JSON.parse(event.data);
      console.log('📨 WebSocket 메시지 수신:', data);
      
      // 모든 메시지에 대한 기본 로그
      console.log('🔍 메시지 타입 확인:', data.type);
      console.log('🎯 타겟 확인:', data.target);
      
      // 일기 생성 알림 처리
      if (data.type === 'diary_available' && data.target === 'blink-study-overlay-monitor') {
        console.log('✨ 일기 생성 알림 수신 - 반짝임 효과 실행');
        console.log('🔍 현재 페이지 요소 확인 중...');
        
        // 현재 페이지의 모든 요소 확인
        const allElements = document.querySelectorAll('*');
        console.log('📊 현재 페이지 요소 수:', allElements.length);
        
       // blink-study-overlay-monitor 요소 찾기 (반짝임 효과용)
      const studyOverlayBlink = document.querySelector('.blink-study-overlay-monitor');
      console.log('🎯 .blink-study-overlay-monitor 요소:', studyOverlayBlink);
      
      if (studyOverlayBlink) {
        console.log('✅ 요소 발견 - 반짝임 효과 시작');
        showStudyOverlayBlink();
      } else {
        console.warn('⚠️ .blink-study-overlay-monitor 요소를 찾을 수 없습니다');
        console.log('🔍 현재 main-content 내용:', document.getElementById('main-content')?.innerHTML?.substring(0, 200));
      }
        
        activateDiaryQuest(); // 퀘스트 활성화 추가
        
        // 일기 생성 컴포넌트에도 메시지 전달
        const customEvent = new CustomEvent('websocket-message', { detail: data });
        document.dispatchEvent(customEvent);
      } else {
        console.log('❌ 조건문 불일치 - 반짝임 효과 실행 안됨');
        console.log('🔍 조건 확인:', {
          'data.type === diary_available': data.type === 'diary_available',
          'data.target === blink-study-overlay-monitor': data.target === 'blink-study-overlay-monitor'
        });
      }
    };
    
    ws.onclose = function(event) {
      console.log('❌ WebSocket 연결 해제됨:', event.code, event.reason);
      
      // 정상적인 종료가 아닌 경우에만 재연결 시도
      if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
        console.log(`🔄 재연결 시도 ${reconnectAttempts + 1}/${maxReconnectAttempts}`);
        setTimeout(connectWebSocket, reconnectDelay);
        reconnectAttempts++;
      } else if (reconnectAttempts >= maxReconnectAttempts) {
        console.error('❌ 최대 재연결 시도 횟수 초과');
      }
    };
    
    ws.onerror = function(error) {
      console.error('❌ WebSocket 에러:', error);
    };
  }

  // 일기 생성 모니터 반짝임 효과
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
    } else {
      console.warn('⚠️ .blink-study-overlay-monitor 요소를 찾을 수 없습니다');
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
        questButton.textContent = '작성하기';
      }
      
      console.log('✅ 일기 작성 퀘스트 활성화');
    }
  }

  // 일기 작성 버튼 클릭 이벤트
  document.addEventListener('click', function(e) {
    if (e.target.classList.contains('diary-write-btn')) {
      // 일기 생성 페이지로 전환
      loadDiaryGenerateSection();
    }
  });


  // 일기 생성 섹션 로드 함수
  function loadDiaryGenerateSection() {
    fetch('/templates/components/study/sub_diary_generate.html')
      .then(res => res.text())
      .then(html => {
        document.getElementById('main-content').innerHTML = html;
        // 일기 생성 컴포넌트 JS 로드
        import('/static/js/components/study/sub_diary_generate.js').then(() => {
          if (window.initDiaryGeneration) window.initDiaryGeneration();
        });
      });
    
    // CSS 동적 로드 (이미 링크되어 있지 않으면)
    if (!document.querySelector('link[href="/static/css/components/study/sub_diary_generate.css"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = '/static/css/components/study/sub_diary_generate.css';
      document.head.appendChild(link);
    }
  }

  // WebSocket 연결 시작
  connectWebSocket();

  // X 버튼 동작
  const closeBtn = document.getElementById('close-dashboard-btn');
  if (closeBtn) {
    closeBtn.addEventListener('click', function() {
      document.querySelectorAll('.main-tab').forEach(tab => tab.classList.remove('active'));
      document.querySelectorAll('.sub-tab').forEach(tab => tab.classList.remove('active'));
      window.location.href = '/';
    });
  }

  const mainTabs = document.querySelectorAll('.main-tab');
  const mainContent = document.getElementById('main-content');
  const subTabs = document.querySelector('.sub-tabs');

  // 공간 탭 콘텐츠 로드 함수
  function loadSpaceSection() {
    fetch('/templates/components/space/section.html')
      .then(res => res.text())
      .then(html => {
        mainContent.innerHTML = html;
      });
  }

  // 서재 탭 콘텐츠 로드 함수
  function loadStudySection() {
    // CSS를 먼저 로드하고 완료될 때까지 기다림
    if (!document.querySelector('link[href="/static/css/components/study/section.css"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = '/static/css/components/study/section.css';
      document.head.appendChild(link);
      
      // CSS 로딩 완료 후 HTML 로드
      link.onload = () => {
        fetch('/templates/components/study/section.html')
          .then(res => res.text())
          .then(html => {
            mainContent.innerHTML = html;
            import('/static/js/components/study/section.js').then(() => {
              // section.js 로드 완료 후 상태 체크 함수 호출
              if (window.checkStudyNotificationStatus) {
                window.checkStudyNotificationStatus();
              }
            });
          });
      };
    } else {
      // 이미 CSS가 로드되어 있으면 바로 HTML 로드
      fetch('/templates/components/study/section.html')
        .then(res => res.text())
        .then(html => {
          mainContent.innerHTML = html;
          import('/static/js/components/study/section.js').then(() => {
            // section.js 로드 완료 후 상태 체크 함수 호출
            if (window.checkStudyNotificationStatus) {
              window.checkStudyNotificationStatus();
            }
          });
        });
    }
  }

  // 채팅하기 탭 콘텐츠 로드 함수
  function loadChattingSection() {
    fetch('/templates/components/chatting/section.html')
      .then(res => res.text())
      .then(html => {
        mainContent.innerHTML = html;
        import('/static/js/components/chatting/section.js').then(() => {
          if (window.initChattingSection) window.initChattingSection();
        });
      });
  }

  // 텃밭 탭 콘텐츠 로드 함수
  function loadGardenSection() {
    fetch('/templates/components/garden/section.html')
      .then(res => res.text())
      .then(html => {
        mainContent.innerHTML = html;
        import('/static/js/components/garden/section.js');
      });
  }

// 서브탭 로드 함수 

  function updateSubTabs(tab) {
    if (!subTabs) return;
    if (tab === 'garden') {
      subTabs.innerHTML = `
        <div class="sub-tab">알림</div>
        <div class="sub-tab active">나의 텃밭</div>
        <div class="sub-tab">씨앗 심기</div>
        <div class="sub-tab">씨앗 가꾸기</div>
      `;
    } else if (tab === 'chatting') {
      subTabs.innerHTML = `
        <div class="sub-tab">알림</div>
        <div class="sub-tab active">대화하기</div>
        <div class="sub-tab">채팅목록</div>
      `;

    } else if (tab === 'study') {
      subTabs.innerHTML = `
        <div class="sub-tab">알림</div>
        <div class="sub-tab active">나의 서재</div>
        <div class="sub-tab">일기생성</div>
        <div class="sub-tab">일주일 차트</div>
        <div class="sub-tab">하루의 마무리</div>
      `;


    } else {
      subTabs.innerHTML = `<div class="sub-tab">알림</div>`;
    }
  }

                              





  // 항상 '공간' 탭이 기본 active + 콘텐츠 로드
  if (mainTabs.length > 0) {
    mainTabs.forEach(tab => tab.classList.remove('active'));
    const spaceTab = document.querySelector('.main-tab[data-tab="space"]');
    if (spaceTab) spaceTab.classList.add('active');
    loadSpaceSection();
    updateSubTabs('space');
  }

  // 탭 클릭 시 active 전환 및 콘텐츠/서브탭 변경
  mainTabs.forEach(tab => {
    tab.addEventListener('click', function() {
      mainTabs.forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      if (this.dataset.tab === 'space') {
        loadSpaceSection();
        updateSubTabs('space');
      } else if (this.dataset.tab === 'study') {
        loadStudySection();
        updateSubTabs('study');
      } else if (this.dataset.tab === 'chatting') {
        loadChattingSection();
        updateSubTabs('chatting');
      } else if (this.dataset.tab === 'garden') {
        loadGardenSection();
        updateSubTabs('garden');
      } else {
        mainContent.innerHTML = '';
        updateSubTabs();
      }
      // 서브탭 active 해제는 updateSubTabs에서 처리됨
    });
  });

  // 서브탭 클릭 시 active 처리 및 콘텐츠 전환
  document.addEventListener('click', function(e) {
    if (e.target.classList.contains('sub-tab')) {
      document.querySelectorAll('.sub-tab').forEach(tab => tab.classList.remove('active'));
      e.target.classList.add('active');
      // 씨앗 심기 클릭 시 콘텐츠 전환
      if (e.target.textContent.trim() === '씨앗 심기') {
        fetch('/templates/components/garden/sub_seed_made.html')
          .then(res => res.text())
          .then(html => {
            mainContent.innerHTML = html;
            import('/static/js/components/garden/sub_seed_made.js');
          });
        // CSS 동적 로드 (이미 링크되어 있지 않으면)
        if (!document.querySelector('link[href="/static/css/components/garden/sub_seed_made.css"]')) {
          const link = document.createElement('link');
          link.rel = 'stylesheet';
          link.href = '/static/css/components/garden/sub_seed_made.css';
          document.head.appendChild(link);
        }
      }
      
      // 대화하기 클릭 시 콘텐츠 전환
      if (e.target.textContent.trim() === '대화하기') {
        fetch('/templates/components/chatting/section.html')
          .then(res => res.text())
          .then(html => {
            mainContent.innerHTML = html;
            import('/static/js/components/chatting/section.js').then(() => {
              if (window.initChattingSection) window.initChattingSection();
            });
          });

      }
      
      // 채팅목록 클릭 시 콘텐츠 전환
      if (e.target.textContent.trim() === '채팅목록') {
        console.log('채팅목록 서브 탭 클릭됨');
        fetch('/templates/components/chatting/sub_chat_list.html')
          .then(res => {
            console.log('sub_chat_list.html 응답 상태:', res.status);
            return res.text();
          })
          .then(html => {
            console.log('sub_chat_list.html 로드됨');
            mainContent.innerHTML = html;
            console.log('sub_chat_list.js 로드 시작');
            import('/static/js/components/chatting/sub_chat_list.js').then(() => {
              console.log('sub_chat_list.js 로드 완료');
              // 초기화 함수 호출
              if (window.initChatList) {
                console.log('initChatList 함수 호출');
                window.initChatList();
              } else {
                console.error('initChatList 함수를 찾을 수 없습니다.');
              }
            }).catch(err => {
              console.error('sub_chat_list.js 로드 실패:', err);
            });
          })
          .catch(err => {
            console.error('sub_chat_list.html 로드 실패:', err);
          });


        // CSS 동적 로드 (이미 링크되어 있지 않으면)
        if (!document.querySelector('link[href="/static/css/components/chatting/sub_chat_list.css"]')) {
          const link = document.createElement('link');
          link.rel = 'stylesheet';
          link.href = '/static/css/components/chatting/sub_chat_list.css';
          document.head.appendChild(link);
        }





      }
      
      // 나의 텃밭밭 클릭 시 콘텐츠 전환
      if (e.target.textContent.trim() === '나의 텃밭') {
        fetch('/templates/components/garden/section.html')
          .then(res => res.text())
          .then(html => {
            mainContent.innerHTML = html;
            import('/static/js/components/garden/section.js');
          });
      }


      // 나의 서재재 클릭 시 콘텐츠 전환
      if (e.target.textContent.trim() === '나의 서재') {
        fetch('/templates/components/study/section.html')
          .then(res => res.text())
          .then(html => {
            mainContent.innerHTML = html;
            import('/static/js/components/study/section.js');
          });
      }
      







      // 일기생성 클릭 시 콘텐츠 전환
      if (e.target.textContent.trim() === '일기생성') {
        console.log('일기생성 서브 탭 클릭됨');
        fetch('/templates/components/study/sub_diary_generate.html')
          .then(res => {
            console.log('sub_diary_generate.html 응답 상태:', res.status);
            return res.text();
          })
          .then(html => {
            console.log('sub_diary_generate.html 로드됨');
            mainContent.innerHTML = html;
            console.log('sub_diary_generate.js 로드 시작');
            import('/static/js/components/study/sub_diary_generate.js').then(() => {
              console.log('sub_diary_generate.js 로드 완료');
              // 초기화 함수 호출
              if (window.initDiaryGeneration) {
                console.log('initDiaryGeneration 함수 호출');
                window.initDiaryGeneration();
              } else {
                console.error('initDiaryGeneration 함수를 찾을 수 없습니다.');
              }
            }).catch(err => {
              console.error('sub_diary_generate.js 로드 실패:', err);
            });
          })
          .catch(err => {
            console.error('sub_diary_generate.html 로드 실패:', err);
          });

        // CSS 동적 로드 (이미 링크되어 있지 않으면)
        if (!document.querySelector('link[href="/static/css/components/study/sub_diary_generate.css"]')) {
          const link = document.createElement('link');
          link.rel = 'stylesheet';
          link.href = '/static/css/components/study/sub_diary_generate.css';
          document.head.appendChild(link);
        }
      }
    }
  });
}); 