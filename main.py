# -*- coding: utf-8 -*-
"""Template Engine - 새 엔진 개발 시 이 파일을 복사하여 시작하세요.

engine.json의 entrypoint가 "main:create_engine"이므로
이 파일의 create_engine() 함수가 엔진 인스턴스를 반환해야 합니다.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TemplateEngine:
    """엔진 뼈대 클래스.

    필수 인터페이스:
    - set_event_handler(handler): 도구 실행 이벤트 핸들러 등록
    - set_status_handler(handler): 상태 업데이트 핸들러 등록
    - chat_with_meta(messages, workdir, session_id, pending_action_response):
        메인 대화 처리. 반환값: (output_lines, is_complete, direct_response, trace_id)
    - get_tool_snapshot(): 도구 목록 스냅샷 반환
    """

    def __init__(self):
        self._event_handler = None
        self._status_handler = None

    def set_event_handler(self, handler):
        self._event_handler = handler

    def set_status_handler(self, handler):
        self._status_handler = handler

    def chat_with_meta(
        self,
        messages: List[Dict],
        workdir: str,
        session_id: str,
        pending_action_response: Optional[Dict] = None,
    ) -> tuple:
        """메인 대화 처리.

        Returns:
            (output_lines, is_complete, direct_response, trace_id)
        """
        # TODO: 엔진 로직 구현
        return (["Hello from Template Engine!"], True, "Hello!", None)

    def get_tool_snapshot(self) -> Dict[str, Any]:
        """도구 목록 스냅샷."""
        return {"tools": []}


def create_engine() -> TemplateEngine:
    """엔진 팩토리 함수 (engine.json entrypoint)."""
    return TemplateEngine()
