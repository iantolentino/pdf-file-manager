# 📑 PDF Toolkit Plus

A modern **black & white themed PDF toolkit** with a fullscreen PyQt5 UI.

---

## 🚀 Features
- 📌 Merge multiple PDFs (order controlled by list + up/down buttons)  
- ✂️ Split PDFs by page range  
- 📄 Extract specific pages  
- 🖊️ Add watermark from another PDF  
- 🔄 Rotate PDFs (90° / 180°)  
- 🖱️ Drag & drop support  
- 🌙 Dark/Light mode toggle  
- 🧾 Metadata preview (page count + file size)  
- 💾 Save recent files (stored in `recent_files.json`)  

---

## 📂 Project Structure
```

pdf-toolkit-plus/
├─ app.py               # Main UI
├─ pdf_utils.py         # PDF operations (merge/split/rotate/...)
├─ preview.py           # Preview helpers
├─ storage.py           # Recent/log helpers
├─ requirements.txt
└─ README.md

````

---

## ▶️ Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
``

2. Start the app:

   ```bash
   python app.py
   ```

