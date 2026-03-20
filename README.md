# Engine Template

새 엔진을 개발할 때 이 폴더를 복사하여 시작하세요.

## 시작 방법

1. 이 폴더를 복사하여 `engines/<DEPT>_LangGraph/` 이름으로 생성합니다.
   ```
   cp -r engines/_template engines/QA_LangGraph
   ```

2. `engine.json`을 수정합니다.
   - `dept`: 부서 코드 (예: "QA")
   - `engine_id`: 고유 엔진 ID (예: "QA.langgraph.v1")
   - `description`: 엔진 설명
   - `ui` 섹션: 필요한 탭만 남기고 나머지는 제거

3. `main.py`에 엔진 로직을 구현합니다.
   - `create_engine()` 팩토리 함수가 엔진 인스턴스를 반환해야 합니다.
   - 필수 메서드: `chat_with_meta()`, `set_event_handler()`, `set_status_handler()`

4. `ui/` 폴더에 엔진 전용 UI를 구현합니다.
   - `home_widget.py`: 홈 화면 (필수 - fallback 있지만 커스텀 권장)
   - `request_page.py`: Request 탭 (선택 - engine.json에서 제거하면 탭 숨김)
   - `pc_status.py`: Remote PC 탭 (선택)

## 파일 구조

```
engines/<DEPT>_LangGraph/
├── __init__.py
├── engine.json          # 엔진 매니페스트 (UI 설정 포함)
├── main.py              # 엔진 진입점 (create_engine)
├── agents/              # 에이전트 로직 (선택)
├── tools/               # 도구 정의 (선택)
├── prompts/             # 프롬프트 (선택)
└── ui/
    ├── __init__.py
    ├── home_widget.py   # 홈 화면 위젯
    ├── request_page.py  # Request 탭 (선택)
    └── pc_status.py     # Remote PC 탭 (선택)
```

## engine.json UI 섹션

```json
{
  "ui": {
    "home_entrypoint": "ui.home_widget:HomeWidget",
    "tabs": {
      "request": {
        "entrypoint": "ui.request_page:create_page",
        "label": "Request 현황"
      },
      "remote_pc": {
        "entrypoint": "ui.pc_status:create_page",
        "label": "Remote PC 현황"
      }
    },
    "hooks": {
      "my_hook": "ui.my_hook_module"
    }
  }
}
```

- `home_entrypoint`: `모듈경로:클래스명` 형식. HomeWidget 클래스를 지정.
- `tabs.{name}.entrypoint`: `모듈경로:팩토리함수명` 형식. `create_page()` 함수를 지정.
- `tabs.{name}.label`: 네비게이션 버튼에 표시할 텍스트.
- `hooks.{name}`: 훅 모듈 경로. 동적으로 로드됨.

탭이 필요 없으면 해당 항목을 제거하면 자동으로 숨겨집니다.
