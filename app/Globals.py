# -*- encoding:UTF-8 -*-
import string
import re
# global constants
sitename = u'成都师范学院计算机科学学院-会会通系统'
siteshort = u'会会通系统'
sitefooter = u'Copyright © 成都师范学院计算机科学学院. All rights reserved.联系方式：lilin201501@126.com'
publishman = u'李林'
systemname = u'会会通后台系统'

#encode html to text
def HTMLEnCode(strtmp):
    """
    python2 version
    strtmp = string.replace(strtmp,">", "&gt;")
    strtmp = string.replace(strtmp,"<", "&lt;")
    strtmp = string.replace(strtmp,chr(32), "&nbsp;")
    strtmp = string.replace(strtmp,chr(9), "&nbsp;")
    strtmp = string.replace(strtmp,chr(34), "&quot;")
    strtmp = string.replace(strtmp,chr(39), "&#39;")
    strtmp = string.replace(strtmp,chr(13), "")
    strtmp = string.replace(strtmp,chr(10) + chr(10), "</P><P> ")
    strtmp = string.replace(strtmp,chr(10), "<BR> ")
    """
    
    #python3 version
    strtmp = re.sub(">", "&gt;", strtmp)
    strtmp = re.sub("<", "&lt;", strtmp)
    strtmp = re.sub(chr(32), "&nbsp;", strtmp)
    strtmp = re.sub(chr(9), "&nbsp;", strtmp)
    strtmp = re.sub(chr(34), "&quot;", strtmp)
    strtmp = re.sub(chr(39), "&#39;", strtmp)
    strtmp = re.sub(chr(13), "", strtmp)
    strtmp = re.sub(chr(10) + chr(10), "</P><P> ", strtmp)
    strtmp = re.sub(chr(10), "<BR> ", strtmp)

    return strtmp
#decode text to html
def HTMLDeCode(strtmp):
    """
    python2 version
    strtmp = string.replace(strtmp,"&gt;", ">")
    strtmp = string.replace(strtmp,"&lt;", "<")
    strtmp = string.replace(strtmp,"&nbsp;"," ")
    strtmp = string.replace(strtmp,"&quot;", chr(34))
    strtmp = string.replace(strtmp,"&#39;", chr(39))
    strtmp = string.replace(strtmp,"</P><P> ",chr(10) + chr(10))
    strtmp = string.replace(strtmp,"<BR> ", chr(10))
    """    
    #python3 version
    strtmp = re.sub("&gt;", ">", strtmp)
    strtmp = re.sub("&lt;", "<", strtmp)
    strtmp = re.sub("&nbsp;"," ", strtmp)
    strtmp = re.sub("&quot;", chr(34), strtmp)
    strtmp = re.sub("&#39;", chr(39), strtmp)
    strtmp = re.sub("</P><P> ",chr(10) + chr(10), strtmp)
    strtmp = re.sub("<BR> ", chr(10), strtmp)
    return strtmp
# This is the path to the upload directory
#main.config['UPLOAD_FOLDER'] = 'static/uploads/'
#print main.config['UPLOAD_FOLDER']
# These are the extension that we are accepting to be uploaded
#main.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'rar','zip','7z'])

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']
