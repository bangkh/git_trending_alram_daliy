# GitHub Trending 개인 맞춤 알림 봇

GitHub 일간 Trending에 새로 등장한 저장소를 **Gemini로 한국어 요약**하고 **텔레그램**으로 보내는 Windows 개인 PC용 프로그램입니다. 매일 오전 9시(한국 시간)에 확인하고, 처음에는 전체 분야를 구독합니다. 이후 텔레그램 버튼으로 필요 없는 분야를 해제할 수 있습니다.

> 이 저장소를 다운로드한 사람은 각자의 Gemini API 키와 텔레그램 봇을 설정해 실행합니다. 코드만 다운로드하면 운영자의 봇에 자동 가입되는 서비스는 아닙니다.

## 무엇을 보내나요?

저장소마다 프로젝트 이름, 목적, 간단한 동작 원리, 활용처, 분류, GitHub 링크를 보냅니다. 문서에 없는 원리는 추측하지 않고 확인되지 않았다고 표시하도록 요청합니다. AI 요약에는 오류가 있을 수 있으므로 실제 사용 전 원문을 확인하세요.

- 매일 09:00 KST에 일간 Trending 확인
- 신규 사용자는 전체 분야 선택, 나중에 개별 해제 가능
- 👍·👎 피드백으로 선택 분야 내 추천 순서 조정
- 이미 만든 요약 재사용, 사람별 발송 이력으로 중복 방지
- 프로그램 자체의 하루/주간 개수 제한 없음
- Gemini 한도 초과(429) 시 당일 새 요약 중단, 유료 API로 자동 전환 없음

**첫 실행에도 현재 Trending 목록 중 선택 분야에 맞는 저장소를 요약해서 보냅니다.** 이후에는 새로 발견한 미발송 항목만 처리합니다. 새로 보낼 항목이 없는 날에도 확인 완료 알림을 보냅니다. ‘새 저장소’는 새로 생성된 저장소가 아니라 이 프로그램이 Trending에서 새로 발견한 저장소입니다.

## 준비물과 비용

| 준비물 | 설명 |
|---|---|
| Windows PC | 인터넷 연결 필요. 종료·절전 중에는 실행되지 않음 |
| Python 3.11 이상 | [Python 다운로드](https://www.python.org/downloads/windows/) |
| Google 계정과 Gemini API 키 | [Google AI Studio](https://aistudio.google.com/api-keys)에서 발급 |
| 텔레그램 계정·본인 봇 | 공식 [BotFather](https://t.me/BotFather)로 생성 |
| Git | 선택 사항. ZIP 다운로드만으로 설치 가능 |

GPT/OpenAI API나 ChatGPT Plus 구독은 필요 없습니다. 현재 코드의 요약 모델은 `gemini-3.5-flash-lite`입니다. 무료로 사용하려면 **결제가 연결되지 않은 Gemini Free Tier 프로젝트**의 키를 사용하세요. 무료 제공 모델·한도·지역 조건은 바뀔 수 있으므로 [공식 요금 안내](https://ai.google.dev/gemini-api/docs/pricing)를 확인하세요.

프로그램은 API 키만으로 무료/유료 프로젝트를 판별하지 못합니다. `GEMINI_FREE_TIER_CONFIRMED=yes`는 사용자가 확인했다는 표시이며 과금 차단 기능이 아닙니다. 유료 프로젝트의 키를 사용하면 같은 호출도 과금될 수 있습니다.

## 1. 다운로드하고 실제 실행 폴더 찾기

[이 저장소](https://github.com/bangkh/git_trending_alram_daliy)에서 **Code → Download ZIP**을 누른 뒤 파일을 우클릭해 **모두 추출**합니다. ZIP 안에서 직접 실행하지 마세요.

압축을 풀면 폴더가 한 겹 더 생길 수 있습니다. 아래 파일들이 실제로 보이는 폴더가 실행 폴더입니다.

```text
agent.py
interests.py
install.ps1
register-startup.ps1
start.bat
requirements.txt
.env.example
```

예를 들어 `D:\dev\github_trending_agent` 같은 고정 위치를 사용하세요. D드라이브가 없으면 문서 폴더도 괜찮습니다. 자동 실행 등록 뒤에는 폴더를 이동하지 마세요.

해당 폴더의 파일 탐색기 **주소창에 `powershell`을 입력하고 Enter**를 누릅니다. 이후 PC용 명령은 이 PowerShell에서 실행합니다.

## 2. Python 확인과 패키지 설치

```powershell
py -3 --version
```

Python 3.11 이상이면 다음을 실행합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

스크립트가 `.venv` 가상환경을 만들고 필요한 패키지를 설치한 뒤 `.env`를 메모장으로 엽니다. 기존 `.env`는 덮어쓰지 않습니다.

`[notice] A new release of pip is available`은 업데이트 안내이며 설치 실패가 아닙니다. 이 안내만 있다면 다음 단계로 넘어가도 됩니다.

### install.ps1이 없다고 나오는 경우

현재 위치가 실제 실행 폴더보다 한 단계 위일 수 있습니다. 압축을 푼 폴더에서 다음으로 찾습니다.

```powershell
Get-ChildItem -Path . -Filter install.ps1 -Recurse | Select-Object FullName
```

표시된 `install.ps1`이 들어 있는 폴더로 이동한 뒤 다시 실행하세요.

```powershell
cd "설치파일이_있는_폴더의_전체_경로"
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

`py`를 찾지 못하면 Python 설치 프로그램에서 Python Launcher 설치 여부를 확인하세요. `python --version`만 작동한다면 아래처럼 수동 설치할 수도 있습니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

## 3. Gemini API 키 입력

1. [Google AI Studio API Keys](https://aistudio.google.com/api-keys)에 로그인합니다.
2. **Create API key**로 프로젝트를 선택하거나 생성하고 키를 만듭니다.
3. 프로젝트가 **Free Tier이며 결제가 연결되지 않은 상태인지** 확인합니다. 무료 운영을 원하면 유료 전환/결제 연결을 진행하지 않습니다.
4. 메모장의 `.env`에서 다음 두 줄을 채웁니다.

```dotenv
GEMINI_API_KEY=여기에_발급받은_키
GEMINI_FREE_TIER_CONFIRMED=yes
```

키를 채팅·GitHub·스크린샷에 공개하지 마세요. 무료 등급에서는 입력과 응답이 Google의 제품 개선에 사용될 수 있습니다. 프로그램은 공개 저장소의 문서 발췌만 보내며 텔레그램 대화와 사용자 프로필은 요약 API에 보내지 않습니다.

## 4. 텔레그램 봇 만들기

1. 공식 인증 표시가 있는 [@BotFather](https://t.me/BotFather)를 엽니다.
2. 시작을 누르고 `/newbot`을 보냅니다.
3. 표시 이름을 입력합니다. 예: `나의 GitHub 알림`.
4. 중복되지 않으며 `bot`으로 끝나는 사용자 이름을 입력합니다. 예: `my_unique_trending_bot`.
5. BotFather가 보내준 API 토큰을 복사해 `.env`에 넣습니다.

```dotenv
TELEGRAM_BOT_TOKEN=여기에_봇_토큰
```

6. BotFather가 알려준 **생성된 봇의 링크**를 엽니다. BotFather와의 대화창이 아닙니다.
7. 본인 봇과의 **개인 대화창**에서 시작을 누르고 `/start` 또는 `hello`를 보냅니다.
8. 메모장에서 **Ctrl+S**로 저장합니다.

## 5. 내 대화 ID 찾기

프로그램을 아직 실행하지 않은 상태에서 다음을 실행합니다.

```powershell
.\.venv\Scripts\python.exe agent.py chat-id
```

다음처럼 나오면 숫자를 복사합니다.

```text
private chat ID: 123456789 name: ...
```

`.env`의 해당 줄에 입력하고 Ctrl+S로 저장합니다.

```dotenv
TELEGRAM_CHAT_ID=123456789
```

### 아무것도 출력되지 않을 때 — 실제 설치 중 발생한 문제

오류 없이 바로 명령 프롬프트로 돌아오면 읽어올 개인 메시지가 없을 수 있습니다. 봇에 새 메시지를 보내고 다시 실행하세요. `start.bat`이나 `agent.py serve`가 실행 중이면 먼저 Ctrl+C로 중지합니다. 이미 자동 시작을 등록했다면 다음으로 중지합니다.

```powershell
Stop-ScheduledTask -TaskName GitHubTrendingPersonalAgent
```

등록 전이라 작업이 없다는 오류가 나오면 이 단계는 건너뜁니다. 같은 봇 토큰을 다른 프로그램에서도 사용 중인지 확인하세요.

그래도 안 나오면 **실제로 어떤 봇에 연결되었는지** 확인합니다. 아래 블록 전체를 붙여 넣으세요. 비밀 토큰은 출력하지 않습니다. Windows PowerShell에서 한글이 `???`로 표시되는 상황을 피하려고 진단 문구는 영어로 작성했습니다.

```powershell
@'
import agent
bot = agent.telegram("getMe", {})
print("Bot: @" + bot["username"])
info = agent.telegram("getWebhookInfo", {})
print("Webhook enabled:", bool(info.get("url")))
print("Pending updates:", info.get("pending_update_count", 0))
'@ | .\.venv\Scripts\python.exe -
```

`Bot: @이름`이 메시지를 보낸 봇과 같은지 확인하세요. 웹훅이 `True`이면 다른 서비스가 이 봇을 사용 중일 수 있습니다. 그 서비스와 함께 사용할 수 없으므로 별도의 새 봇을 만드는 편이 간단합니다.

`Webhook enabled: False`인데도 ID가 안 나오면 아래 **40초 대기 방식**으로 확인합니다.

```powershell
@'
import agent
bot = agent.telegram("getMe", {})
print("Send a NEW private message NOW to @" + bot["username"], flush=True)
updates = agent.telegram("getUpdates", {
    "timeout": 40,
    "allowed_updates": ["message"]
})
print("Update count:", len(updates))
for update in updates:
    chat = update.get("message", {}).get("chat", {})
    if chat:
        print("Chat type:", chat.get("type"))
        print("Chat ID:", chat.get("id"))
'@ | .\.venv\Scripts\python.exe -
```

**명령을 실행해 `Send a NEW private message NOW...`가 나온 뒤 40초 안에** 해당 봇에 `test123`을 새로 보냅니다. 미리 보낸 메시지만 기다리지 마세요. 그룹이 아닌 개인 대화여야 합니다. `Chat type: private` 아래의 숫자를 `.env`에 저장합니다.

## 6. 설정 저장과 테스트 알림

`.env`는 대략 다음 구성입니다. 아래 예시 문자열 대신 본인 값을 사용합니다.

```dotenv
GEMINI_API_KEY=본인_Gemini_API_키
GEMINI_FREE_TIER_CONFIRMED=yes
TELEGRAM_BOT_TOKEN=본인_봇_토큰
TELEGRAM_CHAT_ID=본인_대화_ID
TELEGRAM_ALLOWED_CHAT_IDS=
GITHUB_TOKEN=
```

`TELEGRAM_ALLOWED_CHAT_IDS`와 `GITHUB_TOKEN`은 혼자 사용할 때 비워도 됩니다. 파일 이름은 `.env`여야 하며 `.env.txt`가 아닙니다.

```powershell
notepad .env
```

저장한 다음 테스트합니다.

```powershell
.\.venv\Scripts\python.exe agent.py test-telegram
```

텔레그램에 **GitHub Trending 에이전트 알림 연결 완료**가 도착하면 텔레그램 연결은 성공입니다. 이 명령은 **Gemini 요약 API를 테스트하지는 않습니다.** Gemini는 이후 실제 요약 대상이 생겼을 때 호출됩니다.

## 7. 실행하고 관심 분야 설정

```powershell
.\.venv\Scripts\python.exe agent.py serve
```

이 창은 켜 둔 채 본인 봇에 다음을 보냅니다. 아래 명령은 PowerShell이 아니라 **텔레그램 메시지**로 보냅니다.

```text
/topics
```

새 사용자는 전체 분야가 ✅로 선택됩니다. 원치 않는 분야를 누르면 해제됩니다. 버튼을 누르면 새 메뉴가 오므로 가장 최근 메뉴를 사용하세요. 설정은 재시작 후에도 유지됩니다.

| 명령 | 동작 |
|---|---|
| `/topics` | 분야 선택·해제 버튼 |
| `/all` | 전체 분야 선택. 기존 사용자도 한 번에 전체로 변경 |
| `/only claude_plugins` | Claude 플러그인·스킬 분야만 선택 |
| `/only claude_plugins mcp` | 지정한 두 분야만 선택 |
| `/pause` | 모든 선택 해제, 저장소 알림 중지 |
| `/status` | 현재 선택과 실행 주기 확인 |

| 분야 코드 | 내용 |
|---|---|
| `claude_plugins` | Claude 플러그인·스킬·훅 |
| `mcp` | MCP 서버·연결 도구 |
| `ai_coding` | AI 코딩 도구 |
| `agents` | AI 에이전트·자동화 |
| `web_app` | 웹·모바일 앱 개발 |
| `data_ml` | 데이터·머신러닝 |
| `infra` | 개발 도구·인프라 |
| `security` | 보안·개인정보 |
| `other` | 기타·미분류 |

저장소는 여러 분야에 속할 수 있고, **선택한 분야 중 하나라도 일치하면** 알림 대상입니다. 따라서 한 분야를 해제해도 다른 선택 분야에 일치하면 받을 수 있습니다. 이름·소개·README 앞부분의 정규식 기반 분류라 오탐·누락이 가능합니다.

알림의 👍·👎는 공통 분야를 가진 후보의 처리 순서를 조정합니다. 같은 저장소를 반복 클릭해도 평가가 누적되지 않고 마지막 평가로 바뀝니다. 👎는 차단 버튼이 아닙니다. 개수 제한을 제거한 버전에서는 순서만 바뀌며, 무료 한도가 허용하면 후보를 모두 받습니다.

## 8. 로그인 시 자동 실행 등록

수동 실행으로 `/status` 응답을 확인한 뒤 진행하세요.

1. 실행 중인 PowerShell에서 **Ctrl+C**로 프로그램을 중지합니다.
2. 같은 폴더에서 다음을 실행합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\register-startup.ps1
```

성공하면 다음 문구가 나타납니다.

```text
Registered and started. Do not also run start.bat.
```

3. 텔레그램에서 `/status`를 보내 다시 응답이 오는지 확인합니다.
4. 응답이 오면 PowerShell 창을 닫아도 됩니다. 이후 `start.bat`을 별도로 실행할 필요가 없습니다.

Windows 작업 스케줄러의 작업 이름은 `GitHubTrendingPersonalAgent`입니다. 로그인 시 시작되며 등록 직후에도 실행됩니다. PC가 꺼져 있거나 절전 상태인 동안에는 수집·피드백 처리가 되지 않습니다. 오전 9시를 놓쳤으면 다음 실행 때 최근 놓친 회차를 한 번 처리하며 과거 모든 날짜의 목록을 복원하지 않습니다.

### 중지·재시작·자동 실행 제거

```powershell
# 중지
Stop-ScheduledTask -TaskName GitHubTrendingPersonalAgent

# 다시 시작
Start-ScheduledTask -TaskName GitHubTrendingPersonalAgent

# 자동 실행 등록 제거
powershell -NoProfile -ExecutionPolicy Bypass -File .\unregister-startup.ps1
```

`.env`를 수정하면 중지 후 다시 시작해야 반영됩니다. 폴더를 이동하려면 기존 작업을 먼저 중지·제거하고, 새 위치에서 가상환경을 다시 만든 뒤 자동 실행을 등록하세요. 가상환경은 이동하지 않고 다시 설치하는 편이 안전합니다.

## 자주 묻는 질문과 오류 해결

| 상황 | 확인할 내용 |
|---|---|
| 첫날 저장소 알림이 없음 | 최신 버전은 첫 실행에도 전송. 최근 결과를 /status로 확인하고 API 오류·한도 안내 확인 |
| `/topics`, `/status` 응답 없음 | `serve` 또는 예약 작업이 실행 중인지, 본인 chat ID가 맞는지 확인. 수집 중에는 답변이 지연될 수 있음 |
| 기존에 하루 3개까지만 받음 | 최신 `agent.py`, `interests.py`로 업데이트 후 재시작. `/status`에서 개수 제한 없음 확인 |
| 한글 진단 출력이 `???` | PowerShell 파이프 인코딩 문제 가능. 위 영어 진단 명령 사용 |
| HTTP 401/404 또는 Telegram 오류 | 토큰 오타, 잘못된 봇/폐기된 토큰 확인. Gemini 모델 관련 404는 모델 제공 상태 확인 |
| HTTP 403 | 서비스 접근 권한, 키 제한, 지역·프로젝트 조건 확인. GitHub 요청이라면 API 사용 한도도 확인 |
| HTTP 409 | 같은 봇을 다른 프로세스가 polling하거나 웹훅을 사용하는지 확인 |
| Gemini HTTP 429 | 무료 호출 속도/사용량 한도일 수 있음. 프로그램은 보수적으로 그날 새 요약을 중단하고 다음 날 시도 |
| 요약이 차단되거나 잘렸다는 오류 | 미완성 요약은 저장하지 않음. 해당 저장소는 다음 날 재시도 가능 |
| 패키지가 없다는 오류 | 전역 `python` 대신 `.\.venv\Scripts\python.exe` 사용, `install.ps1` 설치 결과 확인 |
| 자동 실행 등록이 액세스 거부로 실패 | Windows 계정·조직 정책 확인. 필요하면 관리자 PowerShell에서 실행하되 같은 사용자 계정의 작업인지 확인 |
| 실행 실패의 상세 원인을 보고 싶음 | 예약 작업을 중지하고 `agent.py run`을 수동 실행. 오류 공유 시 키/토큰은 제외 |

명령어의 `run`과 `preview`는 다음처럼 사용합니다.

```powershell
# 일간 Trending 목록 수집만 확인: 요약·발송 없음
.\.venv\Scripts\python.exe agent.py preview

# 수집·요약·발송 한 회차 수동 실행: 실제 API 호출 및 알림 가능
.\.venv\Scripts\python.exe agent.py run

# 외부 서비스 호출 없이 모의 테스트
.\.venv\Scripts\python.exe -m unittest -v
```

수동 `run`도 기존 기준 목록·발송 이력·관심 분야를 적용하므로 알림이 꼭 생기는 것은 아닙니다. 원인 확인을 위해 `state.sqlite3`를 지우지 마세요. 삭제하면 개인 설정과 중복 방지 이력이 사라집니다.

## 여러 사람이 쓰는 방법

일반적인 배포 방식은 **각자가 복제/다운로드하고 자기 API 키·봇을 사용하는 방식**입니다. 운영자의 키나 `.env`를 함께 배포하지 않습니다.

하나의 봇을 지인들과 공유하려면 각 사람이 봇에 개인 메시지를 보내고, 프로그램 운영자가 확인한 해당 chat ID를 `TELEGRAM_ALLOWED_CHAT_IDS`에 쉼표로 추가합니다. ID 확인 시 운영 프로그램은 잠시 중지하세요.

```dotenv
TELEGRAM_ALLOWED_CHAT_IDS=111111111,222222222
```

설정 저장 후 재시작합니다. 허용된 개인 대화만 처리하며 관심 분야·피드백·발송 이력은 사람별로 저장합니다. 요약 캐시는 공유하므로 같은 저장소에 API를 반복 호출하지 않습니다. 공유 봇은 운영자의 PC가 켜져 있어야 하며 모든 사용자가 운영자 Gemini 프로젝트의 한도를 공유합니다.

## 동작 방식과 한계

1. 일반 코드로 일간 Trending HTML을 가져옵니다.
2. SQLite의 기존 목록과 비교해 새로 발견한 저장소를 기록합니다.
3. README를 캐시하고 키워드로 분야를 분류합니다(AI 호출 없음).
4. 선택 분야에 맞는 미발송 후보만 Gemini에 공개 문서 발췌를 보내 요약합니다.
5. 저장한 요약을 텔레그램으로 보내고 사람별 발송 이력을 기록합니다.

- 자료 입력은 최대 2,400자, 출력 한도는 생각 토큰을 포함해 최대 1,024토큰입니다. ‘토큰을 안 쓰는 API’가 아니라 무료 등급 내 토큰을 사용하는 방식입니다.
- 개수 제한은 없지만 실패한 저장소에 대한 요약 요청은 날짜당 1회로 제한합니다.
- 429이면 한국 날짜 기준 그날 새 요약을 중단합니다. 제공자의 한도 초기화 시각과 다를 수 있어 다음 실행에서도 제한될 수 있습니다.
- 미발송 신규 후보는 최초 발견 후 7일 동안 재검토합니다. 이후에는 대상에서 제외됩니다.
- 하루 한 번만 확인하므로 그 사이 잠깐 등장했다 사라진 저장소는 놓칠 수 있습니다.
- GitHub HTML 구조 변경, API 한도, 모델 제공 종료, 인터넷 문제로 실패할 수 있습니다.
- 전송 성공 직후 이력 저장 전 PC가 종료되는 경우에는 중복 발송 가능성이 있습니다.
- PC가 오래 꺼져 있으면 Telegram에 보관된 오래된 피드백을 받지 못할 수 있습니다.
- Gemini/Telegram 실서비스 연결은 개인 키로 확인해야 합니다. 자동 테스트는 모의 응답으로 핵심 로직을 검증합니다.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `agent.py` | 수집 공통 기능, Gemini·Telegram 호출, 매일 실행 |
| `interests.py` | 관심 분야, 메뉴, 피드백, 개인별 발송 |
| `test_agent.py` | 외부 호출 없는 모의 테스트 |
| `.env.example` | 비밀값 없는 설정 예시 |
| `install.ps1` | 가상환경·패키지 설치 |
| `start.bat` | 수동 실행 |
| `register-startup.ps1` | 로그인 시 자동 실행 등록 |
| `unregister-startup.ps1` | 자동 실행 제거 |
| `state.sqlite3` | 실행 시 생성되는 개인 데이터, 배포 제외 |

공식 문서: [Telegram Bot API](https://core.telegram.org/bots/api) · [Gemini 요금](https://ai.google.dev/gemini-api/docs/pricing) · [Gemini API](https://ai.google.dev/api/generate-content)


## 첫 알림 및 일일 결과 안내 업데이트

- 첫 실행에 현재 목록을 처리합니다. 구버전에서 기준 목록으로만 저장했던 항목은 현재 Trending에 남아 있고 요약되지 않은 경우 한 번 다시 후보로 전환합니다. 발송 이력과 관심 분야는 유지합니다.
- 같은 날 같은 결과 알림은 반복하지 않습니다. 미발송 대기에서 전송 완료로 바뀌면 새 결과를 안내합니다. /pause 상태에서는 일일 안내도 보내지 않습니다.
- 한도·요약 오류·재시도 대기가 있으면 ‘신규 없음’으로 표시하지 않고 미발송 개수를 알려줍니다. /status에서도 최근 결과를 확인할 수 있습니다.
- 구버전은 오늘 실행 완료로 기록되어 있어도 업데이트 후 첫 재시작 시 한 번 수집합니다. 이후 오전 9시 일정은 유지합니다.
- 적용: 실행 작업을 중지하고 최신 agent.py, interests.py 두 파일을 기존 폴더에 덮어쓴 뒤 다시 시작하세요. .env, .venv, state.sqlite3는 유지합니다.

### 구형 모델 404 오류 수정
`gemini-2.5-flash-lite` 신규 사용자 접근 제한에 대응해 `gemini-3.5-flash-lite`와 `thinkingLevel: MINIMAL`로 변경했습니다. GenerateContent API를 유지합니다. API 키를 재발급할 필요는 없습니다. 과거 모델 실패 기록은 보존하고 새 모델의 일일 시도 이력을 별도로 계산하여 당일 재시도가 가능합니다. 업데이트 후 첫 재시작에는 오늘 회차를 이미 처리했어도 다시 수집합니다. 실제 접근 가능 여부와 무료 한도는 본인의 프로젝트에서 확인해야 합니다.
