"""
PDF Toolkit Plus
Full-featured PDF utility (single-file)
Features:
 - Upload / Drag & Drop multiple PDFs
 - Reorder files (Up/Down), Remove, Clear All
 - Merge (list-order), Split (range), Extract (pages)
 - Add Watermark (single-page PDF)
 - Rotate pages (selected file), Reorder pages inside a PDF
 - Encrypt (password protect) and Decrypt
 - Compress/Optimize (uses pikepdf if installed)
 - Preview first page (uses pdf2image if installed) or text snippet
 - Show extended metadata (title, author, pages, size, creation date)
 - Recent files, action logging, context menu, dark/light mode
 - Saves recent files to `recent.json` beside script
Usage: pip install required libs below, then run:
    python pdf_toolkit_plus.py
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QListWidget, QFileDialog, QMessageBox, QLineEdit, QHBoxLayout,
    QInputDialog, QMenu, QAction, QSpinBox, QDialog, QDialogButtonBox,
    QTextEdit
)
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize

# PDF libs
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except Exception:
    PIKEPDF_AVAILABLE = False

# Optional preview libs
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except Exception:
    PDF2IMAGE_AVAILABLE = False

# Optional OCR
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False

# --- Constants & paths ---
APP_DIR = Path(__file__).resolve().parent
RECENT_FILE = APP_DIR / "recent.json"
LOG_FILE = APP_DIR / "pdf_toolkit.log"
MAX_RECENT = 10

# set up logging
logging.basicConfig(filename=str(LOG_FILE), level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("pdf_toolkit")

# --- Helpers ---
def save_recent(files: List[str]):
    recent = [f for f in files if os.path.isfile(f)]
    recent = recent[:MAX_RECENT]
    try:
        with open(RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump(recent, f, indent=2)
    except Exception as e:
        logger.exception("Failed saving recent")

def load_recent() -> List[str]:
    try:
        if RECENT_FILE.exists():
            with open(RECENT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [p for p in data if os.path.isfile(p)]
    except Exception:
        logger.exception("Failed loading recent")
    return []

def human_size(path):
    try:
        s = os.path.getsize(path)
        for unit in ['B','KB','MB','GB']:
            if s < 1024.0:
                return f"{s:3.1f} {unit}"
            s /= 1024.0
        return f"{s:.1f} TB"
    except Exception:
        return "Unknown"

def read_metadata(path):
    try:
        r = PdfReader(path)
        info = r.metadata or {}
        pages = len(r.pages)
        meta = {
            "title": info.title if hasattr(info, "title") else info.get("/Title", ""),
            "author": info.author if hasattr(info, "author") else info.get("/Author", ""),
            "producer": info.get("/Producer", ""),
            "creator": info.get("/Creator", ""),
            "created": info.get("/CreationDate", ""),
            "pages": pages
        }
        return meta
    except Exception:
        return {"pages": "?"}

# --- UI ---
class PDFToolkitPlus(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Toolkit Plus")
        self.resize(920, 640)
        self.center_window()

        # theme state
        self.is_dark = False
        self.light_theme = """
            QWidget { background-color: #ffffff; color: #000000; font-size: 13px; font-family: Segoe UI, Arial; }
            QPushButton { background-color: #000000; color: #ffffff; border-radius: 6px; padding: 8px; }
            QPushButton:hover { background-color: #333333; }
            QListWidget { border: 1px solid #000000; padding: 4px; }
            QLabel#meta { padding: 6px; }
            QTextEdit { background: #ffffff; color: #000000; }
        """
        self.dark_theme = """
            QWidget { background-color: #0b0b0b; color: #f0f0f0; font-size: 13px; font-family: Segoe UI, Arial; }
            QPushButton { background-color: #f0f0f0; color: #0b0b0b; border-radius: 6px; padding: 8px; }
            QPushButton:hover { background-color: #dddddd; }
            QListWidget { border: 1px solid #f0f0f0; padding: 4px; background: #111111; }
            QLabel#meta { padding: 6px; }
            QTextEdit { background: #111111; color: #f0f0f0; }
        """
        self.setStyleSheet(self.light_theme)

        # layout
        layout = QVBoxLayout()
        title = QLabel("📑 PDF Toolkit Plus")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # top buttons
        top = QHBoxLayout()
        self.upload_btn = QPushButton("Upload PDF(s)")
        self.upload_btn.clicked.connect(self.upload_files)
        top.addWidget(self.upload_btn)

        self.recent_btn = QPushButton("Recent")
        self.recent_btn.clicked.connect(self.show_recent)
        top.addWidget(self.recent_btn)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_files)
        top.addWidget(self.clear_btn)

        self.theme_btn = QPushButton("🌙 Dark Mode")
        self.theme_btn.clicked.connect(self.toggle_theme)
        top.addWidget(self.theme_btn)

        layout.addLayout(top)

        # main row: left file list, right preview/meta + actions
        main_row = QHBoxLayout()

        # left: file list and management
        left_col = QVBoxLayout()
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SingleSelection)
        self.file_list.currentItemChanged.connect(self.on_select)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.context_menu)
        left_col.addWidget(self.file_list)

        manage_row = QHBoxLayout()
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_file)
        manage_row.addWidget(self.remove_btn)
        self.up_btn = QPushButton("Move Up")
        self.up_btn.clicked.connect(self.move_up)
        manage_row.addWidget(self.up_btn)
        self.down_btn = QPushButton("Move Down")
        self.down_btn.clicked.connect(self.move_down)
        manage_row.addWidget(self.down_btn)
        left_col.addLayout(manage_row)

        main_row.addLayout(left_col, 3)

        # right: preview + metadata + operations
        right_col = QVBoxLayout()

        # preview area
        self.preview_label = QLabel("Preview area")
        self.preview_label.setFixedSize(480, 300)
        self.preview_label.setStyleSheet("border:1px solid #888;")
        self.preview_label.setAlignment(Qt.AlignCenter)
        right_col.addWidget(self.preview_label, alignment=Qt.AlignCenter)

        # meta
        self.meta = QLabel("Select a file to view metadata")
        self.meta.setObjectName("meta")
        self.meta.setWordWrap(True)
        right_col.addWidget(self.meta)

        # operations grid (split/extract/merge/etc.)
        ops_row1 = QHBoxLayout()
        self.merge_btn = QPushButton("Merge PDFs")
        self.merge_btn.setEnabled(False)
        self.merge_btn.clicked.connect(self.merge_pdfs)
        ops_row1.addWidget(self.merge_btn)

        self.merge_order_btn = QPushButton("Preview Merge Order")
        self.merge_order_btn.clicked.connect(self.preview_merge_order)
        ops_row1.addWidget(self.merge_order_btn)

        right_col.addLayout(ops_row1)

        # split/extract inputs
        ops_row2 = QHBoxLayout()
        self.split_input = QLineEdit()
        self.split_input.setPlaceholderText("Split range e.g. 1-3")
        ops_row2.addWidget(self.split_input)
        self.split_btn = QPushButton("Split")
        self.split_btn.clicked.connect(self.split_pdf)
        ops_row2.addWidget(self.split_btn)
        right_col.addLayout(ops_row2)

        ops_row3 = QHBoxLayout()
        self.extract_input = QLineEdit()
        self.extract_input.setPlaceholderText("Extract pages e.g. 1,3,5")
        ops_row3.addWidget(self.extract_input)
        self.extract_btn = QPushButton("Extract")
        self.extract_btn.clicked.connect(self.extract_pages)
        ops_row3.addWidget(self.extract_btn)
        right_col.addLayout(ops_row3)

        # watermark, rotate, reorder pages
        ops_row4 = QHBoxLayout()
        self.watermark_btn = QPushButton("Add Watermark")
        self.watermark_btn.clicked.connect(self.add_watermark)
        ops_row4.addWidget(self.watermark_btn)

        self.rotate_btn = QPushButton("Rotate")
        self.rotate_btn.clicked.connect(self.rotate_pages_dialog)
        ops_row4.addWidget(self.rotate_btn)

        self.reorder_pages_btn = QPushButton("Reorder Pages")
        self.reorder_pages_btn.clicked.connect(self.reorder_pages_dialog)
        ops_row4.addWidget(self.reorder_pages_btn)
        right_col.addLayout(ops_row4)

        # encrypt/decrypt/compress
        ops_row5 = QHBoxLayout()
        self.encrypt_btn = QPushButton("Encrypt")
        self.encrypt_btn.clicked.connect(self.encrypt_pdf)
        ops_row5.addWidget(self.encrypt_btn)
        self.decrypt_btn = QPushButton("Decrypt")
        self.decrypt_btn.clicked.connect(self.decrypt_pdf)
        ops_row5.addWidget(self.decrypt_btn)

        if PIKEPDF_AVAILABLE:
            self.compress_btn = QPushButton("Compress (pikepdf)")
            self.compress_btn.clicked.connect(self.compress_pdf)
            ops_row5.addWidget(self.compress_btn)
        else:
            self.compress_btn = QPushButton("Compress (pikepdf not installed)")
            self.compress_btn.setEnabled(False)
            ops_row5.addWidget(self.compress_btn)

        right_col.addLayout(ops_row5)

        # OCR / conversion
        ops_row6 = QHBoxLayout()
        self.ocr_btn = QPushButton("OCR First Page")
        self.ocr_btn.clicked.connect(self.ocr_first_page)
        self.ocr_btn.setEnabled(TESSERACT_AVAILABLE and PDF2IMAGE_AVAILABLE)
        ops_row6.addWidget(self.ocr_btn)

        self.save_text_btn = QPushButton("Save Text (first page)")
        self.save_text_btn.clicked.connect(self.save_first_page_text)
        ops_row6.addWidget(self.save_text_btn)
        right_col.addLayout(ops_row6)

        # log / notes display
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(100)
        right_col.addWidget(self.log_view)

        main_row.addLayout(right_col, 5)

        layout.addLayout(main_row)
        self.setLayout(layout)

        # setup drag & drop
        self.setAcceptDrops(True)

        # load recent
        self.load_recent_list()

        self.update_ui_state()
        logger.info("App started")

    # ---------- window helpers ----------
    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(max(x, 0), max(y, 0))

    # ---------- drag/drop ----------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        added = 0
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path and path.lower().endswith(".pdf"):
                self.file_list.addItem(path)
                added += 1
        if added:
            self.log(f"Added {added} file(s) via drag & drop")
        self.update_ui_state()
        self.save_recent_state()

    # ---------- file loading ----------
    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF files", "", "PDF Files (*.pdf)")
        if files:
            for f in files:
                if f.lower().endswith(".pdf"):
                    self.file_list.addItem(f)
            self.log(f"Uploaded {len(files)} file(s)")
        self.update_ui_state()
        self.save_recent_state()

    def load_recent_list(self):
        recent = load_recent()
        for p in recent:
            self.file_list.addItem(p)
        if recent:
            self.log(f"Loaded {len(recent)} recent file(s)")
        self.update_ui_state()

    def show_recent(self):
        recent = load_recent()
        if not recent:
            QMessageBox.information(self, "Recent", "No recent files.")
            return
        msg = "Recent files:\n" + "\n".join(recent)
        QMessageBox.information(self, "Recent Files", msg)

    def clear_files(self):
        self.file_list.clear()
        self.preview_label.setText("Preview area")
        self.meta.setText("Select a file to view metadata")
        self.log("Cleared file list")
        self.update_ui_state()
        self.save_recent_state()

    def remove_file(self):
        row = self.file_list.currentRow()
        if row >= 0:
            item = self.file_list.takeItem(row)
            self.log(f"Removed file: {item.text()}")
            self.update_ui_state()
            self.save_recent_state()
        else:
            QMessageBox.warning(self, "Remove", "No file selected to remove.")

    def move_up(self):
        row = self.file_list.currentRow()
        if row > 0:
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row - 1, item)
            self.file_list.setCurrentItem(item)
            self.log("Moved item up")
            self.save_recent_state()

    def move_down(self):
        row = self.file_list.currentRow()
        if row < self.file_list.count() - 1 and row >= 0:
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row + 1, item)
            self.file_list.setCurrentItem(item)
            self.log("Moved item down")
            self.save_recent_state()

    # ---------- context menu ----------
    def context_menu(self, pos):
        item = self.file_list.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        open_folder = QAction("Open Containing Folder")
        open_folder.triggered.connect(lambda: self.open_folder(item.text()))
        menu.addAction(open_folder)
        show_meta = QAction("Show Metadata")
        show_meta.triggered.connect(lambda: self.show_metadata_dialog(item.text()))
        menu.addAction(show_meta)
        remove = QAction("Remove")
        remove.triggered.connect(lambda: self.remove_specific(item))
        menu.addAction(remove)
        menu.exec_(self.file_list.mapToGlobal(pos))

    def open_folder(self, path):
        folder = os.path.dirname(path)
        if os.path.isdir(folder):
            if sys.platform.startswith("win"):
                os.startfile(folder)
            elif sys.platform.startswith("darwin"):
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')

    def show_metadata_dialog(self, path):
        meta = read_metadata(path)
        size = human_size(path)
        txt = f"Path: {path}\nSize: {size}\nPages: {meta.get('pages')}\nTitle: {meta.get('title')}\nAuthor: {meta.get('author')}\nCreated: {meta.get('created')}"
        QMessageBox.information(self, "Metadata", txt)

    def remove_specific(self, item):
        row = self.file_list.row(item)
        self.file_list.takeItem(row)
        self.log(f"Removed file: {item.text()}")
        self.save_recent_state()
        self.update_ui_state()

    # ---------- UI helpers ----------
    def update_ui_state(self):
        can_merge = self.file_list.count() >= 2
        self.merge_btn.setEnabled(can_merge)
        # enable/disable other buttons based on selection
        sel = self.file_list.currentItem()
        enabled = sel is not None
        for w in [self.split_btn, self.extract_btn, self.watermark_btn, self.rotate_btn,
                  self.reorder_pages_btn, self.encrypt_btn, self.decrypt_btn, self.ocr_btn, self.save_text_btn]:
            w.setEnabled(enabled)
        if not PIKEPDF_AVAILABLE:
            self.compress_btn.setEnabled(False)

    def on_select(self):
        item = self.file_list.currentItem()
        if item:
            path = item.text()
            self.show_preview(path)
            self.show_meta(path)
        else:
            self.preview_label.setText("Preview area")
            self.meta.setText("Select a file to view metadata")
        self.update_ui_state()

    def show_meta(self, path):
        meta = read_metadata(path)
        size = human_size(path)
        text = f"📄 Pages: {meta.get('pages')}  |  📦 Size: {size}\nTitle: {meta.get('title') or '—'}\nAuthor: {meta.get('author') or '—'}\nProducer: {meta.get('producer') or '—'}"
        self.meta.setText(text)

    def show_preview(self, path):
        # try image preview via pdf2image
        self.preview_label.setPixmap(QPixmap())  # clear
        if PDF2IMAGE_AVAILABLE:
            try:
                imgs = convert_from_path(path, first_page=1, last_page=1, fmt="png", size=(800, None))
                if imgs:
                    pil_img = imgs[0]
                    # convert PIL to QPixmap
                    data = pil_img.convert("RGBA").tobytes("raw", "RGBA")
                    qimg = QPixmap.fromImage(
                        QPixmap.fromImage)
                    # simpler: save to temp and load QPixmap (safer)
                    tmp = APP_DIR / "_preview_tmp.png"
                    pil_img.save(str(tmp))
                    pix = QPixmap(str(tmp)).scaled(self.preview_label.width(), self.preview_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.preview_label.setPixmap(pix)
                    try:
                        tmp.unlink()
                    except Exception:
                        pass
                    return
            except Exception:
                logger.exception("pdf2image preview failed")
        # fallback: extract text snippet
        try:
            reader = PdfReader(path)
            first_page = reader.pages[0]
            txt = ""
            try:
                txt = first_page.extract_text() or ""
            except Exception:
                txt = ""
            snippet = txt.strip().replace("\n", " ")[:800] or "No preview available"
            self.preview_label.setText(snippet)
        except Exception:
            self.preview_label.setText("No preview available")

    # ---------- Persistence ----------
    def save_recent_state(self):
        files = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        save_recent(files)

    # ---------- Logging ----------
    def log(self, message: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_view.append(f"[{ts}] {message}")
        logger.info(message)

    # ---------- Core operations ----------
    def merge_pdfs(self):
        if self.file_list.count() < 2:
            QMessageBox.warning(self, "Merge", "Upload at least 2 PDFs to merge.")
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save merged PDF", "", "PDF Files (*.pdf)")
        if not save_path:
            return
        try:
            merger = PdfMerger()
            for i in range(self.file_list.count()):
                merger.append(self.file_list.item(i).text())
            merger.write(save_path)
            merger.close()
            self.log(f"Merged {self.file_list.count()} files -> {save_path}")
            QMessageBox.information(self, "Merge", "Merged successfully.")
        except Exception as e:
            logger.exception("Merge failed")
            QMessageBox.critical(self, "Merge failed", str(e))

    def preview_merge_order(self):
        items = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        if not items:
            QMessageBox.information(self, "Order", "No files in list.")
            return
        msg = "Merge order:\n" + "\n".join([f"{idx+1}. {Path(p).name}" for idx,p in enumerate(items)])
        QMessageBox.information(self, "Merge Order", msg)

    def split_pdf(self):
        path = self.get_selected_file()
        if not path:
            return
        rng = self.split_input.text().strip()
        if "-" not in rng:
            QMessageBox.warning(self, "Split", "Please enter a range like 1-3")
            return
        try:
            a,b = [int(x.strip()) for x in rng.split("-",1)]
            reader = PdfReader(path)
            if a < 1 or b > len(reader.pages) or a > b:
                QMessageBox.warning(self, "Split", "Invalid range for this document.")
                return
            save_path, _ = QFileDialog.getSaveFileName(self, "Save split PDF", "", "PDF Files (*.pdf)")
            if not save_path:
                return
            writer = PdfWriter()
            for p in range(a-1, b):
                writer.add_page(reader.pages[p])
            with open(save_path, "wb") as f:
                writer.write(f)
            self.log(f"Split {path} pages {a}-{b} -> {save_path}")
            QMessageBox.information(self, "Split", "Split done.")
        except Exception as e:
            logger.exception("Split failed")
            QMessageBox.critical(self, "Split failed", str(e))

    def extract_pages(self):
        path = self.get_selected_file()
        if not path:
            return
        txt = self.extract_input.text().strip()
        if not txt:
            QMessageBox.warning(self, "Extract", "Enter pages like 1,3,5")
            return
        try:
            pages = [int(x.strip()) for x in txt.split(",") if x.strip()]
            reader = PdfReader(path)
            maxp = len(reader.pages)
            if any(p < 1 or p > maxp for p in pages):
                QMessageBox.warning(self, "Extract", "One or more pages out of range.")
                return
            save_path, _ = QFileDialog.getSaveFileName(self, "Save extracted PDF", "", "PDF Files (*.pdf)")
            if not save_path:
                return
            writer = PdfWriter()
            for p in pages:
                writer.add_page(reader.pages[p-1])
            with open(save_path, "wb") as f:
                writer.write(f)
            self.log(f"Extracted pages {pages} from {path} -> {save_path}")
            QMessageBox.information(self, "Extract", "Pages extracted.")
        except Exception as e:
            logger.exception("Extract failed")
            QMessageBox.critical(self, "Extract failed", str(e))

    def add_watermark(self):
        path = self.get_selected_file()
        if not path:
            return
        watermark_file, _ = QFileDialog.getOpenFileName(self, "Select watermark PDF (single page)", "", "PDF Files (*.pdf)")
        if not watermark_file:
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save watermarked PDF", "", "PDF Files (*.pdf)")
        if not save_path:
            return
        try:
            reader = PdfReader(path)
            watermark = PdfReader(watermark_file).pages[0]
            writer = PdfWriter()
            for page in reader.pages:
                page.merge_page(watermark)
                writer.add_page(page)
            with open(save_path, "wb") as f:
                writer.write(f)
            self.log(f"Applied watermark from {watermark_file} to {path} -> {save_path}")
            QMessageBox.information(self, "Watermark", "Watermark added.")
        except Exception as e:
            logger.exception("Watermark failed")
            QMessageBox.critical(self, "Watermark failed", str(e))

    def rotate_pages_dialog(self):
        path = self.get_selected_file()
        if not path:
            return
        angle, ok = QInputDialog.getItem(self, "Rotate", "Rotation (degrees):", ["90","180","270"], 0, False)
        if not ok:
            return
        angle = int(angle)
        save_path, _ = QFileDialog.getSaveFileName(self, "Save rotated PDF", "", "PDF Files (*.pdf)")
        if not save_path:
            return
        try:
            reader = PdfReader(path)
            writer = PdfWriter()
            for p in reader.pages:
                # rotate clockwise
                p.rotate(angle)
                writer.add_page(p)
            with open(save_path, "wb") as f:
                writer.write(f)
            self.log(f"Rotated {path} by {angle} -> {save_path}")
            QMessageBox.information(self, "Rotate", "Rotation complete.")
        except Exception as e:
            logger.exception("Rotate failed")
            QMessageBox.critical(self, "Rotate failed", str(e))

    def reorder_pages_dialog(self):
        path = self.get_selected_file()
        if not path:
            return
        reader = PdfReader(path)
        n = len(reader.pages)
        seq, ok = QInputDialog.getText(self, "Reorder Pages",
                                       f"Enter new page order (1..{n}) separated by commas. Example: 1,3,2")
        if not ok or not seq.strip():
            return
        try:
            order = [int(x.strip()) for x in seq.split(",")]
            if sorted(order) != list(range(1, n+1)):
                QMessageBox.warning(self, "Reorder", "Order must include each page exactly once.")
                return
            save_path, _ = QFileDialog.getSaveFileName(self, "Save reordered PDF", "", "PDF Files (*.pdf')")
            if not save_path:
                return
            writer = PdfWriter()
            for idx in order:
                writer.add_page(reader.pages[idx-1])
            with open(save_path, "wb") as f:
                writer.write(f)
            self.log(f"Reordered pages of {path} -> {save_path}")
            QMessageBox.information(self, "Reorder", "Reordered saved.")
        except Exception as e:
            logger.exception("Reorder failed")
            QMessageBox.critical(self, "Reorder failed", str(e))

    def encrypt_pdf(self):
        path = self.get_selected_file()
        if not path:
            return
        pwd, ok = QInputDialog.getText(self, "Encrypt", "Enter password:", echo=QLineEdit.Password)
        if not ok or not pwd:
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save encrypted PDF", "", "PDF Files (*.pdf')")
        if not save_path:
            return
        try:
            reader = PdfReader(path)
            writer = PdfWriter()
            for p in reader.pages:
                writer.add_page(p)
            writer.encrypt(pwd)
            with open(save_path, "wb") as f:
                writer.write(f)
            self.log(f"Encrypted {path} -> {save_path}")
            QMessageBox.information(self, "Encrypt", "File encrypted.")
        except Exception as e:
            logger.exception("Encrypt failed")
            QMessageBox.critical(self, "Encrypt failed", str(e))

    def decrypt_pdf(self):
        path = self.get_selected_file()
        if not path:
            return
        pwd, ok = QInputDialog.getText(self, "Decrypt", "Enter password:", echo=QLineEdit.Password)
        if not ok:
            return
        try:
            reader = PdfReader(path)
            if reader.is_encrypted:
                try:
                    reader.decrypt(pwd)
                except Exception:
                    QMessageBox.warning(self, "Decrypt", "Wrong password or unsupported encryption.")
                    return
            else:
                QMessageBox.information(self, "Decrypt", "File is not encrypted.")
                return
            save_path, _ = QFileDialog.getSaveFileName(self, "Save decrypted PDF", "", "PDF Files (*.pdf')")
            if not save_path:
                return
            writer = PdfWriter()
            for p in reader.pages:
                writer.add_page(p)
            with open(save_path, "wb") as f:
                writer.write(f)
            self.log(f"Decrypted {path} -> {save_path}")
            QMessageBox.information(self, "Decrypt", "Decrypted and saved.")
        except Exception as e:
            logger.exception("Decrypt failed")
            QMessageBox.critical(self, "Decrypt failed", str(e))

    def compress_pdf(self):
        if not PIKEPDF_AVAILABLE:
            QMessageBox.warning(self, "Compress", "pikepdf not installed.")
            return
        path = self.get_selected_file()
        if not path:
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save compressed PDF", "", "PDF Files (*.pdf')")
        if not save_path:
            return
        try:
            with pikepdf.Pdf.open(path) as pdf:
                pdf.save(save_path, optimize_version=True, linearize=True)
            self.log(f"Compressed {path} -> {save_path}")
            QMessageBox.information(self, "Compress", "Compressed (pikepdf).")
        except Exception as e:
            logger.exception("Compress failed")
            QMessageBox.critical(self, "Compress failed", str(e))

    def ocr_first_page(self):
        if not (TESSERACT_AVAILABLE and PDF2IMAGE_AVAILABLE):
            QMessageBox.warning(self, "OCR", "OCR unavailable (install pytesseract and pdf2image).")
            return
        path = self.get_selected_file()
        if not path:
            return
        try:
            images = convert_from_path(path, first_page=1, last_page=1, fmt="png")
            if not images:
                QMessageBox.warning(self, "OCR", "No page images.")
                return
            text = pytesseract.image_to_string(images[0])
            dlg = QDialog(self)
            dlg.setWindowTitle("OCR Result (first page)")
            v = QVBoxLayout()
            te = QTextEdit()
            te.setPlainText(text)
            v.addWidget(te)
            btns = QDialogButtonBox(QDialogButtonBox.Ok)
            btns.accepted.connect(dlg.accept)
            v.addWidget(btns)
            dlg.setLayout(v)
            dlg.exec_()
            self.log(f"OCR performed on {path}")
        except Exception as e:
            logger.exception("OCR failed")
            QMessageBox.critical(self, "OCR failed", str(e))

    def save_first_page_text(self):
        path = self.get_selected_file()
        if not path:
            return
        try:
            reader = PdfReader(path)
            text = ""
            try:
                text = reader.pages[0].extract_text() or ""
            except Exception:
                text = ""
            save_path, _ = QFileDialog.getSaveFileName(self, "Save text", "", "Text Files (*.txt)")
            if not save_path:
                return
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.log(f"Saved first page text of {path} -> {save_path}")
            QMessageBox.information(self, "Save Text", "Saved.")
        except Exception as e:
            logger.exception("Save text failed")
            QMessageBox.critical(self, "Save text failed", str(e))

    # ---------- utilities ----------
    def get_selected_file(self):
        it = self.file_list.currentItem()
        if not it:
            QMessageBox.warning(self, "No selection", "Please select a file from the list.")
            return None
        path = it.text()
        if not os.path.isfile(path):
            QMessageBox.warning(self, "File missing", "The selected file does not exist.")
            return None
        return path

    def toggle_theme(self):
        if self.is_dark:
            self.setStyleSheet(self.light_theme)
            self.theme_btn.setText("🌙 Dark Mode")
            self.is_dark = False
        else:
            self.setStyleSheet(self.dark_theme)
            self.theme_btn.setText("☀ Light Mode")
            self.is_dark = True

# --- Run ---
def main():
    app = QApplication(sys.argv)
    window = PDFToolkitPlus()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
