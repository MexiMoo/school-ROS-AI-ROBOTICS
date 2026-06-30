import os

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QProgressBar,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QGroupBox,
    QTextEdit, QFrame, QSizePolicy, QComboBox
)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont, QTextCursor
from PyQt5.QtCore import Qt, QTimer, QTime

import config
from ros_interface import STATE_LABELS

ACCENT         = config.ACCENT_COLOR
BG_DARK        = "#1a1d23"
BG_PANEL       = "#232730"
BG_PANEL_2     = "#2b3039"
TEXT_PRIMARY   = "#e8eaed"
TEXT_SECONDARY = "#9aa0a8"
BORDER         = "#3a3f4a"
COLOR_OK       = "#4caf82"
COLOR_WARN     = "#e8a23d"
COLOR_DANGER   = "#e2483d"
COLOR_INFO     = "#3f8efc"
COLOR_IDLE     = "#5b6470"

STATE_COLORS = {
    "idle":       COLOR_IDLE,
    "warming_up": COLOR_IDLE,
    "resetting":  COLOR_IDLE,
    "recording":  COLOR_INFO,
    "saving":     COLOR_WARN,
    "training":   COLOR_WARN,
    "stopped":    COLOR_IDLE,
    "autonomous": COLOR_OK,
    "estop":      COLOR_DANGER,
}

MODE_COLORS = {
    "ros":   COLOR_OK,
    "mock":  COLOR_WARN,
    "error": COLOR_DANGER,
    None:    TEXT_SECONDARY,
}

MODE_LABELS = {
    "ros":   "ROS2 VERBONDEN",
    "mock":  "DEMO-MODUS",
    "error": "FOUT",
    None:    "INITIALISEREN...",
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}}
QGroupBox {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 14px;
    padding: 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {ACCENT};
}}
QPushButton {{
    background-color: {BG_PANEL_2};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 8px;
    color: {TEXT_PRIMARY};
}}
QPushButton:hover {{ border: 1px solid {ACCENT}; }}
QPushButton:disabled {{ color: {TEXT_SECONDARY}; background-color: {BG_PANEL}; }}
QComboBox {{
    background-color: {BG_PANEL_2};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 6px;
    color: {TEXT_PRIMARY};
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
}}
QTableWidget {{
    background-color: {BG_PANEL_2};
    border: 1px solid {BORDER};
    gridline-color: {BORDER};
}}
QHeaderView::section {{
    background-color: {BG_PANEL};
    color: {TEXT_SECONDARY};
    border: none;
    padding: 4px;
}}
QProgressBar {{
    background-color: {BG_PANEL_2};
    border: 1px solid {BORDER};
    border-radius: 4px;
    text-align: center;
    color: {TEXT_PRIMARY};
}}
QProgressBar::chunk {{ background-color: {ACCENT}; border-radius: 4px; }}
QTextEdit {{
    background-color: #14171c;
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    font-family: "Consolas", "DejaVu Sans Mono", monospace;
    font-size: 12px;
}}
"""


class MainWindow(QMainWindow):
    def __init__(self, ros_worker):
        super().__init__()
        self.ros_worker = ros_worker
        self.setWindowTitle(f"{config.APP_TITLE} – Avans Hogeschool Breda")
        self.resize(1100, 720)
        self.setStyleSheet(STYLESHEET)

        self._last_grip_point = None
        self._current_mode = None
        self._current_state = "idle"

        self._build_ui()
        self._connect_signals()
        self._start_clock()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(10)

        root.addWidget(self._build_header())
        root.addWidget(self._build_state_strip())

        body = QHBoxLayout()
        body.addWidget(self._build_camera_box(), stretch=2)
        body.addWidget(self._build_side_panel(), stretch=1)
        root.addLayout(body, stretch=3)

        root.addWidget(self._build_log_box(), stretch=1)
        self.statusBar().showMessage("Topics & instellingen: config.py  |  HMI_MODE env var")

    def _build_header(self):
        header = QFrame()
        header.setFrameShape(QFrame.NoFrame)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(160, 48)
        if os.path.isfile(config.LOGO_PATH):
            pixmap = QPixmap(config.LOGO_PATH).scaledToHeight(48, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
            self.logo_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        else:
            self.logo_label.setText("LOGO HIER")
            self.logo_label.setAlignment(Qt.AlignCenter)
            self.logo_label.setStyleSheet(
                f"border: 1px dashed {BORDER}; border-radius: 4px; color: {TEXT_SECONDARY}; font-size: 11px;"
            )
        layout.addWidget(self.logo_label)

        title_block = QVBoxLayout()
        title_label = QLabel(config.APP_TITLE)
        title_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT_PRIMARY};")
        cell_label = QLabel(config.CELL_NAME)
        cell_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        title_block.addWidget(title_label)
        title_block.addWidget(cell_label)
        layout.addLayout(title_block)
        layout.addStretch(1)

        badge_block = QVBoxLayout()
        badge_block.setSpacing(2)
        self.mode_badge = QLabel("●  INITIALISEREN...")
        self.mode_badge.setAlignment(Qt.AlignRight)
        self.mode_badge.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600;")
        badge_block.addWidget(self.mode_badge)
        self.clock_label = QLabel("--:--:--")
        self.clock_label.setAlignment(Qt.AlignRight)
        self.clock_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-family: Consolas, monospace; font-size: 12px;"
        )
        badge_block.addWidget(self.clock_label)
        layout.addLayout(badge_block)
        return header

    def _build_state_strip(self):
        self.state_strip = QLabel(STATE_LABELS["idle"])
        self.state_strip.setAlignment(Qt.AlignCenter)
        self.state_strip.setFixedHeight(30)
        self._style_state_strip("idle")
        return self.state_strip

    def _style_state_strip(self, state: str):
        color = STATE_COLORS.get(state, COLOR_IDLE)
        self.state_strip.setText(f"STATUS:  {STATE_LABELS.get(state, state.upper())}")
        self.state_strip.setStyleSheet(
            f"background-color: {color}; color: #14171c; font-weight: 700; "
            f"border-radius: 4px; letter-spacing: 1px;"
        )

    def _build_camera_box(self):
        box = QGroupBox("Camera / Vision (monitor-modus)")
        layout = QVBoxLayout()
        self.image_label = QLabel("Wacht op beeld...")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(480, 360)
        self.image_label.setStyleSheet(f"background-color: #0e1014; color: {TEXT_SECONDARY};")
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.image_label)
        box.setLayout(layout)
        return box

    def _build_side_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self._build_joint_box())
        layout.addWidget(self._build_ai_box())
        layout.addWidget(self._build_model_box())
        layout.addWidget(self._build_cmd_box())
        return panel

    def _build_joint_box(self):
        box = QGroupBox("Robot status (joint states)")
        layout = QVBoxLayout()
        self.joint_table = QTableWidget(0, 2)
        self.joint_table.setHorizontalHeaderLabels(["Joint", "Positie (rad)"])
        self.joint_table.horizontalHeader().setStretchLastSection(True)
        self.joint_table.verticalHeader().setVisible(False)
        self.joint_table.setMinimumHeight(70)
        layout.addWidget(self.joint_table)
        box.setLayout(layout)
        return box

    def _build_ai_box(self):
        box = QGroupBox("AI status")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Voortgang:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        layout.addWidget(QLabel("Confidence score:"))
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        layout.addWidget(self.confidence_bar)

        self.confidence_label = QLabel("Confidence: -- (geen data)")
        self.confidence_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self.confidence_label)
        box.setLayout(layout)
        return box

    def _build_model_box(self):
        """Model selectie — dropdown + laden + stoppen."""
        box = QGroupBox("AI model")
        layout = QVBoxLayout()

        # Dropdown met modellen
        self.model_combo = QComboBox()
        self.model_combo.addItem("— selecteer model —")
        # Standaard model alvast toevoegen vanuit config
        self.model_combo.addItem("Syntax-Terror-BV FINAL", userData=config.DEFAULT_POLICY_PATH)
        self.model_combo.setCurrentIndex(1)  # direct geselecteerd
        layout.addWidget(self.model_combo)

        # Vernieuwen knop
        btn_refresh = QPushButton("Vernieuwen")
        btn_refresh.clicked.connect(self._refresh_models)
        layout.addWidget(btn_refresh)

        # Start / Stop knoppen naast elkaar
        btn_row = QHBoxLayout()
        self.btn_start_model = QPushButton("▶  Start model")
        self.btn_start_model.setStyleSheet(
            f"background-color: {COLOR_OK}; color: #14171c; font-weight: 700;"
        )
        self.btn_start_model.clicked.connect(self._start_selected_model)
        btn_row.addWidget(self.btn_start_model)

        self.btn_stop_model = QPushButton("■  Stop model")
        self.btn_stop_model.setStyleSheet(
            f"background-color: {BG_PANEL_2}; color: {TEXT_PRIMARY};"
        )
        self.btn_stop_model.clicked.connect(self.ros_worker.stop_inference)
        btn_row.addWidget(self.btn_stop_model)
        layout.addLayout(btn_row)

        box.setLayout(layout)
        return box

    def _build_cmd_box(self):
        box = QGroupBox("Besturing")
        layout = QVBoxLayout()

        self.btn_robot_start = QPushButton("Start robot")
        self.btn_robot_start.clicked.connect(lambda: self.ros_worker.send_command("start_robot"))
        layout.addWidget(self.btn_robot_start)

        self.btn_robot_stop = QPushButton("Stop robot")
        self.btn_robot_stop.clicked.connect(lambda: self.ros_worker.send_command("stop_robot"))
        layout.addWidget(self.btn_robot_stop)

        self.btn_estop = QPushButton("NOODSTOP")
        self.btn_estop.setStyleSheet(
            f"background-color: {COLOR_DANGER}; color: white; font-weight: 700; padding: 10px;"
        )
        self.btn_estop.clicked.connect(lambda: self.ros_worker.send_command("emergency_stop"))
        layout.addWidget(self.btn_estop)

        self.btn_reset_estop = QPushButton("Reset noodstop")
        self.btn_reset_estop.setEnabled(False)
        self.btn_reset_estop.clicked.connect(lambda: self.ros_worker.send_command("reset_estop"))
        layout.addWidget(self.btn_reset_estop)

        box.setLayout(layout)
        return box

    def _build_log_box(self):
        box = QGroupBox("Logboek")
        layout = QVBoxLayout()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(130)
        layout.addWidget(self.log_view)
        box.setLayout(layout)
        return box

    def _start_clock(self):
        self._tick_clock()
        timer = QTimer(self)
        timer.timeout.connect(self._tick_clock)
        timer.start(1000)
        self._clock_timer = timer

    def _tick_clock(self):
        self.clock_label.setText(QTime.currentTime().toString("HH:mm:ss"))

    def _connect_signals(self):
        self.ros_worker.image_received.connect(self._update_image)
        self.ros_worker.joint_states_received.connect(self._update_joint_states)
        self.ros_worker.progress_received.connect(self._update_progress)
        self.ros_worker.confidence_received.connect(self._update_confidence)
        self.ros_worker.grip_point_received.connect(self._update_grip_point)
        self.ros_worker.state_changed.connect(self._update_state)
        self.ros_worker.mode_changed.connect(self._update_mode)
        self.ros_worker.log_message.connect(self._append_log)
        self.ros_worker.policy_list_received.connect(self._update_model_list)

    # ── Model selectie ─────────────────────────────────────────────────────────
    def _refresh_models(self):
        self.log_message if False else None
        self.ros_worker.get_policy_list()

    def _update_model_list(self, paths: list):
        self.model_combo.clear()
        self.model_combo.addItem("— selecteer model —")
        for path in paths:
            # Toon alleen de bestandsnaam, niet het volledige pad
            self.model_combo.addItem(os.path.basename(path), userData=path)

    def _start_selected_model(self):
        idx = self.model_combo.currentIndex()
        if idx <= 0:
            self._append_log("Selecteer eerst een model.")
            return
        policy_path = self.model_combo.currentData()
        self.ros_worker.start_inference(policy_path)

    # ── Slots ──────────────────────────────────────────────────────────────────
    def _update_image(self, frame):
        h, w, ch = frame.shape
        qimg = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888).copy()
        painter = QPainter(qimg)

        if self._last_grip_point is not None:
            painter.setPen(QPen(QColor(255, 120, 0), 3))
            x = int(self._last_grip_point[0] * w)
            y = int(self._last_grip_point[1] * h)
            r = 12
            painter.drawEllipse(x - r, y - r, 2 * r, 2 * r)
            painter.drawLine(x - 20, y, x + 20, y)
            painter.drawLine(x, y - 20, x, y + 20)

        if self._current_mode == "mock":
            painter.setPen(QPen(QColor(232, 162, 61, 220)))
            painter.setFont(QFont("Consolas", 9))
            painter.drawText(10, 18, "DEMO-BEELD")

        painter.end()
        pixmap = QPixmap.fromImage(qimg).scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(pixmap)

    def _update_joint_states(self, names, positions):
        self.joint_table.setRowCount(len(names))
        for row, (name, pos) in enumerate(zip(names, positions)):
            self.joint_table.setItem(row, 0, QTableWidgetItem(name))
            self.joint_table.setItem(row, 1, QTableWidgetItem(f"{pos:.3f}"))

    def _update_progress(self, value):
        self.progress_bar.setValue(int(max(0, min(100, value))))

    def _update_confidence(self, value):
        pct = int(max(0.0, min(1.0, value)) * 100)
        self.confidence_bar.setValue(pct)
        self.confidence_label.setText(f"Confidence: {pct}%")
        if pct < 50:
            color = COLOR_DANGER
        elif pct < 75:
            color = COLOR_WARN
        else:
            color = COLOR_OK
        self.confidence_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")

    def _update_grip_point(self, x, y):
        self._last_grip_point = (x, y)

    def _update_state(self, state: str):
        self._current_state = state
        self._style_state_strip(state)
        is_estop = state == "estop"
        self.btn_reset_estop.setEnabled(is_estop)
        for btn in (self.btn_robot_start, self.btn_robot_stop,
                    self.btn_start_model, self.btn_stop_model):
            btn.setEnabled(not is_estop)

    def _update_mode(self, mode: str, message: str):
        self._current_mode = mode
        color = MODE_COLORS.get(mode, TEXT_SECONDARY)
        label = MODE_LABELS.get(mode, mode.upper())
        self.mode_badge.setText(f"●  {label}")
        self.mode_badge.setStyleSheet(f"color: {color}; font-weight: 700;")
        self._append_log(message)

    def _append_log(self, text: str):
        timestamp = QTime.currentTime().toString("HH:mm:ss")
        self.log_view.append(f"[{timestamp}] {text}")
        doc = self.log_view.document()
        if doc.blockCount() > 300:
            cursor = self.log_view.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, doc.blockCount() - 300)
            cursor.removeSelectedText()
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())
