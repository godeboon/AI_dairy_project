// register.html에서 분리된 JS 코드
// 아래는 register.html의 <script>...</script> 내부 전체 JS 코드입니다.

// 비밀번호 유효성 검사 함수
function validatePassword(password) {
  const requirements = {
    english: /[A-Za-z]/.test(password),
    number: /\d/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    repeat: !/(\d)\1{2,}/.test(password)
  };

  // 요구사항 표시 업데이트
  document.getElementById('req-english').className =
    `requirement ${requirements.english ? 'valid' : 'invalid'}`;
  document.getElementById('req-number').className =
    `requirement ${requirements.number ? 'valid' : 'invalid'}`;
  document.getElementById('req-special').className =
    `requirement ${requirements.special ? 'valid' : 'invalid'}`;
  document.getElementById('req-repeat').className =
    `requirement ${requirements.repeat ? 'valid' : 'invalid'}`;

  return Object.values(requirements).every(req => req);
}

// 비밀번호 일치 확인 함수
function checkPasswordMatch() {
  const password = document.getElementById('password').value;
  const confirmPassword = document.getElementById('password_confirm').value;
  const matchDiv = document.getElementById('password-match');

  if (confirmPassword === '') {
    matchDiv.textContent = '';
    matchDiv.className = 'password-match';
    return false;
  }

  if (password === confirmPassword) {
    matchDiv.textContent = '✓ 비밀번호가 일치합니다';
    matchDiv.className = 'password-match valid';
    return true;
  } else {
    matchDiv.textContent = '✗ 비밀번호가 일치하지 않습니다';
    matchDiv.className = 'password-match invalid';
    return false;
  }
}

// 폼 유효성 검사
function validateForm() {
  const password = document.getElementById('password').value;
  const isPasswordValid = validatePassword(password);
  const isPasswordMatch = checkPasswordMatch();

  const submitBtn = document.getElementById('submit-btn');
  if (isPasswordValid && isPasswordMatch) {
    submitBtn.disabled = false;
    submitBtn.className = 'submit-btn active';
  } else {
    submitBtn.disabled = true;
    submitBtn.className = 'submit-btn';
  }
}

// 이벤트 리스너 설정
if (document.getElementById('password')) {
  document.getElementById('password').addEventListener('input', function() {
    validatePassword(this.value);
    checkPasswordMatch();
    validateForm();
  });
}

if (document.getElementById('password_confirm')) {
  document.getElementById('password_confirm').addEventListener('input', function() {
    checkPasswordMatch();
    validateForm();
  });
}

// 폼 제출 처리
if (document.getElementById("registerForm")) {
  document.getElementById("registerForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = {
      username: formData.get("username"),
      password: formData.get("password"),
      email: formData.get("email"),
      nickname: formData.get("nickname")
    };

    try {
      const response = await fetch("http://127.0.0.1:8000/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      if (!response.ok) {
        if (Array.isArray(result.detail)) {
          const errorMessages = result.detail.map(e => e.msg).join("\n");
          alert(errorMessages);
        } else {
          alert(result.detail || result.message || "회원가입 실패");
        }
      } else {
        alert(result.message || "회원가입 성공!");
        window.location.href = "/login";
      }

    } catch (error) {
      alert("서버와의 통신에 실패했습니다: " + error.message);
    }
  });
}

// 페이지 로드 시 초기 상태 설정
window.onload = function() {
  validateForm();
}; 