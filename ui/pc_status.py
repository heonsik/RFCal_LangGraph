# -*- coding: utf-8 -*-
"""
RFCal Engine - PC Status Page (Remote PC 현황 탭)

engine.json의 ui.tabs.remote_pc.entrypoint로 등록되어
플랫폼이 동적으로 로드하는 provider 형태의 탭 페이지.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Dict

# .env 파일 로드
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parents[3] / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
)

logger = logging.getLogger(__name__)


def _console_log(msg: str):
    try:
        from rich.console import Console
        Console().print(f"[dim][RFCal/PCStatus] {msg}[/dim]")
    except Exception:
        print(f"[RFCal/PCStatus] {msg}")


class PCStatusPageWidget(QWidget):
    """RFCal Remote PC 현황 페이지 위젯"""

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self._main_window = main_window
        self._pc_status_widget = None
        self._pc_status_enabled = False
        self._setup_ui()

    def _setup_ui(self):
        backend_url = os.getenv("BACKEND_URL", "")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setObjectName("pc_status_scroll")
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        page_layout = QVBoxLayout(content)
        page_layout.setContentsMargins(10, 10, 10, 10)
        page_layout.setSpacing(10)

        pc_title = QLabel("Remote PC 사용 현황")
        pc_title.setStyleSheet(
            "font-size: 18pt; font-weight: bold; color: #bd93f9; padding: 10px 0;"
        )
        page_layout.addWidget(pc_title)

        try:
            from widgets.pc_status_widget import PCStatusWidget

            self._pc_status_widget = PCStatusWidget(
                backend_url=backend_url or None,
                api_key=os.getenv("BACKEND_API_KEY", "")
            )
            self._pc_status_widget.setMinimumHeight(200)
            page_layout.addWidget(self._pc_status_widget)
            self._pc_status_enabled = True

            if backend_url:
                self.refresh()
            else:
                _console_log("BACKEND_URL not set, showing widget without data")
                self._pc_status_widget.status_label.setText("BACKEND_URL 미설정")

        except ImportError as e:
            _console_log(f"Failed to import PCStatusWidget: {e}")
            err_label = QLabel("PC Status 위젯을 로드할 수 없습니다.")
            err_label.setStyleSheet("color: #ff5555; font-size: 14px; padding: 20px;")
            page_layout.addWidget(err_label)
        except Exception as e:
            _console_log(f"Failed to setup PC status: {e}")
            import traceback
            traceback.print_exc()

        page_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def refresh(self):
        """PC 상태 즉시 새로고침"""
        if self._pc_status_widget is not None:
            try:
                self._pc_status_widget._on_refresh_clicked()
            except Exception as e:
                _console_log(f"Failed to refresh PC status: {e}")

    def start_polling(self):
        """PC 상태 폴링 시작"""
        if not self._pc_status_enabled or self._pc_status_widget is None:
            return
        try:
            poll_interval = int(os.getenv("PC_STATUS_POLL_INTERVAL", "5000"))
            self._pc_status_widget.start_polling(poll_interval)
        except Exception as e:
            _console_log(f"Failed to start polling: {e}")

    def stop_polling(self):
        """PC 상태 폴링 중지"""
        if self._pc_status_widget is not None:
            try:
                self._pc_status_widget.stop_polling()
            except Exception as e:
                _console_log(f"Failed to stop polling: {e}")

    def get_summary(self) -> Dict:
        """현재 PC 상태 요약 반환"""
        if self._pc_status_widget is None:
            return {"idle": 0, "busy": 0}
        try:
            from widgets.pc_status_widget import PCStatus
            summary_widget = self._pc_status_widget.summary_widget
            return {
                "idle": int(summary_widget.counts.get(PCStatus.IDLE).text() or "0"),
                "busy": int(summary_widget.counts.get(PCStatus.BUSY).text() or "0"),
            }
        except Exception:
            return {"idle": 0, "busy": 0}

    def cleanup(self):
        """위젯 정리"""
        self.stop_polling()


def create_page(main_window=None, **kwargs) -> QWidget:
    """엔진 UI provider 팩토리 함수."""
    return PCStatusPageWidget(main_window=main_window)
