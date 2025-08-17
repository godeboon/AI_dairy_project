from openai import OpenAI
from fastapi.responses import StreamingResponse
from app.config.settings import settings

# API 키 검증 및 디버깅
print(f"🔍 디버깅: settings.openai_api_key 길이 = {len(settings.openai_api_key) if settings.openai_api_key else 0}")
print(f"🔍 디버깅: settings.openai_api_key 시작 = {settings.openai_api_key[:10] if settings.openai_api_key else 'None'}...")

if not settings.openai_api_key:
    print("⚠️ 경고: OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가하세요.")
else:
    print(f"✅ OpenAI API 키 설정됨: {settings.openai_api_key[:20]}...")

# settings에서 API 키 가져오기
client = OpenAI(api_key=settings.openai_api_key)

# 응답오는 방식 한번에 완성된 문장 보낼수 있는 api
def call_gpt(prompt: list) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=prompt
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            print("❌ OpenAI API 키 인증 실패. .env 파일에 올바른 OPENAI_API_KEY를 설정하세요.")
        elif "429" in error_msg:
            print("❌ OpenAI API 요청 한도 초과. 잠시 후 다시 시도하세요.")
        else:
            print("❌ GPT 호출 실패:", error_msg)
        raise

# 스트리밍 방식으로 gpt 의 api 호출
async def stream_gpt_response(messages: list):
    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            yield "❌ API 키 인증 실패. 관리자에게 문의하세요."
        elif "429" in error_msg:
            yield "❌ 서비스 일시적 과부하. 잠시 후 다시 시도하세요."
        else:
            yield "❌ GPT 응답 중 오류 발생"
        print("❌ GPT 스트리밍 실패:", error_msg)





# 클래스 버전 (일기 생성용)
class GPTClient:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    # 응답오는 방식 한번에 완성된 문장 보낼수 있는 api
    async def call_gpt(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg:
                print("❌ OpenAI API 키 인증 실패. .env 파일에 올바른 OPENAI_API_KEY를 설정하세요.")
            elif "429" in error_msg:
                print("❌ OpenAI API 요청 한도 초과. 잠시 후 다시 시도하세요.")
            else:
                print("❌ GPT 호출 실패:", error_msg)
            raise

    # 스트리밍 방식으로 gpt 의 api 호출
    async def stream_gpt_response(self, prompt: str):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg:
                yield "❌ API 키 인증 실패. 관리자에게 문의하세요."
            elif "429" in error_msg:
                yield "❌ 서비스 일시적 과부하. 잠시 후 다시 시도하세요."
            else:
                yield "❌ GPT 응답 중 오류 발생"
            print("❌ GPT 스트리밍 실패:", error_msg) 