
import pandas as pd
import logging
from django.core.management.base import BaseCommand
from djangoapp.models import Department, Job, HiredEmployee
from djangoapp.serializers import DepartmentSerializer, JobSerializer, HiredEmployeeSerializer
import os

# Configurar el logger
logging.basicConfig(filename='djangoapp/logs/data_errors.log', level=logging.ERROR)

class Command(BaseCommand):
    help = 'Load data from CSV files into the database'

    def handle(self, *args, **kwargs):
        try:
            self.clear_database()
            self.clear_logs()
            self.load_departments()
            self.load_jobs()
            self.load_hired_employees()
            self.stdout.write(self.style.SUCCESS('Data loaded successfully'))
        except Exception as e:
            logging.error(f'Error loading data: {e}')

    def clear_database(self):
        Department.objects.all().delete()
        Job.objects.all().delete()
        HiredEmployee.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Database tables cleared'))

    def clear_logs(self):
        if os.path.exists('djangoapp/logs/data_errors.log'):
            open('djangoapp/logs/data_errors.log', 'w').close()
            self.stdout.write(self.style.SUCCESS('Log file cleared'))
    
    
    def load_departments(self):
        df = pd.read_csv('data/departments.csv', header=None, names=['id', 'department'], dtype={'id': int, 'department': str})
        for _, row in df.iterrows():
            serializer = DepartmentSerializer(data=row.to_dict())
            if serializer.is_valid():
                serializer.save()
            else:
                logging.error(f"Department data error: {serializer.errors} - Data: {row.to_dict()}")
        self.stdout.write(self.style.SUCCESS('Departments loaded successfully'))

    def load_jobs(self):
        df = pd.read_csv('data/jobs.csv', header=None, names=['id', 'job'], dtype={'id': int, 'job': str})
        for _, row in df.iterrows():
            serializer = JobSerializer(data=row.to_dict())
            if serializer.is_valid():
                serializer.save()
            else:
                logging.error(f"Job data error: {serializer.errors} - Data: {row.to_dict()}")
        self.stdout.write(self.style.SUCCESS('Jobs loaded successfully'))

    def load_hired_employees(self):
        df = pd.read_csv('data/hired_employees.csv', header=None, names=['id', 'name', 'datetime', 'department', 'job'], dtype={'id': pd.Int64Dtype(), 'name': pd.StringDtype(), 'datetime': pd.StringDtype(), 'department': pd.Int64Dtype(), 'job': pd.Int64Dtype()})
        for _, row in df.iterrows():
            if row.isnull().any():
                logging.error(f"Invalid employee data: {row.to_dict()}")
                continue
            serializer = HiredEmployeeSerializer(data=row.to_dict())
            if serializer.is_valid():
                serializer.save()
            else:
                logging.error(f"HiredEmployee data error: {serializer.errors} - Data: {row.to_dict()}")
        self.stdout.write(self.style.SUCCESS('Hired employees loaded successfully'))