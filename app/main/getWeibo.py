import requests
import json
import ast


class Spider:

    def __init__(self, page):
        self.page = page
        self.url = "https://m.weibo.cn/api/container/getIndex?type=uid&value=3700687004&containerid=1076033700687004"
        self.session = requests.session()

    def getHtml(self):
        if self.page == 0:
            u = self.session.get(self.url)
        else:
            u = self.session.get(self.url + "&page=" + str(self.page)).text
        return u

    def getJson(self):
        text = self.getHtml()
        js0 = ast.literal_eval(repr(text))
        js1 = json.loads(js0)
        if(js1['ok'] == 1):
            li = list()
            for i in js1['data']['cards']:
                forms = i['mblog']['source']
                name = i['mblog']['user']['screen_name']
                times = i['mblog']['created_at']
                if('original_pic' in i['mblog']):
                    pic = i['mblog']['original_pic']
                    jsons = {'name': name,
                             'times': times, 'forms': forms,
                             'pic': pic}
                else:
                    jsons = {'name': name,
                             'times': times, 'forms': forms,
                             'pic': ""}
                li.append(jsons)
            lis = list()
            for i in li:
                if i['pic'].strip() != "":
                    lis.append(i)
            return lis


class Jwgl:

    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.session = requests.session()

    def tologin(self):
        url = "http://119.29.98.60:8080/WeJfinal/jwgl/login"
        data = {
            'admin': self.user,
            'pass': self.password
        }
        u = self.session.post(url, data=data)
        return u.json()

# print(Jwgl("150015511131", "WANAN116224").tologin())


class Eol:

    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.session = requests.session()

    def tologin(self):
        url = "http://119.29.98.60:8080/WeJfinal/eol/login"
        data = {
            'admin': self.user,
            'pass': self.password
        }
        u = self.session.post(url, data=data)
        return u.json()

#print(Eol("150015511155", "150015511155").tologin())
