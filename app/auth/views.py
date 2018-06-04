# coding:utf-8
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, \
    current_user
from . import auth
from .. import db
from ..models import User
from ..email import send_email
from .forms import  ChangePasswordForm,\
    PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm, JwglForm, EolForm
from ..main.getWeibo import Eol, Jwgl


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        current_user.confirmed = 1
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])  # isRight
def login():
    if request.method == 'POST':
        # print request.form['remember_me']
        email = str(request.form.getlist('email')[0])
        password = str(request.form.getlist('password')[0])

        # print email, password
        user = User.query.filter_by(email=email).first()

        if user is not None:
            if user.verify_password(password):
                login_user(user)
                return redirect(url_for('main.index'))
            else:
                flash(u'用户名或者密码不正确！')
        else:
            flash(u'该用户尚未注册，请注册！')
    return render_template('auth/login.html', title=u'校园新鲜事')


@auth.route('/logout')  # isRigtht
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@auth.route('/jwgl', methods=['GET', 'POST'])  # isRigtht
@login_required
def jwgl():
    admin = str(current_user.city).strip()
    password = str(current_user.dep).strip()
    if(admin != "" and password != ""):
        js = Jwgl(admin, password).tologin()
    else:
        js = ""
    form = JwglForm()
    if form.is_submitted():
        current_user.city = form.city.data
        current_user.dep = form.dep.data
        db.session.add(current_user)
        flash('修改成功')
        return redirect(url_for('auth.jwgl', form=form))
    return render_template('auth/jwgl.html', title=u'教务管理系统', form=form, js=js)


@auth.route('/eol', methods=['GET', 'POST'])  # isRigtht
@login_required
def eol():
    admin = str(current_user.city).strip()
    password = str(current_user.phone).strip()
    if(admin != "" and password != ""):
        js = Eol(admin, password).tologin()
    else:
        js = ""
    form = EolForm()
    if form.is_submitted():
        current_user.city = form.city.data
        current_user.phone = form.phone.data
        db.session.add(current_user)
        flash('修改成功')
        return redirect(url_for('auth.eol', form=form))
    return render_template('auth/eol.html', title=u'网络教学平台', form=form, js=js)


@auth.route('/register', methods=['GET', 'POST'])  # isRight
def register():
    if request.method == 'POST':

        email = str(request.form.getlist('emails')[0])
        name = str(request.form.getlist('names')[0])
        password = str(request.form.getlist('passwords')[0])

        user = User.query.filter_by(email=email).first()

        if user is not None:
            flash(u'该用户已经注册')
        else:
            user = User(email=email,
                        username=name,
                        password=password)
            db.session.add(user)
            db.session.commit()
            token = user.generate_confirmation_token()
            send_email(user.email, '邮箱验证',
                       'auth/email/confirm', user=user, token=token)
            flash('验证邮件已经发送，请前往查收.')
            return redirect(url_for('auth.login'))
    return render_template('auth/login.html', title=u'校园新鲜事', flag=u'register')


@auth.route('/confirm/<token>')  # isRight
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('恭喜您，您已经成功验证您的邮箱!')
    else:
        flash('您还没有验证邮箱，请验证！')
    return redirect(url_for('main.index'))


@auth.route('/confirm')  # isRight
@login_required
def resend_confirmation():
    if current_user.confirmed:
        flash('您已经验证邮箱.')
    else:
        token = current_user.generate_confirmation_token()
        send_email(current_user.email, '邮箱验证',
                   'auth/email/confirm', user=current_user.email, token=token)
        flash('验证邮件已经发送，请前往查收.')
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])  # isright
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash(u'密码已经更新。')
            return redirect(url_for('main.index'))
        else:
            flash(u'无效密码！')
    return render_template("auth/change_password.html", form=form)


@auth.route('/reset', methods=['GET', 'POST'])  # isRight
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, u'重置你的密码！',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash(u'已经发了一封修改密码的邮件给你！')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])  # isRight
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.is_submitted():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash(u'密码修改成功！')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])  # isRight
def change_email_request():
    form = ChangeEmailForm()
    if form.is_submitted():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, u'确认你的电子邮件！',
                       'auth/email/change_email',
                       user=current_user, token=token)
            flash(u'已经发送一份确认电子邮件！')
            return redirect(url_for('main.index'))
        else:
            flash(u'无效邮件或密码。')
    return render_template("auth/change_email.html", form=form)


@auth.route('/change-email/<token>')  # isRight
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash(u'你的电子邮件已经更新！')
    else:
        flash(u'无效请求！')
    return redirect(url_for('main.index'))
