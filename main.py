import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QListWidget, QFileDialog, QMessageBox, QLineEdit, QHBoxLayout
)
from PyQt5.QtGui import QFont
from PyPDF2 import PdfMerger, PdfReader, PdfWriter


class PDFToolkit(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📑 PDF Toolkit - Black & White")
        self.setGeometry(200, 200, 600, 500)

        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #000000;
                font-size: 14px;
            }
            QPushButton {
                background-color: #000000;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QListWidget {
                border: 1px solid #000000;
                padding: 5px;
            }
            QLineEdit {
                border: 1px solid #000000;
                padding: 5px;
            }
        """)

        layout = QVBoxLayout()

        # Title
        title = QLabel("PDF Toolkit - Black & White Edition")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)

        # Upload Button
        self.upload_btn = QPushButton("Upload PDF(s)")
        self.upload_btn.clicked.connect(self.upload_files)
        layout.addWidget(self.upload_btn)

        # File List
        self.file_list = QListWidget()
        layout.addWidget(self.file_list)

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

        self.setLayout(layout)

    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF files", "", "PDF Files (*.pdf)")
        if files:
            self.file_list.addItems(files)
            if self.file_list.count() >= 2:
                self.merge_btn.setEnabled(True)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFToolkit()
    window.show()
    sys.exit(app.exec_())
