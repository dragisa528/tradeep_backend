from django.db import models
from django.contrib.auth.models import User

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Notebook(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return self.title
    
    
    # Define the Notebook model to represent notebooks created by users.
class Notebook(models.Model):
    # The title of the notebook.
    title = models.CharField(max_length=200)
    # The content of the notebook, stored as text.
    content = models.TextField()
    # The owner of the notebook, represented as a foreign key to the User model.
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    # The price of the notebook, stored as a decimal value.
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # The tags associated with the notebook, represented as a many-to-many relationship with the Tag model.
    tags = models.ManyToManyField(Tag)

    # String representation of the Notebook model.
    def __str__(self):
        return self.title