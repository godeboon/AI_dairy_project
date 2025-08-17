// 일기 생성 컴포넌트 초기화
function initDiaryGeneration() {
    console.log('📝 일기 생성 컴포넌트 로드됨');
    setupTabNavigation();
    setupEventListeners();
    // loadDiaryList(); // 임시로 주석 처리 (404 에러 방지)
    
    // 전역 이벤트 리스너 등록
    setupStudyGlobalEventListeners();
    
    // AI 버튼은 기본적으로 비활성화 상태 유지
    // WebSocket 메시지 수신 시에만 활성화됨
}

// 전역 함수로 노출 (mypage_edit.js에서 호출)
window.initDiaryGeneration = initDiaryGeneration;

// 탭 네비게이션 설정
function setupTabNavigation() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            
            // 활성 탭 변경
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            button.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
        });
    });
}

// 이벤트 리스너 설정
function setupEventListeners() {
    console.log('🔧 이벤트 리스너 설정 시작');
    
    // 직접 작성 저장 버튼
    const saveDiaryBtn = document.getElementById('save-diary-btn');
    if (saveDiaryBtn) {
        saveDiaryBtn.addEventListener('click', saveManualDiary);
        console.log('✅ 저장 버튼 이벤트 리스너 등록됨');
    }
    
    // AI 생성 버튼 - 비활성화 상태에서도 클릭 이벤트 처리
    const generateDiaryBtn = document.getElementById('generate-diary-btn');
    console.log('🔍 AI 생성 버튼 찾기:', generateDiaryBtn);
    
    if (generateDiaryBtn) {
        console.log('✅ AI 생성 버튼 이벤트 리스너 등록 시작');
        
        // 버튼의 활성화 상태를 추적하는 변수
        let isButtonActive = false;
        
        // 전역 상태 변수들
        let currentDiaryState = 'unknown'; // 'available', 'unavailable', 'unknown'
        let lastReceivedMessage = null;
        
        generateDiaryBtn.addEventListener('click', function(e) {
            console.log('🖱️ AI 생성 버튼 클릭됨!');
            console.log('버튼 활성화 상태:', isButtonActive);
            
            // 비활성화 상태일 때 라우터 호출로 최종 확인
            if (!isButtonActive) {
                console.log('❌ 버튼이 비활성화 상태 - 라우터 호출로 최종 확인');
                e.preventDefault();
                
                // 라우터에서 최종 확인
                fetch('/study/diary/generate/stream', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    }
                }).then(response => {
                    if (!response.ok) {
                        return response.json().then(errorData => {
                            const errorMessage = errorData.detail;
                            
                            // 라우터에서 받은 정확한 에러 메시지 표시
                            if (window.popupManager) {
                                window.popupManager.show(errorMessage, "알림");
                            } else {
                                alert(errorMessage);
                            }
                        });
                    }
                }).catch(error => {
                    console.error('라우터 호출 실패:', error);
                });
                return;
            }
            // 활성화 상태일 때만 실제 AI 생성 실행
            console.log('✅ 버튼이 활성화 상태 - AI 생성 실행');
            generateAIDiary();
        });
        
        // 버튼 활성화 함수 (내부에서만 사용)
        function activateAIGenerateButton() {
            isButtonActive = true;
            generateDiaryBtn.classList.remove('disabled');
            generateDiaryBtn.classList.add('active');
            console.log('✅ AI 생성 버튼 활성화됨');
        }
        
        console.log('✅ AI 생성 버튼 이벤트 리스너 등록 완료');
    } else {
        console.error('❌ AI 생성 버튼을 찾을 수 없습니다!');
    }
    
    // AI 생성 결과 저장 버튼
    const saveGeneratedBtn = document.getElementById('save-generated-btn');
    if (saveGeneratedBtn) {
        saveGeneratedBtn.addEventListener('click', saveGeneratedDiary);
        console.log('✅ AI 생성 결과 저장 버튼 이벤트 리스너 등록됨');
    }
    
    console.log('🔧 이벤트 리스너 설정 완료');
}

// 직접 작성 일기 저장
async function saveManualDiary() {
    const editor = document.getElementById('diary-editor');
    const content = editor.value.trim();
    
    if (!content) {
        alert('일기 내용을 입력해주세요.');
        return;
    }
    
    try {
        const response = await fetch('/study/user/diary/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify({
                content: content,
                source_type: 'manual'
            })
        });
        
        if (response.ok) {
            alert('일기가 저장되었습니다!');
            editor.value = '';
            loadDiaryList(); // 목록 새로고침
        } else {
            const errorData = await response.json();
            const errorMessage = errorData.detail || '일기 저장에 실패했습니다.';
            
            // 팝업으로 에러 메시지 표시
            if (window.popupManager) {
                window.popupManager.show(errorMessage, "알림");
            } else {
                alert(errorMessage);
            }
        }
    } catch (error) {
        console.error('일기 저장 오류:', error);
        alert('일기 저장 중 오류가 발생했습니다.');
    }
}

// AI 일기 생성 (스트리밍)
async function generateAIDiary() {
    const indicator = document.getElementById('generation-indicator');
    const generatedText = document.getElementById('ai-generated-text');
    const saveGeneratedBtn = document.getElementById('save-generated-btn');
    const generateBtn = document.getElementById('generate-diary-btn');
    
    // UI 상태 변경
    generateBtn.disabled = true;
    indicator.classList.remove('hidden');
    generatedText.textContent = '';
    saveGeneratedBtn.classList.add('hidden');
    
    try {
        const response = await fetch('/study/diary/generate/stream', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            const errorMessage = errorData.detail || 'AI 생성 요청 실패';
            
            // 팝업으로 에러 메시지 표시
            if (window.popupManager) {
                window.popupManager.show(errorMessage, "알림");
            } else {
                alert(errorMessage);
            }
            return;
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            const chunk = decoder.decode(value);
            fullText += chunk;
            
            // 실시간으로 텍스트 표시
            generatedText.textContent = fullText;
            generatedText.scrollTop = generatedText.scrollHeight;
        }
        
        // 생성 완료 후 저장 버튼 표시
        saveGeneratedBtn.classList.remove('hidden');
        
    } catch (error) {
        console.error('AI 생성 오류:', error);
        alert('AI 일기 생성 중 오류가 발생했습니다.');
    } finally {
        // UI 상태 복원
        generateBtn.disabled = false;
        indicator.classList.add('hidden');
    }
}

// AI 생성 결과 저장
async function saveGeneratedDiary() {
    const generatedText = document.getElementById('ai-generated-text');
    const content = generatedText.textContent.trim();
    
    if (!content) {
        alert('저장할 내용이 없습니다.');
        return;
    }
    
    try {
        const response = await fetch('/study/user/diary/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify({
                content: content,
                source_type: 'ai'
            })
        });
        
        if (response.ok) {
            alert('AI 생성 일기가 저장되었습니다!');
            generatedText.textContent = '';
            document.getElementById('save-generated-btn').classList.add('hidden');
            loadDiaryList(); // 목록 새로고침
        } else {
            alert('일기 저장에 실패했습니다.');
        }
    } catch (error) {
        console.error('일기 저장 오류:', error);
        alert('일기 저장 중 오류가 발생했습니다.');
    }
}

// 일기 목록 로드
async function loadDiaryList() {
    const diaryList = document.getElementById('diary-list');
    
    try {
        const response = await fetch('/study/diary/list', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const diaries = await response.json();
            renderDiaryList(diaries);
        } else {
            diaryList.innerHTML = '<p class="no-diaries">일기가 없습니다.</p>';
        }
    } catch (error) {
        console.error('일기 목록 로드 오류:', error);
        diaryList.innerHTML = '<p class="no-diaries">일기 목록을 불러오는데 실패했습니다.</p>';
    }
}

// 일기 목록 렌더링
function renderDiaryList(diaries) {
    const diaryList = document.getElementById('diary-list');
    
    if (!diaries || diaries.length === 0) {
        diaryList.innerHTML = '<p class="no-diaries">아직 작성한 일기가 없습니다.</p>';
        return;
    }
    
    const diaryHTML = diaries.map(diary => {
        const date = new Date(diary.timestamp).toLocaleDateString('ko-KR');
        const sourceClass = diary.source_type === 'ai' ? 'ai' : 'manual';
        const sourceText = diary.source_type === 'ai' ? 'AI 생성' : '직접 작성';
        
        return `
            <div class="diary-item">
                <div class="diary-item-header">
                    <span class="diary-date">${date}</span>
                    <span class="diary-source ${sourceClass}">${sourceText}</span>
                </div>
                <div class="diary-content">${diary.content.substring(0, 200)}${diary.content.length > 200 ? '...' : ''}</div>
            </div>
        `;
    }).join('');
    
    diaryList.innerHTML = diaryHTML;
}

// 전역 이벤트 리스너 설정
function setupStudyGlobalEventListeners() {
    // diary_available 이벤트 리스너
    document.addEventListener('diary_available', function(event) {
        const data = event.detail;
        console.log('📨 일기 생성 컴포넌트에서 diary_available 이벤트 수신:', data);
        activateAIGenerateButton();
    });
    
    // diary_unavailable 이벤트 리스너
    document.addEventListener('diary_unavailable', function(event) {
        const data = event.detail;
        console.log('📨 일기 생성 컴포넌트에서 diary_unavailable 이벤트 수신:', data);
        deactivateAIGenerateButton();
        if (data.reason) {
            window.diaryUnavailableReason = data.reason;
        }
    });
}

// 버튼 활성화 함수
function activateAIGenerateButton() {
    const generateBtn = document.getElementById('generate-diary-btn');
    if (generateBtn) {
        generateBtn.classList.remove('disabled');
        generateBtn.classList.add('active');
        window.isButtonActive = true;
        console.log('✅ AI 생성 버튼 활성화');
    }
}

// 버튼 비활성화 함수
function deactivateAIGenerateButton() {
    const generateBtn = document.getElementById('generate-diary-btn');
    if (generateBtn) {
        generateBtn.classList.add('disabled');
        generateBtn.classList.remove('active');
        window.isButtonActive = false;
        console.log('❌ AI 생성 버튼 비활성화');
    }
}


// 자정 리셋은 mypage_edit.js에서 전역 관리됨

// 전역 함수로 등록
window.initDiaryGeneration = initDiaryGeneration; 