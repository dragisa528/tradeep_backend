from django.db import models

# Create your models here.

class Task(models.Model):
    # Define your model fields

    # Example fields:
    email = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Define any other fields you need for your model

    def __str__(self):
        return self.name