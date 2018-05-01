import re
import json
import docx
import datetime
import threading
import chardet
import requests
import threadpool
from bs4 import BeautifulSoup

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse, HttpResponseRedirect, render_to_response
from django.http import Http404
from django.template.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from .moss import Moss
from .models import MyUser, Task, Submit, Result, Log

LOGIN_URL = "/login"
USERID = '437681782'
SUFFIX = ('c', 'cpp', 'java', 'py', 'htm', 'html', 'asp', 'jsp', 'php', 'js', 'css', 'txt', 'pl')


# 主页
@login_required(login_url=LOGIN_URL)
def home(request):
    if request.session['user']['user_type'] == 'S':
        return s_viewtask(request)
    elif request.session['user']['user_type'] == 'T':
        return t_viewtask(request)
    elif request.session['user']['user_type'] == 'A':
        return a_viewlog(request)
    else:
        raise Http404("你没有权限访问该页面")


# 登陆
@csrf_exempt
def user_login(request):
    url = request.GET.get('next', '')
    if request.method == 'GET':
        context = {'url': url}
        return render(request, 'login.html', context)
    user_id = request.POST.get('user_id')
    password = request.POST.get('password')
    user = authenticate(username=user_id, password=password)
    if user:
        login(request, user)
        request.session['user'] = {
            'user_id': user_id,
            'user_name': MyUser.objects.get(user__username=user_id).name,
            'user_type': MyUser.objects.get(user__username=user_id).user_type,
        }
        return HttpResponseRedirect('/')
    else:
        context = {
            'msg': '账号或密码错误！如果忘记密码，请联系管理员。',
            'url': url,
        }
        return render(request, 'login.html', context)


# 登出
@login_required(login_url=LOGIN_URL)
def user_logout(request):
    logout(request)
    # request.session.clear()
    return HttpResponseRedirect('/login/')


# 注册
@csrf_exempt
def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    elif request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_name = request.POST.get('user_name')
        user_gender = request.POST.get('user_gender')
        user_type = request.POST.get('user_type')
        user_class = request.POST.get('user_class')
        password = request.POST.get('password')
        password_again = request.POST.get('password_again')
        context = {
            'user_id': user_id,
            'user_name': user_name,
            'user_gender': {'F': True, 'M': False}[user_gender],
            'user_type': {'T': True, 'S': False}[user_type],
            'user_class': user_class,
        }
        if '' in [user_id, user_name, user_class, password, password_again]:
            context['msg'] = '请填写完整！'
        elif password == password_again:
            if len(User.objects.filter(username=user_id)) == 0:
                try:
                    user = User(username=user_id)
                    user.save()
                    user.set_password(password)
                    user.save()
                    myuser = MyUser(user=user,
                                    name=user_name,
                                    gender=user_gender,
                                    class_name=user_class,
                                    user_type=user_type,
                                    )
                    myuser.save()
                    context = {
                        'msg': '注册成功！',
                        'url': '/login/',
                        'value': '登陆',
                    }
                except Exception as e:
                    print(e)
                    context = {
                        'color': 'red',
                        'msg': '注册失败！',
                        'url': '/register/',
                        'value': '返回',
                    }
                return render(request, 'register_result.html', context)
            else:
                context['msg'] = '该账号已注册，如非本人注册或忘记密码，请联系管理员！'
        else:
            context['msg'] = '两次密码输入不一致，请重新输入！'
        return render(request, 'register.html', context)


# 修改密码
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def change_password(request):
    if request.method == 'GET':
        return render(request, 'change_password.html')
    elif request.method == 'POST':
        context = {}
        password = request.POST.get('password')
        password_again = request.POST.get('password_again')
        if '' in [password, password_again]:
            context['msg'] = '请填写完整！'
        elif password == password_again:
            context = {}
            try:
                user = User.objects.get(username=request.session['user']['user_id'])
                user.set_password(password)
                user.save()
                context['msg'] = '修改成功！'
                save_log(request, '修改密码成功')
            except:
                context['msg'] = '修改失败！'
                save_log(request, '修改密码失败')
            return render(request, 'change_password_result.html', context)
        else:
            context['msg'] = '两次密码输入不一致，请重新输入！'
        return render(request, 'change_password.html', context)


# 学生查看作业
@login_required(login_url=LOGIN_URL)
def s_viewtask(request):
    if request.session['user']['user_type'] == 'S':
        if request.method == 'GET':
            student_id = request.session['user']['user_id']
            student = MyUser.objects.get(user__username=student_id)
            task_obj_list = Submit.objects.filter(user=student, code='').values('task')
            task_list = []
            for each in task_obj_list:
                task = Task.objects.get(id=each['task'])
                data = dict(
                    id=task.id,
                    name=task.name,
                    teacher=task.teacher.name,
                    status=task.status,
                    get_result=False if len(Result.objects.filter(task__id=task.id)) == 0 else True,
                    submit_times=len(Submit.objects.filter(user=student, task__id=task.id)) - 1,
                )
                task_list.append(data)
            count = len(task_list)
            if request.is_ajax():
                draw = int(request.GET['draw'])
                start = int(request.GET['start'])
                length = int(request.GET['length'])
                search = request.GET['search[value]']
                if search:
                    task_list = [each for each in task_list
                                 if search in str(each['id'])
                                 or search in each['name']
                                 or search in each['teacher']
                                 or search in {True: '已关闭上传', False: '已开启上传'}[each['status']]
                                 or search in {True: '已查重', False: '未查重'}[each['get_result']]
                                 ]
                    count = len(task_list)
                if length != -1:
                    end = start + length
                    task_list = task_list[start:end]
                data_json = {"draw": draw, "recordsTotal": count, "recordsFiltered": count}
                json_data_list = []
                for each in task_list:
                    each['operation'] = ('''
                    <form method="get" action="/s/submit/" style="margin: 0; display: inline">
                        <input type="hidden" value="%d" name="taskid">
                        <button class="btn btn-%s btn-xs %s">%s</button>
                    </form>''' % (each['id'], 'primary' if each['submit_times'] == 0 else 'warning',
                                  'disabled" disabled="disabled' if each['status'] else '',
                                  '提交作业' if each['submit_times'] == 0 else '重新提交')) + (
                            '''
                        <form method="post" action="/s/view_result/" style="margin: 0; display: inline">
                        <input type="hidden" value="%s" name="task_id">
                        <button class="btn btn-primary btn-xs %s">查看结果</button>
                    </form>''' % (each['id'], '' if each['get_result'] else 'disabled" disabled="disabled')
                    )
                    each['status'] = ('已关闭上传' if each['status'] else '已开启上传') \
                                     + ('|已查重' if each['get_result'] else '|未查重'),
                    json_data_list.append(each)
                data_json["data"] = json_data_list
                return HttpResponse(json.dumps(data_json))
            else:
                context = {
                    "task_list": task_list[:10],
                    "defcount": count,
                    "sidebar_collapse": request.GET.get('sidebar_collapse', ''),
                }
                return render(request, 's_viewtask.html', context)
    else:
        raise Http404("你没有权限访问该页面")


# 学生提交作业
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def s_submit(request):
    if request.session['user']['user_type'] == 'S':
        if request.method == 'GET':
            task_id = request.GET.get('taskid')
            student_id = request.session['user']['user_id']
            task = Task.objects.get(id=task_id)
            student = MyUser.objects.get(user__username=student_id)
            task_obj_list = Submit.objects.filter(user=student, task=task)
            if len(task_obj_list) > 0:
                context = {'task_id': task_id}
                return render(request, 's_submit.html', context)
            else:
                raise Http404("你没有权限访问该页面")
        elif request.method == 'POST':
            task_id = request.POST.get('task_id')
            file = request.FILES.get('file')
            filename = file.name.replace(' ', '_')
            suffix = filename.split('.')[-1].lower()
            # 判断格式
            if suffix == 'docx':
                document = docx.Document(file)
                code = '\r\n'.join([paragraph.text for paragraph in document.paragraphs])#.encode('utf-8')
            elif suffix in SUFFIX:
                file_data = file.read()
                encoding = chardet.detect(file_data)['encoding']
                code = file_data.decode(encoding)#.encode('utf-8')
            else:
                context = {'msg': '上传失败：文件格式不支持！'}
                save_log(request, '上传作业到[task_id:%s]失败, 文件格式不正确！' % task_id)
                return render(request, 's_submit_result.html', context)
            # 保存到数据库
            try:
                student_id = request.session['user']['user_id']
                task = Task.objects.get(id=task_id)
                student = MyUser.objects.get(user__username=student_id)
                # Submit.objects.filter(task=task, user=student).exclude(code='').delete()
                submit = Submit(task=task, user=student, filename=filename, code=code)
                submit.save()
                context = {'msg': '上传成功'}
                save_log(request, '上传作业到[task_id:%s]成功' % task_id)
                return render(request, 's_submit_result.html', context)
            except:
                context = {'msg': '上传失败'}
                save_log(request, '上传作业到[task_id:%s]失败' % task_id)
                return render(request, 's_submit_result.html', context)
    else:
        raise Http404("你没有权限访问该页面")


# 学生查看结果
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def s_view_result(request):
    if request.method == "POST":
        if request.session['user']['user_type'] == 'S':
            task_id = request.POST.get('task_id')
            stu_id = request.session['user']['user_id']
            if len(Submit.objects.filter(task__id=task_id, user=MyUser.objects.get(user__username=stu_id))) > 0:
                task = Task.objects.get(id=task_id)
                result_obj_list = Result.objects.filter(task=task)
                data_list = []
                stu_list = []
                for each in result_obj_list:
                    num = 0
                    matched_lines_list = each.matched_lines.split(',')
                    for i in range(0, len(matched_lines_list), 4):
                        split_list = matched_lines_list[i].split('-')
                        num += int(split_list[1]) - int(split_list[0]) + 1
                    data = dict(
                        id=each.id,
                        stu_ids=[each.file1_name.split('_')[0], each.file2_name.split('_')[0]],
                        # filenames=[''.join(each.file1_name.split('_')[1:]), ''.join(each.file2_name.split('_')[1:])],
                        percents=[each.percent1, each.percent2],
                        matched_lines_num=num,
                    )
                    for x in data['stu_ids']:
                        if x not in stu_list:
                            stu_list.append(x)
                    data_list.append(data)
                # 生成二位数组的数据
                result = {}
                for i in stu_list:
                    result_2 = {}
                    for j in stu_list:
                        flag1 = False
                        flag2 = False
                        if i == j:
                            result_2[j] = {'line': 0, 'data': None}
                            continue
                        for each in data_list:
                            if each['stu_ids'] == [i, j]:
                                result_2[j] = {'line': each['matched_lines_num'], 'data': each}
                                flag1 = True
                            elif each['stu_ids'] == [j, i]:
                                result_2[j] = {'line': each['matched_lines_num'], 'data': dict(
                                    id=each['id'],
                                    stu_ids=each['stu_ids'][::-1],
                                    # filenames=each['filenames'][::-1],
                                    percents=each['percents'][::-1],
                                    matched_lines_num=each['matched_lines_num'],
                                )}
                                flag2 = True
                            if flag1 and flag2:
                                break
                        if not flag1 and not flag2:
                            result_2[j] = {'line': 0, 'data': None}
                    result[i] = {'num': len([x for x in result_2 if result_2[x]['data'] is not None]), 'data': result_2}
                # 根据需要调整行列数据
                row_th = [stu_id]  # 行名，result[行名]['data']是一行的数据
                column_th = []  # 列名，result[行名]['data'][列名]['data']是一格的数据
                temp_column = [x for x in result[stu_id]['data']]
                temp_line = [result[stu_id]['data'][x]['line'] for x in temp_column]
                while temp_column:
                    index = temp_line.index(max(temp_line))
                    column_th.append(temp_column[index])
                    temp_line.pop(index)
                    temp_column.pop(index)
                # 准备返回的数据
                result_list = []
                for p in row_th:
                    temp_data = [dict(action='result', value=task_id + '_' + p, type='primary',
                                      disable='disabled" disabled="disabled',
                                      text='%s | %s' % (MyUser.objects.get(user__username=p).name, p))
                                 ]
                    for q in column_th:
                        if q in result[p]['data']:
                            one_data = result[p]['data'][q]['data']
                            one_line = result[p]['data'][q]['line']
                            if one_data:
                                percent = '%d%% | %d%%' % (one_data['percents'][0], one_data['percents'][1])
                                temp_data.append(dict(action='detail', value='_'.join([task_id, str(one_data['id']), str(stu_id)]),
                                                      type='link', disable='', text='%s | %s行' % (percent, one_line)))
                            else:
                                temp_data.append(dict(action='detail', value='', text='', type='link',
                                                      disable='disabled" disabled="disabled'))
                        else:
                            temp_data.append(dict(action='detail', value='', text='', type='link',
                                                  disable='disabled" disabled="disabled'))
                    result_list.append(temp_data)
                context = dict(
                    thead=[(MyUser.objects.get(user__username=x).name + ' | ' + x) for x in column_th],
                    tbody=result_list,
                )
                return render(request, 's_viewresult.html', context)
            else:
                raise Http404("你没有权限访问该页面")
        else:
            raise Http404("你没有权限访问该页面")
    else:
        raise Http404("你没有权限访问该页面")


# 学生查看详细
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def s_view_detail(request):
    if request.method == "POST":
        if request.session['user']['user_type'] == 'S':
            task_id = request.POST.get('task_id')
            user_id = request.session['user']['user_id']
            result_id = request.POST.get('result_id')
            stu_id = request.POST.get('stu_id')
            if len(Submit.objects.filter(task__id=task_id, user=MyUser.objects.get(user__username=stu_id))) > 0 \
                    and user_id == stu_id:
                result = Result.objects.get(id=result_id)
                stu_1_id = result.file1_name.split('_')[0]
                stu_2_id = result.file2_name.split('_')[0]
                stu_1_name = MyUser.objects.get(user__username=stu_1_id).name
                stu_2_name = MyUser.objects.get(user__username=stu_2_id).name
                filename_1 = ''.join(result.file1_name.split('_')[1:])
                filename_2 = ''.join(result.file2_name.split('_')[1:])
                percent1 = result.percent1
                percent2 = result.percent2
                matched_lines = result.matched_lines.split(',')
                matched_times = 0
                matched_1 = []
                matched_2 = []
                for i in range(0, len(matched_lines), 4):
                    matched_times += 1
                    matched_1.append(matched_lines[i] + '(' + matched_lines[i+1] + '%)')
                    matched_2.append(matched_lines[i+2] + '(' + matched_lines[i+3] + '%)')
                info = [
                    dict(id=stu_1_id, name=stu_1_name, fname=filename_1, percent=percent1, matched=matched_1),
                    dict(id=stu_2_id, name=stu_2_name, fname=filename_2, percent=percent2, matched=matched_2),
                ]
                context = dict(
                    stu_id=stu_id,
                    task_id=task_id,
                    result_id=result_id,
                    matched_times=matched_times,
                    info=info,
                    code1=result.file1_code,
                    code2=result.file2_code,
                )
                return render(request, 's_viewdetail.html', context)
            else:
                raise Http404("你没有权限访问该页面")
        else:
            raise Http404("你没有权限访问该页面")
    else:
        raise Http404("你没有权限访问该页面")


# 教师查看作业
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def t_viewtask(request):
    if request.session['user']['user_type'] == 'T':
        if request.method == 'GET':
            teacher_id = request.session['user']['user_id']
            teacher = MyUser.objects.get(user__username=teacher_id)
            task_list = Task.objects.filter(teacher=teacher).values()
            for each in task_list:
                each['create_time'] = datetime.datetime.strftime(each['create_time'], "%Y-%m-%d %H:%M:%S")
                each['get_result'] = False if len(Result.objects.filter(task__id=each['id'])) == 0 else True
                submit_number = len(
                    Submit.objects.exclude(code='').filter(task__id=each['id']).values('user_id').distinct())
                all_number = len(Submit.objects.filter(task__id=each['id']).values('user_id').distinct())
                each['submit_number'] = '%d/%d' % (submit_number, all_number)
            count = len(task_list)
            if request.is_ajax():
                draw = int(request.GET['draw'])
                start = int(request.GET['start'])
                length = int(request.GET['length'])
                search = request.GET['search[value]']
                if search:
                    task_list = [each for each in task_list
                                 if search in str(each['id'])
                                 or search in each['name']
                                 or search in {True: '关闭上传', False: '开启上传'}[each['status']]
                                 or search in {True: '已查重', False: '未查重'}[each['get_result']]
                                 ]
                    count = len(task_list)
                if length != -1:
                    end = start + length
                    task_list = task_list[start:end]
                data_json = {"draw": draw, "recordsTotal": count, "recordsFiltered": count}
                json_data_list = []
                for each in task_list:
                    data = dict(
                        id=each['id'],
                        name=each['name'],
                        create_time=each['create_time'],
                        status=('关闭上传' if each['status'] else '开启上传') +
                               ('|已查重' if each['get_result'] else '|未查重'), submit_number=each['submit_number'],
                        operation=(
                                      '<button action="submit_on" class="btn btn-primary btn-xs" \
                             value="%d">开启</button>' % each['id']
                                      if each['status'] else
                                      '<button action="submit_off" class="btn btn-danger btn-xs"  \
                            value="%d">关闭</button>' % each['id']
                                  ) + '''
                        <form method="get" action="/t/addstudent/" style="margin: 0; display: inline">
                        <input type="hidden" value="%d" name="taskid">
                        <button class="btn btn-primary btn-xs" type="submit">管理学生</button>
                        </form>''' % each['id'] + ('''
                        <button action="start_check" class="btn btn-warning btn-xs" value="%d">再次查重</button>
                        <form method="post" action="/t/view_result/" style="margin: 0; display: inline">
                            <input type="hidden" value="%s" name="task_id">
                        <button action="result" class="btn btn-primary btn-xs" value=%d>查看结果</button></form>
                        ''' % (each['id'], each['id'], each['id']) if each['get_result'] else '''
                        <button action="start_check" class="btn btn-primary btn-xs" value="%d">开始查重</button>
                        <form method="post" action="/t/view_result/" style="margin: 0; display: inline">
                            <input type="hidden" value="%s" name="task_id">
                        <button action="result" class="btn btn-primary btn-xs disabled" disabled="disabled"
                         value=%d>查看结果</button></form>''' % (each['id'], each['id'], each['id'])
                                                   )
                    )
                    json_data_list.append(data)
                data_json["data"] = json_data_list
                return HttpResponse(json.dumps(data_json))
            else:
                context = {
                    "task_list": task_list[:10],
                    "defcount": count,
                    "sidebar_collapse": request.GET.get('sidebar_collapse', ''),
                }
                return render(request, 't_viewtask.html', context)
    else:
        raise Http404("你没有权限访问该页面")


# 教师添加作业
@login_required(login_url=LOGIN_URL)
def t_addtask(request):
    if request.session['user']['user_type'] == 'T':
        if request.method == 'GET':
            return render(request, 't_addtask.html')
        elif request.method == 'POST':
            task_name = request.POST.get('task_name')
            if task_name == '':
                context = {'msg': '请输入作业名！！！'}
                return render(request, 't_addtask.html', context)
            else:
                teacher_id = request.session['user']['user_id']
                a_new_task = Task(name=task_name, teacher=MyUser.objects.get(user__username=teacher_id))
                a_new_task.save()
                task_id = a_new_task.id
                save_log(request, '添加作业[%s:%s]' % (task_id, task_name))
                return HttpResponseRedirect('/t/addstudent/?taskid=%d' % task_id)

    else:
        raise Http404("你没有权限访问该页面")


# 教师为作业添加学生页面
@login_required(login_url=LOGIN_URL)
def t_addstudent(request):
    if request.session['user']['user_type'] == 'T':
        if request.method == 'GET':
            task_id = request.GET.get('taskid')
            teacher_id = request.session['user']['user_id']
            teacher = MyUser.objects.get(user__username=teacher_id)
            if Task.objects.get(id=task_id).teacher == teacher:
                student_list = MyUser.objects.filter(user_type='S').values('user', 'name', 'gender', 'class_name')
                for each in student_list:
                    stu_id = User.objects.get(id=each['user']).username
                    each['id'] = stu_id
                    submit = Submit.objects.filter(task=Task.objects.get(id=request.GET.get('taskid')),
                                                   user=MyUser.objects.get(user__username=stu_id))
                    if len(submit) == 0:
                        each['status'] = False
                    else:
                        each['status'] = True
                        each['submit_times'] = len(submit) - 1
                count = len(student_list)
                if request.is_ajax():
                    draw = int(request.GET['draw'])
                    start = int(request.GET['start'])
                    length = int(request.GET['length'])
                    search = request.GET['search[value]']
                    if search:
                        student_list = [each for each in student_list
                                        if search in each['id']
                                        or search in each['name']
                                        or search in each['gender']
                                        or search in each['class_name']
                                        or search in {True: '已添加', False: '未添加'}[each['status']]
                                        ]
                        count = len(student_list)
                    if length != -1:
                        end = start + length
                        student_list = student_list[start:end]
                    data_json = {"draw": draw, "recordsTotal": count, "recordsFiltered": count}
                    json_data_list = []
                    for each in student_list:
                        data = dict(
                            id=each['id'],
                            name=each['name'],
                            gender='男' if each['gender'] == 'M' else '女',
                            class_name=each['class_name'],
                            status=(('已添加|未上传' if each['submit_times'] == 0 else '已上传%d次' % each['submit_times'])
                                    if each['status'] else '未添加'),
                            operation='<button action="remove" class="btn btn-danger btn-xs" \
                             value="%s">移除</button>' % each['id'] if each['status'] else
                            '<button action="add" class="btn btn-primary btn-xs" value="%s">添加</button>' % each['id']
                        )
                        json_data_list.append(data)
                    data_json["data"] = json_data_list
                    return HttpResponse(json.dumps(data_json))
                else:
                    context = {
                        "student_list": student_list[:10],
                        "defcount": count,
                        "sidebar_collapse": request.GET.get('sidebar_collapse', ''),
                    }
                    return render(request, 't_addstudent.html', context)
            else:
                raise Http404("你没有权限访问该页面")
    else:
        raise Http404("你没有权限访问该页面")


# 教师关闭作业
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def t_task_off(request):
    if request.method == "POST":
        if request.session['user']['user_type'] == 'T':
            data = json.loads(request.POST.get("data"))
            task_id = data['task_id']
            teacher_id = request.session['user']['user_id']
            teacher = MyUser.objects.get(user__username=teacher_id)
            if Task.objects.get(id=task_id).teacher == teacher:
                try:
                    task = Task.objects.get(id=task_id)
                    task.status = True
                    task.save()
                    save_log(request, '关闭作业[%s]成功' % task_id)
                    return HttpResponse("1")
                except:
                    save_log(request, '关闭作业[%s]失败' % task_id)
                    return HttpResponse("0")
            else:
                return HttpResponse("0")
        else:
            return HttpResponse("0")


# 教师开启作业
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def t_task_on(request):
    if request.method == "POST":
        if request.session['user']['user_type'] == 'T':
            data = json.loads(request.POST.get("data"))
            task_id = data['task_id']
            teacher_id = request.session['user']['user_id']
            teacher = MyUser.objects.get(user__username=teacher_id)
            if Task.objects.get(id=task_id).teacher == teacher:
                try:
                    task = Task.objects.get(id=task_id)
                    task.status = False
                    task.save()
                    save_log(request, '开启作业[%s]成功' % task_id)
                    return HttpResponse("1")
                except:
                    save_log(request, '开启作业[%s]失败' % task_id)
                    return HttpResponse("0")
            else:
                return HttpResponse("0")
        else:
            return HttpResponse("0")


# 教师移除学生
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def t_remove_student(request):
    if request.method == "POST":
        if request.session['user']['user_type'] == 'T':
            data = json.loads(request.POST.get("data"))
            stu_id = data['stu_id']
            task_id = data['task_id']
            teacher_id = request.session['user']['user_id']
            teacher = MyUser.objects.get(user__username=teacher_id)
            if Task.objects.get(id=task_id).teacher == teacher:
                try:
                    student = MyUser.objects.get(user__username=stu_id)
                    task = Task.objects.get(id=task_id)
                    Submit.objects.filter(task=task, user=student).delete()
                    save_log(request, '作业[%s]移除学生[%s]成功' % (task_id, stu_id))
                    return HttpResponse("1")
                except:
                    save_log(request, '作业[%s]移除学生[%s]失败' % (task_id, stu_id))
                    return HttpResponse("0")
            else:
                return HttpResponse("0")
        else:
            return HttpResponse("0")


# 教师添加学生
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def t_add_student(request):
    if request.method == "POST":
        if request.session['user']['user_type'] == 'T':
            data = json.loads(request.POST.get("data"))
            stu_id = data['stu_id']
            task_id = data['task_id']
            teacher_id = request.session['user']['user_id']
            teacher = MyUser.objects.get(user__username=teacher_id)
            if Task.objects.get(id=task_id).teacher == teacher:
                try:
                    student = MyUser.objects.get(user__username=stu_id)
                    task = Task.objects.get(id=task_id)
                    submit_init = Submit(task=task, user=student)
                    submit_init.save()
                    save_log(request, '作业[%s]添加学生[%s]成功' % (task_id, stu_id))
                    return HttpResponse("1")
                except:
                    save_log(request, '作业[%s]添加学生[%s]失败' % (task_id, stu_id))
                    return HttpResponse("0")
            else:
                return HttpResponse("0")
        else:
            return HttpResponse("0")


# 教师提交作业
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def t_submit_task(request):
    if request.method == "POST":
        if request.session['user']['user_type'] == 'T':
            data = json.loads(request.POST.get("data"))
            task_id = data['task_id']
            teacher_id = request.session['user']['user_id']
            teacher = MyUser.objects.get(user__username=teacher_id)
            if Task.objects.get(id=task_id).teacher == teacher:
                try:
                    task = Task.objects.get(id=task_id)
                    codes = Submit.objects.exclude(code='').filter(task=task)
                    stu_list = codes.values('user').distinct()
                    latest_code_list = []
                    for each in stu_list:
                        latest_code = codes.filter(user_id=each['user']).order_by('-time')[0]
                        latest_code_list.append(latest_code)
                    codes_list = []
                    for each in latest_code_list:
                        user_id = User.objects.get(id=each.user.user.id).username
                        data = {
                            'filename': '_'.join([user_id, each.filename]),
                            'code': each.code,
                        }
                        codes_list.append(data)
                    save_log(request, '作业[%s]上传作业检测成功' % task_id)
                    t = threading.Thread(target=mul_get_result, args=(request, codes_list, task_id))
                    t.setDaemon(False)
                    t.start()
                    return HttpResponse("1")
                except:
                    save_log(request, '作业[%s]上传作业检测失败' % task_id)
                    return HttpResponse("0")
        else:
            return HttpResponse("0")
    else:
        return HttpResponse("0")


# 提交作业多线程获得结果
def mul_get_result(request, codes_list, task_id):
    m = Moss(USERID)
    for each in codes_list:
        m.add_file(each['filename'], each['code'])
    url = m.send()
    save_log(request, '作业[%s]查重结果链接获取成功[%s]' % (task_id, url))
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    num = int(soup.find_all('tr')[-1].find('a').get('href').split('/')[-1].split('.')[0][5:])
    Result.objects.filter(task=Task.objects.get(id=task_id)).delete()  # 清除之前的记录
    # 多线程
    func_vars = []  # 参数
    for i in range(num + 1):
        func_vars.append(([request, task_id, url, i], None))
    pool = threadpool.ThreadPool(4)
    reqs = threadpool.makeRequests(sin_get_result, func_vars)
    [pool.putRequest(req) for req in reqs]
    pool.wait()
    if len(Result.objects.filter(task=Task.objects.get(id=task_id))) == num + 1:
        save_log(request, '作业[%s]查重结果全部获取完成' % task_id)
    else:
        Result.objects.filter(task=Task.objects.get(id=task_id)).delete()
        save_log(request, '作业[%s]查重结果获取失败' % task_id)


# 获得一条结果
def sin_get_result(request, task_id, url, num):
    try:
        url_top = '%s/match%d-top.html' % (url, num)
        url_1 = '%s/match%d-0.html' % (url, num)
        url_2 = '%s/match%d-1.html' % (url, num)
        # 顶部
        r = requests.get(url_top)
        th_list = re.findall(r'<th>(.*?)<th>', r.content.decode('utf-8'), re.I)
        filename_1 = '('.join(th_list[0].split('(')[:-1])
        percent_1 = th_list[0].split('(')[-1][:-2]
        filename_2 = '('.join(th_list[1].split('(')[:-1])
        percent_2 = th_list[1].split('(')[-1][:-2]
        soup_top = BeautifulSoup(r.content, "html.parser")
        a_list = soup_top.find_all('a')
        matched_data = []
        for i in range(0, len(a_list), 2):
            matched_line = a_list[i].text
            percent = a_list[i + 1].find('img').get('src').split('_')[-1].split('.')[0]
            matched_data.extend([matched_line, percent])
        matched_lines = ','.join(matched_data)
        # 第一个代码
        soup_1 = BeautifulSoup(requests.get(url_1).content, "html.parser")
        text_1 = str(soup_1.body)
        tag_a_1 = re.findall(r'<a.*?</a>', text_1)
        for each in tag_a_1:
            text_1 = text_1.replace(each, '')
        text_1 = text_1[28:-7]
        # 第二个代码
        soup_2 = BeautifulSoup(requests.get(url_2).content, "html.parser")
        text_2 = str(soup_2.body)
        tag_a_2 = re.findall(r'<a.*?</a>', text_2)
        for each in tag_a_2:
            text_2 = text_2.replace(each, '')
        text_2 = text_2[28:-7]
        # text_1 = requests.get(url_1).content
        # text_2 = requests.get(url_2).content
        result = Result(
            task=Task.objects.get(id=task_id),
            file1_name=filename_1,
            file2_name=filename_2,
            percent1=percent_1,
            percent2=percent_2,
            matched_lines=matched_lines,
            file1_code=text_1,
            file2_code=text_2,
        )
        result.save()
        save_log(request, '作业[%s]查重结果第[%d]条获取完成[%d]' % (task_id, num+1, result.id))
    except:
        save_log(request, '作业[%s]查重结果第[%d]条获取失败' % (task_id, num + 1))


# 教师查看结果
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def t_view_result(request):
    if request.method == "POST":
        if request.session['user']['user_type'] == 'T':
            task_id = request.POST.get('task_id')
            stu_id = request.POST.get('stu_id')
            teacher_id = request.session['user']['user_id']
            teacher = MyUser.objects.get(user__username=teacher_id)
            task = Task.objects.get(id=task_id)
            if task.teacher == teacher:
                result_obj_list = Result.objects.filter(task=task)
                data_list = []
                stu_list = []
                for each in result_obj_list:
                    num = 0
                    matched_lines_list = each.matched_lines.split(',')
                    for i in range(0, len(matched_lines_list), 4):
                        split_list = matched_lines_list[i].split('-')
                        num += int(split_list[1]) - int(split_list[0]) + 1
                    data = dict(
                        id=each.id,
                        stu_ids=[each.file1_name.split('_')[0], each.file2_name.split('_')[0]],
                        # filenames=[''.join(each.file1_name.split('_')[1:]), ''.join(each.file2_name.split('_')[1:])],
                        percents=[each.percent1, each.percent2],
                        matched_lines_num=num,
                    )
                    for x in data['stu_ids']:
                        if x not in stu_list:
                            stu_list.append(x)
                    data_list.append(data)
                # 生成二位数组的数据
                result = {}
                for i in stu_list:
                    result_2 = {}
                    for j in stu_list:
                        flag1 = False
                        flag2 = False
                        if i == j:
                            result_2[j] = {'line': 0, 'data': None}
                            continue
                        for each in data_list:
                            if each['stu_ids'] == [i, j]:
                                result_2[j] = {'line': each['matched_lines_num'], 'data': each}
                                flag1 = True
                            elif each['stu_ids'] == [j, i]:
                                result_2[j] = {'line': each['matched_lines_num'], 'data': dict(
                                    id=each['id'],
                                    stu_ids=each['stu_ids'][::-1],
                                    # filenames=each['filenames'][::-1],
                                    percents=each['percents'][::-1],
                                    matched_lines_num=each['matched_lines_num'],
                                )}
                                flag2 = True
                            if flag1 and flag2:
                                break
                        if not flag1 and not flag2:
                            result_2[j] = {'line': 0, 'data': None}
                    result[i] = {'num': len([x for x in result_2 if result_2[x]['data'] is not None]), 'data': result_2}
                # 根据需要调整行列数据
                row_th = []  # 行名，result[行名]['data']是一行的数据
                temp_row = [x for x in result]
                temp_num = [result[x]['num'] for x in temp_row]
                while temp_num:
                    index = temp_num.index(max(temp_num))
                    row_th.append(temp_row[index])
                    temp_num.pop(index)
                    temp_row.pop(index)
                column_th = []  # 列名，result[行名]['data'][列名]['data']是一格的数据
                if not stu_id:
                    stu_id = row_th[0]
                temp_column = [x for x in result[stu_id]['data']]
                temp_line = [result[stu_id]['data'][x]['line'] for x in temp_column]
                while temp_column:
                    index = temp_line.index(max(temp_line))
                    column_th.append(temp_column[index])
                    temp_line.pop(index)
                    temp_column.pop(index)
                # 准备返回的数据
                result_list = []
                for p in row_th:
                    temp_data = [dict(action='result', value=task_id + '_' + p, type='primary', disable='',
                                    text='%s | %s' % (MyUser.objects.get(user__username=p).name, p))
                                 ]
                    for q in column_th:
                        if q in result[p]['data']:
                            one_data = result[p]['data'][q]['data']
                            one_line = result[p]['data'][q]['line']
                            if one_data:
                                percent = '%d%% | %d%%' % (one_data['percents'][0], one_data['percents'][1])
                                temp_data.append(dict(action='detail', value='_'.join([task_id, str(one_data['id']), str(stu_id)]),
                                                      type='link', disable='', text='%s | %s行' % (percent, one_line)))
                            else:
                                temp_data.append(dict(action='detail', value='', text='', type='link',
                                                      disable='disabled" disabled="disabled'))
                        else:
                            temp_data.append(dict(action='detail', value='', text='', type='link',
                                                  disable='disabled" disabled="disabled'))
                    result_list.append(temp_data)
                context = dict(
                    thead=[(MyUser.objects.get(user__username=x).name + ' | ' + x) for x in column_th],
                    tbody=result_list,
                )
                return render(request, 't_viewresult.html', context)
            else:
                raise Http404("你没有权限访问该页面")
        else:
            raise Http404("你没有权限访问该页面")
    else:
        raise Http404("你没有权限访问该页面")


# 教师查看详细
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def t_view_detail(request):
    if request.method == "POST":
        if request.session['user']['user_type'] == 'T':
            task_id = request.POST.get('task_id')
            result_id = request.POST.get('result_id')
            stu_id = request.POST.get('stu_id')
            teacher_id = request.session['user']['user_id']
            teacher = MyUser.objects.get(user__username=teacher_id)
            task = Task.objects.get(id=task_id)
            if task.teacher == teacher:
                result = Result.objects.get(id=result_id)
                stu_1_id = result.file1_name.split('_')[0]
                stu_2_id = result.file2_name.split('_')[0]
                stu_1_name = MyUser.objects.get(user__username=stu_1_id).name
                stu_2_name = MyUser.objects.get(user__username=stu_2_id).name
                filename_1 = ''.join(result.file1_name.split('_')[1:])
                filename_2 = ''.join(result.file2_name.split('_')[1:])
                percent1 = result.percent1
                percent2 = result.percent2
                matched_lines = result.matched_lines.split(',')
                matched_times = 0
                matched_1 = []
                matched_2 = []
                for i in range(0, len(matched_lines), 4):
                    matched_times += 1
                    matched_1.append(matched_lines[i] + '(' + matched_lines[i+1] + '%)')
                    matched_2.append(matched_lines[i+2] + '(' + matched_lines[i+3] + '%)')
                info = [
                    dict(id=stu_1_id, name=stu_1_name, fname=filename_1, percent=percent1, matched=matched_1),
                    dict(id=stu_2_id, name=stu_2_name, fname=filename_2, percent=percent2, matched=matched_2),
                ]
                context = dict(
                    stu_id=stu_id,
                    task_id=task_id,
                    result_id=result_id,
                    matched_times=matched_times,
                    info=info,
                    code1=result.file1_code,
                    code2=result.file2_code,
                )
                return render(request, 't_viewdetail.html', context)
            else:
                raise Http404("你没有权限访问该页面")
        else:
            raise Http404("你没有权限访问该页面")
    else:
        raise Http404("你没有权限访问该页面")


# 管理员查看日志
@login_required(login_url=LOGIN_URL)
def a_viewlog(request):
    if request.session['user']['user_type'] == 'A':
        if request.method == 'GET':
            log_obj_list = Log.objects.all().values()
            log_list = []
            for each in log_obj_list:
                myuser = MyUser.objects.get(id=each['user_id'])
                user_id = User.objects.get(id=myuser.user_id).username
                data = dict(
                    id=user_id,
                    name=myuser.name,
                    gender={'M': '男', 'F': '女'}[myuser.gender],
                    user_type={'S': '学生', 'T': '教师', 'A': '管理员'}[myuser.user_type],
                    user_class=myuser.class_name,
                    operation=each['operation'],
                    time=datetime.datetime.strftime(each['time'], "%Y-%m-%d %H:%M:%S")
                )
                log_list.append(data)
            count = len(log_list)
            if request.is_ajax():
                draw = int(request.GET['draw'])
                start = int(request.GET['start'])
                length = int(request.GET['length'])
                search = request.GET['search[value]']
                if search:
                    log_list = [each for each in log_list
                                if search in str(each['id'])
                                or search in each['name']
                                or search in each['gender']
                                or search in each['user_type']
                                or search in each['user_class']
                                or search in each['operation']
                                or search in each['time']
                                ]
                    count = len(log_list)
                if length != -1:
                    end = start + length
                    log_list = log_list[start:end]
                data_json = {"draw": draw, "recordsTotal": count, "recordsFiltered": count, "data": log_list}
                return HttpResponse(json.dumps(data_json))
            else:
                context = {
                    "task_list": log_list[:10],
                    "defcount": count,
                    "sidebar_collapse": request.GET.get('sidebar_collapse', ''),
                }
                return render(request, 'a_viewlog.html', context)
        return render(request, 'a_viewlog.html')
    else:
        raise Http404("你没有权限访问该页面")


# 管理员管理成员
@login_required(login_url=LOGIN_URL)
def a_manage(request):
    if request.session['user']['user_type'] == 'A':
        if request.method == 'GET':
            myuser_obj_list = MyUser.objects.all().values()
            user_list = []
            for each in myuser_obj_list:
                user_id = User.objects.get(id=each['user_id']).username
                data = dict(
                    id=user_id,
                    name=each['name'],
                    gender={'M': '男', 'F': '女'}[each['gender']],
                    user_type={'S': '学生', 'T': '教师', 'A': '管理员'}[each['user_type']],
                    remove=False if each['user_type'] == 'A' else True,
                    user_class=each['class_name'],
                )
                user_list.append(data)
            count = len(user_list)
            if request.is_ajax():
                draw = int(request.GET['draw'])
                start = int(request.GET['start'])
                length = int(request.GET['length'])
                search = request.GET['search[value]']
                if search:
                    user_list = [each for each in user_list
                                 if search in str(each['id'])
                                 or search in each['name']
                                 or search in each['gender']
                                 or search in each['user_type']
                                 or search in each['user_class']
                                 ]
                    count = len(user_list)
                if length != -1:
                    end = start + length
                    user_list = user_list[start:end]
                for each in user_list:
                    each['operation'] = '<button action="remove" class="btn btn-danger btn-xs %s"value="%s">\
                    移除</button>' % (('disabled" disabled="disabled' if not each['remove'] else ''), each['id'])
                data_json = {"draw": draw, "recordsTotal": count, "recordsFiltered": count, "data": user_list}
                return HttpResponse(json.dumps(data_json))
            else:
                context = {
                    "user_list": user_list[:10],
                    "defcount": count,
                    "sidebar_collapse": request.GET.get('sidebar_collapse', ''),
                }
                return render(request, 'a_manage.html', context)
        return render(request, 'a_manage.html')
    else:
        raise Http404("你没有权限访问该页面")


# 管理员删除用户
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def a_remove_user(request):
    if request.session['user']['user_type'] == 'A':
        if request.method == "POST":
            data = json.loads(request.POST.get("data"))
            remove_user_id = data['user_id']
            try:
                User.objects.get(username=remove_user_id).delete()
                save_log(request, '移除用户[%s]成功' % remove_user_id)
                return HttpResponse("1")
            except:
                save_log(request, '移除用户[%s]失败' % remove_user_id)
                return HttpResponse("0")
    else:
        raise Http404("你没有权限访问该页面")


# 管理员管理作业
@login_required(login_url=LOGIN_URL)
def a_task(request):
    if request.session['user']['user_type'] == 'A':
        if request.method == 'GET':
            task_obj_list = Task.objects.all().values()
            task_list = []
            for each in task_obj_list:
                myuser = MyUser.objects.get(id=each['teacher_id'])
                t_name = myuser.name
                t_id = User.objects.get(id=myuser.user_id).username
                data = dict(
                    id=each['id'],
                    name=each['name'],
                    teacher='|'.join((t_name, t_id)),
                    create_time=datetime.datetime.strftime(each['create_time'], "%Y-%m-%d %H:%M:%S"),
                    student_number=len(Submit.objects.filter(task__id=each['id']).values('user_id').distinct()),
                    status='%s上传|%s查重' % (('关闭' if each['status'] else '开启'),
                                           ('未' if len(Result.objects.filter(task__id=each['id'])) == 0 else '已'))
                )
                task_list.append(data)
            count = len(task_list)
            if request.is_ajax():
                draw = int(request.GET['draw'])
                start = int(request.GET['start'])
                length = int(request.GET['length'])
                search = request.GET['search[value]']
                if search:
                    task_list = [each for each in task_list
                                 if search in str(each['id'])
                                 or search in each['name']
                                 or search in each['teacher']
                                 or search in each['status']
                                 or search in each['create_time']
                                 ]
                    count = len(task_list)
                if length != -1:
                    end = start + length
                    task_list = task_list[start:end]
                data_json = {"draw": draw, "recordsTotal": count, "recordsFiltered": count}
                for each in task_list:
                    each['operation'] = '<button action="remove" class="btn btn-danger btn-xs"' \
                                        ' value="%s">移除</button>' % each['id']
                data_json["data"] = task_list
                return HttpResponse(json.dumps(data_json))
            else:
                context = {
                    "task_list": task_list[:10],
                    "defcount": count,
                    "sidebar_collapse": request.GET.get('sidebar_collapse', ''),
                }
                return render(request, 'a_task.html', context)
        return render(request, 'a_task.html')
    else:
        raise Http404("你没有权限访问该页面")


# 管理员删除作业
@csrf_exempt
@login_required(login_url=LOGIN_URL)
def a_remove_task(request):
    if request.session['user']['user_type'] == 'A':
        if request.method == "POST":
            data = json.loads(request.POST.get("data"))
            remove_task_id = data['task_id']
            try:
                Task.objects.get(id=remove_task_id).delete()
                save_log(request, '删除作业[%s]成功' % remove_task_id)
                return HttpResponse("1")
            except:
                save_log(request, '删除作业[%s]失败' % remove_task_id)
                return HttpResponse("0")
    else:
        raise Http404("你没有权限访问该页面")


# 保存日志
def save_log(request, operation):
    user_id = request.session['user']['user_id']
    user = MyUser.objects.get(user__username=user_id)
    log = Log(user=user, operation=operation)
    log.save()
