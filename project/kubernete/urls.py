from django.contrib import admin
from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path('monitor', views.monitor),
    path('console', views.console),
    path('free_mem', views.free_mem),
    path('', views.login),
    path('login', views.login),
    path('management', views.management),
    path('manage_user/<int:user_id>', views.manage_user),
    path('change_host/<str:host_ip>', views.change_host),
    path('delete_user', views.delete_user),
    path('delete_host', views.delete_host),
    path('kuber', views.kuber),
    path('create_ns', views.create_ns),
    path('create_pd', views.create_pd),
    path('delete_pd', views.delete_pd),
    path('create_dp', views.create_dp),
    path('delete_dp', views.delete_dp),
    path('log_info/<str:name>', views.log_info),
    path('pod_info/<str:pod_name>', views.pod_info),
    path('dp_info/<int:deploy_id>', views.deploy_info),
    path('node_info/<str:node_name>', views.node_info),
    path('manage_namespaces/<int:ns_id>', views.manage_namespace),
    path('check_service/<int:ser_id>', views.check_service),
    path('backup', views.backup),
    path('restore_backup', views.restore_backup),
    path('delete_backup', views.delete_backup),
    path('log', views.log),
    path('log/<str:name>', views.log_2),
    path('register', views.register),
    path('create_host', views.create_host),
]