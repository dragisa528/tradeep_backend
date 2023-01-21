from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class AuthUser(AbstractUser):

    email = models.EmailField(blank=False, verbose_name="email")

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
