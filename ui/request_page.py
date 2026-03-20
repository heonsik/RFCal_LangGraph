# -*- coding: utf-8 -*-
"""
RFCal Engine - Request Page (의뢰 현황 탭)

engine.json의 ui.tabs.request.entrypoint로 등록되어
플랫폼이 동적으로 로드하는 provider 형태의 탭 페이지.

[주의] Home 탭의 대시보드(ui/mixins/dashboard_mixin.py)와
필터/테이블 로직이 동일 패턴입니다. 수정 시 양쪽 동기화 필요.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QLineEdit, QHeaderView, QMessageBox,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import QTimer, QThread, Signal, Qt


def _console_log(msg: str):
    try:
        from rich.console import Console
        Console().print(f"[dim][RFCal/RequestPage] {msg}[/dim]")
    except Exception:
        print(f"[RFCal/RequestPage] {msg}")


class RequestFetchThread(QThread):
    """백그라운드에서 의뢰 목록을 가져오는 Worker."""
    finished_success = Signal(list, int)
    finished_error = Signal(str)

    def __init__(self, status_filter="PENDING", assignee="", days_back=30, parent=None):
        super().__init__(parent)
        self.status_filter = status_filter
        self.assignee = assignee
        self.days_back = days_back

    def run(self):
        try:
            from engines.IMEI_LangGraph.tools import fetch_request_list
            result = fetch_request_list.invoke({
                "status_filter": self.status_filter,
                "assignee": self.assignee,
                "days_back": self.days_back
            })
            if hasattr(result, 'ok') and result.ok:
                requests = result.data.get("requests", []) if result.data else []
                total_count = result.data.get("total_count", 0) if result.data else 0
                self.finished_success.emit(requests, total_count)
            elif hasattr(result, 'ok'):
                error_text = result.error if hasattr(result, 'error') else "Unknown error"
                self.finished_error.emit(error_text)
            elif isinstance(result, dict):
                requests = result.get("data", {}).get("requests", [])
                total_count = result.get("data", {}).get("total_count", 0)
                self.finished_success.emit(requests, total_count)
            else:
                self.finished_error.emit("Unknown response format")
        except Exception as e:
            _console_log(f"RequestFetchThread error: {e}")
            self.finished_error.emit(str(e)[:50])


class RequestPageWidget(QWidget):
    """RFCal 의뢰 현황 페이지 위젯"""

    # 발행 요청 시그널: (model_name, buyer, request_no)
    releaseRequested = Signal(str, str, str)

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self._main_window = main_window
        self._all_requests: list = []
        self._request_fetch_thread: QThread = None
        self._setup_ui()

    def _t(self, key: str, default: str) -> str:
        mw = self._main_window
        if mw is not None:
            i18n = getattr(mw, "_i18n", None)
            if i18n is not None:
                try:
                    return i18n.t(key, default)
                except Exception:
                    pass
        return default

    # 콤보박스 공통 스타일
    _COMBO_STYLE = (
        "QComboBox { background-color: #282a36; border: 1px solid #44475a; border-radius: 5px;"
        " color: #f8f8f2; padding: 6px 10px; font-size: 10pt; }"
        "QComboBox:focus { border-color: #bd93f9; }"
        "QComboBox::drop-down { border: none; background: transparent; width: 20px;"
        " subcontrol-origin: padding; subcontrol-position: center right; }"
        "QComboBox::down-arrow { image: none; border-left: 5px solid transparent;"
        " border-right: 5px solid transparent; border-top: 5px solid #bd93f9; }"
        "QComboBox QAbstractItemView { background-color: #282a36; border: 1px solid #44475a;"
        " color: #f8f8f2; selection-background-color: #44475a; }"
    )

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 10)
        layout.setSpacing(12)

        # 페이지 타이틀
        title_label = QLabel("TSMS 의뢰 현황")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #bd93f9;
                padding-bottom: 8px;
            }
        """)
        layout.addWidget(title_label)

        # 상단 필터/액션 바 (정상 화면과 동일한 순서로)
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # 새로고침 버튼
        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.setMinimumSize(100, 35)
        top_bar.addWidget(self.refresh_btn)

        # 발행 버튼
        self.release_btn = QPushButton("발행")
        self.release_btn.setEnabled(False)
        self.release_btn.setMinimumSize(100, 35)
        top_bar.addWidget(self.release_btn)

        # Separator
        top_bar.addSpacing(16)

        # 모델명 라벨 + 입력칸
        top_bar.addWidget(QLabel("모델명"))
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("SM-G990U")
        self.model_input.setFixedWidth(120)
        top_bar.addWidget(self.model_input)

        # 바이어(거래선) 라벨 + 입력칸
        top_bar.addWidget(QLabel("바이어"))
        self.buyer_input = QLineEdit()
        self.buyer_input.setPlaceholderText("VZW")
        self.buyer_input.setFixedWidth(80)
        top_bar.addWidget(self.buyer_input)

        # Separator
        top_bar.addSpacing(16)

        # 분류 라벨 + 드롭다운
        top_bar.addWidget(QLabel("분류"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("전체")
        self.category_filter.setFixedWidth(120)
        self.category_filter.setStyleSheet(self._COMBO_STYLE)
        top_bar.addWidget(self.category_filter)

        # 담당자 라벨 + 드롭다운
        top_bar.addWidget(QLabel("담당자"))
        self.assignee_filter = QComboBox()
        self.assignee_filter.addItem("전체")
        self.assignee_filter.setFixedWidth(120)
        self.assignee_filter.setStyleSheet(self._COMBO_STYLE)
        top_bar.addWidget(self.assignee_filter)

        # 상태 라벨 + 드롭다운
        top_bar.addWidget(QLabel("상태"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("전체")
        self.status_filter.setFixedWidth(120)
        self.status_filter.setStyleSheet(self._COMBO_STYLE)
        top_bar.addWidget(self.status_filter)

        # Spacer
        top_bar.addStretch()

        # 상태 라벨
        self.status_label = QLabel("")
        top_bar.addWidget(self.status_label)

        layout.addLayout(top_bar)

        # 테이블
        self.request_table = QTableWidget()
        self.request_table.setColumnCount(5)
        self.request_table.setHorizontalHeaderLabels(["분류", "제목", "상태", "요청일", "담당자"])
        header = self.request_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 제목 열: 나머지 공간 채우기
        self.request_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.request_table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.request_table, 1)

        # 로딩 오버레이
        self._loading_overlay = QWidget(self.request_table)
        self._loading_overlay.setStyleSheet("""
            QWidget { background-color: rgba(30, 30, 46, 220); border-radius: 8px; }
        """)
        overlay_layout = QVBoxLayout(self._loading_overlay)
        overlay_layout.setAlignment(Qt.AlignCenter)
        self._loading_label = QLabel()
        self._loading_label.setStyleSheet("""
            QLabel { color: #cdd6f4; font-size: 15px; font-weight: 500; background: transparent; }
        """)
        self._loading_label.setAlignment(Qt.AlignCenter)
        overlay_layout.addWidget(self._loading_label)

        self._spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spinner_index = 0
        self._spinner_timer = QTimer()
        self._spinner_timer.setInterval(80)
        self._spinner_timer.timeout.connect(self._update_spinner)

        self._loading_messages = [
            "의뢰 현황 불러오는 중...",
            "의뢰 제목을 선택해서 프로그램 발행을 쉽게 지시해 보세요!",
            "오늘도 같이 화이팅 해봅시다^^",
        ]
        self._message_index = 0
        self._message_timer = QTimer()
        self._message_timer.setInterval(2000)
        self._message_timer.timeout.connect(self._update_message)

        self._loading_overlay.hide()

        # 시그널 연결
        self.refresh_btn.clicked.connect(self.refresh_request_list)
        self.release_btn.clicked.connect(self._on_release_clicked)
        self.model_input.textChanged.connect(self._auto_uppercase_model)
        self.buyer_input.textChanged.connect(self._auto_uppercase_buyer)
        self.request_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.request_table.doubleClicked.connect(self._on_release_clicked)
        self.category_filter.currentTextChanged.connect(self._on_filter_changed)
        self.assignee_filter.currentTextChanged.connect(self._on_filter_changed)
        self.status_filter.currentTextChanged.connect(self._on_filter_changed)

    # --- 공개 API ---

    def refresh_request_list(self):
        """의뢰 목록 새로고침"""
        if self._request_fetch_thread and self._request_fetch_thread.isRunning():
            return
        self.refresh_btn.setEnabled(False)
        self._show_loading(True)
        self._request_fetch_thread = RequestFetchThread()
        self._request_fetch_thread.finished_success.connect(self._on_fetch_success)
        self._request_fetch_thread.finished_error.connect(self._on_fetch_error)
        self._request_fetch_thread.finished.connect(self._on_fetch_finished)
        self._request_fetch_thread.start()

    def cleanup(self):
        """위젯 정리"""
        self._spinner_timer.stop()
        self._message_timer.stop()
        if self._request_fetch_thread and self._request_fetch_thread.isRunning():
            self._request_fetch_thread.quit()
            self._request_fetch_thread.wait(3000)

    # --- 내부 메서드 ---

    @staticmethod
    def _fit_popup_width(combo):
        """드롭다운 팝업 너비를 가장 긴 항목에 맞춤"""
        fm = combo.fontMetrics()
        max_w = combo.width()
        for i in range(combo.count()):
            w = fm.horizontalAdvance(combo.itemText(i)) + 40
            if w > max_w:
                max_w = w
        combo.view().setMinimumWidth(max_w)

    def _on_fetch_success(self, requests, total_count):
        self._all_requests = sorted(requests, key=lambda x: x.get("request_date", ""), reverse=True)
        self._update_category_filter()
        self._update_assignee_filter()
        self._update_status_filter()
        self._apply_filter_and_display()
        self.status_label.setText(
            self._t("dashboard.status.total", "Total {count}").format(count=total_count)
        )

    def _on_fetch_error(self, error):
        self.status_label.setText(
            self._t("dashboard.status.error", "Error: {error}").format(error=error)
        )
        self._all_requests = []
        self._apply_filter_and_display()

    def _on_fetch_finished(self):
        self.refresh_btn.setEnabled(True)
        self._show_loading(False)

    def _update_category_filter(self):
        current = self.category_filter.currentText()
        categories = sorted({(r.get("category") or "").strip() for r in self._all_requests if (r.get("category") or "").strip()})
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("전체")
        for c in categories:
            self.category_filter.addItem(c)
        idx = self.category_filter.findText(current)
        if idx >= 0:
            self.category_filter.setCurrentIndex(idx)
        self.category_filter.blockSignals(False)
        self._fit_popup_width(self.category_filter)

    def _update_assignee_filter(self):
        current = self.assignee_filter.currentText()
        assignees = sorted({(r.get("assignee") or "").strip() for r in self._all_requests if (r.get("assignee") or "").strip()})
        self.assignee_filter.blockSignals(True)
        self.assignee_filter.clear()
        self.assignee_filter.addItem("전체")
        for a in assignees:
            self.assignee_filter.addItem(a)
        idx = self.assignee_filter.findText(current)
        if idx >= 0:
            self.assignee_filter.setCurrentIndex(idx)
        self.assignee_filter.blockSignals(False)
        self._fit_popup_width(self.assignee_filter)

    def _update_status_filter(self):
        current = self.status_filter.currentText()
        statuses = sorted({(r.get("status") or "").strip() for r in self._all_requests if (r.get("status") or "").strip()})
        self.status_filter.blockSignals(True)
        self.status_filter.clear()
        self.status_filter.addItem("전체")
        for s in statuses:
            self.status_filter.addItem(s)
        idx = self.status_filter.findText(current)
        if idx >= 0:
            self.status_filter.setCurrentIndex(idx)
        self.status_filter.blockSignals(False)
        self._fit_popup_width(self.status_filter)

    def _on_filter_changed(self, _text):
        self._apply_filter_and_display()

    def _apply_filter_and_display(self):
        cat = self.category_filter.currentText()
        asg = self.assignee_filter.currentText()
        sts = self.status_filter.currentText()
        filtered = self._all_requests
        if cat != "전체":
            filtered = [r for r in filtered if (r.get("category") or "").strip() == cat]
        if asg != "전체":
            filtered = [r for r in filtered if (r.get("assignee") or "").strip() == asg]
        if sts != "전체":
            filtered = [r for r in filtered if (r.get("status") or "").strip() == sts]
        self._populate_table(filtered)

    def _populate_table(self, requests):
        table = self.request_table
        table.setRowCount(0)
        if not requests:
            return
        table.setRowCount(len(requests))
        status_colors = {"PENDING": "#f1fa8c", "IN_PROGRESS": "#50fa7b", "COMPLETED": "#6272a4"}
        for row, req in enumerate(requests):
            table.setItem(row, 0, QTableWidgetItem(req.get("category", "")))
            table.setItem(row, 1, QTableWidgetItem(req.get("title", "")))
            status = req.get("status", "")
            item_status = QTableWidgetItem(status)
            if status in status_colors:
                item_status.setForeground(QColor(status_colors[status]))
            table.setItem(row, 2, item_status)
            table.setItem(row, 3, QTableWidgetItem(req.get("request_date", "")))
            table.setItem(row, 4, QTableWidgetItem(req.get("assignee", "")))

    def _auto_uppercase_model(self, text):
        upper = text.upper()
        if upper != text:
            pos = self.model_input.cursorPosition()
            self.model_input.setText(upper)
            self.model_input.setCursorPosition(pos)

    def _auto_uppercase_buyer(self, text):
        upper = text.upper()
        if upper != text:
            pos = self.buyer_input.cursorPosition()
            self.buyer_input.setText(upper)
            self.buyer_input.setCursorPosition(pos)

    def _on_selection_changed(self):
        selected = self.request_table.selectedItems()
        self.release_btn.setEnabled(len(selected) > 0)
        row = self.request_table.currentRow()
        if row < 0:
            return
        cat = self.category_filter.currentText()
        asg = self.assignee_filter.currentText()
        sts = self.status_filter.currentText()
        filtered = self._all_requests
        if cat != "전체":
            filtered = [r for r in filtered if (r.get("category") or "").strip() == cat]
        if asg != "전체":
            filtered = [r for r in filtered if (r.get("assignee") or "").strip() == asg]
        if sts != "전체":
            filtered = [r for r in filtered if (r.get("status") or "").strip() == sts]
        if row < len(filtered):
            req = filtered[row]
            self.model_input.setText(req.get("model_name", ""))
            self.buyer_input.setText(req.get("buyer", ""))
            self._selected_request_no = req.get("request_no", "")
        else:
            self.model_input.setText("")
            self.buyer_input.setText("")
            self._selected_request_no = ""

    def _on_release_clicked(self):
        model_name = self.model_input.text().strip()
        buyer = self.buyer_input.text().strip().upper()
        if not model_name or not buyer:
            return
        import re
        if not re.match(r'^[A-Z]{3}$', buyer):
            QMessageBox.warning(
                self, self._t("dashboard.error.title", "입력 오류"),
                self._t("dashboard.error.invalid_buyer", "거래선은 3자리 영문 코드여야 합니다. (예: ATT, VZW)")
            )
            return
        request_no = getattr(self, "_selected_request_no", "")
        self.releaseRequested.emit(model_name, buyer, request_no)

    def _show_loading(self, show):
        if show:
            self._loading_overlay.setGeometry(0, 0, self.request_table.width(), self.request_table.height())
            self._loading_overlay.raise_()
            self._loading_overlay.show()
            self._spinner_index = 0
            self._message_index = 0
            self._update_spinner()
            self._spinner_timer.start()
            self._message_timer.start()
        else:
            self._spinner_timer.stop()
            self._message_timer.stop()
            self._loading_overlay.hide()

    def _update_spinner(self):
        self._spinner_index = (self._spinner_index + 1) % len(self._spinner_frames)
        spinner = self._spinner_frames[self._spinner_index]
        message = self._loading_messages[self._message_index]
        self._loading_label.setText(f"{spinner} {message}")

    def _update_message(self):
        self._message_index = (self._message_index + 1) % len(self._loading_messages)


def create_page(main_window=None, **kwargs) -> QWidget:
    """엔진 UI provider 팩토리 함수.

    engine_ui_loader가 호출하며, 반환된 위젯이 stackedWidget에 삽입된다.
    """
    page = RequestPageWidget(main_window=main_window)

    # 발행 요청 시그널을 MainWindow에 연결
    if main_window is not None:
        def _on_release(model_name, buyer, request_no):
            main_window._set_nav_selection("chat")
            main_window._create_chat_session(force_imei=True)
            session = main_window._get_selected_session()
            if session:
                session["is_auto_generated"] = True
                main_window._schedule_save_all_sessions()
            QTimer.singleShot(100, lambda: _send_release(main_window, model_name, buyer, request_no))

        def _send_release(mw, model_name, buyer, request_no):
            session = mw._get_selected_session()
            if not session:
                return
            i18n = getattr(mw, "_i18n", None)
            if i18n:
                try:
                    msg = i18n.t("dashboard.release_message", "Please release {model} {buyer} (request_no: {request_no})")
                except Exception:
                    msg = "Please release {model} {buyer} (request_no: {request_no})"
            else:
                msg = "Please release {model} {buyer} (request_no: {request_no})"
            mw.chat_input.setPlainText(msg.format(model=model_name, buyer=buyer, request_no=request_no))
            mw._send_message()

        page.releaseRequested.connect(_on_release)

    return page
