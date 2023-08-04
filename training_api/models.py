from django.db import models
class Task(models.Model):
    email = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:  
        db_table = "postgres"