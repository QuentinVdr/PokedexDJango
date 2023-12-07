from django.db import models

# Create your models here.
class Person(models.Model):
    username = models.CharField(max_length=50)
    email = models.EmailField()
    def __str__(self):
        return self.username
    