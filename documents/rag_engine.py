import os
import pdfplumber
import docx
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
from transformers import pipeline, AutoModelForQuestionAnswering, AutoTokenizer
import openai

# Initialize embedding and vector DB
chroma_client = PersistentClient(path="chromadb/")
collection = chroma_client.get_or_create_collection("documents")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Extractive QA pipeline
extractive_qa = pipeline("question-answering")

# LLM Fallback (OpenAI)
openai.api_key = os.getenv("OPENAI_API_KEY")  # Ensure this is set in your environment

def chunk_text(text, chunk_size=500):
    chunks = []
    current_chunk = ""
    for line in text.splitlines():
        if len(current_chunk) + len(line) < chunk_size:
            current_chunk += line + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = line
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

# 🆕 Helper: Extract text based on file extension
def extract_text(file_path):
    ext = os.path.splitext(file_path)[-1].lower()

    if ext == '.pdf':
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    elif ext == '.docx':
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    elif ext == '.txt':
        with open(file_path, "r") as f:
            return f.read()

    else:
        raise ValueError(f"Unsupported file type: {ext}")

# 🧠 Main Document Processing Function
def process_document(document_id, file_path):
    text = extract_text(file_path)
    chunks = chunk_text(text)

    embeddings = embedding_model.encode(chunks).tolist()
    ids = [f"{document_id}_{i}" for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=[{"document_id": str(document_id), "chunk_index": i} for i in range(len(chunks))]
    )

    return len(chunks)

def search_similar_chunks(question, top_k=3, document_id=None):
    question_embedding = embedding_model.encode(question).tolist()

    where_filter = {"document_id": str(document_id)} if document_id is not None else {}

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        where=where_filter
    )

    chunks = results.get("documents", [[]])[0]
    return chunks

def generate_answer(question, context):
    try:
        result = extractive_qa(question=question, context=context)
        return result['answer']
    except Exception as e:
        return None

def generate_llm_answer(question, context):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions from documents."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "LLM fallback failed."

def search_similar_chunks(question, top_k=3, document_id=None):
    question_embedding = embedding_model.encode(question).tolist()
    where_clause = {"document_id": str(document_id)} if document_id is not None else {}

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        where=where_clause
    )
    chunks = results.get("documents", [[]])[0]
    return chunks



def answer_question_with_fallback(question, document_id=None):
    top_chunks = search_similar_chunks(question, top_k=3, document_id=document_id)
    context = "\n".join(top_chunks)

    if not top_chunks:
        return {
            "answer": "🔍 Top 3 relevant chunks:\nNo chunks found.",
            "chunks": [],
        }

    extractive_answer = generate_answer(question, context)
    if extractive_answer:
        return {
            "answer": extractive_answer,
            "chunks": top_chunks
        }
    else:
        fallback_answer = generate_llm_answer(question, context)
        return {
            "answer": fallback_answer,
            "chunks": top_chunks
        }



def debug_chroma_entries():
    results = collection.get()
    for i in range(len(results['ids'])):
        print(f"ID: {results['ids'][i]}")
        print(f"Metadata: {results['metadatas'][i]}")
        print(f"Document: {results['documents'][i]}")
        print("---")
