#!/usr/bin/env python
#coding:utf8


from flask import Flask,request,escape,session,redirect,url_for,render_template,make_response
from flask import jsonify
import sqlite3
import json
import os
import time

app = Flask(__name__)

#用户注册表单数据过滤函数
def saferegister(req):
    not_safe = ['/','\\','*','#','$','^',')','(','+','-','%','!','~','?','[',']','{','}','<','>','=']
    email_need = ['@','.']
    email = req.form['email']
    password = req.form['password']
    repeate = req.form['repeate']
    if password == repeate:
        if email_need[0] in email:
            if email_need[1] in email:
                for x in not_safe:
                    if x in email:
                        return False
                        break
                    else:
                        if x in password:
                            return False
                            break
                        else:
                            return True
            else:
                return False
        else:
            return False


#用户登陆数据过滤函数
def safelogin(req):
    not_safe = ['/','\\','*','#','$','^',')','(','+','-','%','!','~','?','[',']','{','}','<','>','=']
    email_need = ['@','.']
    email = req.form['email']
    password = req.form['password']
    if email_need[0] in email:
        if email_need[1] in email:
            for x in not_safe:
                if x in email:
                    return False
                    break
                else:
                    if x in password:
                        return False
                        break
                    else:
                        return True
    else:
        return False



@app.route('/')
def index():
    try:
        names = request.cookies['user']
        user_article_path = './database/user_info/' + names + '/'
        article_number = len(os.listdir(user_article_path))
        return render_template('index.html',name=names,article_number=article_number)
    except:
        return render_template('login.html')


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if safelogin(request):
            conn = sqlite3.connect('database/user_info/user_account.db')
            cursor = conn.cursor()
            sql = "select password from account where email=?"
            a = cursor.execute(sql,(request.form['email'],))
            b = a.fetchall()
            cursor.close()
            conn.close()
            try:
                if b[0][0] == request.form['password'] :
                    resp = make_response(render_template('index.html',name=request.form['email']))
                    resp.set_cookie('user',request.form['email'])
                    return resp
                else:
                    return render_template('login.html',content='账户错误')
            except:
                    return render_template('login.html',content='账户错误')
        else:
            return render_template('login.html',content='非法字符！')

    if request.method == 'GET':
        try:
            if request.cookies['Isregister'] == 'True':
                return render_template('login.html',content='您已完成注册，请登录')    #这个页面这里会显示注册过后进行登陆的提示语
        except:
            try:
                if request.cookies['user']:
                    username = request.cookies['user']
                    return render_template('user.html',name=username)
                else:
                    return render_template('login.html')              #这里返回直接点击登陆后的登陆页面
            except:
                return render_template('login.html')


@app.route('/logout')
def logout():
    resp = make_response(render_template('login.html'))
    resp.set_cookie('user','',expires=0)
    return resp



@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        if saferegister(request):
            conn = sqlite3.connect('database/user_info/user_account.db')
            cursor = conn.cursor()
            sql = 'insert into account values(?,?)'
            cursor.execute(sql,(request.form['email'],request.form['password']))
            conn.commit()
            cursor.close()
            conn.close()
            #创建一个用户自己的文章目录存放用户的静态文章文件
            user_file_path = os.path.join('./database/user_info',request.form['email'])
            os.mkdir(user_file_path)
            return render_template('login.html',content='您已完成注册，请登录')
        else:
            resp = make_response(render_template('register.html',content='非法字符或者重复密码不一致'))
            resp.set_cookie('q3','qqwasas')
            return resp
    if request.method == 'GET':
        return render_template('register.html')



@app.route('/add_article',methods=['POST'])      #ajax
def add_article():
    if request.method == 'POST':
        name = request.cookies['user']
        article_title = request.form['article_title']
        article_content = request.form['article_content']
        user_article_path = './database/user_info/'+name+'/'
        article_file = article_title+'_'+str(time.time())
        with open(user_article_path+article_file,'w')as f:
            f.write(article_content)
            f.close()
        return redirect('/article_list/1')
    else:
        return redirect('/')


@app.route('/update_article/<article_id>',methods=['POST'])
def update_article(article_id):
    try:
        name = request.cookies['user']
        user_article_path = './database/user_info/' + name + '/'
        with open(user_article_path+article_id,'w')as f:
            f.write(request.form['data'])
        return 'ok!'
    except:
        return 'no cookies , no way'



@app.route('/article_list/<page>',methods=['GET'])
def article_list(page):
    try:
        page = int(page)
        name = request.cookies['user']
        user_article_path = './database/user_info/' + name + '/'
        articles_list = [x for x in os.listdir(user_article_path)]
        result = sorted([[float(y.split('_')[1]),[y.split('_')[0],y]] for y in articles_list],reverse=True)
        if page<1:
            return 'error page'
        if page == 1:
            return render_template('article_list.html',previous=1,next=page+1,article_lists=result[:20],name=name)
        if page>1:
            page1 = (page - 1)*20
            page2 = (page + 1)*20
            return render_template('article_list.html', previous=page - 1, next=page + 1, article_lists=result[page1:page2],name=name)
    except:
        return 'no cookies , no way'


@app.route('/article_detail/<article_id>',methods=['GET'])
def article_detail(article_id):
    # try:
    name = request.cookies['user']
    user_article_path = './database/user_info/' + name + '/'
    article_title = article_id.split('_')[0]
    article_timestamp = article_id.split('_')[1]
    article_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(article_timestamp)))
    if os.path.exists(user_article_path+article_id):
        with open(user_article_path+article_id,'r') as f:
            content = f.read()
        return render_template('article_detail.html',title=article_title,content=content,name=name,article_id=article_id,article_time=article_time)
    else:
        return render_template('article_detail.html',title=article_title,content='内容不存在',name=name)
    # except:
    #     return 'no cookies , no way'


@app.route('/delete_article/<article_id>',methods=['GET'])
def delete_article(article_id):
    try:
        name = request.cookies['user']
        user_article_path = './database/user_info/' + name + '/'
        if os.path.exists(user_article_path+article_id):
            os.remove(user_article_path+article_id)
            return redirect('/article_list/1')
        else:
            return 'article not exist!'
    except:
        return 'no cookies , no way'


if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'chunli'
    app.run(host='0.0.0.0',debug=True)