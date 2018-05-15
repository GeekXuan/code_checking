# 抄袭检测系统

## 1.所需环境
* **[Python 3.6](https://www.python.org/downloads/)**
* **[MySQL 5.7](https://www.mysql.com/downloads/)**


## 2.本地调试
* 安装需要的Python模块

进入项目文件夹下运行
```console
pip install -r requirements.txt
```
如果装有python2和python3多个版本的python可能需要使用pip3
```console
pip3 install -r requirements.txt 
```
使用虚拟环境并且存在多个虚拟环境的情况下需要找到该虚拟环境下的pip或pip3运行，例如：
```console
venv\Scripts\pip3 install -r requirements.txt
```

* 配置数据库

（1）MySQL 5.7版本安装后设置的默认编码为utf-8，如果使用其他版本的请确认编码是否为utf-8，如果不是请自行搜索设置编码为utf-8。

（2）登陆MySQL后创建数据库
```mysql
mysql>create database code_checking;
```

* 修改配置文件

修改project文件夹下的settings.py文件

(1)将DATABASES中的NAME、USER、PASSWORD、HOST、PORT分别修改为项目数据库的名称、用户名、密码、地址和端口号。
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'code_checking',
        'USER': 'root',
        'PASSWORD': 'password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8',
            'use_unicode': True,
            'init_command': 'SET CHARACTER SET utf8'
        },
    }
}
```
（2）修改code_checking/config.py中的USERID为moss的账户
```python
USERID = '987654321'
```
（3）修改code_checking/config.py中支持的纯文本文件的后缀格式，该项目已支持2003后的word格式，即docx格式，纯文本格式的后缀名，在下面的语句中添加。
```python
SUFFIX = ('c', 'cpp', 'java', 'py', 'htm', 'html', 'asp', 'jsp', 'php', 'js', 'css', 'txt', 'pl')
```

* 配置Django项目

（1）根据模型创建数据库表

在项目文件夹下运行
```console
python manage.py migrate
```
如果装有python2和python3多个版本的python可能需要使用python3
```console
python3 manage.py migrate
```
使用虚拟环境并且存在多个虚拟环境的情况下需要找到该虚拟环境下的python运行，例如：
```console
venv\Scripts\python manage.py migrate
```

（2）创建超级管理员
命令行输入
```console
python manage.py createsuperuser
```
根据提示创建超级管理员，该管理员可以登陆HOST:PORT/admin/

* 使用Django提供的服务器启动项目

在项目文件夹下运行
```console
python manage.py runserver
```
如果需要配置地址和端口
```console
python manage.py runserver 0.0.0.0:80
```


## 3.在服务器上部署项目

Django项目用于生产多采用uwsgi + nginx来部署。注意：uwsgi模块只能在UNIX系统下使用，这里以centos6.5为例。

**在上面的步骤的基础上**
* 配置settings.py文件，关闭DEBUG信息，调整允许访问的地址，*为允许所有地址访问。
```python
DEBUG = False

ALLOWED_HOSTS = ['*']
```

* 配置uwsgi和nginx
安装uwsgi使用pip命令即可
nginx的安装、配置、运行以及uwsgi的配置、运行网上教程很多，这里不再赘述

* 静态文件配置
由于Django提供的测试服务器完全无法用于生产，所以生产环境我们选择了uwsgi + nginx的模式，那么Django服务器就无法替我们收集静态文件，
因此我们需要将静态文件整理到统一的文件夹下，然后交给uwsgi来访问。

修改settings.py文件，添加
```python
STATIC_ROOT = os.path.join(BASE_DIR, "static")
```
注释
```python
# STATICFILES_DIRS = [
    # os.path.join(BASE_DIR, "static"),
# ]
```
其中STATIC_ROOT就是汇总静态文件的目录，会用于nginx的配置

接着在命令行运行
```console
python manage.py collectstatic
```

* 配置验证码的字体路径
修改code_checking/config.py中的TIFPATH为字体的绝对路径（UNIX机器上会提示找不到该字体，windows暂时未发现该问题），该字体MONACO.TIF位于static/source/font/

到这里配置完成了，启动uwsgi和nginx来运行这个web应用。

## 4.Django后台使用说明
访问HOST:PORT/admin，使用创建的超级管理员登陆，即可添加成员，包括教师、学生、管理员和超级管理员。

在user type中可以选择学生、教师、管理员三种，创建完成后可以进行授权。

（1）把一个成员的Staff status勾选上，那么他将可以通过访问admin登陆django后台。

（2）把一个成员的Superuser status勾选上，那么他将拥有**超级管理员权限**。

（3）把一个成员的Active勾选掉，那么他将无法登陆系统。

