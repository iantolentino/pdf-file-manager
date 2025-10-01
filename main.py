import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QListWidget, QFileDialog, QMessageBox, QLineEdit, QHBoxLayout
)
from PyQt5.QtGui import QFont, QDropEvent, QDragEnterEvent
from PyQt5.QtCore import Qt
from PyPDF2 import PdfMerger, PdfReader, PdfWriter


class PDFToolkit(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📑 PDF Toolkit - Modern Edition")
        self.resize(700, 550)

        # Default theme is light
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

        layout = QVBoxLayout()

        # Title
        title = QLabel("PDF Toolkit - Black & White Modern Edition")
        title.setFont(QFont("Arial", 16, QFont.Bold))
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

        # Dark/Light mode toggle
        self.theme_btn = QPushButton("🌙 Toggle Dark/Light Mode")
        self.theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_btn)

        self.setLayout(layout)
        self.center_window()

    # Center the window
    def center_window(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # Drag & Drop events
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".pdf"):
                self.file_list.addItem(file_path)
        if self.file_list.count() >= 2:
            self.merge_btn.setEnabled(True)

    # File upload
    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF files", "", "PDF Files (*.pdf)")
        if files:
            self.file_list.addItems(files)
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
        else:
            QMessageBox.warning(self, "Error", "No file selected to remove!")

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
            try:
                reader = PdfReader(file)
                pages = len(reader.pages)
                size = os.path.getsize(file) / 1024  # in KB
                self.meta_label.setText(f"📄 Pages: {pages} | 📦 Size: {size:.1f} KB")
            except Exception:
                self.meta_label.setText("⚠️ Could not read metadata")

    def get_selected_file(self):
        selected = self.file_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Please select a PDF from the list first!")
            return None
        return selected.text()

    def merge_pdfs(self):
        if self.file_list.count() < 2:
            QMessageBox.warning(self, "Error", "Upload at least 2 PDFs to merge.")
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", "", "PDF Files (*.pdf)")
        if save_path:
            merger = PdfMerger()
            for i in range(self.file_list.count()):
                merger.append(self.file_list.item(i).text())
            merger.write(save_path)
            merger.close()
            QMessageBox.information(self, "Success", "PDFs merged successfully!")

    def split_pdf(self):
        file = self.get_selected_file()
        if not file:
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Split PDF", "", "PDF Files (*.pdf)")
        if save_path:
            try:
                reader = PdfReader(file)
                writer = PdfWriter()
                page_range = self.split_input.text().split("-")
                start, end = int(page_range[0]) - 1, int(page_range[1])
                for page in range(start, end):
                    writer.add_page(reader.pages[page])
                with open(save_path, "wb") as output:
                    writer.write(output)
                QMessageBox.information(self, "Success", "PDF split successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def extract_pages(self):
        file = self.get_selected_file()
        if not file:
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Extracted PDF", "", "PDF Files (*.pdf)")
        if save_path:
            try:
                reader = PdfReader(file)
                writer = PdfWriter()
                pages = [int(x.strip()) - 1 for x in self.extract_input.text().split(",")]
                for page in pages:
                    writer.add_page(reader.pages[page])
                with open(save_path, "wb") as output:
                    writer.write(output)
                QMessageBox.information(self, "Success", "Pages extracted successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def add_watermark(self):
        file = self.get_selected_file()
        if not file:
            return
        watermark_file, _ = QFileDialog.getOpenFileName(self, "Select Watermark PDF", "", "PDF Files (*.pdf)")
        if file and watermark_file:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Watermarked PDF", "", "PDF Files (*.pdf)")
            if save_path:
                try:
                    reader = PdfReader(file)
                    watermark = PdfReader(watermark_file).pages[0]
                    writer = PdfWriter()
                    for page in reader.pages:
                        page.merge_page(watermark)
                        writer.add_page(page)
                    with open(save_path, "wb") as output:
                        writer.write(output)
                    QMessageBox.information(self, "Success", "Watermark added successfully!")
                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))

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
