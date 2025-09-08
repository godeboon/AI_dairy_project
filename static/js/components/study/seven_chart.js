// seven_chart.js - 7일 감정 레포트 차트 관리
console.log('📊 seven_chart.js 로드됨');

// Chart.js 라이브러리 로드 확인
if (typeof Chart === 'undefined') {
  console.error('❌ Chart.js 라이브러리가 로드되지 않았습니다.');
}

// 서버 API 호출 - 7일 리포트 데이터 가져오기
async function fetchSevenDayReportData(analysisId) {
  try {
    console.log('🔄 7일 리포트 데이터 요청 시작:', analysisId);
    
    const response = await fetch(`/study/seven-day-report/${analysisId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ 7일 리포트 데이터 수신:', data);
      
      // 데이터 구조 상세 출력
      console.log('📊 weekly_analysis 데이터:', data.weekly_analysis);
      console.log('📊 diary_analyses 개수:', data.diary_analyses.length);
      console.log('📊 diary_analyses 첫 번째 데이터:', data.diary_analyses[0]);
      console.log('📊 emotion_trend 결과:', data.weekly_analysis.emotion_trend);
      console.log('📊 keyword_patterns 결과:', data.weekly_analysis.keyword_patterns);
      console.log('📊 overall_assessment 결과:', data.weekly_analysis.overall_assessment);
      
      // 로컬스토리지에 저장 (analysis_id, 날짜 정보 포함)
      const dataWithDates = {
        ...data,
        analysis_id: analysisId, // analysis_id 추가
        week_start_date: data.weekly_analysis.start_date || null,
        week_end_date: data.weekly_analysis.end_date || null
      };
      localStorage.setItem('seven_day_report_data', JSON.stringify(dataWithDates));
      
      // 차트 렌더링
      renderSevenDayCharts(data);
      
      // 로딩 완료 알림 서버에 전송
      notifyChartLoadingComplete(analysisId);
    } else {
      console.error('❌ 7일 리포트 데이터 요청 실패:', response.status);
    }
  } catch (error) {
    console.error('❌ 7일 리포트 데이터 가져오기 실패:', error);
  }
}

// 로딩 완료 알림 - 서버에 전송
async function notifyChartLoadingComplete(analysisId) {
  try {
    console.log('📤 차트 로딩 완료 알림 전송:', analysisId);
    
    // 기존 데이터에서 날짜 정보 추출
    const existingData = localStorage.getItem('seven_day_report_data');
    let weekStartDate = null;
    let weekEndDate = null;
    
    if (existingData) {
      try {
        const data = JSON.parse(existingData);
        if (data.weekly_analysis && data.weekly_analysis.start_date && data.weekly_analysis.end_date) {
          // 서버에서 이미 mm-dd 형식으로 받았으므로 그대로 사용
          weekStartDate = data.weekly_analysis.start_date;
          weekEndDate = data.weekly_analysis.end_date;
        }
      } catch (error) {
        console.error('❌ 기존 데이터 파싱 실패:', error);
      }
    }
    
    const response = await fetch('/study/chart-loading-complete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({ 
        analysis_id: analysisId,
        status: 'completed',
        week_start_date: weekStartDate,
        week_end_date: weekEndDate
      })
    });
    
    if (response.ok) {
      console.log('✅ 차트 로딩 완료 알림 전송 성공');
    } else {
      console.error('❌ 차트 로딩 완료 알림 전송 실패:', response.status);
    }
  } catch (error) {
    console.error('❌ 차트 로딩 완료 알림 전송 실패:', error);
  }
}

// 차트 렌더링 함수
function renderSevenDayCharts(data) {
  console.log('🎨 7일 리포트 차트 렌더링 시작:', data);
  
  try {
    // 기존 차트 제거
    destroyExistingCharts();
    
    // 감정 트렌드 라인 차트 렌더링
    renderEmotionTrendChart(data);
    
    // 레이더 차트 렌더링
    renderRadarChart(data);
    
    // 감정 트렌드 텍스트 표시
    renderEmotionTrendText(data);
    
    // 종합 평가 텍스트 표시
    renderComprehensiveAssessment(data);
    
    console.log('✅ 7일 리포트 차트 렌더링 완료');
  } catch (error) {
    console.error('❌ 차트 렌더링 실패:', error);
  }
}

// 기존 차트 제거
function destroyExistingCharts() {
  const charts = Chart.getChart('emotionTrendChart');
  if (charts) {
    charts.destroy();
  }
  
  const radarChart = Chart.getChart('radarChart');
  if (radarChart) {
    radarChart.destroy();
  }
}

// 감정 트렌드 라인 차트 렌더링
function renderEmotionTrendChart(data) {
  const ctx = document.getElementById('emotionTrendChart');
  if (!ctx) {
    console.error('❌ emotionTrendChart 캔버스를 찾을 수 없습니다.');
    return;
  }
  
  // diary_analyses 데이터에서 감정 점수 합산
  const chartData = data.diary_analyses.map(diary => {
    // 실제 응답 데이터 구조에 맞게 수정
    // diary.scores가 없을 경우 기본값 사용
    const scores = diary.scores || [0, 0, 0];
    const totalScore = scores.reduce((sum, score) => sum + score, 0);
    return {
      date: diary.date_str,
      score: totalScore,
      diaryData: diary // 팝업용 데이터 저장
    };
  }).sort((a, b) => new Date(a.date) - new Date(b.date));
  
  const labels = chartData.map(item => {
    const date = new Date(item.date);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  });
  
  const scores = chartData.map(item => item.score);
  
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: '감정 점수',
        data: scores,
        borderColor: '#ffe1d2', // 베이지색 계열
        backgroundColor: 'rgba(255, 225, 210, 0.3)', // 연한 베이지색
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#ffd4c2', // 진한 베이지색
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        pointHoverBackgroundColor: '#ffc4b2', // 더 진한 베이지색
        pointHoverBorderColor: '#fff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.9)', // 검정색 배경
          titleColor: '#ffffff',
          bodyColor: '#ffffff',
          borderColor: '#333333', // 진한 회색 테두리
          borderWidth: 1,
          cornerRadius: 8,
          displayColors: false,
          callbacks: {
            label: function(context) {
              const score = context.parsed.y;
              const scoreText = score >= 0 ? `+${score.toFixed(1)}` : score.toFixed(1);
              return `감정 점수: ${scoreText}`;
            }
          }
        }
      },
      scales: {
        y: {
          min: -1,
          max: 1,
          ticks: {
            stepSize: 0.5,
            color: '#6b7280', // 회색
            font: {
              size: 12
            }
          },
          grid: {
            color: 'rgba(255, 225, 210, 0.2)' // 연한 베이지색
          }
        },
        x: {
          ticks: {
            color: '#6b7280', // 회색
            font: {
              size: 12
            }
          },
          grid: {
            color: 'rgba(255, 225, 210, 0.2)' // 연한 베이지색
          }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      },
      onClick: async function(event, elements) {
        if (elements.length > 0) {
          const index = elements[0].index;
          const diaryData = chartData[index].diaryData;
          
          // 클릭 시점에 chart_popup 동적 로드
          try {
            const { showChartPopup } = await import('/static/js/components/popup/chart_popup.js');
            showChartPopup(diaryData);
          } catch (error) {
            console.error('❌ chart_popup 로드 실패:', error);
          }
        }
      }
    }
  });
}

// 레이더 차트 렌더링
function renderRadarChart(data) {
  const ctx = document.getElementById('radarChart');
  if (!ctx) {
    console.error('❌ radarChart 캔버스를 찾을 수 없습니다.');
    return;
  }
  
  // weekly_analysis에서 데이터 추출
  const weeklyData = data.weekly_analysis;
  
  // 서버 데이터에서 radar 차트 데이터 추출
  const radarData = {
    life_satisfaction: weeklyData.comprehensive_pattern_result?.life_satisfaction || 0,
    emotion_stability: weeklyData.emotion_trend?.emotion_stability || 0,
    stress_level: weeklyData.comprehensive_pattern_result?.stress_level || 0
  };
  
  new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['생활 만족도', '감정 안정성', '스트레스 수준'],
      datasets: [{
        label: '주간 분석',
        data: [
          radarData.life_satisfaction,
          radarData.emotion_stability,
          radarData.stress_level
        ],
        backgroundColor: 'rgba(255, 225, 210, 0.3)', // 연한 베이지색
        borderColor: '#ffe1d2', // 베이지색
        borderWidth: 2,
        pointBackgroundColor: '#ffd4c2', // 진한 베이지색
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.9)', // 검정색 배경
          titleColor: '#ffffff', // 흰색 제목
          bodyColor: '#ffffff', // 흰색 본문
          borderColor: '#333333', // 진한 회색 테두리
          borderWidth: 1,
          cornerRadius: 8,
          displayColors: false,
          callbacks: {
            label: function(context) {
              const labels = ['생활 만족도', '감정 안정성', '스트레스 수준'];
              const label = labels[context.dataIndex];
              const value = context.parsed.r.toFixed(1);
              return `${label} : ${value}`;
            },
            title: function(context) {
              return null; // 제목 제거
            }
          }
        }
      },
      scales: {
        r: {
          min: 0,
          max: 1,
          beginAtZero: true,
          ticks: {
            stepSize: 0.2,
            color: '#6b7280', // 회색
            font: {
              size: 12
            }
          },
          grid: {
            color: 'rgba(255, 225, 210, 0.2)' // 연한 베이지색
          },
          pointLabels: {
            color: '#374151', // 진한 회색
            font: {
              size: 14,
              weight: 'bold'
            }
          }
        }
      }
    }
  });
}

// 감정 트렌드 텍스트 표시
function renderEmotionTrendText(data) {
  const trendContainer = document.getElementById('emotionTrendText');
  if (!trendContainer) {
    console.error('❌ emotionTrendText 컨테이너를 찾을 수 없습니다.');
    return;
  }
  
  const trendData = data.weekly_analysis.emotion_trend;
  if (!trendData) {
    trendContainer.innerHTML = '<p>현재 수집된 데이터가 부족해 표시할 수 없습니다.</p>';
    return;
  }
  
  // 기존 trend-section 내용 설정
  const mainTrendElement = document.getElementById('mainTrend');
  const dominantEmotionElement = document.getElementById('dominantEmotion');
  const recommendationsElement = document.getElementById('recommendations');
  const weeklyAssessmentElement = document.getElementById('weeklyAssessment');
  
  if (mainTrendElement) {
    mainTrendElement.textContent = trendData.trend || '분석 중';
  }
  if (dominantEmotionElement) {
    dominantEmotionElement.textContent = trendData.dominant_emotion || '분석 중';
  }
  if (recommendationsElement) {
    recommendationsElement.textContent = trendData.recommendation || '분석 중';
  }
  if (weeklyAssessmentElement) {
    // 주간 종합 평가는 overall_assessment 데이터 사용
    const overallAssessment = data.weekly_analysis.overall_assessment;
    weeklyAssessmentElement.textContent = overallAssessment || '분석 중';
  }
  
  // trend-analysis 섹션 표시
  const trendAnalysis = trendContainer.querySelector('.trend-analysis');
  if (trendAnalysis) {
    trendAnalysis.style.display = 'block';
  }
  
  // 로딩 메시지 숨기기
  const loadingElement = trendContainer.querySelector('.chart-loading');
  if (loadingElement) {
    loadingElement.style.display = 'none';
  }
}

// 종합 평가 텍스트 표시
function renderComprehensiveAssessment(data) {
  const assessmentContainer = document.getElementById('comprehensiveAssessment');
  if (!assessmentContainer) {
    console.error('❌ comprehensiveAssessment 컨테이너를 찾을 수 없습니다.');
    return;
  }
  
  // keyword_patterns에서 데이터 가져오기
  const keywordPatterns = data.weekly_analysis?.keyword_patterns;
  console.log('📊 keyword_patterns 데이터:', keywordPatterns);
  
  if (!keywordPatterns) {
    assessmentContainer.innerHTML = '<div class="chart-loading">현재 수집된 데이터가 부족해 표시할 수 없습니다.</div>';
    return;
  }
  
  // JSON 파싱 (문자열인 경우)
  let parsedData = keywordPatterns;
  if (typeof keywordPatterns === 'string') {
    try {
      parsedData = JSON.parse(keywordPatterns);
    } catch (error) {
      console.error('❌ keyword_patterns 파싱 실패:', error);
      assessmentContainer.innerHTML = '<div class="chart-loading">데이터 파싱에 실패했습니다.</div>';
      return;
    }
  }
  
  const mainThemes = parsedData.main_themes || [];
  const insights = parsedData.insights || '';
  
  console.log('📊 파싱된 데이터:', { mainThemes, insights });
  
  // 로딩 메시지 숨기기
  const loadingElement = assessmentContainer.querySelector('.chart-loading');
  if (loadingElement) {
    loadingElement.style.display = 'none';
  }
  
  // 키워드 및 인사이트 컨테이너 표시
  const keywordInsightsContainer = assessmentContainer.querySelector('.keyword-insights-container');
  if (keywordInsightsContainer) {
    keywordInsightsContainer.style.display = 'flex';
  }
  
  // 메인 테마 키워드 렌더링
  const mainThemesList = document.getElementById('mainThemesList');
  if (mainThemesList) {
    if (mainThemes.length > 0) {
      mainThemesList.innerHTML = mainThemes.slice(0, 3).map(theme => 
        `<span class="keyword-item">${theme}</span>`
      ).join('');
    } else {
      mainThemesList.innerHTML = '<p style="color: #999; font-style: italic;">키워드 데이터가 없습니다.</p>';
    }
  }
  
  // 인사이트 렌더링
  const insightsContainer = document.getElementById('insightsContainer');
  if (insightsContainer) {
    if (insights) {
      insightsContainer.innerHTML = `<div class="insight-text">${insights}</div>`;
    } else {
      insightsContainer.innerHTML = '<p style="color: #999; font-style: italic;">인사이트 데이터가 없습니다.</p>';
    }
  }
}



// 전역 리스너 등록 (한 번만)
function bindSevenChartListenersOnce() {
  if (window.__sevenChartListenersBound) return;
  window.__sevenChartListenersBound = true;
  
  console.log('📊 seven_chart 리스너 등록됨');
  
  // seven day report 알림 리스너
  document.addEventListener('seven_day_report', function(event) {
    const data = event.detail;
    console.log('📊 seven day report 알림 수신:', data);
    
    // 서버에서 데이터 가져오기
    fetchSevenDayReportData(data.analysis_id);
  });
}

// 초기화 함수 - 탭 진입 시 호출
window.initSevenChartUI = function() {
  bindSevenChartListenersOnce();  // 리스너 보장
  
  console.log('📊 seven_chart UI 초기화 시작');
  

  
  // 기존 데이터가 있으면 차트 렌더링
  const existingData = localStorage.getItem('seven_day_report_data');
  if (existingData) {
    try {
      const data = JSON.parse(existingData);
      console.log('📊 기존 데이터 발견, 차트 렌더링:', data);
      renderSevenDayCharts(data);
    } catch (error) {
      console.error('❌ 기존 데이터 파싱 실패:', error);
    }
  } else {
    // 기존 데이터가 없으면 로딩 상태 유지 (다른 영역들과 동일)
    console.log('📊 기존 차트 데이터 없음, 로딩 상태 유지');
    // HTML의 기본 로딩 메시지가 그대로 표시됨
  }
  
  // WebSocket 알림 상태 복원
  if (window.globalNotificationManager) {
    console.log('📤 seven_chart 서브탭 - WebSocket 알림 상태 복원');
    window.globalNotificationManager.restoreNotifications('study');
  }
  
  console.log('✅ seven_chart UI 초기화 완료');
};

console.log('✅ seven_chart.js 초기화 완료');
