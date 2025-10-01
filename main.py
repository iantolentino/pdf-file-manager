import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel,
    QLineEdit, QMessageBox, QHBoxLayout
)
from PyQt5.QtGui import QFont
from PyPDF2 import PdfMerger, PdfReader, PdfWriter


class PDFToolkit(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📑 PDF Toolkit")
        self.setGeometry(200, 200, 500, 400)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #000000;
                font-size: 14px;
            }
            QPushButton {
                background-color: #000000;
                color: #ffffff;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QLineEdit {
                border: 1px solid #000000;
                padding: 5px;
            }
        """)

        layout = QVBoxLayout()

        title = QLabel("PDF Toolkit - Black & White Edition")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: black;")
        layout.addWidget(title)

        # Merge PDFs
        merge_btn = QPushButton("Merge PDFs")
        merge_btn.clicked.connect(self.merge_pdfs)
        layout.addWidget(merge_btn)

        # Split PDF
        split_layout = QHBoxLayout()
        self.split_input = QLineEdit()
        self.split_input.setPlaceholderText("Enter page range (e.g., 1-3)")
        split_btn = QPushButton("Split PDF")
        split_btn.clicked.connect(self.split_pdf)
        split_layout.addWidget(self.split_input)
        split_layout.addWidget(split_btn)
        layout.addLayout(split_layout)

        # Extract pages
        extract_layout = QHBoxLayout()
        self.extract_input = QLineEdit()
        self.extract_input.setPlaceholderText("Enter page numbers (e.g., 1,3,5)")
        extract_btn = QPushButton("Extract Pages")
        extract_btn.clicked.connect(self.extract_pages)
        extract_layout.addWidget(self.extract_input)
        extract_layout.addWidget(extract_btn)
        layout.addLayout(extract_layout)

        # Watermark
        watermark_btn = QPushButton("Add Watermark")
        watermark_btn.clicked.connect(self.add_watermark)
        layout.addWidget(watermark_btn)

        self.setLayout(layout)

    def merge_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDFs to Merge", "", "PDF Files (*.pdf)")
        if files:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", "", "PDF Files (*.pdf)")
            if save_path:
                merger = PdfMerger()
                for pdf in files:
                    merger.append(pdf)
                merger.write(save_path)
                merger.close()
                QMessageBox.information(self, "Success", "PDFs merged successfully!")

    def split_pdf(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF to Split", "", "PDF Files (*.pdf)")
        if file:
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
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF to Extract From", "", "PDF Files (*.pdf)")
        if file:
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
        file, _ = QFileDialog.getOpenFileName(self, "Select PDF to Watermark", "", "PDF Files (*.pdf)")
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
