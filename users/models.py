from django.db import models  
class UserModel(models.Model):  
    uid = models.CharField(max_length=50) 
    username = models.CharField(max_length=50)  
    email = models.CharField(max_length=50)  
    upass = models.CharField(max_length=50)
    class Meta:  
        db_table = "postgres"