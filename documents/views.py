from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, parser_classes
from rest_framework import status

from transformers import pipeline
from sentence_transformers import SentenceTransformer

from .models import Document
from .serializers import DocumentSerializer
from .rag_engine import process_document, chroma_client

# Initialize embedding model and ChromaDB collection
qa_model = SentenceTransformer("all-MiniLM-L6-v2")
qa_pipeline = pipeline("question-answering", model="distilbert/distilbert-base-cased-distilled-squad")
qa_collection = chroma_client.get_or_create_collection("documents")


class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            doc = serializer.save()
            doc.status = 'processing'
            doc.save()

            try:
                num_chunks = process_document(doc.id, doc.file.path)
                doc.status = f"processed ({num_chunks} chunks)"
                doc.pages = num_chunks
            except Exception as e:
                doc.status = f"error: {str(e)}"

            doc.save()
            return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentListView(APIView):
    def get(self, request):
        docs = Document.objects.all()
        serializer = DocumentSerializer(docs, many=True)
        return Response(serializer.data)


@api_view(['POST'])
def ask_question(request):
    try:
        document_id = int(request.data.get("document_id"))
        question = request.data.get("question")
        top_k = int(request.data.get("top_k", 3))

        if not document_id or not question:
            return Response({"error": "Missing 'document_id' or 'question'"}, status=400)

        query_embedding = qa_model.encode(question).tolist()
        results = qa_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"document_id": str(document_id)}
        )

        retrieved_chunks = results.get("documents", [[]])[0]
        context = " ".join(retrieved_chunks)

        if not context.strip():
            return Response({
                "document_id": document_id,
                "question": question,
                "answer": f"🔍 Top {top_k} relevant chunks:\nNo chunks found.",
                "chunks": []
            })

        llm_response = qa_pipeline(question=question, context=context)
        answer = llm_response.get("answer", "")

        return Response({
            "document_id": document_id,
            "question": question,
            "answer": answer,
            "chunks": retrieved_chunks
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_document(request):
    print("DEBUG request.FILES:", request.FILES)
    print("DEBUG request.data:", request.data)

    file = request.FILES.get("file")
    title = request.data.get("title")

    if not file or not title:
        return Response({"error": "File and title are required"}, status=400)


    document = Document.objects.create(
        title=title,
        file=file,
        file_type=file.name.split(".")[-1].lower(),
        size=file.size
    )

    chunks = process_document(document.id, document.file.path)
    document.pages = chunks
    document.status = f"processed ({chunks} chunks)"
    document.save()

    return Response({
        "id": document.id,
        "title": document.title,
        "file": document.file.url,
        "file_type": document.file_type,
        "size": document.size,
        "pages": document.pages,
        "status": document.status,
        "uploaded_at": document.uploaded_at
    })
