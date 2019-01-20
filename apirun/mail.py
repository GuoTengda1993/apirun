# -*- coding: utf-8 -*-
import os
import sys
import re
import logging
import getpass
import zipfile
import keyring
from keyring.errors import PasswordDeleteError
import yagmail
from smtplib import SMTPException


def zip_report(filepath, zipname):
    startdir = filepath
    file_news = zipname
    z = zipfile.ZipFile(file_news, 'w', zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(startdir):
        fpath = dirpath.replace(startdir, '')
        for filename in filenames:
            z.write(os.path.join(dirpath, filename), os.path.join(fpath, filename))
    logging.info('压缩成功')
    z.close()


def init_email(username, host):
    try:
        _pass = keyring.get_password('apirun_yagmail', username)
        if _pass is None:
            yn = ''
            while True:
                yn = input('Your password is not saved in this system, do you want to SAVE it(y/n)?\n').strip()
                if yn.lower() == 'y' or yn == 'n':
                    break
            p1 = getpass.getpass('Please input your password:')
            p2 = getpass.getpass('Please conform your password:')
            while p1 != p2:
                print('The password you typed is NOT same.')
                p1 = getpass.getpass('Please input your password:')
                p2 = getpass.getpass('Please conform your password:')
            _pass = p1
            if yn.lower() == 'y':
                print('Your password will save in this system.')
                keyring.set_password('apirun_yagmail', username=username, password=_pass)
            else:
                print('Your password is just worked in this time.')
        return yagmail.SMTP(user=username, password=_pass, host=host)
    except SMTPException as e:
        logging.error('SMTP Error: {}'.format(e))
        sys.exit(1)


def send_email(yag, subject, to, msg, attachment, cc=None):
    try:
        yag.send(to=to, cc=cc, subject=subject, contents=[msg, attachment])
    except SMTPException as er:
        logging.error('SMTP Error: {}'.format(er))
        sys.exit(1)


def del_account(username):
    try:
        keyring.delete_password('apirun_yagmail', username=username)
        logging.info('Delete account success.')
    except PasswordDeleteError:
        logging.error('Your password is not saved in this system.')


def check_address(address):
    pattern = '\w+@(\w+\.)?\w+\.\w+'
    addr = re.match(pattern, address)
    if addr:
        return True
    else:
        return False


def email_in_cil(parameter):
    e_list = []
    if '(' and ')' in parameter:
        row_para = re.sub('[()]', '', parameter)
        e_list = re.split(',\s?', row_para)
    elif '[' and ']' in parameter:
        row_para = re.sub('[\[\]]', '', parameter)
        e_list = re.split(',\s?', row_para)
    else:
        e_list.append(parameter)
    return e_list


if __name__ == '__main__':
    a = email_in_cil('aa')
    print(a)
