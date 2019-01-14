# -*- coding: utf-8 -*-
import xlrd
from .dealParameter import deal_parameter


class HandleExcel:
    def __init__(self, filename):
        self.filename = filename
        self.workbook = xlrd.open_workbook(self.filename)

    def url_parameter(self):
        url_para_sheet = self.workbook.sheet_by_index(1)
        nrows = url_para_sheet.nrows
        url_para = {}
        for i in range(1, nrows):
            key = url_para_sheet.cell_value(i, 0)
            value = url_para_sheet.cell_value(i, 1)
            if not isinstance(value, str):
                value = str(int(value))
            url_para[key] = value
        return url_para

    def request_parameter(self):
        url_para_sheet = self.workbook.sheet_by_index(2)
        nrows = url_para_sheet.nrows
        req_para = {}
        for i in range(1, nrows):
            key = url_para_sheet.cell_value(i, 0)
            value = url_para_sheet.cell_value(i, 1)
            if not isinstance(value, str):
                value = str(int(value))
            req_para[key] = value
        return req_para

    def testcase_list(self):
        testcase_sheet = self.workbook.sheet_by_index(0)
        nrows = testcase_sheet.nrows
        testcases = []
        for i in range(1, nrows):
            title = testcase_sheet.cell_value(i, 0)

            url = testcase_sheet.cell_value(i, 1)
            url_para = self.url_parameter()
            url = deal_parameter(url, url_para)
            if ('http://' or 'https://') not in url:
                url = url_para['BASE_URL'] + url
            url = url.strip()

            auth = testcase_sheet.cell_value(i, 2)
            method = testcase_sheet.cell_value(i, 3)

            query = testcase_sheet.cell_value(i, 4)
            query = deal_parameter(query, url_para)

            request_data = testcase_sheet.cell_value(i, 5)
            req_para = self.request_parameter()
            request_data = deal_parameter(request_data, req_para).replace('\r\n', '')

            expect_status_code = testcase_sheet.cell_value(i, 6)
            expect_str = testcase_sheet.cell_value(i, 7)
            testcases.append(
                {'title': title, 'url': url, 'auth': auth, 'method': method, 'query': query,
                    'request_data': request_data, 'expect_status': expect_status_code, 'expect_str': expect_str}
            )
        return testcases

    def auth_info(self):
        auth_sheet = self.workbook.sheet_by_index(3)
        token_url = auth_sheet.cell_value(0, 1)
        body = auth_sheet.cell_value(1, 1)
        token_para = auth_sheet.cell_value(2, 0)
        token_locate = auth_sheet.cell_value(2, 1)
        return token_url, body, token_para, token_locate

    def report_info(self):
        report_sheet = self.workbook.sheet_by_index(4)
        report_title = report_sheet.cell_value(0, 1)
        report_description = report_sheet.cell_value(1, 1)
        return report_title, report_description


if __name__ == '__main__':
    test = HandleExcel('E:\\Temp\\demo2.xls')
    t = test.testcase_list()
    for each in t:
        print(each)
    url = test.url_parameter()
    print(url)
    req = test.request_parameter()
    print(req)
    a, b, c, d = test.auth_info()
    print(a, b, c, d)
