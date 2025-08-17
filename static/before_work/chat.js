let messages = [];
let turn = null;
let sessionId = null;

// 페이지 로딩 시 history 불러오기
window.chatInit = async () => {
  // 날짜 표시
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("chat-date").textContent = today;
  
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
  messages.forEach(msg => renderBubble(msg.role, msg.message));
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

  const div = document.createElement("div");
  div.className = "bubble assistant";
  document.getElementById("chat-box").appendChild(div);

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
      div.style.color = "red";
    }

    assistantMsg += chunk;
    div.textContent = assistantMsg;
    document.getElementById("chat-box").scrollTop =
      document.getElementById("chat-box").scrollHeight;
  }

  messages.push({ role: "assistant", message: assistantMsg });
}

function renderBubble(role, message) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  div.textContent = message;
  const box = document.getElementById("chat-box");
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function bindChatEvents() {
  // 채팅창 종료 버튼
  const closeBtn = document.getElementById("close-chat");
  if (closeBtn) {
    closeBtn.addEventListener("click", async () => {
      const token = localStorage.getItem("access_token");
      await fetch("/chat/close", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        }
      });
      window.location.href = "/mypage";
    });
  }
  // 전송 버튼
  const sendBtn = document.querySelector("#input-box button");
  if (sendBtn) {
    sendBtn.onclick = sendMessage;
  }
}

// chat.html이 동적으로 로드된 후 호출 필요
window.initChatUI = function() {
  window.chatInit();
  bindChatEvents();
}; 