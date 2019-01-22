# -*- coding: utf-8 -*-
import logging
import paramiko


class ConnectSlave:

    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password

    def trans_file(self, source, dest):
        trans = paramiko.Transport((self.ip, 22))
        trans.connect(username=self.username, password=self.password)
        ft = paramiko.SFTPClient.from_transport(trans)
        ft.put(localpath=source, remotepath=dest)
        ft.close()

    def remote_command(self, command):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=self.ip, port=22, username=self.username, password=self.password)
        stdin, stdout, stderr = ssh.exec_command(command)
        error = stderr.readlines()
        ssh.close()
        if error:
            return 0
        else:
            return 1

    def check_locust(self):
        res = self.remote_command('locust -V')
        if not res:
            pipit = self.remote_command('pip install locustio')
            if not pipit:
                logging.error('Can not install locustio in this slave: {}'.format(self.ip))
                return 0
            else:
                return 1
        else:
            return 1
