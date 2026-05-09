import sys
import cv2
import numpy as np
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QComboBox, QFileDialog, QSplitter,
    QGroupBox, QProgressBar, QSpinBox,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QImage

from models import MIDISettings, SCALES, ROOT_NOTES
from image_analyzer import analyze_image
from midi_generator import assign_midi_properties, generate_midi
from annotator import annotate_image


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bgr_to_pixmap(img_bgr: np.ndarray) -> QPixmap:
    img_rgb = np.ascontiguousarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    h, w = img_rgb.shape[:2]
    qimg = QImage(img_rgb.tobytes(), w, h, w * 3, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(qimg)


# ---------------------------------------------------------------------------
# Image display widget
# ---------------------------------------------------------------------------

class ImagePane(QLabel):
    """QLabel that always scales its pixmap to fill available space."""

    image_dropped = Signal(str)

    def __init__(self, placeholder: str = ""):
        super().__init__(placeholder)
        self._source_pixmap: QPixmap | None = None
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(360, 260)
        self.setStyleSheet(
            "background:#1a1a1a; border-radius:6px; color:#666; font-size:14px;"
        )

    def set_pixmap(self, pm: QPixmap) -> None:
        self._source_pixmap = pm
        self._refresh()

    def set_image(self, img_bgr: np.ndarray) -> None:
        self.set_pixmap(_bgr_to_pixmap(img_bgr))

    def clear_image(self, text: str = "") -> None:
        self._source_pixmap = None
        self.setPixmap(QPixmap())
        self.setText(text)

    def _refresh(self) -> None:
        if self._source_pixmap:
            scaled = self._source_pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            super().setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh()

    # drag-and-drop support on the source pane
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toLocalFile().lower()
            if url.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")):
                event.acceptProposedAction()

    def dropEvent(self, event):
        path = event.mimeData().urls()[0].toLocalFile()
        self.image_dropped.emit(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.image_dropped.receivers(self.image_dropped):
            path, _ = QFileDialog.getOpenFileName(
                self, "Open Image", "",
                "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
            )
            if path:
                self.image_dropped.emit(path)


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

class AnalysisWorker(QThread):
    finished = Signal(list, object)
    error = Signal(str)

    def __init__(self, path: str, settings: MIDISettings, sensitivity: int):
        super().__init__()
        self.path = path
        self.settings = settings
        self.sensitivity = sensitivity

    def run(self):
        try:
            elements, img = analyze_image(
                self.path,
                num_clusters=self.settings.num_clusters,
                sensitivity=self.sensitivity,
            )
            assign_midi_properties(elements, self.settings)
            self.finished.emit(elements, img)
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

_DARK_STYLE = """
QMainWindow,QWidget{background:#1e1e1e;color:#d4d4d4}
QGroupBox{border:1px solid #3a3a3a;border-radius:6px;margin-top:6px;
    font-weight:bold;color:#aaa;padding-top:4px}
QGroupBox::title{subcontrol-origin:margin;left:10px;padding:0 4px}
QPushButton{background:#2d5a8e;color:#fff;border:none;border-radius:6px;
    padding:6px 14px;font-size:13px;font-weight:bold}
QPushButton:hover{background:#3a6fa8}
QPushButton:pressed{background:#1e4a78}
QPushButton:disabled{background:#2a2a2a;color:#555}
QPushButton#btnExport{background:#2d7a5a}
QPushButton#btnExport:hover{background:#3a9870}
QPushButton#btnSave{background:#6a3a8e}
QPushButton#btnSave:hover{background:#7a4aa0}
QComboBox{background:#2a2a2a;border:1px solid #444;border-radius:4px;
    padding:3px 8px;color:#d4d4d4}
QComboBox::drop-down{border:none}
QComboBox QAbstractItemView{background:#2a2a2a;color:#d4d4d4;
    selection-background-color:#2d5a8e}
QSlider::groove:horizontal{height:4px;background:#3a3a3a;border-radius:2px}
QSlider::handle:horizontal{width:14px;height:14px;background:#2d5a8e;
    border-radius:7px;margin:-5px 0}
QSlider::sub-page:horizontal{background:#2d5a8e;border-radius:2px}
QSpinBox{background:#2a2a2a;border:1px solid #444;border-radius:4px;
    padding:3px 8px;color:#d4d4d4}
QProgressBar{background:#2a2a2a;border-radius:4px;text-align:center}
QProgressBar::chunk{background:#2d5a8e;border-radius:4px}
QSplitter::handle{background:#2a2a2a;width:4px}
QLabel{color:#d4d4d4}
"""


class MusiCatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("musiCat — Image to MIDI")
        self.setMinimumSize(1060, 680)

        self._elements = []
        self._original_img = None
        self._annotated_img = None
        self._image_path: str | None = None
        self._worker: AnalysisWorker | None = None

        self._build_ui()
        self.setStyleSheet(_DARK_STYLE)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(8)

        # Image panels
        splitter = QSplitter(Qt.Horizontal)

        left_box = QGroupBox("Source Image")
        ll = QVBoxLayout(left_box)
        self._src_pane = ImagePane("Drop image here\nor click to browse")
        self._src_pane.setCursor(Qt.PointingHandCursor)
        self._src_pane.image_dropped.connect(self._load_image)
        ll.addWidget(self._src_pane)

        right_box = QGroupBox("Annotated Output")
        rl = QVBoxLayout(right_box)
        self._ann_pane = ImagePane("Annotated result will appear here")
        rl.addWidget(self._ann_pane)

        splitter.addWidget(left_box)
        splitter.addWidget(right_box)
        splitter.setSizes([500, 500])
        layout.addWidget(splitter, stretch=1)

        # Controls row
        ctrl_box = QGroupBox("Controls")
        ctrl = QHBoxLayout(ctrl_box)

        ctrl.addWidget(QLabel("Scale:"))
        self._scale_cb = QComboBox()
        self._scale_cb.addItems(list(SCALES.keys()))
        self._scale_cb.setCurrentText("Major")
        self._scale_cb.setMinimumWidth(138)
        ctrl.addWidget(self._scale_cb)

        ctrl.addWidget(QLabel("Root:"))
        self._root_cb = QComboBox()
        self._root_cb.addItems(ROOT_NOTES)
        ctrl.addWidget(self._root_cb)

        ctrl.addWidget(QLabel("BPM:"))
        self._bpm_sl = QSlider(Qt.Horizontal)
        self._bpm_sl.setRange(40, 240)
        self._bpm_sl.setValue(120)
        self._bpm_sl.setMaximumWidth(110)
        self._bpm_lbl = QLabel("120")
        self._bpm_lbl.setMinimumWidth(28)
        self._bpm_sl.valueChanged.connect(lambda v: self._bpm_lbl.setText(str(v)))
        ctrl.addWidget(self._bpm_sl)
        ctrl.addWidget(self._bpm_lbl)

        ctrl.addWidget(QLabel("Colors:"))
        self._clusters_sp = QSpinBox()
        self._clusters_sp.setRange(2, 12)
        self._clusters_sp.setValue(6)
        self._clusters_sp.setToolTip("Number of color clusters (more = more detail)")
        ctrl.addWidget(self._clusters_sp)

        ctrl.addWidget(QLabel("Sensitivity:"))
        self._sens_sl = QSlider(Qt.Horizontal)
        self._sens_sl.setRange(10, 90)
        self._sens_sl.setValue(50)
        self._sens_sl.setMaximumWidth(100)
        self._sens_sl.setToolTip("Higher = detect smaller elements")
        ctrl.addWidget(self._sens_sl)

        ctrl.addWidget(QLabel("Bars:"))
        self._bars_sp = QSpinBox()
        self._bars_sp.setRange(1, 32)
        self._bars_sp.setValue(4)
        ctrl.addWidget(self._bars_sp)

        ctrl.addStretch()
        layout.addWidget(ctrl_box)

        # Buttons
        btn_row = QHBoxLayout()
        self._btn_analyze = QPushButton("Analyze Image")
        self._btn_analyze.setEnabled(False)
        self._btn_analyze.setMinimumHeight(36)
        self._btn_analyze.clicked.connect(self._run_analysis)

        self._btn_midi = QPushButton("Export MIDI")
        self._btn_midi.setObjectName("btnExport")
        self._btn_midi.setEnabled(False)
        self._btn_midi.setMinimumHeight(36)
        self._btn_midi.clicked.connect(self._export_midi)

        self._btn_img = QPushButton("Save Annotated Image")
        self._btn_img.setObjectName("btnSave")
        self._btn_img.setEnabled(False)
        self._btn_img.setMinimumHeight(36)
        self._btn_img.clicked.connect(self._save_image)

        btn_row.addWidget(self._btn_analyze)
        btn_row.addWidget(self._btn_midi)
        btn_row.addWidget(self._btn_img)
        layout.addLayout(btn_row)

        # Status bar
        status_row = QHBoxLayout()
        self._status = QLabel("Ready — load an image to begin")
        self._status.setStyleSheet("color:#888;font-size:12px")
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setMaximumWidth(160)
        self._progress.setMaximumHeight(8)
        status_row.addWidget(self._status)
        status_row.addWidget(self._progress)
        layout.addLayout(status_row)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _load_image(self, path: str):
        img = cv2.imread(path)
        if img is None:
            self._status.setText(f"Failed to load: {path}")
            return
        self._image_path = path
        self._original_img = img
        self._elements = []
        self._annotated_img = None
        self._src_pane.set_image(img)
        self._ann_pane.clear_image("Click 'Analyze Image' to process")
        self._btn_analyze.setEnabled(True)
        self._btn_midi.setEnabled(False)
        self._btn_img.setEnabled(False)
        self._status.setText(f"Loaded: {Path(path).name}")

    def _settings(self) -> MIDISettings:
        return MIDISettings(
            scale_name=self._scale_cb.currentText(),
            root_note_name=self._root_cb.currentText(),
            bpm=self._bpm_sl.value(),
            num_clusters=self._clusters_sp.value(),
            bars=self._bars_sp.value(),
            ticks_per_beat=480,
        )

    def _run_analysis(self):
        if not self._image_path:
            return
        self._btn_analyze.setEnabled(False)
        self._btn_midi.setEnabled(False)
        self._btn_img.setEnabled(False)
        self._progress.setRange(0, 0)
        self._progress.setVisible(True)
        self._status.setText("Analyzing…")

        self._worker = AnalysisWorker(
            self._image_path, self._settings(), self._sens_sl.value()
        )
        self._worker.finished.connect(self._analysis_done)
        self._worker.error.connect(self._analysis_error)
        self._worker.start()

    def _analysis_done(self, elements, original_img):
        self._elements = elements
        self._original_img = original_img
        self._annotated_img = annotate_image(original_img, elements)
        self._ann_pane.set_image(self._annotated_img)

        self._progress.setVisible(False)
        self._btn_analyze.setEnabled(True)
        self._btn_midi.setEnabled(bool(elements))
        self._btn_img.setEnabled(True)

        n_ch = len(set(el.midi_channel for el in elements))
        self._status.setText(
            f"Found {len(elements)} element(s) across {n_ch} MIDI channel(s) — ready to export"
        )

    def _analysis_error(self, msg: str):
        self._progress.setVisible(False)
        self._btn_analyze.setEnabled(True)
        self._status.setText(f"Error: {msg}")

    def _export_midi(self):
        if not self._elements:
            return
        stem = Path(self._image_path).stem if self._image_path else "musiCat"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save MIDI File", f"{stem}_musiCat.mid", "MIDI Files (*.mid)"
        )
        if not path:
            return
        settings = self._settings()
        assign_midi_properties(self._elements, settings)
        try:
            generate_midi(self._elements, settings, path)
            self._status.setText(f"MIDI saved: {Path(path).name}")
        except Exception as exc:
            self._status.setText(f"Export error: {exc}")

    def _save_image(self):
        if self._annotated_img is None:
            return
        stem = Path(self._image_path).stem if self._image_path else "musiCat"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Annotated Image", f"{stem}_annotated.png",
            "PNG (*.png);;JPEG (*.jpg)"
        )
        if not path:
            return
        try:
            cv2.imwrite(path, self._annotated_img)
            self._status.setText(f"Image saved: {Path(path).name}")
        except Exception as exc:
            self._status.setText(f"Save error: {exc}")


# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("musiCat")
    win = MusiCatWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
