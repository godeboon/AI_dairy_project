// constellation/report.js - 성격 리포트 관리
console.log('🌟 constellation/report.js 로드됨');

// 서버 API 호출 - 성격 리포트 데이터 가져오기
async function fetchPersonalityReportData(reportId) {
  try {
    console.log('🔄 성격 리포트 데이터 요청 시작:', reportId);
    
    const response = await fetch(`/personality-report/${reportId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ 성격 리포트 데이터 수신:', data);
      
      // 로컬스토리지에 저장
      localStorage.setItem('personality_report_data', JSON.stringify(data));
      
      // 리포트 렌더링
      renderPersonalityReport(data);
    } else {
      console.error('❌ 성격 리포트 데이터 요청 실패:', response.status);
    }
  } catch (error) {
    console.error('❌ 성격 리포트 데이터 가져오기 실패:', error);
  }
}

// 리포트 렌더링 함수
function renderPersonalityReport(data) {
  console.log('🎨 성격 리포트 렌더링 시작:', data);
  
  try {
    // 첫 번째 박스: 정서적 패턴
    const topBox = document.querySelector('.constellation-report-box.top-box');
    if (topBox) {
      topBox.innerHTML = `
        <div class="report-content">
          <h3>정서적 패턴</h3>
          <p>${data.emotional_pattern}</p>
        </div>
      `;
    }
    
    // 두 번째 박스: 성향
    const middleBox = document.querySelector('.constellation-report-box.middle-box');
    if (middleBox) {
      middleBox.innerHTML = `
        <div class="report-content">
          <h3>성향</h3>
          <p>${data.personality_tendency}</p>
        </div>
      `;
    }
    
    // 세 번째 박스: 무의식적 통찰
    const bottomBox = document.querySelector('.constellation-report-box.bottom-box');
    if (bottomBox) {
      bottomBox.innerHTML = `
        <div class="report-content">
          <h3>무의식적 통찰</h3>
          <p>${data.unconscious_insight}</p>
        </div>
      `;
    }
    
    console.log('✅ 성격 리포트 렌더링 완료');
  } catch (error) {
    console.error('❌ 리포트 렌더링 실패:', error);
  }
}

// 전역 리스너 등록 (한 번만)
function bindConstellationListenersOnce() {
  if (window.__constellationListenersBound) return;
  window.__constellationListenersBound = true;
  
  console.log('🌟 constellation 리스너 등록됨');
  
  // final_report 알림 리스너
  document.addEventListener('final_report', function(event) {
    const data = event.detail;
    console.log(' final_report 알림 수신:', data);
    
    // 서버에서 데이터 가져오기
    fetchPersonalityReportData(data.report_id);
  });
}

// 초기화 함수 - 탭 진입 시 호출
window.initConstellationUI = function() {
  bindConstellationListenersOnce();  // 리스너 보장
  
  console.log(' constellation UI 초기화 시작');
  
  // 기존 데이터가 있으면 리포트 렌더링
  const existingData = localStorage.getItem('personality_report_data');
  if (existingData) {
    try {
      const data = JSON.parse(existingData);
      console.log(' 기존 데이터 발견, 리포트 렌더링:', data);
      renderPersonalityReport(data);
    } catch (error) {
      console.error('❌ 기존 데이터 파싱 실패:', error);
    }
  } else {
    // 기존 데이터가 없으면 로딩 상태 유지
    console.log('🌟 기존 리포트 데이터 없음, 로딩 상태 유지');
    // HTML의 기본 로딩 메시지가 그대로 표시됨
  }
  
  // WebSocket 알림 상태 복원
  if (window.globalNotificationManager) {
    console.log('📤 constellation 서브탭 - WebSocket 알림 상태 복원');
    window.globalNotificationManager.restoreNotifications('constellation');
  }
  
  console.log('✅ constellation UI 초기화 완료');
};

console.log('✅ constellation/report.js 초기화 완료');
