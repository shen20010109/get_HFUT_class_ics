# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


import requests
import re
import hashlib

'''
抓取课表
'''


class get():
    host = r'http://jxglstu.hfut.edu.cn'
    username = ''
    password = ''
    studentId = ''
    semesterId = ''
    bizTypeId = ''
    session = requests.session()

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def login(self):        # 登录
        salt = self.session.get('{host}/eams5-student/login-salt'.format(host=self.host)).text
        data = {
            'username': self.username,
            'password': hashlib.sha1((salt + '-' + self.password).encode('utf-8')).hexdigest(),
                                                    # 密码加密 生成salt串+password串
            'captcha': ''
        }
        self.session.post(url='{host}/eams5-student/login'.format(host=self.host), json=data)
        return self

    def set(self):
        result = self.session.get('{host}/eams5-student/for-std/course-table'.format(host=self.host))
        self.studentId = re.search(r'(?<=var studentId = )\d+', result.text)[0]
        self.semesterId = re.search(r'(?<=<option selected="selected" value=")\d+', result.text)[0]
        self.bizTypeId = re.search(r'(?<=bizTypeId: )\d+', result.text)[0]
        return self

    def get_lesson(self):
        params = {
            'bizTypeId': self.bizTypeId,
            'semesterId': self.semesterId,
            'dataId': self.studentId
        }
        lessonIds = self.session.get(url='{host}/eams5-student/for-std/course-table/get-data'.format(host=self.host),
                               params=params).json()['lessonIds']
        data = {'lessonIds': lessonIds, 'studentId': self.studentId, 'weekIndex': ''}
        datum = self.session.post(url='{host}/eams5-student/ws/schedule-table/datum'.format(host=self.host),
                            json=data).json()
        return datum


'''
将爬取的课表转为ics文件
'''


def Trans(datum: dict):
    file = open('class.ics', 'w', encoding='utf-8')

    result = datum['result']
    lessonList = result['lessonList']
    scheduleList = result['scheduleList']
    scheduleGroupList = result['scheduleGroupList']
    lessonName = { lesson['id']: lesson['courseName'] for lesson in lessonList}

    for cls in scheduleList:
        DTSTART = 'DTSTART:{}T{:0>4d}00Z'.format(cls['date'].replace('-', ''), cls['startTime'] - 800)
        DTEND = 'DTEND:{}T{:0>4d}00Z'.format(cls['date'].replace('-', ''), cls['endTime'] - 800)
        DESCRIPTION = 'DESCRIPTION:' + cls['personName']
        if cls['room'] == None:
            LOCATION = 'LOCATION: 暂无信息'
        else:
            LOCATION = 'LOCATION:' + cls['room']['nameZh']
        SUMMARY = 'SUMMARY:' + lessonName[cls['lessonId']]
        file.write('BEGIN:VEVENT' + '\n')
        file.write(
            'UID:' + hashlib.sha1(lessonName[cls['lessonId']].encode(encoding='utf-8')).hexdigest()
            + '-{}T{:0>4d}00Z'.format(cls['date'].replace('-', ''), cls['startTime'] - 800)
            + '-{}T{:0>4d}00Z'.format(cls['date'].replace('-', ''), cls['endTime'] - 800) + '\n'
        )
        file.write('DTSTAMP:20210101T00000Z' + '\n')
        file.write(DTSTART + '\n' + DTEND + '\n' + DESCRIPTION + '\n' + LOCATION + '\n' + SUMMARY)
        file.write('END:VEVENT' + '\n')
        file.write('\n')

    file.write('END:VCALENDAR' + '\n')
    file.close()


if __name__ == '__main__':
    username = input('请输入您的学号：')
    password = input('请输入您的密码：')

    Trans(get(username, password).login().set().get_lesson())