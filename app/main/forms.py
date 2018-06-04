# coding:utf-8
from flask_wtf import Form
from wtforms import StringField, TextAreaField, BooleanField, SelectField, FileField, IntegerField,\
    SubmitField
from wtforms.fields.html5 import DateField, DateTimeField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError

from flask_pagedown.fields import PageDownField
from ..models import Role, User, Types, Conference, AlgoTypes


class NameForm(Form):
    name = StringField(u'姓名是什么?', validators=[Required()])
    submit = SubmitField(u'提交')


class EditProfileForm(Form):
    name = StringField(u'真实姓名:', validators=[Length(0, 64)])
    city = StringField(u'学号:', validators=[Length(0, 64)])
    dep = StringField(u'教务管理系统密码:', validators=[Length(0, 64)])
    phone = StringField(u'网络教学平台密码:', validators=[Length(0, 64)])
    location = StringField(u'地&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;点:', validators=[Length(0, 64)])
    about_me = TextAreaField(u'关&nbsp;&nbsp;于&nbsp;我:')
    submit = SubmitField(u'提交')


class EditProfileAdminForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class PostForm(Form):
    body = PageDownField(u"您的看法是什么？", validators=[Required()])
    submit = SubmitField(u'提交')


class CommentForm(Form):
    body = StringField(u'输入您的评论', validators=[Required()])
    submit = SubmitField(u'提交')

# 添加会务信息


class AddNewsForm(Form):
    title = StringField(u'标题：', validators=[Length(0, 64)])
    #location = SelectField(u'会务类别:')
    #result = User.query.filter_by(username='lilin201501').first()
    # print result
    #[(r.value, r.name) for r in result]
    type_id = SelectField(u'类别：', coerce=int)
    # type_id = SelectField(u'会务类别：',
    #    choices=[('1', 'C++'), ('2', 'Python'), ('3', 'Plain Text')])
    address = StringField(u'地点：', validators=[Length(0, 128)])
    arrivingtime = DateField(u'报道时间：', validators=[Length(0, 128)])
    conftime = DateField(u'时间：', validators=[Length(0, 128)])
    fee = IntegerField(u'费用：', validators=[Length(0, 128)])
    content = TextAreaField(u"内容：", validators=[Required()])
    author = StringField(u'单位：', validators=[Length(0, 64)])
    files = FileField(u'附件:', validators=[Required()])
    submit = SubmitField(u'添加新鲜事')

    def __init__(self, types, *args, **kwargs):
        super(AddNewsForm, self).__init__(*args, **kwargs)
        self.type_id.choices = [(type_id.id, type_id.name)
                                for type_id in Types.query.all()]
        self.types = types
# 修改会务信息


class EditNewsForm(Form):
    title = StringField(u'标题：', validators=[Length(0, 64)])
    type_id = SelectField(u'类别：', coerce=int)
    address = StringField(u'地点：', validators=[Length(0, 128)])
    arrivingtime = DateField(u'报道时间：', validators=[Length(0, 128)])
    conftime = DateField(u'时间：', validators=[Length(0, 128)])
    fee = IntegerField(u'费用：', validators=[Length(0, 128)])
    content = TextAreaField(u"内容：", validators=[Required()])
    author = StringField(u'单位：', validators=[Length(0, 64)])
    files = FileField(u'图片附件:', validators=[Required()])

    submit = SubmitField(u'修改')

    def __init__(self, types, *args, **kwargs):
        super(EditNewsForm, self).__init__(*args, **kwargs)
        self.type_id.choices = [(0, u'不限制')]
        self.type_id.choices += [(type_id.id, type_id.name)
                                 for type_id in Types.query.all()]
        self.types = types

# 浏览会务信息


class BrowseNewsForm(Form):
    title = StringField(u'标题：', validators=[Length(0, 64)])
    type_id = SelectField(u'类别：', coerce=int)
    #type_id = SelectField(u'会务类别：', choices=[('0', u'不限制')])
    submit = SubmitField(u'查询')

    def __init__(self, types, *args, **kwargs):
        super(BrowseNewsForm, self).__init__(*args, **kwargs)
        self.type_id.choices = [(0, u'不限制')]
        self.type_id.choices += [(type_id.id, type_id.name)
                                 for type_id in Types.query.all()]
        self.types = types

# 添加广告信息


class AddAdsForm(Form):
    title = StringField(u'推送标题：', validators=[Length(0, 64)])
    type_id = SelectField(u'推送类别：', coerce=int)
    link = StringField(u'推送链接：', validators=[Length(0, 500)])
    content = TextAreaField(u"推送内容：", validators=[Required()])
    author = StringField(u'推送单位：', validators=[Length(0, 64)])
    files = FileField(u'图片附件:', validators=[Required()])
    submit = SubmitField(u'添加推送')

    def __init__(self, types, *args, **kwargs):
        super(AddAdsForm, self).__init__(*args, **kwargs)
        self.type_id.choices = [(type_id.id, type_id.name)
                                for type_id in Types.query.all()]
        self.types = types
# 修改广告信息


class EditAdsForm(Form):
    title = StringField(u'广告标题：', validators=[Length(0, 64)])
    type_id = SelectField(u'广告类别：', coerce=int)
    link = StringField(u'广告链接：', validators=[Length(0, 500)])
    content = TextAreaField(u"广告内容：", validators=[Required()])
    author = StringField(u'发布单位：', validators=[Length(0, 64)])
    files = FileField(u'图片附件:', validators=[Required()])
    submit = SubmitField(u'修改广告')

    def __init__(self, types, *args, **kwargs):
        super(EditAdsForm, self).__init__(*args, **kwargs)
        self.type_id.choices = [(0, u'不限制')]
        self.type_id.choices += [(type_id.id, type_id.name)
                                 for type_id in Types.query.all()]
        self.types = types

# 浏览广告信息


class BrowseAdsForm(Form):
    title = StringField(u'推送标题：', validators=[Length(0, 64)])
    type_id = SelectField(u'推送类别：', coerce=int)
    submit = SubmitField(u'查询推送')

    def __init__(self, types, *args, **kwargs):
        super(BrowseAdsForm, self).__init__(*args, **kwargs)
        self.type_id.choices = [(0, u'不限制')]
        self.type_id.choices += [(type_id.id, type_id.name)
                                 for type_id in Types.query.all()]
        self.types = types
# 浏览日志信息


class BrowseUserlogsForm(Form):
    search_review = StringField(u'查询和评论', validators=[Length(0, 64)])
    submit = SubmitField(u'查询日志')

# 添加日志信息


class AddUserlogsForm(Form):
    news_id = IntegerField(u'会务编号')
    uuid = StringField(u'用户uuid')
    useremail = StringField(u'用户电子邮件', validators=[Length(0, 64)])
    useractions = StringField(u'用户行为', validators=[Length(0, 64)])
    search_review = StringField(u'查询和评论', validators=[Length(0, 64)])
    user_id = IntegerField(u'用户编号')
    submit = SubmitField(u'查询日志')

# 推荐算法设置


class RefTypeForm(Form):
    type_id = SelectField(u'推荐算法', coerce=int)
    submit = SubmitField(u'设置算法')

    def __init__(self, algotypes, *args, **kwargs):
        super(RefTypeForm, self).__init__(*args, **kwargs)
        self.type_id.choices = []
        self.type_id.choices += [(type_id.id, type_id.name) for type_id in algotypes.query.all()]
        self.algotypes = algotypes
