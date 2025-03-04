from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import User
from djangoapp.models import Department, Job, HiredEmployee
from .serializers import UserSerializer, DepartmentSerializer, JobSerializer, HiredEmployeeSerializer
import pandas as pd
import fastavro
import os
from django.db.models import Count, Q, Avg
from django.db.models.functions import ExtractQuarter, Cast
from django.db.models import DateTimeField

# Create your views here.

# get all users
@api_view(['GET'])
def getUsers(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

# get single user
@api_view(['GET'])
def getUser(request, pk):
    user = User.objects.get(id=pk)
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)

# add user
@api_view(['POST'])
def addUser(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)

# update user
@api_view(['PUT'])
def updateUser(request, pk):
    user = User.objects.get(id=pk)
    serializer = UserSerializer(instance=user, data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)

# delete user
@api_view(['DELETE'])
def deleteUser(request, pk):
    user = User.objects.get(id=pk)
    user.delete()
    return Response('User deleted')

@api_view(['POST'])
def batch_insert(request):
    departments_data = request.data.get('departments', [])
    jobs_data = request.data.get('jobs', [])
    employees_data = request.data.get('hired_employees', [])

    errors = []

    # Validar tamaño de lote (entre 1 y 1000 filas)
    if not (1 <= len(departments_data) <= 1000 or len(departments_data) == 0):
        return Response({'error': 'Departments batch size must be between 1 and 1000'}, status=status.HTTP_400_BAD_REQUEST)
    if not (1 <= len(jobs_data) <= 1000 or len(jobs_data) == 0):
        return Response({'error': 'Jobs batch size must be between 1 and 1000'}, status=status.HTTP_400_BAD_REQUEST)
    if not (1 <= len(employees_data) <= 1000 or len(employees_data) == 0):
        return Response({'error': 'Hired employees batch size must be between 1 and 1000'}, status=status.HTTP_400_BAD_REQUEST)

    if departments_data:
        for data in departments_data:
            department_serializer = DepartmentSerializer(data=data)
            if department_serializer.is_valid():
                department_serializer.save()
            else:
                errors.append({'departments': {'error': department_serializer.errors, 'data': data}})

    if jobs_data:
        for data in jobs_data:
            job_serializer = JobSerializer(data=data)
            if job_serializer.is_valid():
                job_serializer.save()
            else:
                errors.append({'jobs': {'error': job_serializer.errors, 'data': data}})

    if employees_data:
        for data in employees_data:
            employee_serializer = HiredEmployeeSerializer(data=data)
            if employee_serializer.is_valid():
                employee_serializer.save()
            else:
                errors.append({'hired_employees': {'error': employee_serializer.errors, 'data': data}})

    if errors:
        return Response({'errors': errors}, status=status.HTTP_207_MULTI_STATUS)

    return Response({'message': 'Data inserted successfully'}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def backup_table(request, table_name):
    data = None
    if table_name == 'departments':
        data = pd.DataFrame(list(Department.objects.values()))
    elif table_name == 'jobs':
        data = pd.DataFrame(list(Job.objects.values()))
    elif table_name == 'hired_employees':
        data = pd.DataFrame(list(HiredEmployee.objects.values()))
        data.rename(columns={'department_id': 'department', 'job_id': 'job'}, inplace=True)
    else:
        return Response({'error': 'Invalid table name'}, status=status.HTTP_400_BAD_REQUEST)

    if data.empty:
        return Response({'message': f'No data found in table {table_name}'}, status=status.HTTP_404_NOT_FOUND)

    file_path = f'backup/{table_name}_backup.avro'

    for col in data.columns:
        print(data[col].dtype) 

    def get_avro_type(dtype):
        if pd.api.types.is_integer_dtype(dtype):
            return "int"
        elif pd.api.types.is_string_dtype(dtype):
            return "string"
        else:
            return "string"

    with open(file_path, 'wb') as f:
        schema = {
            "type": "record",
            "name": f"{table_name}_record",
            "fields": [{"name": col, "type": get_avro_type(data[col].dtype)} for col in data.columns]
        }
        records = data.to_dict(orient='records')
        fastavro.writer(f, schema, records)

    return Response({'message': f'Backup for {table_name} saved at {file_path}', 'schema': schema}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def restore_table(request, table_name):
    file_path = f'backup/{table_name}_backup.avro'

    if not os.path.exists(file_path):
        return Response({'error': f'Backup file for {table_name} not found'}, status=status.HTTP_404_NOT_FOUND)

    with open(file_path, 'rb') as f:
        records = list(fastavro.reader(f))

    if table_name == 'departments':
        Department.objects.all().delete()
        serializer = DepartmentSerializer(data=records, many=True)
    elif table_name == 'jobs':
        Job.objects.all().delete()
        serializer = JobSerializer(data=records, many=True)
    elif table_name == 'hired_employees':
        HiredEmployee.objects.all().delete()
        serializer = HiredEmployeeSerializer(data=records, many=True)
    else:
        return Response({'error': 'Invalid table name'}, status=status.HTTP_400_BAD_REQUEST)

    if serializer.is_valid():
        serializer.save()
        return Response({'message': f'Table {table_name} restored successfully'}, status=status.HTTP_201_CREATED)
    else:
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def employees_hired_by_quarter(request):
    employees = (HiredEmployee.objects
                 .annotate(datetime_cast=Cast('datetime', DateTimeField()))
                 .filter(datetime_cast__year=2021)
                 .annotate(quarter=ExtractQuarter('datetime_cast'))
                 .values('department__department', 'job__job', 'quarter')
                 .annotate(total=Count('id'))
                 .order_by('department__department', 'job__job'))

    result = {}
    for emp in employees:
        dept = emp['department__department']
        job = emp['job__job']
        quarter = f"Q{emp['quarter']}"
        if (dept, job) not in result:
            result[(dept, job)] = {'department': dept, 'job': job, 'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
        result[(dept, job)][quarter] = emp['total']

    return Response(list(result.values()), status=status.HTTP_200_OK)

@api_view(['GET'])
def departments_above_average(request):
    avg_hires = (HiredEmployee.objects
                 .annotate(datetime_cast=Cast('datetime', DateTimeField()))
                 .filter(datetime_cast__year=2021)
                 .values('department')
                 .annotate(total_hired=Count('id'))
                 .aggregate(average_hired=Avg('total_hired'))['average_hired'])

    departments = (HiredEmployee.objects
                   .values('department__id', 'department__department')
                   .annotate(total_hired=Count('id'))
                   .filter(total_hired__gt=avg_hires)
                   .order_by('-total_hired'))

    return Response(departments, status=status.HTTP_200_OK)