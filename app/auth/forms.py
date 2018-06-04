# coding:utf-8
from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(Form):
    email = StringField(u'电子邮件', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField(u'用户密码', validators=[Required()])
    remember_me = BooleanField(u'保持登录状态')
    submit = SubmitField(u'登录')


class LoginForm1(Form):
    email = StringField(u'电子邮件', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField(u'密码', validators=[Required()])
    remember_me = BooleanField(u'保持登录状态')
    submit = SubmitField(u'登录系统')


class EolForm(Form):
    city = StringField(u'学号', validators=[Required()])
    phone = PasswordField(u'网络教学平台密码', validators=[Required()])
    submit = SubmitField(u'登录')


class JwglForm(Form):
    city = StringField(u'学号', validators=[Required()])
    dep = PasswordField(u'教务管理系统密码', validators=[Required()])
    submit = SubmitField(u'确定')


class RegistrationForm(Form):
    email = StringField(u'电子邮件：', validators=[Required(), Length(1, 64),
                                              Email()])
    username = StringField(u'用户姓名：', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          u'用户名必须只含有字母, '
                                          u'数字, 点或 下横线')])
    passwords = PasswordField(u'用户密码：', validators=[
        Required(), EqualTo('password2', message=u'两次密码必须匹配.')])
    password = PasswordField(u'用户密码：', validators=[
        Required(), EqualTo('password2', message=u'两次密码必须匹配.')])
    password2 = PasswordField(u'确认密码：', validators=[Required()])
    submit = SubmitField(u'用户注册')
    submi = SubmitField(u'用户')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'电子邮件已经存在.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(u'用户已经存在.')


class ChangePasswordForm(Form):
    old_password = PasswordField(u'输入旧密码', validators=[Required()])
    password = PasswordField(u'输入新密码', validators=[Required(), EqualTo('password2', message=u'两次密码不相同！')])
    password2 = PasswordField(u'确认新密码', validators=[Required()])
    submit = SubmitField(u'更新密码')


class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    submit = SubmitField(u'重置密码')


class PasswordResetForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField(u'新密码：', validators=[
        Required(), EqualTo('password2', message=u'前后密码必须匹配')])
    password2 = PasswordField(u'确认密码：', validators=[Required()])
    submit = SubmitField(u'重置密码')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(u'未知电子邮件.')


class ChangeEmailForm(Form):
    email = StringField(u'新电子邮件', validators=[Required(), Length(1, 64),
                                              Email()])
    password = PasswordField(u'用户密码', validators=[Required()])
    submit = SubmitField(u'更新电子邮件地址')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'电子邮件已经注册.')
