// 채팅 목록 전용 JS
let currentPage = 1;
const itemsPerPage = 10;
let allChatDates = [];

// 채팅 목록 초기화 함수
function initChatList() {
  console.log('채팅 목록 JS 로드됨');
  
  // 초기 로드
  loadChatList();
  
  // 이벤트 리스너 등록
  setupEventListeners();
}

// 이벤트 리스너 설정 함수
function setupEventListeners() {
  // 이전 페이지 버튼 이벤트
  document.addEventListener('click', function(e) {
    if (e.target.id === 'prev-btn' && currentPage > 1) {
      currentPage--;
      renderChatList();
    }
  });
  
  // 다음 페이지 버튼 이벤트
  document.addEventListener('click', function(e) {
    if (e.target.id === 'next-btn') {
      const totalPages = Math.ceil(allChatDates.length / itemsPerPage);
      if (currentPage < totalPages) {
        currentPage++;
        renderChatList();
      }
    }
  });
  
  // 채팅 아이템 클릭 이벤트
  document.addEventListener('click', function(e) {
    if (e.target.closest('.chat-item')) {
      const chatItem = e.target.closest('.chat-item');
      const chatDate = chatItem.getAttribute('data-date');
      console.log('채팅 선택됨:', chatDate);
      
      // 선택된 채팅으로 이동하는 로직
      loadChatHistory(chatDate);
    }
  });
}

// 채팅 목록 로드 함수
async function loadChatList() {
  try {
    const token = localStorage.getItem("access_token");
    console.log('토큰 확인:', token ? '토큰 있음' : '토큰 없음');
    
    if (!token) {
      console.error('토큰이 유효하지 않습니다.');
      return;
    }
    
    const headers = {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    };
    
    console.log('API 호출 시작: /chat/list');
    const response = await fetch("/chat/list", {
      method: "GET",
      headers
    });
    
    console.log('API 응답 상태:', response.status);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('API 응답 데이터:', data);
    
    allChatDates = data.chat_dates || [];
    
    console.log('채팅 목록 로드됨:', allChatDates);
    renderChatList();
    
  } catch (error) {
    console.error('채팅 목록 로드 실패:', error);
  }
}

// 채팅 목록 렌더링 함수
function renderChatList() {
  const chatListContainer = document.getElementById('chat-list');
  if (!chatListContainer) {
    console.error('chat-list 요소를 찾을 수 없습니다.');
    return;
  }
  
  console.log('채팅 목록 렌더링 시작');
  
  // 페이지네이션 계산
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentPageItems = allChatDates.slice(startIndex, endIndex);
  
  console.log('현재 페이지 아이템:', currentPageItems);
  
  // 기존 내용 클리어
  chatListContainer.innerHTML = '';
  
  if (currentPageItems.length === 0) {
    chatListContainer.innerHTML = '<div class="no-chats">채팅 기록이 없습니다.</div>';
    return;
  }
  
  // 채팅 아이템 생성
  currentPageItems.forEach(date => {
    const chatItem = document.createElement('div');
    chatItem.className = 'chat-item';
    chatItem.setAttribute('data-date', date);
    
    // 날짜 포맷팅 (YYYY-MM-DD를 YYYY년 MM월 DD일로 변환)
    const formattedDate = formatDate(date);
    
    chatItem.innerHTML = `
      <div class="chat-date">${formattedDate}</div>
    `;
    
    chatListContainer.appendChild(chatItem);
  });
  
  // 페이지네이션 업데이트
  updatePagination();
  
  console.log('채팅 목록 렌더링 완료');
}

// 날짜 포맷팅 함수
function formatDate(dateStr) {
  // KST 기준으로 날짜 포맷팅
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  return `${year}년 ${month}월 ${day}일`;
}

// 페이지네이션 업데이트 함수
function updatePagination() {
  const totalPages = Math.ceil(allChatDates.length / itemsPerPage);
  const pageInfo = document.getElementById('page-info');
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');
  
  if (pageInfo) {
    pageInfo.textContent = `${currentPage}/${totalPages}`;
  }
  
  if (prevBtn) {
    prevBtn.disabled = currentPage <= 1;
    prevBtn.style.opacity = currentPage <= 1 ? '0.5' : '1';
  }
  
  if (nextBtn) {
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.style.opacity = currentPage >= totalPages ? '0.5' : '1';
  }
}

// 채팅 히스토리 로드 함수
async function loadChatHistory(date) {
  try {
    const token = localStorage.getItem("access_token");
    if (!token) {
      console.error('토큰이 없습니다.');
      return;
    }
    
    const headers = {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    };
    
    const response = await fetch("/chat/history", {
      method: "POST",
      headers,
      body: JSON.stringify({ date: date })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    const messages = data.messages || [];
    
    console.log('채팅 히스토리 로드됨:', messages);
    
    // 채팅 대화 내용 표시
    showChatHistory(date, messages);
    
  } catch (error) {
    console.error('채팅 히스토리 로드 실패:', error);
  }
}

// 채팅 대화 내용 표시 함수
function showChatHistory(date, messages) {
  // 기존 채팅 목록 컨테이너 숨기기
  const chatListContainer = document.querySelector('.chat-list-container');
  if (chatListContainer) {
    chatListContainer.style.display = 'none';
  }
  
  // 채팅 대화 내용을 표시할 컨테이너 생성
  let chatHistoryContainer = document.getElementById('chat-history-container');
  if (!chatHistoryContainer) {
    chatHistoryContainer = document.createElement('div');
    chatHistoryContainer.id = 'chat-history-container';
    chatHistoryContainer.className = 'chat-history-container';
    document.querySelector('.chat-list-container').parentNode.appendChild(chatHistoryContainer);
  }
  
  // 날짜 포맷팅
  const formattedDate = formatDate(date);
  
  // 채팅 대화 내용 HTML 생성
  chatHistoryContainer.innerHTML = `
    <div class="chat-outer">
      <div id="chat-header">
        <button class="back-btn" onclick="goBackToList()">← 목록으로</button>
        <div id="chat-date">${formattedDate}</div>
      </div>
      <h2>채팅하기</h2>
      <div class="chat-main">
        <div id="chat-box">
          ${messages.map(msg => `
            <div class="bubble ${msg.role}">${msg.message}</div>
          `).join('')}
        </div>
        <div id="input-box">
          <textarea id="input-field" rows="2" placeholder="메시지를 입력하세요..."></textarea>
          <button type="button">전송</button>
        </div>
      </div>
    </div>
  `;
  
  // 채팅 박스 스크롤을 맨 아래로
  const chatBox = chatHistoryContainer.querySelector('#chat-box');
  if (chatBox) {
    chatBox.scrollTop = chatBox.scrollHeight;
  }
}

// 목록으로 돌아가기 함수 (전역 함수로 등록)
window.goBackToList = function() {
  const chatHistoryContainer = document.getElementById('chat-history-container');
  if (chatHistoryContainer) {
    chatHistoryContainer.remove();
  }
  
  const chatListContainer = document.querySelector('.chat-list-container');
  if (chatListContainer) {
    chatListContainer.style.display = 'block';
  }
};

// 전역 함수로 등록
window.initChatList = initChatList; 