from krita import DockWidget
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton,
    QLabel, QLineEdit, QTextEdit, QFrame, QSizePolicy,
    QApplication, QToolButton, QGridLayout, QSpacerItem,
    QLayout, QLayoutItem, QStyle, QMessageBox,
    QFileDialog, QInputDialog, QComboBox
)
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QPalette
import json
import os
import random
import copy

from .tag_data import SECTIONS, PALETTE, HEX_PALETTES, MODEL_PRESETS


# ═══════════════════════════════════════════════════════════════════════════════
# FLOW LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._items = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        size += QSize(margin.left() + margin.right(), margin.top() + margin.bottom())
        return size

    def _doLayout(self, rect, testOnly):
        x = rect.x(); y = rect.y(); lineHeight = 0
        for item in self._items:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x(); y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = nextX; lineHeight = max(lineHeight, item.sizeHint().height())
        return y + lineHeight - rect.y()


# ═══════════════════════════════════════════════════════════════════════════════
# THREE-STATE CHIP
# ═══════════════════════════════════════════════════════════════════════════════

class ThreeStateChip(QPushButton):
    stateChanged = pyqtSignal()

    def __init__(self, label, sec_color, parent=None):
        super().__init__(label, parent)
        self._state = None
        self._sec_color = sec_color
        self.setCheckable(False)
        self.setFixedHeight(24)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.clicked.connect(self._cycle)
        self._update_style()

    def state(self): return self._state
    def setState(self, state):
        self._state = state
        self._update_style()
        self.stateChanged.emit()

    def _cycle(self):
        if self._state is None: self._state = 'pos'
        elif self._state == 'pos': self._state = 'neg'
        else: self._state = None
        self._update_style(); self.stateChanged.emit()

    def _update_style(self):
        if self._state == 'pos':
            self.setStyleSheet(f"""
                QPushButton {{ background-color: {self._sec_color}1a; color: {self._sec_color};
                    border: 1px solid {self._sec_color}; border-radius: 3px;
                    padding: 2px 10px; font-size: 11px; font-weight: 500;
                    font-family: 'JetBrains Mono', 'Consolas', monospace; }}
                QPushButton:hover {{ background-color: {self._sec_color}33; }}
            """)
        elif self._state == 'neg':
            self.setStyleSheet("""
                QPushButton { background-color: rgba(248,113,113,0.1); color: #f87171;
                    border: 1px solid rgba(248,113,113,0.4); border-radius: 3px;
                    padding: 2px 10px; font-size: 11px; font-weight: 500;
                    font-family: 'JetBrains Mono', 'Consolas', monospace; }
                QPushButton:hover { background-color: rgba(248,113,113,0.18); }
            """)
        else:
            self.setStyleSheet("""
                QPushButton { background-color: #18182a; color: #55557a;
                    border: 1px solid #26263a; border-radius: 3px;
                    padding: 2px 10px; font-size: 11px; font-weight: 500;
                    font-family: 'JetBrains Mono', 'Consolas', monospace; }
                QPushButton:hover { background-color: #22223a; color: #dcdcf0; border-color: #3a3a5c; }
            """)


# ═══════════════════════════════════════════════════════════════════════════════
# TAG TOKEN (output display with weight support)
# ═══════════════════════════════════════════════════════════════════════════════

class TagToken(QFrame):
    weightChanged = pyqtSignal(str, float)

    def __init__(self, text, key, is_neg, color=None, weight=1.0, parent=None):
        super().__init__(parent)
        self._key = key; self._weight = weight; self._is_neg = is_neg; self._color = color
        self.setFixedHeight(22); self.setFrameShape(QFrame.NoFrame); self.setCursor(Qt.SizeVerCursor)
        layout = QHBoxLayout(self); layout.setContentsMargins(6, 0, 6, 0); layout.setSpacing(3)
        self._label = QLabel(text)
        self._label.setStyleSheet("font-size: 11px; font-family: 'JetBrains Mono', monospace;")
        layout.addWidget(self._label)
        self._badge = None
        if abs(weight - 1.0) > 0.001:
            self._badge = QLabel(f"{weight:.1f}")
            self._badge.setStyleSheet("font-size: 9px; opacity: 0.7;")
            layout.addWidget(self._badge)
        self._update_style()

    def _update_style(self):
        if self._is_neg:
            self.setStyleSheet("""
                QFrame { background-color: rgba(248,113,113,0.08); border: 1px solid rgba(248,113,113,0.25);
                    border-radius: 3px; color: #f87171; }
                QLabel { color: #f87171; }
            """)
        elif self._color:
            c = self._color
            self.setStyleSheet(f"""
                QFrame {{ background-color: {c}18; border: 1px solid {c}66;
                    border-radius: 3px; color: {c}; }}
                QLabel {{ color: {c}; }}
            """)
        else:
            self.setStyleSheet("""
                QFrame { background-color: rgba(52,211,153,0.1); border: 1px solid rgba(52,211,153,0.3);
                    border-radius: 3px; color: #34d399; }
                QLabel { color: #34d399; }
            """)

    def wheelEvent(self, event):
        delta = 0.1 if event.angleDelta().y() > 0 else -0.1
        new_w = round(max(0.1, min(2.0, self._weight + delta)) * 10) / 10
        if new_w != self._weight:
            self._weight = new_w
            if self._badge:
                if abs(self._weight - 1.0) > 0.001:
                    self._badge.setText(f"{self._weight:.1f}")
                    self._badge.show()
                else:
                    self._badge.hide()
            elif abs(self._weight - 1.0) > 0.001:
                self._badge = QLabel(f"{self._weight:.1f}")
                self._badge.setStyleSheet("font-size: 9px; opacity: 0.7;")
                self.layout().addWidget(self._badge)
            self.weightChanged.emit(self._key, self._weight)
        event.accept()


class ColorDot(QLabel):
    def __init__(self, color, parent=None):
        super().__init__(parent); self.setFixedSize(7, 7)
        self.setStyleSheet(f"background-color: {color}; border-radius: 3px;")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DOCKER
# ═══════════════════════════════════════════════════════════════════════════════

class PromptBuilderDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prompt Builder")
        self._sections = copy.deepcopy(SECTIONS)
        self._chip_state = {}
        self._weight_state = {}
        self._multi_mode = False
        self._edit_mode = False
        self._active_palette = None
        self._collapsed = set()
        self._chip_widgets = []
        self._sec_widgets = []
        self._current_model = "Illustrious XL"
        self._presets_path = self._get_presets_path()
        self._neg_presets_path = self._get_neg_presets_path()
        self._build_ui()
        self._render_sections()
        self._rebuild_outputs()
        self._render_presets()
        self._render_neg_presets()

    def canvasChanged(self, canvas): pass

    def _get_presets_path(self):
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(plugin_dir, "presets.json")

    def _get_neg_presets_path(self):
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(plugin_dir, "neg_presets.json")

    # ── UI Construction ─────────────────────────────────────────────────────

    def _build_ui(self):
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget { background-color: #0d0d0f; color: #dcdcf0;
                font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 13px; }
            QScrollArea { border: none; background-color: #0d0d0f; }
            QLineEdit { background-color: #13131a; color: #dcdcf0; border: 1px solid #3a3a5c;
                border-radius: 4px; padding: 6px 10px; font-family: 'JetBrains Mono', monospace; font-size: 12px; }
            QLineEdit:focus { border-color: #c084fc; }
            QTextEdit { background-color: #0d0d0f; color: #c4b5fd; border: 1px solid #26263a;
                border-radius: 4px; padding: 8px; font-size: 12px;
                font-family: 'JetBrains Mono', monospace; }
            QPushButton { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
            QComboBox { background-color: #13131a; color: #dcdcf0; border: 1px solid #3a3a5c;
                border-radius: 4px; padding: 5px 10px; font-size: 12px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #13131a; color: #dcdcf0;
                selection-background-color: #3a3a5c; }
        """)

        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)

        # ═════ LEFT PANEL ═════
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        left_widget = QWidget()
        self._left_layout = QVBoxLayout(left_widget)
        self._left_layout.setContentsMargins(18, 18, 18, 18); self._left_layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Illustrious <span style='color:#c084fc'>·</span> Prompt Builder")
        title.setStyleSheet("font-size: 15px; font-weight: 600; letter-spacing: 0.08em;")
        header.addWidget(title); header.addStretch()

        self._btn_multi = self._make_tbtn("multi")
        self._btn_multi.clicked.connect(self._toggle_multi); header.addWidget(self._btn_multi)
        self._btn_clear = self._make_tbtn("clear", hover_color="#f87171")
        self._btn_clear.clicked.connect(self._clear_tags); header.addWidget(self._btn_clear)
        self._btn_rand = self._make_tbtn("random", hover_color="#fbbf24")
        self._btn_rand.clicked.connect(self._randomize); header.addWidget(self._btn_rand)
        self._btn_edit = self._make_tbtn("edit", hover_color="#fbbf24")
        self._btn_edit.clicked.connect(self._toggle_edit); header.addWidget(self._btn_edit)

        self._left_layout.addLayout(header)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet("color: #26263a;")
        self._left_layout.addWidget(sep)

        # Model selector
        model_row = QHBoxLayout()
        model_label = QLabel("Model:")
        model_label.setStyleSheet("font-size: 10px; color: #55557a;")
        model_row.addWidget(model_label)
        self._model_combo = QComboBox()
        for name in MODEL_PRESETS:
            self._model_combo.addItem(name)
        self._model_combo.setCurrentText(self._current_model)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        model_row.addWidget(self._model_combo)
        model_row.addStretch()
        self._left_layout.addLayout(model_row)

        # Sections container
        self._sections_container = QWidget()
        self._sections_layout = QVBoxLayout(self._sections_container)
        self._sections_layout.setContentsMargins(0, 0, 0, 0); self._sections_layout.setSpacing(10)
        self._left_layout.addWidget(self._sections_container)

        # Add section row (edit mode)
        self._add_sec_row = QWidget()
        add_layout = QHBoxLayout(self._add_sec_row); add_layout.setContentsMargins(0, 0, 0, 0)
        self._new_sec_input = QLineEdit(); self._new_sec_input.setPlaceholderText("Section name...")
        self._new_sec_input.setFixedWidth(140); add_layout.addWidget(self._new_sec_input)
        btn_add_sec = QPushButton("+ add section")
        btn_add_sec.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #34d399;
                color: #34d399; border-radius: 3px; padding: 4px 10px; font-size: 10px; }
            QPushButton:hover { background: rgba(52,211,153,0.1); }
        """)
        btn_add_sec.clicked.connect(self._add_section); add_layout.addWidget(btn_add_sec)
        add_layout.addStretch()
        self._left_layout.addWidget(self._add_sec_row); self._add_sec_row.hide()

        self._left_layout.addStretch()
        left_scroll.setWidget(left_widget)
        main_layout.addWidget(left_scroll, 1)

        # ═════ RIGHT PANEL ═════
        right_widget = QWidget()
        right_widget.setMinimumWidth(480)
        right_widget.setStyleSheet("background-color: #13131a; border-left: 1px solid #26263a;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(16, 16, 16, 16); right_layout.setSpacing(12)

        # Sidebar title
        top_bar = QHBoxLayout()
        sidebar_title = QLabel("Prompt")
        sidebar_title.setStyleSheet("font-size: 11px; text-transform: uppercase; letter-spacing: 0.14em; color: #818cf8; font-weight: 500;")
        top_bar.addWidget(sidebar_title); top_bar.addStretch()
        self._tag_count_label = QLabel("0 tags")
        self._tag_count_label.setStyleSheet("font-size: 10px; color: #55557a;")
        top_bar.addWidget(self._tag_count_label)
        right_layout.addLayout(top_bar)

        # ═════ POSITIVE PRESETS ═════
        pos_preset_row = QHBoxLayout()
        pos_preset_lbl = QLabel("Pos Presets")
        pos_preset_lbl.setStyleSheet("font-size: 10px; color: #34d399;")
        pos_preset_row.addWidget(pos_preset_lbl)
        self._pos_preset_input = QLineEdit(); self._pos_preset_input.setPlaceholderText("name...")
        self._pos_preset_input.setFixedWidth(100); pos_preset_row.addWidget(self._pos_preset_input)
        btn_save_pos = QPushButton("Save")
        btn_save_pos.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #34d399;
                color: #34d399; border-radius: 3px; padding: 3px 8px; font-size: 10px; }
            QPushButton:hover { background: rgba(52,211,153,0.1); }
        """)
        btn_save_pos.clicked.connect(self._save_pos_preset); pos_preset_row.addWidget(btn_save_pos)
        pos_preset_row.addStretch()
        right_layout.addLayout(pos_preset_row)

        self._pos_preset_list = QWidget()
        self._pos_preset_list_layout = QHBoxLayout(self._pos_preset_list)
        self._pos_preset_list_layout.setContentsMargins(0, 0, 0, 0); self._pos_preset_list_layout.setSpacing(4)
        right_layout.addWidget(self._pos_preset_list)

        # ═════ POSITIVE OUTPUT ═════
        pos_row = QHBoxLayout()
        pos_label = QLabel("positive")
        pos_label.setStyleSheet("font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; color: #34d399;")
        pos_row.addWidget(pos_label)
        self._btn_copy_pos = QPushButton("Copy")
        self._btn_copy_pos.setStyleSheet("""
            QPushButton { background: rgba(52,211,153,0.1); border: 1px solid #34d399;
                color: #34d399; border-radius: 3px; padding: 4px 10px; font-size: 10px; }
            QPushButton:hover { background: #34d399; color: #000; }
        """)
        self._btn_copy_pos.clicked.connect(lambda: self._copy_prompt(True))
        pos_row.addWidget(self._btn_copy_pos)
        right_layout.addLayout(pos_row)

        self._char_output = QLineEdit(); self._char_output.setPlaceholderText("character, series...")
        self._rebuild_timer = QTimer()
        self._rebuild_timer.setSingleShot(True)
        self._rebuild_timer.timeout.connect(self._rebuild_outputs)
        self._char_output.textChanged.connect(self._on_char_input_changed)
        right_layout.addWidget(self._char_output)

        self._pos_display = QWidget()
        self._pos_display.setMinimumHeight(140)
        self._pos_display.setStyleSheet("""
            QWidget { background-color: #0d0d0f; border: 1px solid rgba(52,211,153,0.2); border-radius: 4px; }
        """)
        self._pos_display_layout = QHBoxLayout(self._pos_display)
        self._pos_display_layout.setContentsMargins(8, 8, 8, 8); self._pos_display_layout.setSpacing(6)
        self._pos_display_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        right_layout.addWidget(self._pos_display, 1)

        # ═════ NEGATIVE PRESETS ═════
        neg_preset_row = QHBoxLayout()
        neg_preset_lbl = QLabel("Neg Presets")
        neg_preset_lbl.setStyleSheet("font-size: 10px; color: #f87171;")
        neg_preset_row.addWidget(neg_preset_lbl)
        self._neg_preset_input = QLineEdit(); self._neg_preset_input.setPlaceholderText("name...")
        self._neg_preset_input.setFixedWidth(100); neg_preset_row.addWidget(self._neg_preset_input)
        btn_save_neg = QPushButton("Save")
        btn_save_neg.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #f87171;
                color: #f87171; border-radius: 3px; padding: 3px 8px; font-size: 10px; }
            QPushButton:hover { background: rgba(248,113,113,0.1); }
        """)
        btn_save_neg.clicked.connect(self._save_neg_preset); neg_preset_row.addWidget(btn_save_neg)
        neg_preset_row.addStretch()
        right_layout.addLayout(neg_preset_row)

        self._neg_preset_list = QWidget()
        self._neg_preset_list_layout = QHBoxLayout(self._neg_preset_list)
        self._neg_preset_list_layout.setContentsMargins(0, 0, 0, 0); self._neg_preset_list_layout.setSpacing(4)
        right_layout.addWidget(self._neg_preset_list)

        # ═════ NEGATIVE OUTPUT ═════
        neg_row = QHBoxLayout()
        neg_label = QLabel("negative")
        neg_label.setStyleSheet("font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; color: #f87171;")
        neg_row.addWidget(neg_label)
        self._btn_copy_neg = QPushButton("Copy")
        self._btn_copy_neg.setStyleSheet("""
            QPushButton { background: rgba(248,113,113,0.08); border: 1px solid rgba(248,113,113,0.4);
                color: #f87171; border-radius: 3px; padding: 4px 10px; font-size: 10px; }
            QPushButton:hover { background: #f87171; color: #000; }
        """)
        self._btn_copy_neg.clicked.connect(lambda: self._copy_prompt(False))
        neg_row.addWidget(self._btn_copy_neg)
        right_layout.addLayout(neg_row)

        self._neg_display = QWidget()
        self._neg_display.setMinimumHeight(140)
        self._neg_display.setStyleSheet("""
            QWidget { background-color: #0d0d0f; border: 1px solid rgba(248,113,113,0.2); border-radius: 4px; }
        """)
        self._neg_display_layout = QHBoxLayout(self._neg_display)
        self._neg_display_layout.setContentsMargins(8, 8, 8, 8); self._neg_display_layout.setSpacing(6)
        self._neg_display_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        right_layout.addWidget(self._neg_display, 1)

        # ═════ MODEL INFO ═════
        self._model_info = QLabel("")
        self._model_info.setStyleSheet("font-size: 9px; color: #55557a;")
        self._model_info.setWordWrap(True)
        right_layout.addWidget(self._model_info)
        self._update_model_info()

        # ═════ HEX PALETTES ═════
        hex_header = QHBoxLayout()
        hex_title = QLabel("Hex Palette Challenge")
        hex_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #a78bfa; text-transform: uppercase;")
        hex_header.addWidget(hex_title); hex_header.addStretch()
        btn_shuffle = QPushButton("Shuffle")
        btn_shuffle.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #55557a;
                color: #55557a; border-radius: 3px; padding: 3px 8px; font-size: 10px; }
            QPushButton:hover { color: #c084fc; border-color: #c084fc; }
        """)
        btn_shuffle.clicked.connect(self._shuffle_palettes); hex_header.addWidget(btn_shuffle)
        right_layout.addLayout(hex_header)

        hex_desc = QLabel("Restrict generation to these colors. Click a palette to lock it into your prompt.")
        hex_desc.setWordWrap(True); hex_desc.setStyleSheet("font-size: 10px; color: #55557a;")
        right_layout.addWidget(hex_desc)

        palette_scroll = QScrollArea(); palette_scroll.setWidgetResizable(True)
        palette_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        palette_scroll.setStyleSheet("background: transparent; border: none;")
        self._palette_container = QWidget()
        self._palette_layout = QVBoxLayout(self._palette_container)
        self._palette_layout.setContentsMargins(0, 0, 0, 0); self._palette_layout.setSpacing(6)
        palette_scroll.setWidget(self._palette_container)
        right_layout.addWidget(palette_scroll, 1)

        self._active_palette_label = QLabel("")
        self._active_palette_label.setStyleSheet("font-size: 10px; color: #a78bfa;")
        self._active_palette_label.setWordWrap(True)
        right_layout.addWidget(self._active_palette_label)

        # Footer
        footer = QHBoxLayout()
        self._btn_reset = QPushButton("Reset")
        self._btn_reset.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #55557a;
                color: #55557a; border-radius: 3px; padding: 5px 10px; font-size: 10px; }
            QPushButton:hover { border-color: #f87171; color: #f87171; }
        """)
        self._btn_reset.clicked.connect(self._reset_all); footer.addWidget(self._btn_reset)
        self._btn_export = QPushButton("Export HTML")
        self._btn_export.setStyleSheet("""
            QPushButton { background: rgba(251,191,36,0.08); border: 1px solid rgba(251,191,36,0.4);
                color: #fbbf24; border-radius: 3px; padding: 5px 10px; font-size: 10px; }
            QPushButton:hover { background: #fbbf24; color: #000; }
        """)
        self._btn_export.clicked.connect(self._export_html); self._btn_export.hide(); footer.addWidget(self._btn_export)
        right_layout.addLayout(footer)

        main_layout.addWidget(right_widget)
        self.setWidget(main_widget)
        self._render_palettes()

    def _make_tbtn(self, text, hover_color=None):
        btn = QPushButton(text)
        base = """
            QPushButton { background: transparent; border: 1px solid #3a3a5c;
                color: #55557a; border-radius: 3px; padding: 3px 8px;
                font-size: 10px; text-transform: uppercase; letter-spacing: 0.07em; }
        """
        if hover_color:
            base += f"QPushButton:hover {{ border-color: {hover_color}; color: {hover_color}; }}"
        btn.setStyleSheet(base); btn.setCursor(Qt.PointingHandCursor)
        return btn

    # ── Section Rendering ───────────────────────────────────────────────────

    def _render_sections(self):
        while self._sections_layout.count():
            item = self._sections_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._chip_widgets.clear(); self._sec_widgets.clear()

        for si, sec in enumerate(self._sections):
            container = self._create_section(si, sec)
            self._sections_layout.addWidget(container)
        self._sections_layout.addStretch()

    def _create_section(self, si, sec):
        color = sec.get('color', '#94a3b8'); sec_id = sec['id']
        div = QFrame()
        div.setStyleSheet("QFrame { background-color: #13131a; border: 1px solid #2a2a3a; border-radius: 5px; }")
        layout = QVBoxLayout(div); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("""
            QFrame { background-color: #181820; border-bottom: 1px solid #26263a;
                border-top-left-radius: 5px; border-top-right-radius: 5px; }
        """)
        header.setCursor(Qt.PointingHandCursor)
        hdr_layout = QHBoxLayout(header); hdr_layout.setContentsMargins(8, 5, 8, 5); hdr_layout.setSpacing(6)

        arrow = QLabel("▾" if si not in self._collapsed else "▸")
        arrow.setStyleSheet("font-size: 9px; color: #55557a;"); hdr_layout.addWidget(arrow)
        dot = ColorDot(color); hdr_layout.addWidget(dot)
        lbl = QLabel(sec['label'])
        lbl.setStyleSheet("font-size: 10px; color: #55557a; text-transform: uppercase; letter-spacing: 0.14em;")
        hdr_layout.addWidget(lbl); hdr_layout.addStretch()

        # Edit controls
        ec = QWidget(); ec_layout = QHBoxLayout(ec); ec_layout.setContentsMargins(0, 0, 0, 0); ec_layout.setSpacing(3)
        btn_toggle = QPushButton("multi" if not sec.get('single', True) else "single")
        btn_toggle.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: 1px solid {'#818cf8' if not sec.get('single',True) else '#3a3a5c'};
                color: {'#818cf8' if not sec.get('single',True) else '#55557a'}; border-radius: 2px; padding: 2px 6px; font-size: 9px; }}
        """)
        btn_toggle.clicked.connect(lambda: self._toggle_section_single(si)); ec_layout.addWidget(btn_toggle)
        btn_add = QPushButton("+ chip")
        btn_add.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid rgba(52,211,153,0.3);
                color: #34d399; border-radius: 2px; padding: 2px 6px; font-size: 9px; }
            QPushButton:hover { background: rgba(52,211,153,0.1); }
        """)
        btn_add.clicked.connect(lambda: self._show_add_chip(si)); ec_layout.addWidget(btn_add)
        btn_del = QPushButton("× section")
        btn_del.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid rgba(248,113,113,0.3);
                color: #f87171; border-radius: 2px; padding: 2px 6px; font-size: 9px; }
            QPushButton:hover { background: rgba(248,113,113,0.15); }
        """)
        btn_del.clicked.connect(lambda: self._delete_section(si)); ec_layout.addWidget(btn_del)
        hdr_layout.addWidget(ec); ec.setVisible(self._edit_mode)

        cp = QWidget(); cp_layout = QHBoxLayout(cp); cp_layout.setContentsMargins(8, 3, 8, 3); cp_layout.setSpacing(4)
        for c in PALETTE:
            swatch = QLabel(); swatch.setFixedSize(14, 14)
            swatch.setStyleSheet(f"background-color: {c}; border-radius: 7px; border: 2px solid {'#fff' if c==color else 'transparent'};")
            swatch.setCursor(Qt.PointingHandCursor)
            swatch.mousePressEvent = lambda e, col=c, idx=si: self._set_section_color(idx, col)
            cp_layout.addWidget(swatch)
        cp_layout.addStretch(); cp.setVisible(self._edit_mode)

        layout.addWidget(header); layout.addWidget(cp)

        body = QWidget()
        body.setStyleSheet("background-color: #13131a; border-bottom-left-radius: 5px; border-bottom-right-radius: 5px;")
        body_layout = QVBoxLayout(body); body_layout.setContentsMargins(8, 6, 8, 8); body_layout.setSpacing(4)

        for ci, cat in enumerate(sec.get('categories', [])):
            cat_label = QLabel(cat['label'])
            cat_label.setStyleSheet("font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.08em;")
            body_layout.addWidget(cat_label)

            flow = FlowLayout(spacing=3)
            chips_container = QWidget(); chips_container.setLayout(flow)

            for chi, (label, val) in enumerate(cat.get('chips', [])):
                chip = ThreeStateChip(label, color)
                k = f"{sec_id}|{ci}|{chi}"
                state = self._chip_state.get(k)
                if state: chip.setState(state)
                chip.stateChanged.connect(lambda s=si, c=ci, h=chi: self._on_chip_changed(s, c, h))
                flow.addWidget(chip); self._chip_widgets.append((si, ci, chi, chip))

            body_layout.addWidget(chips_container)

        layout.addWidget(body)
        is_collapsed = si in self._collapsed
        body.setVisible(not is_collapsed); arrow.setText("▸" if is_collapsed else "▾")

        def toggle_collapse():
            if si in self._collapsed:
                self._collapsed.remove(si); body.setVisible(True); arrow.setText("▾")
            else:
                self._collapsed.add(si); body.setVisible(False); arrow.setText("▸")
        header.mousePressEvent = lambda e: toggle_collapse()

        self._sec_widgets.append({'container': div, 'header': header, 'body': body,
            'arrow': arrow, 'edit_controls': ec, 'color_picker': cp, 'label': lbl})
        return div

    # ── Chip Logic ────────────────────────────────────────────────────────────

    def _on_chip_changed(self, si, ci, chi):
        sec = self._sections[si]; sec_id = sec['id']; k = f"{sec_id}|{ci}|{chi}"
        chip = None
        for s, c, h, w in self._chip_widgets:
            if s == si and c == ci and h == chi: chip = w; break
        if chip is None: return
        state = chip.state(); self._chip_state[k] = state

        is_single = not self._multi_mode and sec.get('single', True)
        if is_single and state == 'pos':
            for oci in range(len(sec['categories'])):
                cat = sec['categories'][oci]
                if oci != ci: continue
                for ochi in range(len(cat.get('chips', []))):
                    if ochi == chi: continue
                    ok = f"{sec_id}|{oci}|{ochi}"
                    if self._chip_state.get(ok) == 'pos':
                        self._chip_state[ok] = None
                        for s, c, h, w in self._chip_widgets:
                            if s == si and c == oci and h == ochi:
                                w.setState(None); break
        self._rebuild_outputs()

    # ── Output Rendering ────────────────────────────────────────────────────

    def _on_char_input_changed(self):
        self._rebuild_timer.stop()
        self._rebuild_timer.start(300)

    def _rebuild_outputs(self):
        while self._pos_display_layout.count():
            item = self._pos_display_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        while self._neg_display_layout.count():
            item = self._neg_display_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        pos_tags = []; neg_tags = []
        for si, sec in enumerate(self._sections):
            sec_id = sec['id']; color = sec.get('color', '#34d399')
            for ci, cat in enumerate(sec.get('categories', [])):
                for chi, (label, val) in enumerate(cat.get('chips', [])):
                    k = f"{sec_id}|{ci}|{chi}"
                    s = self._chip_state.get(k)
                    if s == 'pos': pos_tags.append((val, k, color))
                    elif s == 'neg': neg_tags.append((val, k, None))

        char = self._char_output.text().strip()
        total = len(pos_tags) + len(neg_tags)

        if not pos_tags and not char:
            hint = QLabel("no tags selected")
            hint.setStyleSheet("font-size: 10px; color: #55557a; font-style: italic;")
            self._pos_display_layout.addWidget(hint)
        else:
            for val, k, color in pos_tags:
                w = self._weight_state.get(k, 1.0)
                token = TagToken(val, k, False, color, w)
                token.weightChanged.connect(self._on_weight_changed)
                self._pos_display_layout.addWidget(token)
            wb = QLabel("white background")
            wb.setStyleSheet("font-size: 10px; color: #34d399; opacity: 0.4;")
            self._pos_display_layout.addWidget(wb)

        if not neg_tags:
            hint = QLabel("no negative tags")
            hint.setStyleSheet("font-size: 10px; color: #55557a; font-style: italic;")
            self._neg_display_layout.addWidget(hint)
        else:
            for val, k, _ in neg_tags:
                w = self._weight_state.get(k, 1.0)
                token = TagToken(val, k, True, None, w)
                token.weightChanged.connect(self._on_weight_changed)
                self._neg_display_layout.addWidget(token)

        self._tag_count_label.setText(f"{total} tags")

    def _on_weight_changed(self, key, weight):
        self._weight_state[key] = weight

    def _build_prompt_string(self, include_char=True):
        parts = []
        if include_char:
            char = self._char_output.text().strip()
            if char: parts.append(char)

        # Model prefix
        model_preset = MODEL_PRESETS.get(self._current_model, {})
        prefix = model_preset.get('pos_prefix', '')
        if prefix: parts.append(prefix)

        for sec in self._sections:
            sec_id = sec['id']
            for ci, cat in enumerate(sec.get('categories', [])):
                for chi, (label, val) in enumerate(cat.get('chips', [])):
                    k = f"{sec_id}|{ci}|{chi}"
                    if self._chip_state.get(k) == 'pos':
                        w = self._weight_state.get(k, 1.0)
                        if abs(w - 1.0) < 0.001: parts.append(val)
                        else: parts.append(f"({val}:{w:.1f})")

        if self._active_palette is not None:
            p = HEX_PALETTES[self._active_palette]
            parts.append(f"color palette: {', '.join(p['colors'])}")

        parts.append("white background")
        return ", ".join(parts)

    def _build_neg_string(self):
        parts = []
        # Model default negative
        model_preset = MODEL_PRESETS.get(self._current_model, {})
        neg_default = model_preset.get('neg_default', '')
        if neg_default: parts.append(neg_default)

        for sec in self._sections:
            sec_id = sec['id']
            for ci, cat in enumerate(sec.get('categories', [])):
                for chi, (label, val) in enumerate(cat.get('chips', [])):
                    k = f"{sec_id}|{ci}|{chi}"
                    if self._chip_state.get(k) == 'neg':
                        w = self._weight_state.get(k, 1.0)
                        if abs(w - 1.0) < 0.001: parts.append(val)
                        else: parts.append(f"({val}:{w:.1f})")
        return ", ".join(parts)

    # ── Model Presets ───────────────────────────────────────────────────────

    def _on_model_changed(self, name):
        self._current_model = name
        self._update_model_info()

    def _update_model_info(self):
        preset = MODEL_PRESETS.get(self._current_model, {})
        desc = preset.get('desc', '')
        sampler = preset.get('sampler', '')
        steps = preset.get('steps', '')
        cfg = preset.get('cfg', '')
        info = f"<b>{self._current_model}</b><br>{desc}"
        if sampler: info += f"<br>Sampler: {sampler} | Steps: {steps} | CFG: {cfg}"
        self._model_info.setText(info)

    # ── Palettes ────────────────────────────────────────────────────────────

    def _render_palettes(self):
        while self._palette_layout.count():
            item = self._palette_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for idx, palette in enumerate(HEX_PALETTES):
            container = QFrame(); is_active = self._active_palette == idx
            container.setStyleSheet(f"""
                QFrame {{ background-color: {'#2e1065' if is_active else '#1a1d24'};
                    border: 1px solid {'#7c3aed' if is_active else '#26263a'}; border-radius: 5px; }}
                QFrame:hover {{ border-color: {'#7c3aed' if is_active else '#4b5563'}; }}
            """)
            container.setCursor(Qt.PointingHandCursor)
            container.mousePressEvent = lambda e, i=idx: self._on_palette_click(i)
            layout = QVBoxLayout(container); layout.setContentsMargins(6, 4, 6, 4); layout.setSpacing(3)

            hdr = QHBoxLayout()
            name = QLabel(palette['name']); name.setStyleSheet("font-size: 10px; font-weight: 500; color: #d1d5db;")
            hdr.addWidget(name); hdr.addStretch()
            lock = QLabel("🔒" if is_active else "🔓"); lock.setStyleSheet("font-size: 10px;")
            hdr.addWidget(lock); layout.addLayout(hdr)

            swatches = QHBoxLayout(); swatches.setSpacing(3)
            for hex_color in palette['colors']:
                swatch = QFrame(); swatch.setFixedSize(48, 20)
                swatch.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #374151; border-radius: 2px;")
                swatch.setToolTip(hex_color); swatches.addWidget(swatch)
            swatches.addStretch(); layout.addLayout(swatches)

            hex_row = QHBoxLayout(); hex_row.setSpacing(3)
            for hex_color in palette['colors']:
                hl = QLabel(hex_color); hl.setStyleSheet("font-size: 8px; color: #6b7280; font-family: monospace;")
                hl.setAlignment(Qt.AlignCenter); hl.setFixedWidth(48); hex_row.addWidget(hl)
            hex_row.addStretch(); layout.addLayout(hex_row)
            self._palette_layout.addWidget(container)

        self._palette_layout.addStretch()

    def _on_palette_click(self, idx):
        if self._active_palette == idx:
            self._active_palette = None; self._active_palette_label.setText("")
        else:
            self._active_palette = idx; p = HEX_PALETTES[idx]
            self._active_palette_label.setText(f"<b>Active:</b> {p['name']}<br><span style='color:#6b7280'>Appended to prompt.</span>")
        self._render_palettes(); self._rebuild_outputs()

    def _shuffle_palettes(self):
        random.shuffle(HEX_PALETTES); self._render_palettes()

    # ── Toolbar Actions ─────────────────────────────────────────────────────

    def _toggle_multi(self):
        self._multi_mode = not self._multi_mode
        self._btn_multi.setStyleSheet(f"""
            QPushButton {{ background: {'rgba(129,140,248,0.1)' if self._multi_mode else 'transparent'};
                border: 1px solid {'#818cf8' if self._multi_mode else '#3a3a5c'};
                color: {'#818cf8' if self._multi_mode else '#55557a'};
                border-radius: 3px; padding: 3px 8px;
                font-size: 10px; text-transform: uppercase; letter-spacing: 0.07em; }}
        """)

    def _clear_tags(self):
        self._chip_state.clear()
        for si, ci, chi, w in self._chip_widgets: w.setState(None)
        self._rebuild_outputs()

    def _randomize(self):
        self._chip_state.clear()
        for si, ci, chi, w in self._chip_widgets: w.setState(None)
        for si, sec in enumerate(self._sections):
            if not sec.get('randomize', True): continue
            if not sec.get('categories'): continue
            for ci, cat in enumerate(sec['categories']):
                chips = cat.get('chips', [])
                if not chips or random.random() < 0.35: continue
                chi = random.randint(0, len(chips) - 1)
                k = f"{sec['id']}|{ci}|{chi}"
                self._chip_state[k] = 'pos'
                for s, c, h, w in self._chip_widgets:
                    if s == si and c == ci and h == chi: w.setState('pos'); break
        self._rebuild_outputs()

    def _toggle_edit(self):
        self._edit_mode = not self._edit_mode
        self._btn_edit.setStyleSheet(f"""
            QPushButton {{ background: {'rgba(251,191,36,0.08)' if self._edit_mode else 'transparent'};
                border: 1px solid {'#fbbf24' if self._edit_mode else '#3a3a5c'};
                color: {'#fbbf24' if self._edit_mode else '#55557a'};
                border-radius: 3px; padding: 3px 8px;
                font-size: 10px; text-transform: uppercase; letter-spacing: 0.07em; }}
        """)
        self._add_sec_row.setVisible(self._edit_mode); self._btn_export.setVisible(self._edit_mode)
        for sec_data in self._sec_widgets:
            sec_data['edit_controls'].setVisible(self._edit_mode)
            sec_data['color_picker'].setVisible(self._edit_mode)

    def _reset_all(self):
        self._chip_state.clear(); self._weight_state.clear()
        for si, ci, chi, w in self._chip_widgets: w.setState(None)
        self._char_output.setText(""); self._active_palette = None
        self._active_palette_label.setText(""); self._render_palettes(); self._rebuild_outputs()

    # ── Edit Mode Actions ───────────────────────────────────────────────────

    def _toggle_section_single(self, si):
        self._sections[si]['single'] = not self._sections[si].get('single', True)
        self._render_sections(); self._rebuild_outputs()

    def _delete_section(self, si):
        sec = self._sections[si]
        reply = QMessageBox.question(self, "Delete Section", f'Delete "{sec["label"]}"?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes: return
        sec_id = sec['id']
        for k in list(self._chip_state.keys()):
            if k.startswith(sec_id + "|"): del self._chip_state[k]
        for k in list(self._weight_state.keys()):
            if k.startswith(sec_id + "|"): del self._weight_state[k]
        self._sections.pop(si); self._render_sections(); self._rebuild_outputs()

    def _add_section(self):
        name = self._new_sec_input.text().strip()
        if not name: return
        import time
        sec_id = f"sec_{int(time.time() * 1000)}"
        self._sections.append({'id': sec_id, 'label': name, 'single': True, 'color': '#94a3b8', 'categories': []})
        self._new_sec_input.clear(); self._render_sections()

    def _set_section_color(self, si, color):
        self._sections[si]['color'] = color
        self._render_sections(); self._rebuild_outputs()

    def _show_add_chip(self, si):
        label, ok1 = QInputDialog.getText(self, "Add Chip", "Button label:")
        if not ok1 or not label: return
        val, ok2 = QInputDialog.getText(self, "Add Chip", "Tag value:")
        if not ok2 or not val: return
        # Add to first category or create one
        sec = self._sections[si]
        if not sec.get('categories'):
            sec['categories'] = [{'label': 'General', 'single': True, 'chips': []}]
        sec['categories'][0]['chips'].append((label.strip(), val.strip()))
        self._render_sections()

    # ── Copy & Export ───────────────────────────────────────────────────────

    def _copy_prompt(self, is_pos):
        if is_pos: text = self._build_prompt_string(True)
        else: text = self._build_neg_string()
        if not text: return
        clipboard = QApplication.clipboard(); clipboard.setText(text)
        btn = self._btn_copy_pos if is_pos else self._btn_copy_neg
        btn.setText("Copied!"); QTimer.singleShot(1500, lambda: btn.setText("Copy"))

    def _export_html(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export HTML", "illus-prompt-builder.html", "HTML Files (*.html)")
        if not path: return
        config = {'sections': self._sections, 'chip_state': self._chip_state,
                  'weight_state': self._weight_state, 'char': self._char_output.text()}
        with open(path, 'w', encoding='utf-8') as f:
            f.write('<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>')
            f.write('<h1>Prompt Builder Config</h1><pre>')
            f.write(json.dumps(config, indent=2))
            f.write('</pre></body></html>')

    # ── Positive Presets ────────────────────────────────────────────────────

    def _load_pos_presets(self):
        if os.path.exists(self._presets_path):
            try:
                with open(self._presets_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {}

    def _save_pos_presets_file(self, presets):
        try:
            with open(self._presets_path, 'w', encoding='utf-8') as f:
                json.dump(presets, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save presets: {e}")

    def _render_presets(self):
        while self._pos_preset_list_layout.count():
            item = self._pos_preset_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        presets = self._load_pos_presets()
        if not presets:
            empty = QLabel("no presets"); empty.setStyleSheet("font-size: 10px; color: #55557a; font-style: italic;")
            self._pos_preset_list_layout.addWidget(empty); return
        for name in presets:
            chip = self._make_preset_chip(name, '#c084fc', lambda n=name: self._load_pos_preset(n),
                                          lambda n=name: self._delete_pos_preset(n))
            self._pos_preset_list_layout.addWidget(chip)

    def _make_preset_chip(self, name, color, load_fn, del_fn):
        chip = QFrame()
        chip.setStyleSheet(f"""
            QFrame {{ background-color: #18182a; border: 1px solid #3a3a5c; border-radius: 3px; padding: 2px 6px; }}
            QFrame:hover {{ border-color: {color}; }}
        """)
        layout = QHBoxLayout(chip); layout.setContentsMargins(4, 1, 4, 1); layout.setSpacing(4)
        lbl = QLabel(name); lbl.setStyleSheet("font-size: 10px; color: #dcdcf0;")
        lbl.setCursor(Qt.PointingHandCursor); lbl.mousePressEvent = lambda e: load_fn()
        layout.addWidget(lbl)
        dl = QLabel("×"); dl.setStyleSheet("font-size: 11px; color: #55557a; cursor: pointer;")
        dl.setCursor(Qt.PointingHandCursor); dl.mousePressEvent = lambda e: del_fn()
        layout.addWidget(dl)
        return chip

    def _save_pos_preset(self):
        name = self._pos_preset_input.text().strip()
        if not name: return
        presets = self._load_pos_presets()
        presets[name] = {'char': self._char_output.text().strip(), 'chips': dict(self._chip_state),
                         'weights': dict(self._weight_state), 'model': self._current_model}
        self._save_pos_presets_file(presets); self._pos_preset_input.clear(); self._render_presets()

    def _load_pos_preset(self, name):
        presets = self._load_pos_presets(); preset = presets.get(name)
        if not preset: return
        self._chip_state.clear(); self._weight_state.clear()
        for si, ci, chi, w in self._chip_widgets: w.setState(None)
        self._char_output.setText(preset.get('char', ''))
        if preset.get('model') and preset['model'] in MODEL_PRESETS:
            self._current_model = preset['model']
            self._model_combo.setCurrentText(self._current_model)
        for k, v in preset.get('chips', {}).items():
            self._chip_state[k] = v
            parts = k.split('|')
            if len(parts) == 3:
                sec_id, ci_str, chi_str = parts
                ci, chi = int(ci_str), int(chi_str)
                for s, c, h, w in self._chip_widgets:
                    if s < len(self._sections) and self._sections[s]['id'] == sec_id and c == ci and h == chi:
                        w.setState(v); break
        for k, v in preset.get('weights', {}).items(): self._weight_state[k] = v
        self._rebuild_outputs()

    def _delete_pos_preset(self, name):
        presets = self._load_pos_presets()
        if name in presets: del presets[name]; self._save_pos_presets_file(presets); self._render_presets()

    # ── Negative Presets ────────────────────────────────────────────────────

    def _load_neg_presets(self):
        if os.path.exists(self._neg_presets_path):
            try:
                with open(self._neg_presets_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {}

    def _save_neg_presets_file(self, presets):
        try:
            with open(self._neg_presets_path, 'w', encoding='utf-8') as f:
                json.dump(presets, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save neg presets: {e}")

    def _render_neg_presets(self):
        while self._neg_preset_list_layout.count():
            item = self._neg_preset_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        presets = self._load_neg_presets()
        if not presets:
            empty = QLabel("no presets"); empty.setStyleSheet("font-size: 10px; color: #55557a; font-style: italic;")
            self._neg_preset_list_layout.addWidget(empty); return
        for name in presets:
            chip = self._make_preset_chip(name, '#f87171', lambda n=name: self._load_neg_preset(n),
                                          lambda n=name: self._delete_neg_preset(n))
            self._neg_preset_list_layout.addWidget(chip)

    def _save_neg_preset(self):
        name = self._neg_preset_input.text().strip()
        if not name: return
        presets = self._load_neg_presets()
        presets[name] = {'chips': dict(self._chip_state), 'weights': dict(self._weight_state),
                         'model': self._current_model}
        self._save_neg_presets_file(presets); self._neg_preset_input.clear(); self._render_neg_presets()

    def _load_neg_preset(self, name):
        presets = self._load_neg_presets(); preset = presets.get(name)
        if not preset: return
        self._chip_state.clear(); self._weight_state.clear()
        for si, ci, chi, w in self._chip_widgets: w.setState(None)
        if preset.get('model') and preset['model'] in MODEL_PRESETS:
            self._current_model = preset['model']
            self._model_combo.setCurrentText(self._current_model)
        for k, v in preset.get('chips', {}).items():
            self._chip_state[k] = v
            parts = k.split('|')
            if len(parts) == 3:
                sec_id, ci_str, chi_str = parts
                ci, chi = int(ci_str), int(chi_str)
                for s, c, h, w in self._chip_widgets:
                    if s < len(self._sections) and self._sections[s]['id'] == sec_id and c == ci and h == chi:
                        w.setState(v); break
        for k, v in preset.get('weights', {}).items(): self._weight_state[k] = v
        self._rebuild_outputs()

    def _delete_neg_preset(self, name):
        presets = self._load_neg_presets()
        if name in presets: del presets[name]; self._save_neg_presets_file(presets); self._render_neg_presets()
