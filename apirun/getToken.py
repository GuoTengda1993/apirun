# -*- coding: utf-8 -*-
import requests


def get_token(url, body, locate):
    response = requests.post(url=url, json=body)
    l = locate.split(':')
    if l[0].lower() == ('header' or 'headers'):
        token = response.headers[l[1].strip()]
    elif l[0].lower() == 'json':
        rep = response.json()
        section = l[1].strip().split('.')
        if section[-1].endwith(']'):
            t_index = section[-1][-2]
            section[-1] = section[-1][:-3]
        token = rep
        for x in section:
            token = token[x]
        if t_index:
            token = token[t_index]
    return token
