from django.db import models

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50)

class Department(models.Model):
    id = models.IntegerField(primary_key=True)
    department = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.department

class Job(models.Model):
    id = models.IntegerField(primary_key=True)
    job = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.job

class HiredEmployee(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, null=False, blank=False)
    datetime = models.CharField(max_length=100, null=False, blank=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=False, blank=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=False, blank=False)

    def __str__(self):
        return self.name