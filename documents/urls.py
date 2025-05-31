from django.urls import path
from .views import DocumentUploadView, DocumentListView, upload_document

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('list/', DocumentListView.as_view(), name='document-list'),
    path('upload/', upload_document, name='upload_document'),
]
from .views import DocumentUploadView, DocumentListView, ask_question

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('list/', DocumentListView.as_view(), name='document-list'),
    path('ask/', ask_question, name='document-ask'),
]
