// 일기 생성 컴포넌트 초기화 (간단 버전)
function initDiaryGeneration() {
    console.log('📝 일기 생성 컴포넌트 로드됨 (간단 버전)');
    setupTabNavigation();
    setupEventListeners();
}

// 전역 함수로 노출
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
            
            // 일기 목록 탭이 활성화되면 자동으로 로드
            if (targetTab === 'list') {
                loadDiaryList();
            }
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
    
    // AI 생성 버튼 - 무조건 서버 호출
    const generateDiaryBtn = document.getElementById('generate-diary-btn');
    console.log('🔍 AI 생성 버튼 찾기:', generateDiaryBtn);
    
    if (generateDiaryBtn) {
        console.log('✅ AI 생성 버튼 이벤트 리스너 등록 시작');
        
        generateDiaryBtn.addEventListener('click', function(e) {
            console.log('🖱️ AI 생성 버튼 클릭됨!');
            
            // 무조건 서버 호출
            fetch('/study/diary/generate/stream', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            }).then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => {
                        const errorMessage = errorData.detail;
                        
                        // 서버에서 오는 detail 메시지를 그대로 popup으로 표시
                        if (window.popupManager) {
                            window.popupManager.show(errorMessage, "알림");
                        } else {
                            alert(errorMessage);
                        }
                    });
                }
                // 성공 시 스트리밍 처리
                console.log('✅ AI 생성 요청 성공 - 스트리밍 시작');
                handleStreamingResponse(response);
            }).catch(error => {
                console.error('AI 생성 요청 실패:', error);
                if (window.popupManager) {
                    window.popupManager.show('AI 생성 요청 중 오류가 발생했습니다.', "알림");
                } else {
                    alert('AI 생성 요청 중 오류가 발생했습니다.');
                }
            });
        });
        
        console.log('✅ AI 생성 버튼 이벤트 리스너 등록 완료');
    } else {
        console.error('❌ AI 생성 버튼을 찾을 수 없습니다!');
    }
    
    // AI 생성 결과 저장 버튼 제거 (AI 생성 시 자동 저장됨)
    // const saveGeneratedBtn = document.getElementById('save-generated-btn');
    // if (saveGeneratedBtn) {
    //     saveGeneratedBtn.addEventListener('click', saveGeneratedDiary);
    //     console.log('✅ AI 생성 결과 저장 버튼 이벤트 리스너 등록됨');
    // }
    
    console.log('🔧 이벤트 리스너 설정 완료');
}

// 스트리밍 응답 처리
async function handleStreamingResponse(response) {
    const indicator = document.getElementById('generation-indicator');
    const generatedText = document.getElementById('ai-generated-text');
    const generateBtn = document.getElementById('generate-diary-btn');
    
    // UI 상태 변경
    generateBtn.disabled = true;
    indicator.classList.remove('hidden');
    generatedText.textContent = '';
    
    try {
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
        
        // 생성 완료 후 성공 메시지 표시
        if (window.popupManager) {
            window.popupManager.show('AI 일기 생성이 완료되었습니다!', "알림");
        } else {
            alert('AI 일기 생성이 완료되었습니다!');
        }
        
    } catch (error) {
        console.error('스트리밍 처리 오류:', error);
        if (window.popupManager) {
            window.popupManager.show('AI 일기 생성 중 오류가 발생했습니다.', "알림");
        } else {
            alert('AI 일기 생성 중 오류가 발생했습니다.');
        }
    } finally {
        // UI 상태 복원
        generateBtn.disabled = false;
        indicator.classList.add('hidden');
    }
}

// 직접 작성 일기 저장
async function saveManualDiary() {
    const editor = document.getElementById('diary-editor');
    const content = editor.value.trim();
    
    if (!content) {
        if (window.popupManager) {
            window.popupManager.show('일기 내용을 입력해주세요.', "알림");
        } else {
            alert('일기 내용을 입력해주세요.');
        }
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
            if (window.popupManager) {
                window.popupManager.show('일기가 저장되었습니다!', "알림");
            } else {
                alert('일기가 저장되었습니다!');
            }
            editor.value = '';
            loadDiaryList(); // 목록 새로고침
        } else {
            const errorData = await response.json();
            const errorMessage = errorData.detail || '일기 저장에 실패했습니다.';
            
            // 서버에서 오는 detail 메시지를 그대로 popup으로 표시
            if (window.popupManager) {
                window.popupManager.show(errorMessage, "알림");
            } else {
                alert(errorMessage);
            }
        }
    } catch (error) {
        console.error('일기 저장 오류:', error);
        if (window.popupManager) {
            window.popupManager.show('일기 저장 중 오류가 발생했습니다.', "알림");
        } else {
            alert('일기 저장 중 오류가 발생했습니다.');
        }
    }
}

// AI 생성 결과 저장 함수 제거 (AI 생성 시 자동 저장됨)
// async function saveGeneratedDiary() {
//     // AI 생성 시 자동으로 저장되므로 별도 저장 버튼 불필요
// }

// 일기 목록 로드
async function loadDiaryList() {
    const userDiaryList = document.getElementById('user-diary-list');
    const aiDiaryList = document.getElementById('ai-diary-list');
    
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
            userDiaryList.innerHTML = '<p class="no-diaries">일기가 없습니다.</p>';
            aiDiaryList.innerHTML = '<p class="no-diaries">일기가 없습니다.</p>';
        }
    } catch (error) {
        console.error('일기 목록 로드 오류:', error);
        userDiaryList.innerHTML = '<p class="no-diaries">일기 목록을 불러오는데 실패했습니다.</p>';
        aiDiaryList.innerHTML = '<p class="no-diaries">일기 목록을 불러오는데 실패했습니다.</p>';
    }
}

// 일기 목록 렌더링 (좌우 분할)
function renderDiaryList(diaries) {
    const userDiaryList = document.getElementById('user-diary-list');
    const aiDiaryList = document.getElementById('ai-diary-list');
    
    if (!diaries || diaries.length === 0) {
        userDiaryList.innerHTML = '<p class="no-diaries">아직 작성한 일기가 없습니다.</p>';
        aiDiaryList.innerHTML = '<p class="no-diaries">아직 작성한 일기가 없습니다.</p>';
        return;
    }
    
    // source_type에 따라 분리
    const userDiaries = diaries.filter(diary => diary.source_type === 'user');
    const aiDiaries = diaries.filter(diary => diary.source_type === 'ai');
    
    // 사용자 일기 렌더링
    if (userDiaries.length === 0) {
        userDiaryList.innerHTML = '<p class="no-diaries">직접 작성한 일기가 없습니다.</p>';
    } else {
        const userDiaryHTML = userDiaries.map(diary => {
            const date = new Date(diary.timestamp).toLocaleDateString('ko-KR');
            return `
                <div class="diary-item" data-diary-id="${diary.id}">
                    <div class="diary-date">${date}</div>
                </div>
            `;
        }).join('');
        userDiaryList.innerHTML = userDiaryHTML;
    }
    
    // AI 일기 렌더링
    if (aiDiaries.length === 0) {
        aiDiaryList.innerHTML = '<p class="no-diaries">AI 생성한 일기가 없습니다.</p>';
    } else {
        const aiDiaryHTML = aiDiaries.map(diary => {
            const date = new Date(diary.timestamp).toLocaleDateString('ko-KR');
            return `
                <div class="diary-item" data-diary-id="${diary.id}">
                    <div class="diary-date">${date}</div>
                </div>
            `;
        }).join('');
        aiDiaryList.innerHTML = aiDiaryHTML;
    }
    
    // 일기 아이템 클릭 이벤트 추가
    setupDiaryItemClickEvents();
}

// 일기 아이템 클릭 이벤트 설정
function setupDiaryItemClickEvents() {
    const diaryItems = document.querySelectorAll('.diary-item');
    
    diaryItems.forEach(item => {
        item.addEventListener('click', () => {
            const diaryId = item.getAttribute('data-diary-id');
            showDiaryDetail(diaryId);
        });
    });
}

// 일기 상세보기 표시 (템플릿 전환)
async function showDiaryDetail(diaryId) {
    try {
        const response = await fetch(`/study/diary/${diaryId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const diary = await response.json();
            displayDiaryDetail(diary);
        } else {
            if (window.popupManager) {
                window.popupManager.show('일기를 불러오는데 실패했습니다.', "알림");
            } else {
                alert('일기를 불러오는데 실패했습니다.');
            }
        }
    } catch (error) {
        console.error('일기 상세보기 로드 오류:', error);
        if (window.popupManager) {
            window.popupManager.show('일기를 불러오는데 실패했습니다.', "알림");
        } else {
            alert('일기를 불러오는데 실패했습니다.');
        }
    }
}

// 일기 상세보기 화면 표시 (템플릿 전환)
function displayDiaryDetail(diary) {
    const listView = document.getElementById('diary-list-view');
    const detailView = document.getElementById('diary-detail-view');
    const dateElement = document.getElementById('diary-detail-date');
    const timeElement = document.getElementById('diary-detail-time');
    const textElement = document.getElementById('diary-detail-text');
    
    // 날짜 표시
    const date = new Date(diary.timestamp);
    dateElement.textContent = date.toLocaleDateString('ko-KR');
    
    // 시간 표시
    timeElement.textContent = date.toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    // 내용 표시
    textElement.textContent = diary.content;
    
    // 화면 전환
    listView.classList.add('hidden');
    detailView.classList.remove('hidden');
    
    // 뒤로가기 버튼 이벤트
    document.getElementById('diary-back-btn').addEventListener('click', goBackToList);
}

// 목록으로 돌아가기
function goBackToList() {
    const listView = document.getElementById('diary-list-view');
    const detailView = document.getElementById('diary-detail-view');
    
    detailView.classList.add('hidden');
    listView.classList.remove('hidden');
}

// 전역 함수로 등록
window.initDiaryGeneration = initDiaryGeneration;



// // AI 탭 활성화 + 자동 생성 함수 (전역으로 노출)
// function activateAITabAndGenerate() {
//     console.log('🤖 AI 탭 활성화 + 자동 생성 시작');
    
//     // 1. AI 탭 활성화
//     const tabButtons = document.querySelectorAll('.tab-button');
//     const tabContents = document.querySelectorAll('.tab-content');
    
//     tabButtons.forEach(btn => btn.classList.remove('active'));
//     tabContents.forEach(content => content.classList.remove('active'));
    
//     const aiTabButton = document.querySelector('[data-tab="ai"]');
//     const aiTabContent = document.getElementById('ai-tab');
    
//     if (aiTabButton && aiTabContent) {
//         aiTabButton.classList.add('active');
//         aiTabContent.classList.add('active');
//         console.log('✅ AI 탭 활성화 완료');
        
//         // 2. 잠시 후 AI 생성 버튼 클릭 (DOM 업데이트 대기)
//         setTimeout(() => {
//             const generateDiaryBtn = document.getElementById('generate-diary-btn');
//             if (generateDiaryBtn) {
//                 console.log('🖱️ AI 생성 버튼 자동 클릭');
//                 generateDiaryBtn.click();
//             } else {
//                 console.error('❌ AI 생성 버튼을 찾을 수 없습니다');
//             }
//         }, 50);
//     } else {
//         console.error('❌ AI 탭 요소를 찾을 수 없습니다');
//     }
// }



// AI 생성 버튼 자동 클릭 함수 (전역으로 노출)
function activateAITabAndGenerate() {
    console.log('🤖 AI 자동 생성 시작');

    // 잠시 후 AI 생성 버튼 클릭 (DOM 업데이트 대기)
    setTimeout(() => {
        const generateDiaryBtn = document.getElementById('generate-diary-btn');
        if (generateDiaryBtn) {
            console.log('🖱️ AI 생성 버튼 자동 클릭');
            generateDiaryBtn.click();
        } else {
            console.error('❌ generate-diary-btn 버튼을 찾을 수 없습니다');
        }
    }, 50);  // 필요시 시간 조정 (로드 속도 고려)
}



// 전역으로 노출
window.activateAITabAndGenerate = activateAITabAndGenerate; 

