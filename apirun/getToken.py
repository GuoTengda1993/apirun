# -*- coding: utf-8 -*-
import requests


def is_num(any_param):
    '''
    Check is number or string, if number, return it
    :param any_param:
    :return: int or False
    '''
    if isinstance(any_param, int):
        return any_param
    else:
        try:
            num = int(any_param)
            return num
        except ValueError:
            return False


def get_token(url, body, locate):
    '''
    Get token
    :param url:
    :param body: Request body
    :param locate: The token location in Header or Json
    :return: token
    '''
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
        token = rep
        section = l[1].strip().split('.')
        for sec in section:
            sn = is_num(sec)
            if sn:
                token = token[sn]
            else:
                token = token[sec]
        return token
