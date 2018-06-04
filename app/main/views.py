import os
import re
import json
import hashlib
import datetime
import uuid
from .getWeibo import Spider
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response, app
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm,\
    CommentForm, AddNewsForm, EditNewsForm, BrowseNewsForm, AddAdsForm, EditAdsForm, BrowseAdsForm, BrowseUserlogsForm, BrowseUserlogsForm, RefTypeForm
from .. import db
from ..models import Permission, Role, User, Post, Comment, Types, Conference, Ads, Userlogs, AlgoTypes
from ..decorators import admin_required, permission_required
from werkzeug import check_password_hash, generate_password_hash, secure_filename
from ..Globals import *
from .uploader import Uploader
#from flask_login import *
from sqlite3 import IntegrityError
from config import Config
root_dir = os.getcwd()
# For a given file, return whether it's an allowed type or not


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ['png', 'jpg', 'jpeg', 'gif']


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.route('/', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 2, type=int)
    return render_template('index.html', li=Spider(page).getJson())


@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.is_submitted():
        current_user.name = form.name.data
        current_user.city = form.city.data
        current_user.dep = form.dep.data
        current_user.phone = form.phone.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('修改成功.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    form.city.data = current_user.city
    form.dep.data = current_user.dep
    form.phone.data = current_user.phone
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('修改成功.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('Your comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户错误.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))

# 添加会务信息


@main.route('/add-conference', methods=['GET', 'POST'])
@login_required
def add_news():
    form = AddNewsForm(types=Types)
    form.process(request.form)  # needed because a default is overriden
    # print "rootdir=", root_dir

    if form.is_submitted():
        filenames = []
        uploaded_files = request.files.getlist("files")
        for file in uploaded_files:

            # Check if the file is one of the allowed types/extensions
            if file and allowed_file(file.filename):
                # Make the filename safe, remove unsupported chars
                #filename = secure_filename(file.filename)
                filename = file.filename
                # Move the file form the temporal folder to the upload
                # folder we setup
                file.save(os.path.join(root_dir, 'app/static/uploads/', filename))
                # Save the filename into a list, we'll use it later
                filenames.append(filename)
        # print form.arrivingtime.data
        conference = Conference(title=form.title.data, type_id=form.type_id.data, address=form.address.data,
                                arrivingtime=form.arrivingtime.data, conftime=form.conftime.data, content=HTMLEnCode(form.content.data), author=form.author.data, files=','.join(filenames), fee=form.fee.data)
        db.session.add(conference)
        try:
            db.session.commit()
            # pass
        except IntegrityError:
            db.session.rollback()
            # pass
        flash(u'成功添加新鲜事.')
    form.title.data = ''
    form.content.data = ''
    # return redirect(url_for('.user', username=current_user.username))
    return render_template('add_news.html', form=form)

# 浏览会务


@main.route('/browse-conference', methods=['GET', 'POST'])
@login_required
def browse_news():
    form = BrowseNewsForm(types=Types)

    if form.is_submitted():
        type_id = eval(str(request.form.getlist('type_id')))
        searchbutton = eval(str(request.form.getlist('searchbutton')))
        if searchbutton:
            uuid = eval(str(request.form.getlist('uuid')))[0]
            title = eval(str(request.form.getlist('title1')))[0]
        submit = eval(str(request.form.getlist('submit')))
        if submit:
            uuid = eval(str(request.form.getlist('uuid2')))[0]
            title = eval(str(request.form.getlist('title')))[0]
        # print current_user.username,current_user.email,current_user.id,uuid

        # insert logs
        if current_user.id:
            userlogs = Userlogs(uuid=uuid, useremail=current_user.email, search_review=title, useractions=u'查询', user_id=current_user.id)
        else:
            userlogs = Userlogs(uuid=uuid, useremail=current_user.email, search_review=title, useractions=u'查询')
        db.session.add(userlogs)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        # end of insert logs

        if type_id:
            type_id = int(type_id[0])
        if type_id == 0 or not type_id:
            query = Conference.query.filter(Conference.title.like('%' + title + '%'))
            #query = Conference.query.filter(title = form.title.data)
        else:
            query = Conference.query.filter(Conference.title.like('%' + form.title.data + '%')).filter_by(type_id=type_id)
    else:
        query = Conference.query
    # print query
    form.type_id.data = ''
    page = request.args.get('page', 1, type=int)

    pagination = query.order_by(Conference.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    conference = pagination.items
    return render_template('browse_news.html', form=form, conference=conference, pagination=pagination)

# 浏览会务


@main.route('/browse-conference-del', methods=['GET', 'POST'])
@login_required
def browse_news_del():
    form = BrowseNewsForm(types=Types)
    # print "sdfsdf====", form.type_id.data
    # print request.form.getlist("sel")
    if form.is_submitted():
        ids = request.form.getlist("sel")
        for id in ids:
            conference = Conference.query.get_or_404(int(eval(id)))
            # print "sfsd"
            db.session.delete(conference)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
    query = Conference.query
    # print query
    form.type_id.data = ''
    page = request.args.get('page', 1, type=int)

    pagination = query.order_by(Conference.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    conference = pagination.items

    return render_template('browse_news.html', form=form, conference=conference, pagination=pagination)


@main.route('/edit-conference/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    conference = Conference.query.get_or_404(id)
    form = EditNewsForm(types=Types)
    if form.is_submitted():
        conference.title = form.title.data
        conference.type_id = form.type_id.data
        conference.content = HTMLEnCode(form.content.data)
        conference.author = form.author.data
        conference.address = form.address.data
        conference.arrivingtime = form.arrivingtime.data
        conference.conftime = form.conftime.data
        conference.fee = form.fee.data
        filenames = []
        uploaded_files = request.files.getlist("files")
        for file in uploaded_files:

            # Check if the file is one of the allowed types/extensions
            if file and allowed_file(file.filename):
                # Make the filename safe, remove unsupported chars
                #filename = secure_filename(file.filename)
                filename = file.filename
                # Move the file form the temporal folder to the upload
                # folder we setup
                file.save(os.path.join(root_dir, 'app/static/uploads/', filename))
                # Save the filename into a list, we'll use it later
                filenames.append(filename)
                conference.files = ','.join(filenames)
        db.session.add(conference)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        flash(u'成功修改会务！')
    form.title.data = conference.title
    #form.content.data = HTMLDeCode(conference.content)
    content = HTMLDeCode(conference.content)
    form.author.data = conference.author
    form.type_id.data = conference.type_id
    form.files.data = conference.files
    form.arrivingtime.data = conference.arrivingtime
    form.conftime.data = conference.conftime
    form.address.data = conference.address
    # print "conference.files=", conference.files
    return render_template('edit_news.html', form=form, content=content)

# 删除会务


@main.route('/del-conference/<int:id>', methods=['GET', 'POST'])
@login_required
def del_news(id):
    conference = Conference.query.get_or_404(id)

    db.session.delete(conference)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

    form = BrowseNewsForm(types=Types)
    query = Conference.query
    form.type_id.data = ''
    page = request.args.get('page', 1, type=int)

    pagination = query.order_by(Conference.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    conference = pagination.items
    return render_template('browse_news.html', form=form, conference=conference, pagination=pagination)

# 删除会务


@main.route('/del-conference-sel', methods=['GET', 'POST'])
@login_required
def del_news_sel():
    pass
    id = -1
    conference = Conference.query.get_or_404(id)

    db.session.delete(conference)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

    form = BrowseNewsForm(types=Types)
    query = Conference.query
    form.type_id.data = ''
    page = request.args.get('page', 1, type=int)

    pagination = query.order_by(Conference.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    conference = pagination.items
    return render_template('browse_news.html', form=form, conference=conference, pagination=pagination)

# 显示会务


@main.route('/display-conference/<int:id>', methods=['GET', 'POST'])
@login_required
def display_news(id):
    conference = Conference.query.get_or_404(id)
    files = conference.files.split(',')
    # print uuid.uuid1()
    # print uuid
    uuid = request.args.get('uuid')
    # print uuid
    # insert logs
    userlogs = Userlogs(uuid=uuid, useremail=current_user.email, search_review='', useractions=u'查看', user_id=current_user.id, news_id=id)
    db.session.add(userlogs)
    # try:
    db.session.commit()
    # except IntegrityError:
    #    db.session.rollback()
    # end of insert logs
    return render_template('display_news.html', conference=conference, files=files, content=HTMLDeCode(conference.content))

# Route that will process the file upload


@main.route('/upload/', methods=['GET', 'POST', 'OPTIONS'])
def upload():
    """UEditor文件上传接口
    config 配置文件
    result 返回结果
    """
    mimetype = 'application/json'
    result = {}
    action = request.args.get('action')
    #print (action + 'kkkkk!')
    cur_folder = os.getcwd()
    static_folder = os.path.join(cur_folder, 'app', 'static')
    # 解析JSON格式的配置文件
    with open(os.path.join(static_folder, 'ueditor', 'asp',
                           'config.json')) as fp:
        try:
            # 删除 `/**/` 之间的注释
            CONFIG = json.loads(re.sub(r'\/\*.*\*\/', '', fp.read()))
        except:
            CONFIG = {}
    # print CONFIG
    if action == 'config':
        # 初始化时，返回配置文件给客户端
        result = CONFIG

    elif action in ('uploadimage', 'uploadfile', 'uploadvideo'):
        # 图片、文件、视频上传
        if action == 'uploadimage':
            fieldName = CONFIG.get('imageFieldName')
            config = {
                "pathFormat": CONFIG['imagePathFormat'],
                "maxSize": CONFIG['imageMaxSize'],
                "allowFiles": CONFIG['imageAllowFiles']
            }
        elif action == 'uploadvideo':
            fieldName = CONFIG.get('videoFieldName')
            config = {
                "pathFormat": CONFIG['videoPathFormat'],
                "maxSize": CONFIG['videoMaxSize'],
                "allowFiles": CONFIG['videoAllowFiles']
            }
        else:
            fieldName = CONFIG.get('fileFieldName')
            config = {
                "pathFormat": CONFIG['filePathFormat'],
                "maxSize": CONFIG['fileMaxSize'],
                "allowFiles": CONFIG['fileAllowFiles']
            }
        # print static_folder+"_dddd"
        if fieldName in request.files:
            field = request.files[fieldName]
            uploader = Uploader(field, config, static_folder)
            result = uploader.getFileInfo()
        else:
            result['state'] = u'上传接口出错'

    elif action in ('uploadscrawl'):
        # 涂鸦上传
        fieldName = CONFIG.get('scrawlFieldName')
        config = {
            "pathFormat": CONFIG.get('scrawlPathFormat'),
            "maxSize": CONFIG.get('scrawlMaxSize'),
            "allowFiles": CONFIG.get('scrawlAllowFiles'),
            "oriName": "scrawl.png"
        }

        if fieldName in request.form:
            field = request.form[fieldName]
            uploader = Uploader(field, config, static_folder, 'base64')
            result = uploader.getFileInfo()
        else:
            result['state'] = u'上传接口出错'

    elif action in ('catchimage'):
        config = {
            "pathFormat": CONFIG['catcherPathFormat'],
            "maxSize": CONFIG['catcherMaxSize'],
            "allowFiles": CONFIG['catcherAllowFiles'],
            "oriName": "remote.png"
        }
        fieldName = CONFIG['catcherFieldName']

        if fieldName in request.form:
            # 这里比较奇怪，远程抓图提交的表单名称不是这个
            source = []
        elif '%s[]' % fieldName in request.form:
            # 而是这个
            source = request.form.getlist('%s[]' % fieldName)

        _list = []
        for imgurl in source:
            uploader = Uploader(imgurl, config, static_folder, 'remote')
            info = uploader.getFileInfo()
            _list.append({
                'state': info['state'],
                'url': info['url'],
                'original': info['original'],
                'source': imgurl,
            })

        result['state'] = 'SUCCESS' if len(_list) > 0 else 'ERROR'
        result['list'] = _list

    else:
        result['state'] = u'请求地址出错'
    # print result
    result = json.dumps(result)

    if 'callback' in request.args:
        callback = request.args.get('callback')
        if re.match(r'^[\w_]+$', callback):
            result = '%s(%s)' % (callback, result)
            mimetype = 'application/javascript'
        else:
            result = json.dumps({'state': 'callback参数不合法'})

    res = make_response(result)
    res.mimetype = mimetype
    res.headers['Access-Control-Allow-Origin'] = '*'
    res.headers['Access-Control-Allow-Headers'] = 'X-Requested-With,X_Requested_With'
    return res


# 广告处理
# 添加广告信息
@main.route('/add-ads', methods=['GET', 'POST'])
@login_required
def add_ads():
    form = AddAdsForm(types=Types)
    form.process(request.form)  # needed because a default is overriden
    # print "rootdir=", root_dir

    if form.is_submitted():
        filenames = []
        uploaded_files = request.files.getlist("files")
        for file in uploaded_files:

            # Check if the file is one of the allowed types/extensions
            if file and allowed_file(file.filename):
                filename = file.filename
                file.save(os.path.join(root_dir, 'app/static/uploads/', filename))
                filenames.append(filename)
        # print filenames
        ads = Ads(title=form.title.data, type_id=form.type_id.data, content=HTMLEnCode(form.content.data), author=form.author.data, files=','.join(filenames), link=form.link.data)
        db.session.add(ads)
        try:
            db.session.commit()
            pass
        except IntegrityError:
            db.session.rollback()
            pass
        flash(u'成功添加推送.')
    form.title.data = ''
    form.content.data = ''
    # return redirect(url_for('.user', username=current_user.username))
    return render_template('add_ads.html', form=form)

# 浏览广告


@main.route('/browse-ads', methods=['GET', 'POST'])
@login_required
def browse_ads():
    form = BrowseAdsForm(types=Types)
    # print "sdfsdf====", form.type_id.data

    if form.is_submitted():
        title = eval(str(request.form.getlist('title')))[0]
        type_id = eval(str(request.form.getlist('type_id')))
        # print "==", title, type_id
        # print type(title)
        if type_id:
            # print "dfsf"
            type_id = int(type_id[0])

        if type_id == 0 or not type_id:
            query = Ads.query.filter(Ads.title.like('%' + title + '%'))
            #query = Conference.query.filter(title = form.title.data)
        else:
            #query = db.session.query(Conference).filter(Conference.title.like('%'+ form.title.data + '%'))
            query = Ads.query.filter(Ads.title.like('%' + form.title.data + '%')).filter_by(type_id=type_id)
    else:
        query = Ads.query
    # print query
    #query = Ads.query
    form.type_id.data = ''
    page = request.args.get('page', 1, type=int)

    pagination = query.order_by(Ads.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    ads = pagination.items

    return render_template('browse_ads.html', form=form, ads=ads, pagination=pagination)


# 删除广告
@main.route('/browse-ads-del', methods=['GET', 'POST'])
@login_required
def browse_ads_del():
    form = BrowseAdsForm(types=Types)
    # print "sdfsdf====", form.type_id.data
    # print request.form.getlist("sel")
    if form.is_submitted():
        ids = request.form.getlist("sel")
        for id in ids:
            ads = Ads.query.get_or_404(int(eval(id)))
            # print "sfsd"
            db.session.delete(ads)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
    query = Ads.query
    # print query
    form.type_id.data = ''
    page = request.args.get('page', 1, type=int)

    pagination = query.order_by(Ads.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    ads = pagination.items

    return render_template('browse_ads.html', form=form, ads=ads, pagination=pagination)


@main.route('/edit-ads/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_ads(id):
    ads = Ads.query.get_or_404(id)
    form = EditAdsForm(types=Types)
    if form.is_submitted():
        ads.title = form.title.data
        ads.type_id = form.type_id.data
        ads.content = HTMLEnCode(form.content.data)
        ads.author = form.author.data
        ads.link = form.link.data
        filenames = []
        uploaded_files = request.files.getlist("files")
        for file in uploaded_files:

            # Check if the file is one of the allowed types/extensions
            if file and allowed_file(file.filename):
                # Make the filename safe, remove unsupported chars
                #filename = secure_filename(file.filename)
                filename = file.filename
                # Move the file form the temporal folder to the upload
                # folder we setup
                file.save(os.path.join(root_dir, 'app/static/uploads/', filename))
                # Save the filename into a list, we'll use it later
                filenames.append(filename)
                ads.files = ','.join(filenames)
        db.session.add(ads)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        flash(u'成功修改广告！')
    form.title.data = ads.title
    #form.content.data = HTMLDeCode(conference.content)
    content = HTMLDeCode(ads.content)
    form.author.data = ads.author
    form.type_id.data = ads.type_id
    form.files.data = ads.files
    # print "ads.files=", ads.files
    return render_template('edit_ads.html', form=form, content=content)

# 删除广告


@main.route('/del-ads/<int:id>', methods=['GET', 'POST'])
@login_required
def del_ads(id):
    ads = Ads.query.get_or_404(id)

    db.session.delete(ads)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

    form = BrowseAdsForm(types=Types)
    query = Ads.query
    form.type_id.data = ''
    page = request.args.get('page', 1, type=int)

    pagination = query.order_by(Ads.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    ads = pagination.items
    return render_template('browse_ads.html', form=form, ads=ads, pagination=pagination)

# 删除广告


@main.route('/del-ads-sel', methods=['GET', 'POST'])
@login_required
def del_ads_sel():
    pass
    id = -1
    ads = Ads.query.get_or_404(id)

    db.session.delete(conference)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

    form = BrowseAdsForm(types=Types)
    query = Ads.query
    form.type_id.data = ''
    page = request.args.get('page', 1, type=int)

    pagination = query.order_by(Ads.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    ads = pagination.items
    return render_template('browse_ads.html', form=form, ads=ads, pagination=pagination)

# 显示广告


@main.route('/display-ads/<int:id>', methods=['GET', 'POST'])
@login_required
def display_ads(id):
    ads = Ads.query.get_or_404(id)
    files = ads.files.split(',')

    return render_template('display_ads.html', ads=ads, files=files, content=HTMLDeCode(ads.content))

# 浏览用户日志


@main.route('/browse-userlogs', methods=['GET', 'POST'])
@login_required
def browse_userlogs():
    form = BrowseUserlogsForm()

    if form.is_submitted():
        search_review = eval(str(request.form.getlist('search_review')))[0]
        query = Userlogs.query.filter(Userlogs.search_review.like('%' + form.search_review.data + '%'))
    else:
        query = Userlogs.query
    # print query
    page = request.args.get('page', 1, type=int)

    pagination = query.order_by(Userlogs.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    userlogs = pagination.items

    return render_template('browse_userlogs.html', form=form, userlogs=userlogs, pagination=pagination)
# 删除日志


@main.route('/del-userlogs/<int:id>', methods=['GET', 'POST'])
@login_required
def del_userlogs(id):
    userlogs = Userlogs.query.get_or_404(id)
    db.session.delete(userlogs)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
    form = BrowseUserlogsForm()
    query = Userlogs.query
    page = request.args.get('page', 1, type=int)

    pagination = query.order_by(Userlogs.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    userlogs = pagination.items
    return render_template('browse_userlogs.html', form=form, userlogs=userlogs, pagination=pagination)


# 删除日志
@main.route('/browse-userlogs-del', methods=['GET', 'POST'])
@login_required
def browse_userlogs_del():
    form = BrowseUserlogsForm()
    # print "sdfsdf====", form.type_id.data
    # print request.form.getlist("sel")
    if form.is_submitted():
        ids = request.form.getlist("sel")
        for id in ids:
            userlogs = Userlogs.query.get_or_404(int(eval(id)))
            # print "sfsd"
            db.session.delete(userlogs)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
    query = Userlogs.query
    # print query
    page = request.args.get('page', 1, type=int)

    pagination = query.order_by(Userlogs.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    userlogs = pagination.items

    return render_template('browse_userlogs.html', form=form, userlogs=userlogs, pagination=pagination)

# 删除日志


@main.route('/refence-algo-set', methods=['GET', 'POST'])
@login_required
def refence_algo():
    form = RefTypeForm(algotypes=AlgoTypes)
    if form.is_submitted():
        type_id = form.type_id.data
        # print form.type_id.label.encode('gbk')
        # print type_id
        cur_dir = os.getcwd()
        filename = os.path.join(cur_dir, 'app', 'config.json')
        # print filename
        CONFIG = {}
        with open(filename, 'r') as fr:
            try:
                # 删除 `/**/` 之间的注释
                CONFIG = json.loads(re.sub(r'\/\*.*\*\/', '', fr.read()))
            except:
                CONFIG = {}
            # print [CONFIG[k] for k in CONFIG.keys()][0]
            with open(filename, 'w') as fw:
                CONFIG["selectalgorithm"] = type_id
                #data = json.dumps(CONFIG)
                # print data
                fw.write(json.dumps(CONFIG))
                # json.dumps(data)

        # print [CONFIG[k] for k in CONFIG.keys()][0]
        # print result
    return render_template('set_algorithm.html', form=form)

# 返回最新会务


@main.route('/returnCurConf', methods=['GET', 'POST'])
def returnCurNews():
    query = Conference.query
    pagination = query.order_by(Conference.timestamp.desc()).paginate(
        1, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    conference = pagination.items
    ll = []
    for new in conference:
        ll.append({'title': new.title, 'file': new.files})

    encoded_json = json.dumps(ll, ensure_ascii=False)
    return encoded_json
# 微信提交数据信息


@main.route('/returnGetData', methods=['GET', 'POST'])
def GetData():
    data = request.form.getlist("data")
    # print data
    datax = request.form.getlist("datax")
    # print datax
    ll = []
    ll.append({'reason': 'res.data.reason',
               'city_name': 'res.data.result.data.realtime.city_name',
               'date': 'res.data.result.data.realtime.date',
               'info': 'res.data.result.data.realtime.weather.info'})
    encoded_json = json.dumps(ll, ensure_ascii=False)
    return encoded_json


@main.route('/returnSlideData', methods=['GET', 'POST'])
def GetSlideData():
    query = Conference.query.filter(' id >0 order by timestamp desc')
    query = query.limit(3)

    conference = query
    ll = []
    for new in conference:
        ll.append({'title': new.title, 'picurl': current_app.config['HOSTURL'] + current_app.config['UPLOAD_FOLDER'] + new.files})

    encoded_json = json.dumps(ll, ensure_ascii=False)
    return encoded_json


@main.route('/returnChoiceList', methods=['GET', 'POST'])
def GetChoiceList():
    query = Conference.query.filter(' id >0 order by timestamp desc')
    query = query.limit(10)
    conference = query
    ll = []
    for new in conference:
        ll.append({'title': new.title, 'picurl': current_app.config['HOSTURL'] + current_app.config['UPLOAD_FOLDER'] + new.files})

    encoded_json = json.dumps(ll, ensure_ascii=False)
    return encoded_json


@main.route('/returnVenuesList', methods=['GET', 'POST'])
def GetVenuesList():
    query0 = Types.query.all()
    ll = []
    for type in query0:
        query = Conference.query.filter(' type_id =' + str(type.id) + ' order by timestamp desc')
        query = query.limit(1)
        conference = query
        for new in conference:
            ll.append({'title': new.title, 'picurl': current_app.config['HOSTURL'] + current_app.config['UPLOAD_FOLDER'] + new.files})

    encoded_json = json.dumps(ll, ensure_ascii=False)
    return encoded_json


@main.route('/postData', methods=['GET', 'POST'])
def postData():
    data = request.json
    title = data['title']
    dep = data['dep']
    phone = data['phone']
    email = data['email']
    userInfo = data['userInfo']
    province = userInfo['province']
    gender = userInfo['gender']
    nickName = userInfo['nickName']
    city = userInfo['city']
    avatarUrl = userInfo['avatarUrl']

    # print   title, dep,phone,email
    # print userInfo
    # print userInfo['province']

    user = User(email=form.email.data,
                username=form.username.data,
                password=form.password.data)
    db.session.add(user)
    db.session.commit()

    ll = []
    ll.append({'successinfo': 1})

    encoded_json = json.dumps(ll, ensure_ascii=False)
    return encoded_json
