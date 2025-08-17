let messages = [];
let turn = null;
let sessionId = null;

window.initChattingSection = async () => {
  // 로컬 시간 기준 오늘 날짜 표시
  const today = new Date().toLocaleDateString('ko-KR').replace(/\. /g, '-').replace(/\./g, '').replace(/-/g, '-');
  const dateElem = document.getElementById("chat-date");
  if (dateElem) dateElem.textContent = today;

  const token = localStorage.getItem("access_token");
  const headers = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  };
  const res = await fetch("/chat/history", {
    method: "POST",
    headers,
    body: JSON.stringify({ date: today })
  });
  const data = await res.json();
  messages = data.messages || [];
  messages.forEach(msg => renderBubble(msg.role, msg.message, msg.timestamp));

  // 전송 버튼 이벤트
  const sendBtn = document.querySelector("#input-box button");
  if (sendBtn) sendBtn.onclick = sendMessage;
};

async function sendMessage() {
  const input = document.getElementById("input-field");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";

  const token = localStorage.getItem("access_token");
  const headers = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  };

  renderBubble("user", message);
  messages.push({ role: "user", message });

  const sendRes = await fetch("/chat/send", {
    method: "POST",
    headers,
    body: JSON.stringify({ message })
  });
  const sendData = await sendRes.json();
  turn = sendData.turn;
  sessionId = sendData.session_id;

  // 어시스턴트 응답용 말풍선과 시간 생성
  const bubble = document.createElement("div");
  bubble.className = "bubble assistant";
  
  const timeSpan = document.createElement("span");
  timeSpan.className = "message-time";
  timeSpan.textContent = new Date().toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit'
  });
  
  // chat-box에 각각 추가
  const box = document.getElementById("chat-box");
  box.appendChild(bubble);
  box.appendChild(timeSpan);

  const streamRes = await fetch("/chat/response_stream", {
    method: "POST",
    headers,
    body: JSON.stringify({ turn, session_id: sessionId })
  });
  const reader = streamRes.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let assistantMsg = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });

    if (chunk.startsWith("[Error]")) {
      alert(chunk.replace(/^\[Error\]\s*/, ""));
      bubble.style.color = "red";
    }

    assistantMsg += chunk;
    bubble.textContent = assistantMsg;
    document.getElementById("chat-box").scrollTop =
      document.getElementById("chat-box").scrollHeight;
  }

  messages.push({ role: "assistant", message: assistantMsg });
}

function renderBubble(role, message, timestamp) {
  // 말풍선 생성
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  bubble.textContent = message;
  
  // 시간 표시 요소 생성
  const timeSpan = document.createElement("span");
  timeSpan.className = "message-time";
  
  // timestamp가 있으면 사용, 없으면 현재 시간
  const timeToShow = timestamp ? new Date(timestamp) : new Date();
  timeSpan.textContent = timeToShow.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit'
  });
  
  // chat-box에 각각 독립적으로 추가
  const box = document.getElementById("chat-box");
  box.appendChild(bubble);
  box.appendChild(timeSpan);
  box.scrollTop = box.scrollHeight;
} 