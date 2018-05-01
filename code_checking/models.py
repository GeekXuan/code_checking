# coding: utf-8
from django.db import models
from django.contrib.auth.models import User


# Create your models here.
# 用户表
class MyUser(models.Model):
    GENDER_CHOICES = (
        ('M', '男'),
        ('F', '女'),
    )
    USER_TYPES = (
        ('A', '管理员'),
        ('T', '教师'),
        ('S', '学生'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    class_name = models.CharField(max_length=20, null=True)
    user_type = models.CharField(max_length=1, choices=USER_TYPES)

    class Meta:
        db_table = 'myuser'


# 作业表
class Task(models.Model):
    name = models.CharField(max_length=20)
    teacher = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'task'


# 上传作业表
class Submit(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    filename = models.CharField(max_length=30)
    code = models.TextField()
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'submit'


# 结果表
class Result(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    file1_name = models.CharField(max_length=100)
    file2_name = models.CharField(max_length=100)
    percent1 = models.IntegerField()
    percent2 = models.IntegerField()
    matched_lines = models.CharField(max_length=100)
    file1_code = models.TextField()
    file2_code = models.TextField()
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'result'


# 记录表
class Log(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    operation = models.CharField(max_length=100)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'log'
