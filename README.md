# 🧠 Document Intelligence Platform (Backend-Only)

A backend-powered Retrieval-Augmented Generation (RAG) system that allows users to upload documents (PDF, DOCX, TXT) and ask contextual questions. It retrieves relevant document chunks and generates intelligent answers using transformer-based models.

---

## 📌 Features

- Upload PDF/DOCX/TXT documents via API
- Automatic text extraction and chunking
- Embedding via SentenceTransformer
- Similarity search using ChromaDB
- Contextual answers via HuggingFace QA pipeline
- Document filtering for accurate responses
- Admin interface for document management

---

## 🖼️ Screenshots

> Add your images in the `screenshots/` folder, e.g.:

- ![Upload API - Postman](screenshots/Upload_Sample_docx.png)
- ![Upload API - Postman](screenshots/Upload_sample_pdf.png)
- ![Upload API - Postman](screenshots/Upload_sample_text.png)
- ![Ask Question API - Postman](screenshots/Ask_sample_pdf.png)
- ![Ask Question API - Postman](screenshots/Ask_sample_text.png)
- ![Ask Question API - Postman](screenshots/Ask_Sample_docx.png)
- ![Admin Panel](screenshots/Admin_panel.png)

---

## ⚙️ Setup Instructions

```bash
# Clone the repository
git clone https://github.com/your-username/doc-intel-backend.git
cd doc-intel-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Start the Django server
python manage.py runserver
