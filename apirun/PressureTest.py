# -*- coding: utf-8 -*-
BASIC_IMPORT = '''# -*- coding: utf-8 -*-
import sys
import requests
import logging
from locust import TaskSet, HttpLocust, TaskSequence, task, seq_task
from requests.packages import urllib3


urllib3.disable_warnings()

def get_token(url, body, locate):
    try:
        response = requests.post(url=url, json=body, verify=False)
        if ':' in locate:
            l = locate.split(':')
        else:
            l = locate.split('：')
        if l[0].lower() == ('header' or 'headers'):
            token = response.headers[l[1].strip()]
            return token
        elif l[0].lower() == 'json':
            rep = response.json()
            section = l[1].strip().split('.')
            t_index = None
            if section[-1].endswith(']'):
                t_index = section[-1][-2]
                section[-1] = section[-1][:-3]
            token = rep
            for x in section:
                token = token[x]
            if t_index:
                token = token[int(t_index)]
            return token
    except KeyError:
        logging.error('Please check your auth info, cannot get correct response.')
        sys.exit(1)
    except Exception as e:
        logging.error('{}'.format(e))
        sys.exit(1)

'''
BASIC_LAST = '''

class ApiTest(HttpLocust):
    host = '{HOST}'
    task_set = PressureTest
    min_wait = {MIN_WAIT}
    max_wait = {MAX_WAIT}
'''
BASIC_MODE = '''
class PressureTest({TASK_MODE}):
'''
MODE_TOKEN_FIRST_TIME = '''
    def setup(self):
        global headers
        body = {TOKEN_BODY}
        token = get_token(url='{TOKEN_URL}', body=body, locate='{TOKEN_LOCATE}')
        headers = @-'Content-Type': 'application/json', '{TOKEN_PARAM}': token-@
'''
MODE_TOKEN_NEVER = '''
    def setup(self):
        global headers
        headers = {"Content-Type": "application/json"}
'''
MODE_TASKSET_GET = '''
    @task({WEIGHT})
    def test{NUM}(self):
        query = {QUERY}
        self.client.get('{URL}', headers=headers, params=query, verify=False)
'''
MODE_TASKSET_POST = '''
    @task({WEIGHT})
    def test{NUM}(self):
        query = {QUERY}
        body = {POST_BODY}
        self.client.post('{URL}', json=body, headers=headers, params=query, verify=False)
'''
MODE_TASK_SEQ_GET = '''
    @seq_task({SEQ})
    @task({WEIGHT})
    def test{NUM}(self):
        query = {QUERY}
        self.client.get('{URL}', headers=headers, params=query, verify=False)
'''
MODE_TASK_SEQ_POST = '''
    @seq_task({SEQ})
    @task({WEIGHT})
    def test{NUM}(self):
        query = {QUERY}
        body = {POST_BODY}
        self.client.post('{URL}', json=body, headers=headers, params=query, verify=False)
'''
MODE_TASKSET_GET_TOKEN = '''
    @task({WEIGHT})
    def test{NUM}(self):
        body = {TOKEN_BODY}
        token = get_token(url='{TOKEN_URL}', body=body, locate='{TOKEN_LOCATE}')
        headers = @-"Content-Type": "application/json", "{TOKEN_PARAM}": token-@
        query = {QUERY}
        self.client.get('{URL}', headers=headers, params=query, verify=False)
'''
MODE_TASKSET_POST_TOKEN = '''
    @task({WEIGHT})
    def test{NUM}(self):
        body = {TOKEN_BODY}
        token = get_token(url='{TOKEN_URL}', body=body, locate='{TOKEN_LOCATE}')
        headers = @-"Content-Type": "application/json", "{TOKEN_PARAM}": token-@
        query = {QUERY}
        body = {POST_BODY}
        self.client.post('{URL}', json=body, headers=headers, params=query, verify=False)
'''
MODE_TASK_SEQ_GET_TOKEN = '''
    @seq_task({SEQ})
    @task({WEIGHT})
    def test{NUM}(self):
        body = {TOKEN_BODY}
        token = get_token(url='{TOKEN_URL}', body=body, locate='{TOKEN_LOCATE}')
        headers = @-"Content-Type": "application/json", "{TOKEN_PARAM}": token-@
        query = {QUERY}
        self.client.get('{URL}', headers=headers, params=query, verify=False)
'''
MODE_TASK_SEQ_POST_TOKEN = '''
    @seq_task({SEQ})
    @task({WEIGHT})
    def test{NUM}(self):
        body = {TOKEN_BODY}
        token = get_token(url='{TOKEN_URL}', body=body, locate='{TOKEN_LOCATE}')
        headers = @-"Content-Type": "application/json", "{TOKEN_PARAM}": token-@
        query = {QUERY}
        body = {POST_BODY}
        self.client.post('{URL}', json=body, headers=headers, params=query, verify=False)
'''
