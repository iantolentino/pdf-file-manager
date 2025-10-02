import os
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PyQt5.QtWidgets import QFileDialog, QMessageBox


class PDFUtils:
    def merge(self, files):
        save_path, _ = QFileDialog.getSaveFileName(None, "Save Merged PDF", "", "PDF Files (*.pdf)")
        if save_path:
            try:
                merger = PdfMerger()
                for f in files:
                    merger.append(f)
                merger.write(save_path)
                merger.close()
                QMessageBox.information(None, "Success", "PDFs merged successfully!")
            except Exception as e:
                QMessageBox.warning(None, "Error", str(e))

    def split(self, file, page_range):
        save_path, _ = QFileDialog.getSaveFileName(None, "Save Split PDF", "", "PDF Files (*.pdf)")
        if save_path:
            try:
                reader = PdfReader(file)
                writer = PdfWriter()
                start, end = [int(x) for x in page_range.split("-")]
                for page in range(start - 1, end):
                    writer.add_page(reader.pages[page])
                with open(save_path, "wb") as output:
                    writer.write(output)
                QMessageBox.information(None, "Success", "PDF split successfully!")
            except Exception as e:
                QMessageBox.warning(None, "Error", str(e))

    def extract(self, file, pages_str):
        save_path, _ = QFileDialog.getSaveFileName(None, "Save Extracted PDF", "", "PDF Files (*.pdf)")
        if save_path:
            try:
                reader = PdfReader(file)
                writer = PdfWriter()
                pages = [int(x.strip()) - 1 for x in pages_str.split(",")]
                for p in pages:
                    writer.add_page(reader.pages[p])
                with open(save_path, "wb") as output:
                    writer.write(output)
                QMessageBox.information(None, "Success", "Pages extracted successfully!")
            except Exception as e:
                QMessageBox.warning(None, "Error", str(e))

    def watermark(self, file):
        watermark_file, _ = QFileDialog.getOpenFileName(None, "Select Watermark PDF", "", "PDF Files (*.pdf)")
        if not watermark_file:
            return
        save_path, _ = QFileDialog.getSaveFileName(None, "Save Watermarked PDF", "", "PDF Files (*.pdf)")
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
                QMessageBox.information(None, "Success", "Watermark added successfully!")
            except Exception as e:
                QMessageBox.warning(None, "Error", str(e))

    def rotate(self, file, angle):
        save_path, _ = QFileDialog.getSaveFileName(None, "Save Rotated PDF", "", "PDF Files (*.pdf)")
        if save_path:
            try:
                reader = PdfReader(file)
                writer = PdfWriter()
                for page in reader.pages:
                    page.rotate(angle)
                    writer.add_page(page)
                with open(save_path, "wb") as output:
                    writer.write(output)
                QMessageBox.information(None, "Success", f"PDF rotated {angle}° successfully!")
            except Exception as e:
                QMessageBox.warning(None, "Error", str(e))
