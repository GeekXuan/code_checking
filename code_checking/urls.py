from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home),
    re_path('^login/', views.user_login),
    path('logout/', views.user_logout),
    path('register/', views.register),
    path('change_password/', views.change_password),
    path('create_code/', views.create_code),
    # 学生
    path('s/viewtask/', views.s_viewtask),
    path('s/submit/', views.s_submit),
    path('s/view_result/', views.s_view_result),
    path('s/view_detail/', views.s_view_detail),
    # 教师
    path('t/viewtask/', views.t_viewtask),
    path('t/addtask/', views.t_addtask),
    re_path('^t/addstudent/', views.t_addstudent),
    path('t/task_off/', views.t_task_off),
    path('t/task_on/', views.t_task_on),
    path('t/remove_student/', views.t_remove_student),
    path('t/add_student/', views.t_add_student),
    path('t/submit_task/', views.t_submit_task),
    path('t/view_result/', views.t_view_result),
    path('t/view_detail/', views.t_view_detail),
    # 管理员
    path('a/manage/', views.a_manage),
    path('a/task/', views.a_task),
    path('a/viewlog/', views.a_viewlog),
    path('a/remove_user/', views.a_remove_user),
    path('a/remove_task/', views.a_remove_task),
]