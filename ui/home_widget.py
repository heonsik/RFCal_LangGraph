# -*- coding: utf-8 -*-
"""
HomeWidget - 앱 소개 및 빠른 시작 화면
PyDracula 테마와 일관성 있는 스타일 적용
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QFrame, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QCursor
from PySide6.QtWidgets import QGraphicsOpacityEffect


class HomeWidget(QWidget):
    """앱 홈 화면 위젯"""

    # 탭 전환 시그널: tab_name을 emit
    tabChangeRequested = Signal(str)
    # 현재 엔진(RFCal)으로 새 채팅 세션 생성 요청 — dept-neutral 이름.
    # 근거: docs/engine_app_decoupling_analysis.md §5 우선순위 9.
    newEngineSessionRequested = Signal()
    # 호환용 alias: 기존 main_window 슬롯이 newImeiSessionRequested를 받기 때문에
    # transition 기간 동안 둘 다 emit. (docs/개발체크리스트.md 부록 D)
    newImeiSessionRequested = Signal()
    # DeepAgent(일반 대화) 엔진으로 새 채팅 세션 생성 요청
    newDeepagentSessionRequested = Signal()
    # 엔진 선택 팝업 포함 새 채팅 세션 생성 요청
    newChatWithPopupRequested = Signal()

    # PyDracula 테마 색상
    COLORS = {
        'bg_primary': '#1e1e2e',
        'bg_secondary': '#282a36',
        'bg_card': '#2b2d3e',
        'bg_card_hover': '#333550',
        'border': '#44475a',
        'text_primary': '#f8f8f2',
        'text_secondary': '#8888a0',
        'text_muted': '#6272a4',
        'accent_purple': '#bd93f9',
        'accent_pink': '#ff79c6',
        'accent_green': '#50fa7b',
        'accent_cyan': '#8be9fd',
        'accent_orange': '#ffb86c',
        'accent_yellow': '#f1fa8c',
        'accent_red': '#ff5555',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HomeWidget")
        self._setup_ui()

    def _emit_new_session(self):
        """현재 엔진 세션 생성 요청 — transition 기간 동안 신/구 signal 모두 emit."""
        self.newEngineSessionRequested.emit()
        self.newImeiSessionRequested.emit()

    def _setup_ui(self):
        """UI 구성"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setObjectName("homeScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {self.COLORS['bg_secondary']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.COLORS['border']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.COLORS['text_muted']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        # 스크롤 내부 컨텐츠
        content = QWidget()
        content.setObjectName("homeContent")
        content.setStyleSheet("background: transparent;")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(48, 40, 48, 40)
        content_layout.setSpacing(0)

        # 섹션들 추가
        self._add_header_section(content_layout)
        self._add_modes_section(content_layout)
        self._add_features_section(content_layout)

        # 하단 여백
        content_layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _add_header_section(self, layout):
        """상단 앱 소개 섹션"""
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 40)
        header_layout.setSpacing(8)

        # 앱 뱃지 - engine.json에서 버전 읽기
        engine_version = "0.2.0a10"
        try:
            import json
            from pathlib import Path
            engine_json = Path(__file__).parent.parent / "engine.json"
            if engine_json.exists():
                with open(engine_json, 'r', encoding='utf-8') as f:
                    engine_data = json.load(f)
                engine_version = engine_data.get("version", engine_version)
        except Exception:
            pass

        badge = QWidget()
        badge.setFixedHeight(32)
        badge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        badge.setStyleSheet(f"""
            QWidget {{
                background: rgba(189, 147, 249, 0.15);
                border: 1px solid rgba(189, 147, 249, 0.25);
                border-radius: 16px;
            }}
        """)
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(14, 0, 14, 0)
        badge_layout.setSpacing(6)

        # 초록 동그라미 (깜빡임 애니메이션)
        dot = QLabel("●")
        dot.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {self.COLORS['accent_green']};
                background: transparent;
                border: none;
            }}
        """)
        dot.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        dot_opacity = QGraphicsOpacityEffect(dot)
        dot.setGraphicsEffect(dot_opacity)
        self._dot_anim = QPropertyAnimation(dot_opacity, b"opacity")
        self._dot_anim.setDuration(1500)
        self._dot_anim.setStartValue(1.0)
        self._dot_anim.setKeyValueAt(0.5, 0.3)
        self._dot_anim.setEndValue(1.0)
        self._dot_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._dot_anim.setLoopCount(-1)
        self._dot_anim.start()

        badge_layout.addWidget(dot)

        # 텍스트 (보라색)
        badge_text = QLabel(f"RFCal Engine v{engine_version}")
        badge_text.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {self.COLORS['accent_purple']};
                font-weight: 500;
                background: transparent;
                border: none;
            }}
        """)
        badge_layout.addWidget(badge_text)

        header_layout.addWidget(badge)

        # 제목
        title = QLabel("RFCal Release Agent")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                font-weight: bold;
                color: {self.COLORS['text_primary']};
                padding-top: 8px;
            }}
        """)
        header_layout.addWidget(title)

        # 설명
        desc = QLabel(
            "RFCal 프로그램 검증과 발행을 AI 에이전트가 자동으로 처리합니다.\n"
            "채팅에서 모델명과 거래선 코드를 입력하면 바로 시작할 수 있습니다."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                color: {self.COLORS['text_secondary']};
                line-height: 1.6;
            }}
        """)
        header_layout.addWidget(desc)

        layout.addWidget(header)

    def _add_modes_section(self, layout):
        """3개 모드 카드 섹션"""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 44)
        section_layout.setSpacing(16)

        # 섹션 제목
        title = QLabel("채팅 한 줄이면 무엇이든")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 500;
                color: {self.COLORS['text_muted']};
                text-transform: uppercase;
                letter-spacing: 1.5px;
            }}
        """)
        section_layout.addWidget(title)

        # 카드 컨테이너
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(14)

        # TASK 카드 (1.4배 넓게)
        task_card = self._create_mode_card(
            badge_text="TASK",
            badge_color=self.COLORS['accent_purple'],
            title="검증 · 발행 업무",
            desc="프로그램 검증부터 발행까지 자동 수행",
            flow_text="의뢰 접수 → 프로그램 제작 → 프로그램 검증 → 발행",
            examples=[
                '"RF 프로그램 발행해줘"',
                '"Cal 테스트 해봐"',
            ],
            hover_color=self.COLORS['accent_purple']
        )
        task_card.mousePressEvent = lambda e: self._emit_new_session()
        cards_layout.addWidget(task_card, 1)

        # QUERY 카드
        query_card = self._create_mode_card(
            badge_text="QUERY",
            badge_color=self.COLORS['accent_cyan'],
            title="정보 조회",
            desc="담당자, 에러코드, 모델 정보를 즉시 검색",
            flow_text="질문 입력 → 즉시 응답",
            examples=[
                '"SM-A111X 담당자 누구야?"',
                '"불량 조회해줘"',
            ],
            hover_color=self.COLORS['accent_cyan']
        )
        query_card.mousePressEvent = lambda e: self._emit_new_session()
        cards_layout.addWidget(query_card, 1)

        # CHAT 카드
        chat_card = self._create_mode_card(
            badge_text="CHAT",
            badge_color=self.COLORS['accent_orange'],
            title="일반 대화 · 파일",
            desc="업무 외 질의, 로컬 파일 접근 및 분석",
            flow_text="자유 입력 → AI 응답",
            examples=[
                '"이 로그 파일 분석해줘"',
                '"RFCal 발행 절차 설명해줘"',
            ],
            hover_color=self.COLORS['accent_orange']
        )
        chat_card.mousePressEvent = lambda e: self.newDeepagentSessionRequested.emit()
        cards_layout.addWidget(chat_card, 1)

        section_layout.addWidget(cards_container)
        layout.addWidget(section)

    def _create_mode_card(self, badge_text, badge_color, title, desc, flow_text, examples, hover_color):
        """모드 카드 생성"""
        card = QFrame()
        card.setObjectName(f"modeCard_{badge_text}")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setStyleSheet(f"""
            QFrame#modeCard_{badge_text} {{
                background: {self.COLORS['bg_card']};
                border: 1px solid {self.COLORS['border']};
                border-radius: 14px;
            }}
            QFrame#modeCard_{badge_text}:hover {{
                border-color: {hover_color};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # 헤더 (뱃지 + 제목)
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        # 뱃지
        badge = QLabel(badge_text)
        badge.setStyleSheet(f"""
            QLabel {{
                background: rgba({self._hex_to_rgb(badge_color)}, 0.2);
                color: {badge_color};
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 3px 8px;
                border-radius: 5px;
                font-family: 'Consolas', 'Monaco', monospace;
            }}
        """)
        badge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        header_layout.addWidget(badge)

        # 제목
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: 600;
                color: {self.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addWidget(header)

        # 설명
        desc_label = QLabel(desc)
        desc_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {self.COLORS['text_secondary']};
                line-height: 1.5;
            }}
        """)
        layout.addWidget(desc_label)

        # 플로우 다이어그램 (단순 텍스트)
        flow_label = QLabel(flow_text)
        flow_label.setWordWrap(True)
        flow_label.setStyleSheet(f"""
            QLabel {{
                background: rgba(0, 0, 0, 0.15);
                border-radius: 8px;
                padding: 10px 12px;
                color: {self.COLORS['text_secondary']};
                font-size: 12px;
            }}
        """)
        layout.addWidget(flow_label)

        # 예시들
        for example in examples:
            ex_label = QLabel(example)
            ex_label.setStyleSheet(f"""
                QLabel {{
                    background: rgba(0, 0, 0, 0.12);
                    border-left: 2px solid {badge_color};
                    border-radius: 6px;
                    padding: 5px 10px;
                    font-size: 12px;
                    color: {self.COLORS['text_muted']};
                    font-family: 'Consolas', 'Monaco', monospace;
                }}
            """)
            layout.addWidget(ex_label)

        return card

    def _add_features_section(self, layout):
        """기능 카드 4개 섹션"""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 44)
        section_layout.setSpacing(16)

        # 섹션 제목
        title = QLabel("기능 안내")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 500;
                color: {self.COLORS['text_muted']};
                text-transform: uppercase;
                letter-spacing: 1.5px;
            }}
        """)
        section_layout.addWidget(title)

        # 1x4 한 줄 배치
        grid_widget = QWidget()
        grid = QHBoxLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(14)

        # 기능 카드들
        features = [
            {
                'icon': '💬',
                'color': self.COLORS['accent_pink'],
                'title': 'AI 채팅',
                'desc': '자연어로 에이전트에게 프로그램 발행을 요청하고, 진행 상황을 확인합니다.',
                'tab': '_chat_with_popup'
            },
            {
                'icon': '📋',
                'color': self.COLORS['accent_cyan'],
                'title': '작업 로그',
                'desc': '에이전트의 모든 작업 이력과 검증 결과를 상세히 확인할 수 있습니다.',
                'tab': 'logs'
            },
            {
                'icon': '🖥️',
                'color': self.COLORS['accent_green'],
                'title': 'Remote PC 현황',
                'desc': '원격 PC의 연결 상태를 확인하고, Idle/Busy/Reserved 현황을 관리합니다.',
                'tab': 'pc_status'
            },
        ]

        for i, feat in enumerate(features):
            card = self._create_feature_card(
                icon=feat['icon'],
                color=feat['color'],
                title=feat['title'],
                desc=feat['desc'],
                tab_name=feat['tab']
            )
            grid.addWidget(card, 1)

        section_layout.addWidget(grid_widget)
        layout.addWidget(section)

    def _create_feature_card(self, icon, color, title, desc, tab_name):
        """기능 카드 생성"""
        card = QFrame()
        card.setObjectName(f"featureCard_{title.replace(' ', '_')}")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setProperty("tab_name", tab_name)

        card.setStyleSheet(f"""
            QFrame#featureCard_{title.replace(' ', '_')} {{
                background: {self.COLORS['bg_card']};
                border: 1px solid {self.COLORS['border']};
                border-radius: 14px;
            }}
            QFrame#featureCard_{title.replace(' ', '_')}:hover {{
                background: {self.COLORS['bg_card_hover']};
                border-color: rgba({self._hex_to_rgb(self.COLORS['accent_purple'])}, 0.3);
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 22, 20, 22)
        layout.setSpacing(6)

        # 아이콘
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                background: rgba({self._hex_to_rgb(color)}, 0.15);
                border-radius: 10px;
                padding: 8px;
                font-size: 18px;
            }}
        """)
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        layout.addSpacing(8)

        # 제목
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: 600;
                color: {self.COLORS['text_primary']};
            }}
        """)
        layout.addWidget(title_label)

        # 설명
        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {self.COLORS['text_secondary']};
                line-height: 1.55;
            }}
        """)
        layout.addWidget(desc_label)

        # 바로가기 링크
        link = QLabel("바로가기 →")
        link.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {self.COLORS['accent_purple']};
                font-weight: 500;
                padding-top: 8px;
            }}
        """)
        layout.addWidget(link)

        # 클릭 이벤트
        card.mousePressEvent = lambda e, t=tab_name: self._on_feature_card_clicked(t)

        return card

    def _on_feature_card_clicked(self, tab_name):
        """기능 카드 클릭 시 해당 탭으로 전환 시그널 emit"""
        if tab_name == '_chat_with_popup':
            self.newChatWithPopupRequested.emit()
        else:
            self.tabChangeRequested.emit(tab_name)

    def _add_quickstart_section(self, layout):
        """빠른 시작 배너"""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 40)
        section_layout.setSpacing(16)

        # 섹션 제목
        title = QLabel("빠른 시작")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 500;
                color: {self.COLORS['text_muted']};
                text-transform: uppercase;
                letter-spacing: 1.5px;
            }}
        """)
        section_layout.addWidget(title)

        # 배너 박스
        banner = QFrame()
        banner.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(189, 147, 249, 0.08),
                    stop:1 rgba(255, 121, 198, 0.05)
                );
                border: 1px solid rgba(189, 147, 249, 0.2);
                border-radius: 14px;
            }}
        """)

        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(28, 24, 28, 24)
        banner_layout.setSpacing(20)

        # 텍스트
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        text_title = QLabel("채팅에 자유롭게 입력하면, 에이전트가 자동으로 분류합니다")
        text_title.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: 600;
                color: {self.COLORS['text_primary']};
            }}
        """)
        text_layout.addWidget(text_title)

        text_desc = QLabel("업무 요청, 정보 조회, 일반 질의를 구분할 필요 없이 그냥 말하세요.")
        text_desc.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {self.COLORS['text_secondary']};
            }}
        """)
        text_layout.addWidget(text_desc)

        banner_layout.addWidget(text_widget, 1)

        # 채팅 이동 버튼
        chat_btn = QPushButton("💬 채팅으로 이동")
        chat_btn.setCursor(QCursor(Qt.PointingHandCursor))
        chat_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.COLORS['accent_purple']};
                color: {self.COLORS['bg_primary']};
                border: none;
                border-radius: 10px;
                padding: 10px 22px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: #c9a3ff;
            }}
            QPushButton:pressed {{
                background: #a77de8;
            }}
        """)
        chat_btn.clicked.connect(lambda: self.tabChangeRequested.emit('chat'))
        banner_layout.addWidget(chat_btn)

        section_layout.addWidget(banner)
        layout.addWidget(section)

    def _add_version_info(self, layout):
        """버전 정보"""
        version_widget = QWidget()
        version_layout = QHBoxLayout(version_widget)
        version_layout.setContentsMargins(0, 8, 0, 0)
        version_layout.setSpacing(16)

        # 버전 파일에서 읽기 시도
        version_text = "v1.0.6"
        try:
            from pathlib import Path
            version_file = Path(__file__).parent.parent / "VERSION"
            if version_file.exists():
                version_text = f"v{version_file.read_text(encoding='utf-8').strip()}"
        except Exception:
            pass

        labels = [version_text, "·", "Process S/W R&D Group"]

        for text in labels:
            label = QLabel(text)
            label.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    color: {self.COLORS['text_muted']};
                    font-family: 'Consolas', 'Monaco', monospace;
                }}
            """)
            version_layout.addWidget(label)

        version_layout.addStretch()

        version_widget.setStyleSheet("")

        layout.addWidget(version_widget)

    def _hex_to_rgb(self, hex_color):
        """#RRGGBB를 R, G, B로 변환"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"
