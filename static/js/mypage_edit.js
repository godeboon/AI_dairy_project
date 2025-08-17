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
      console.log('🔍 메시지 상세:', {
        type: data.type,
        priority: data.priority,
        reason: data.reason,
        message: data.message
      });
      
      // 전역 알림 관리자에 저장 (우선순위 처리 포함)
      window.globalNotificationManager.storeNotification(data);
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

  // 전역 알림 관리자 초기화
  window.globalNotificationManager = {
    storedNotifications: {},
    
    // 페이지 로드 시 localStorage에서 복원
    initializeFromStorage() {
      const savedNotifications = localStorage.getItem('notifications');
      if (savedNotifications) {
        this.storedNotifications = JSON.parse(savedNotifications);
        console.log('📦 localStorage에서 알림 복원:', this.storedNotifications);
      }
    },
    
    // 메시지 저장 (우선순위 기반)
    storeNotification(data) {
      console.log('📦 전역 알림 관리자 - 메시지 저장 시작:', data);
      const key = data.type; // 'diary_available' 또는 'diary_unavailable'
      
      if (this.storedNotifications[key]) {
        const existing = this.storedNotifications[key];
        console.log('📊 기존 저장된 알림:', existing);
        
        // 우선순위가 높으면 무조건 업데이트
        if (data.priority === 'high' && existing.priority !== 'high') {
          console.log('🔄 우선순위 높은 메시지로 업데이트');
          this.updateNotification(key, data);
        }
        // 우선순위가 같으면 최신 것으로 업데이트
        else if (data.priority === existing.priority) {
          console.log('🔄 최신 메시지로 업데이트');
          this.updateNotification(key, data);
        }
        // 우선순위가 낮으면 무시
        else {
          console.log('❌ 우선순위 낮아서 무시');
          return;
        }
      } else {
        // 첫 번째 메시지면 저장
        console.log('📝 첫 번째 메시지 저장');
        this.updateNotification(key, data);
      }
    },
    
    // 알림 업데이트 (우선순위 처리 완료된 것만 localStorage에 저장)
    updateNotification(key, data) {
      console.log('🔄 알림 업데이트 중:', key, data);
      
      this.storedNotifications[key] = {
        ...data,
        timestamp: Date.now(),
        isActive: true
      };
      
      // localStorage에 저장 (우선순위 처리 완료된 것만)
      localStorage.setItem('notifications', JSON.stringify(this.storedNotifications));
      console.log('💾 localStorage에 알림 저장 완료');
      
      // study 관련 알림이면 즉시 전송
      if (data.type === 'diary_available' || data.type === 'diary_unavailable' || data.type === 'encourage_available') {
        this.dispatchToAllComponents(data);
      }
    },
    
    // 모든 컴포넌트로 전역 전달
    dispatchToAllComponents(data) {
      console.log(`📤 전역으로 ${data.type} 알림 전달 시작:`, data);
      const customEvent = new CustomEvent(data.type, { detail: data });
      document.dispatchEvent(customEvent);
      console.log(`✅ 전역으로 ${data.type} 알림 전달 완료`);
    },
    
    // 페이지 전환 시 복원
    restoreNotifications(page) {
      console.log('🔄 페이지 전환 시 알림 복원 시작:', page);
      console.log('📦 현재 저장된 모든 알림:', this.storedNotifications);
      
      if (page === 'study') {
        // diary_available 복원
        const availableNotification = this.storedNotifications['diary_available'];
        if (availableNotification && availableNotification.isActive) {
          console.log('✅ diary_available 알림 복원:', availableNotification);
          this.dispatchToAllComponents(availableNotification);
        } else {
          console.log('❌ diary_available 알림 없음 또는 비활성');
        }
        
        // diary_unavailable도 복원
        const unavailableNotification = this.storedNotifications['diary_unavailable'];
        if (unavailableNotification && unavailableNotification.isActive) {
          console.log('✅ diary_unavailable 알림 복원:', unavailableNotification);
          this.dispatchToAllComponents(unavailableNotification);
        } else {
          console.log('❌ diary_unavailable 알림 없음 또는 비활성');
        }
        
        // encourage_available 복원
        const encourageNotification = this.storedNotifications['encourage_available'];
        if (encourageNotification && encourageNotification.isActive) {
          console.log('✅ encourage_available 알림 복원:', encourageNotification);
          this.dispatchToAllComponents(encourageNotification);
        } else {
          console.log('❌ encourage_available 알림 없음 또는 비활성');
        }
        
        // encourage_unavailable 복원
        const encourageUnavailableNotification = this.storedNotifications['encourage_unavailable'];
        if (encourageUnavailableNotification && encourageUnavailableNotification.isActive) {
          console.log('✅ encourage_unavailable 알림 복원:', encourageUnavailableNotification);
          this.dispatchToAllComponents(encourageUnavailableNotification);
        } else {
          console.log('❌ encourage_unavailable 알림 없음 또는 비활성');
        }
      }
    },
    
    // 특정 알림 제거
    clearNotification(type) {
      console.log(`🗑️ 알림 제거: ${type}`);
      if (this.storedNotifications[type]) {
        delete this.storedNotifications[type];
        // localStorage에서도 제거
        localStorage.setItem('notifications', JSON.stringify(this.storedNotifications));
        console.log(`✅ ${type} 알림 제거 완료 (localStorage 포함)`);
      } else {
        console.log(`❌ ${type} 알림이 존재하지 않음`);
      }
    },
    
    // 알림 상태 확인 (전역 함수)
    checkNotificationStatus(page) {
      console.log('🔍 알림 상태 확인:', page);
      
      if (page === 'study') {
        const availableNotification = this.storedNotifications['diary_available'];
        const unavailableNotification = this.storedNotifications['diary_unavailable'];
        
        return {
          hasAvailable: availableNotification && availableNotification.isActive,
          hasUnavailable: unavailableNotification && unavailableNotification.isActive,
          hasAnyNotification: (availableNotification && availableNotification.isActive) || 
                             (unavailableNotification && unavailableNotification.isActive)
        };
      }
      
      if (page === 'study_encourage') {
        const encourageAvailableNotification = this.storedNotifications['encourage_available'];
        const encourageUnavailableNotification = this.storedNotifications['encourage_unavailable'];
      
        return {
          hasEncourage: encourageAvailableNotification && encourageAvailableNotification.isActive,
          hasUnavailable: encourageUnavailableNotification && encourageUnavailableNotification.isActive,
          hasAnyNotification: (encourageAvailableNotification && encourageAvailableNotification.isActive) || 
                             (encourageUnavailableNotification && encourageUnavailableNotification.isActive)
        };
      }
    }
  };





  // 전역 알림 관리자 초기화 (localStorage에서 복원)
  window.globalNotificationManager.initializeFromStorage();

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

  // 동적 영역 지정 
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
    fetch('/templates/components/study/section.html')
      .then(res => res.text())
      .then(html => {
        mainContent.innerHTML = html;
        
        // section.js 로딩 완료 대기 후 알림 복원
        setTimeout(() => {
          window.globalNotificationManager.restoreNotifications('study');
        }, 200);

        
        // study/section.js 로드 (section.js에서 자동으로 알림 상태 체크)
        import('/static/js/components/study/section.js');
      });
    
    // CSS 동적 로드 (이미 링크되어 있지 않으면)
    if (!document.querySelector('link[href="/static/css/components/study/section.css"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = '/static/css/components/study/section.css';
      document.head.appendChild(link);
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
      
      // 나의 텃밭 클릭 시 콘텐츠 전환
      if (e.target.textContent.trim() === '나의 텃밭') {
        fetch('/templates/components/garden/section.html')
          .then(res => res.text())
          .then(html => {
            mainContent.innerHTML = html;
            import('/static/js/components/garden/section.js');
          });
      }

      // 나의 서재 클릭 시 콘텐츠 전환
      if (e.target.textContent.trim() === '나의 서재') {
        fetch('/templates/components/study/section.html')
          .then(res => res.text())
          .then(html => {
            mainContent.innerHTML = html;
            import('/static/js/components/study/section.js').then(() => {
              // WebSocket 알림 상태 복원
              console.log('📤 나의 서재 서브탭 - WebSocket 알림 상태 복원');
              window.globalNotificationManager.restoreNotifications('study');
              
              // 상태 체크 함수 호출
              if (window.checkStudyNotificationStatus) {
                window.checkStudyNotificationStatus();
              }
            });
          });
      }


      // 일기생성 클릭 시 콘텐츠 전환
      if (e.target.textContent.trim() === '일기생성') {
        switchToDiaryGenerateTab();
      }

      // 하루의 마무리 클릭 시 콘텐츠 전환
      if (e.target.textContent.trim() === '하루의 마무리') {
        switchToEncourageTab();
      }



    }
  });

  // 일기생성 서브탭 전환 함수
  function switchToDiaryGenerateTab() {
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
          
          // WebSocket 알림 상태 복원
          console.log('📤 일기생성 서브탭 - WebSocket 알림 상태 복원');
          window.globalNotificationManager.restoreNotifications('study');
          
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

  // 하루의 마무리 서브탭 전환 함수
  function switchToEncourageTab() {
    console.log('하루의 마무리 서브 탭 클릭됨');
    fetch('/templates/components/study/encourage.html')
      .then(res => {
        console.log('encourage.html 응답 상태:', res.status);
        return res.text();
      })
      .then(html => {
        console.log('encourage.html 로드됨');
        mainContent.innerHTML = html;

        // ✅ 1) 모듈 import
        import('/static/js/components/study/encourage.js')
          .then(() => {
            // ✅ 2) 리스너 보장 + 즉시 상태 동기화
            if (window.initEncourageUI) {
              window.initEncourageUI();
            }

            // ✅ 3) (리스너 준비된 상태에서) 복원 이벤트 전파
            console.log('📤 하루의 마무리 서브탭 - WebSocket 알림 상태 복원');
            window.globalNotificationManager.restoreNotifications('study');
          })
          .catch(err => {
            console.error('encourage.js 로드 실패:', err);
          });
      })
      .catch(err => {
        console.error('encourage.html 로드 실패:', err);
      });
  }

  // diary_reset 이벤트 리스너 추가
  document.addEventListener('diary_reset', function(event) {
    const data = event.detail;
    console.log('🕛 diary_reset 이벤트 수신:', data);
    
    // 전역 알림 관리자에서 diary_unavailable 제거
    if (window.globalNotificationManager) {
      window.globalNotificationManager.clearNotification('diary_unavailable');
    }
    
    // 전역 상태 초기화
    window.diaryUnavailableReason = null;
        window.lastCheckedDate = new Date().toLocaleDateString('ko-KR');
    
    console.log('✅ 자정 리셋 완료 - diary_unavailable 상태 제거');
  });

  // 전역으로 노출
  window.switchToDiaryGenerateTab = switchToDiaryGenerateTab;
  window.switchToEncourageTab = switchToEncourageTab;
}); 
