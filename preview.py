import os
from PyPDF2 import PdfReader


def get_metadata_preview(file):
    try:
        reader = PdfReader(file)
        pages = len(reader.pages)
        size = os.path.getsize(file) / 1024  # KB
        return f"📄 Pages: {pages} | 📦 Size: {size:.1f} KB"
    except Exception:
        return "⚠️ Could not read metadata"
