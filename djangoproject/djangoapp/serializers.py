from rest_framework import serializers
from .models import User, Department, Job, HiredEmployee

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'

class HiredEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HiredEmployee
        fields = '__all__'