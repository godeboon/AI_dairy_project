// --- 그대로 유지 ---
function typewriterEffect(text, element) {
  if (!element) return;
  element.innerHTML = '';
  let i = 0;
  (function type() {
    if (i < text.length) {
      element.innerHTML += text.charAt(i++);
      setTimeout(type, 50);
    }
  })();
}

function renderEncourageFromLocalStorage() {
  const messageElement = document.getElementById('encourage-message');
  const content = localStorage.getItem('encourage_content');
  const timestamp = localStorage.getItem('encourage_timestamp');

  if (content && timestamp && messageElement) {
    messageElement.innerHTML = content;
    messageElement.style.display = 'block';
    console.log('✅ 로컬스토리지에서 응원 메시지 렌더링 완료');
  }
}

// ✅ 추가: 오늘 날짜 비교(로컬 타임존 기준)
function isToday(ts) {
  if (!ts) return false;
  const d1 = new Date(ts);
  const d2 = new Date();
  const toYMD = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  return toYMD(d1) === toYMD(d2);
}

// ✅ 전역 1회 바인딩 가드
window.__encourageListenersBound = window.__encourageListenersBound || false;

// ✅ 클릭 처리(위임)
async function handleEncourageClick() {
  const btn = document.getElementById('encourage-btn');
  const msg = document.getElementById('encourage-message');
  if (!btn) return;

  // 비활성 상태이면 안내만
  if (btn.classList.contains('disabled') || btn.getAttribute('aria-disabled') === 'true') {
    // ✅ 변경: 로컬스토리지에 "오늘 생성한" 메시지가 있으면 해당 문구로 안내
    const content = localStorage.getItem('encourage_content');
    const ts = localStorage.getItem('encourage_timestamp');
    const alreadyToday = content && ts && isToday(ts);

    const show = window.popupManager
      ? (m,t) => window.popupManager.show(m, t)
      : (m) => alert(m);

    if (alreadyToday) {
      show("오늘 생성한 응원메세지가 있습니다.", "안내");
    } else {
      show("오늘 응원 메시지 생성하기엔 채팅이 부족합니다.", "안내");
    }
    return;
  }

  try {
    const res = await fetch('/study/encourage', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    if (!res.ok) {
      console.error('응원 메시지 조회 실패');
      return;
    }
    const data = await res.json();
    localStorage.setItem('encourage_content', data.encourage_content);
    localStorage.setItem('encourage_timestamp', new Date().toISOString());

    const messageEl = document.getElementById('encourage-message');
    typewriterEffect(data.encourage_content, messageEl);
  } catch (e) {
    console.error('응원 메시지 요청 오류:', e);
  }
}

// 전역으로 노출
window.handleEncourageClick = handleEncourageClick;

// ✅ 전역 리스너를 "한 번만" 등록 + 항상 현재 DOM 재조회
function bindEncourageGlobalListenersOnce() {
  if (window.__encourageListenersBound) return;
  window.__encourageListenersBound = true;

  console.log('[encourage] global listeners bound');

  // (캡처 단계) 문서 레벨 클릭 위임: stopPropagation에도 안전
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('#encourage-btn');
    if (!btn) return;
    console.log('[encourage] (capture) click on #encourage-btn');
    handleEncourageClick();
  }, { capture: true });

  // 알림 도착: 항상 최신 DOM을 조회해 활성화
  document.addEventListener('encourage_available', () => {
    const btn = document.getElementById('encourage-btn');
    if (!btn) return;
    btn.classList.remove('disabled');
    btn.classList.add('active');
    btn.setAttribute('aria-disabled', 'false'); // 접근성
  });

  // 알림 불가: 비활성 + 저장된 메시지 렌더
  document.addEventListener('encourage_unavailable', () => {
    const btn = document.getElementById('encourage-btn');
    if (!btn) return;
    btn.classList.remove('active');
    btn.classList.add('disabled');
    btn.setAttribute('aria-disabled', 'true');
    renderEncourageFromLocalStorage();
  });
}

// ✅ 탭 진입 시: 전역 리스너 보장 + 현재 상태 동기화
window.initEncourageUI = function() {
  bindEncourageGlobalListenersOnce();

  const status = window.globalNotificationManager?.checkNotificationStatus('study_encourage') || {};
  const btn = document.getElementById('encourage-btn');
  if (btn) {
    if (status.hasAnyNotification) {
      btn.classList.remove('disabled');
      btn.classList.add('active');
      btn.setAttribute('aria-disabled', 'false');
    } else {
      btn.classList.remove('active');
      btn.classList.add('disabled');
      btn.setAttribute('aria-disabled', 'true');
    }

    // (보강) 직접 바인딩 1회 — 혹시 위임이 막힐 때 대비
    // if (!btn.dataset.encourageBound) {
    //   btn.addEventListener('click', () => {
    //     console.log('[encourage] (direct) click on #encourage-btn');
    //     handleEncourageClick();
    //   });
    //   btn.dataset.encourageBound = '1';
    // }

    // 버튼이 폼 안에 있을 수 있으니 안전하게
    if (!btn.hasAttribute('type')) btn.setAttribute('type', 'button');
  }

  renderEncourageFromLocalStorage();
};

// ❌ 최상단 자동 호출(과거 setupEncourageEventListeners)은 더 이상 없음
