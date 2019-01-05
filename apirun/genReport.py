# -*- coding: utf-8 -*-
import time
import os
from .HTMLTestRunner_Modified import HTMLTestRunner


def html_report(title, filename, report_path, description):
    fpath = report_path
    fname = 'report_' + filename + '_' + time.strftime('%Y%m%d-%H%M%S', time.localtime()) + '.html'  # 报告的名称
    f_name = os.path.join(fpath, fname)
    fp = open(f_name, 'wb')
    runner = HTMLTestRunner(stream=fp, title=title, description=description)
    return runner, fp   # 返回的fp为open状态，写入完毕后需要进行关闭，否则写入失败
