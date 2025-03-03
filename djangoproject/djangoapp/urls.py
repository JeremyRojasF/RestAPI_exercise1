from django.urls import path
from . import views

urlpatterns = [
    path('create', views.batch_insert),
    path('backup/<str:table_name>', views.backup_table),
    path('restore/<str:table_name>', views.restore_table),
    path('employees_hired_by_quarter', views.employees_hired_by_quarter),
    path('departments_above_average', views.departments_above_average),
]
