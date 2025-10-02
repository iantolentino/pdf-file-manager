import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QListWidget, QFileDialog, QMessageBox, QLineEdit, QHBoxLayout
)
from PyQt5.QtGui import QFont, QDropEvent, QDragEnterEvent
from PyQt5.QtCore import Qt

from pdf_utils import PDFUtils
from preview import get_metadata_preview
from storage import RecentStorage


class PDFToolkit(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📑 PDF Toolkit Plus")
        self.showMaximized()  # 🔹 open fullscreen but with title bar (min/max/close buttons)

        # Utils
        self.pdf_utils = PDFUtils()
        self.storage = RecentStorage()

        # Themes
        self.is_dark = False
        self.light_theme = """
            QWidget { background-color: #ffffff; color: #000000; font-size: 14px; }
            QPushButton { background-color: #000000; color: #ffffff; border-radius: 6px; padding: 8px; }
            QPushButton:hover { background-color: #444444; }
            QListWidget, QLineEdit { border: 1px solid #000000; padding: 5px; }
        """
        self.dark_theme = """
            QWidget { background-color: #000000; color: #ffffff; font-size: 14px; }
            QPushButton { background-color: #ffffff; color: #000000; border-radius: 6px; padding: 8px; }
            QPushButton:hover { background-color: #cccccc; }
            QListWidget, QLineEdit { border: 1px solid #ffffff; padding: 5px; background: #111111; color: #ffffff; }
        """
        self.setStyleSheet(self.light_theme)

        # Enable drag & drop
        self.setAcceptDrops(True)

        # Layout
        layout = QVBoxLayout()

        # Title
        title = QLabel("PDF Toolkit Plus")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)

        # Upload and clear buttons
        top_buttons = QHBoxLayout()
        self.upload_btn = QPushButton("Upload PDF(s)")
        self.upload_btn.clicked.connect(self.upload_files)
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_files)
        top_buttons.addWidget(self.upload_btn)
        top_buttons.addWidget(self.clear_btn)
        layout.addLayout(top_buttons)

        # File List
        self.file_list = QListWidget()
        self.file_list.currentItemChanged.connect(self.show_metadata)
        layout.addWidget(self.file_list)

        # File management buttons
        file_buttons = QHBoxLayout()
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_file)
        self.up_btn = QPushButton("Move Up")
        self.up_btn.clicked.connect(self.move_up)
        self.down_btn = QPushButton("Move Down")
        self.down_btn.clicked.connect(self.move_down)
        file_buttons.addWidget(self.remove_btn)
        file_buttons.addWidget(self.up_btn)
        file_buttons.addWidget(self.down_btn)
        layout.addLayout(file_buttons)

        # Metadata label
        self.meta_label = QLabel("Select a file to see metadata")
        layout.addWidget(self.meta_label)

        # Merge Button
        self.merge_btn = QPushButton("Merge PDFs")
        self.merge_btn.setEnabled(False)
        self.merge_btn.clicked.connect(self.merge_pdfs)
        layout.addWidget(self.merge_btn)

        # Split PDF
        split_layout = QHBoxLayout()
        self.split_input = QLineEdit()
        self.split_input.setPlaceholderText("Page range (e.g., 1-3)")
        self.split_btn = QPushButton("Split PDF")
        self.split_btn.clicked.connect(self.split_pdf)
        split_layout.addWidget(self.split_input)
        split_layout.addWidget(self.split_btn)
        layout.addLayout(split_layout)

        # Extract PDF
        extract_layout = QHBoxLayout()
        self.extract_input = QLineEdit()
        self.extract_input.setPlaceholderText("Pages (e.g., 1,3,5)")
        self.extract_btn = QPushButton("Extract Pages")
        self.extract_btn.clicked.connect(self.extract_pages)
        extract_layout.addWidget(self.extract_input)
        extract_layout.addWidget(self.extract_btn)
        layout.addLayout(extract_layout)

        # Watermark
        self.watermark_btn = QPushButton("Add Watermark")
        self.watermark_btn.clicked.connect(self.add_watermark)
        layout.addWidget(self.watermark_btn)

        # Rotate PDF
        rotate_layout = QHBoxLayout()
        self.rotate_btn = QPushButton("Rotate 90°")
        self.rotate_btn.clicked.connect(lambda: self.rotate_pdf(90))
        self.rotate180_btn = QPushButton("Rotate 180°")
        self.rotate180_btn.clicked.connect(lambda: self.rotate_pdf(180))
        rotate_layout.addWidget(self.rotate_btn)
        rotate_layout.addWidget(self.rotate180_btn)
        layout.addLayout(rotate_layout)

        # Dark/Light mode toggle
        self.theme_btn = QPushButton("🌙 Toggle Dark/Light Mode")
        self.theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_btn)

        self.setLayout(layout)

    # Drag & Drop events
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".pdf"):
                self.file_list.addItem(file_path)
                self.storage.save_recent(file_path)
        if self.file_list.count() >= 2:
            self.merge_btn.setEnabled(True)

    # File operations
    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF files", "", "PDF Files (*.pdf)")
        if files:
            self.file_list.addItems(files)
            for f in files:
                self.storage.save_recent(f)
            if self.file_list.count() >= 2:
                self.merge_btn.setEnabled(True)

    def clear_files(self):
        self.file_list.clear()
        self.merge_btn.setEnabled(False)
        self.meta_label.setText("Select a file to see metadata")

    def remove_file(self):
        selected = self.file_list.currentRow()
        if selected >= 0:
            self.file_list.takeItem(selected)
            if self.file_list.count() < 2:
                self.merge_btn.setEnabled(False)

    def move_up(self):
        row = self.file_list.currentRow()
        if row > 0:
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row - 1, item)
            self.file_list.setCurrentItem(item)

    def move_down(self):
        row = self.file_list.currentRow()
        if row < self.file_list.count() - 1:
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row + 1, item)
            self.file_list.setCurrentItem(item)

    def show_metadata(self):
        item = self.file_list.currentItem()
        if item:
            file = item.text()
            self.meta_label.setText(get_metadata_preview(file))

    # PDF operations using utils
    def merge_pdfs(self):
        files = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        self.pdf_utils.merge(files)

    def split_pdf(self):
        file = self.get_selected_file()
        if file:
            self.pdf_utils.split(file, self.split_input.text())

    def extract_pages(self):
        file = self.get_selected_file()
        if file:
            self.pdf_utils.extract(file, self.extract_input.text())

    def add_watermark(self):
        file = self.get_selected_file()
        if file:
            self.pdf_utils.watermark(file)

    def rotate_pdf(self, angle):
        file = self.get_selected_file()
        if file:
            self.pdf_utils.rotate(file, angle)

    def get_selected_file(self):
        item = self.file_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "Please select a PDF first!")
            return None
        return item.text()

    def toggle_theme(self):
        if self.is_dark:
            self.setStyleSheet(self.light_theme)
            self.is_dark = False
        else:
            self.setStyleSheet(self.dark_theme)
            self.is_dark = True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFToolkit()
    window.show()
    sys.exit(app.exec_())
