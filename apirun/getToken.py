# -*- coding: utf-8 -*-
import requests


def get_token(url, body, locate):
    response = requests.post(url=url, json=body)
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
        if section[-1].endswith(']'):
            t_index = section[-1][-2]
            section[-1] = section[-1][:-3]
        token = rep
        for x in section:
            token = token[x]
        if t_index:
            token = token[int(t_index)]
        return token
