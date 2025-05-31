from django.db import models

class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    file_type = models.CharField(max_length=10)
    size = models.BigIntegerField()
    pages = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='processing')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
