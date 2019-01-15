import logging
import os
import sys
import shutil
from threading import Thread
from threading import Lock
import unittest
from optparse import OptionParser
import ddt
import requests
import json
from json import JSONDecodeError
import apirun

from .genReport import html_report
from .getToken import get_token
from .extractExcel import HandleExcel


logger = logging.getLogger(__name__)
version = apirun.__version__
report_dir = ''
headers = {"Content-Type": "application/json"}
_success = 0
_failure = 0
_error = 0
_count_lock = Lock()


def add_success(num_s):
    global _success
    _count_lock.acquire()
    _success += num_s
    _count_lock.release()


def add_failure(num_f):
    global _failure
    _count_lock.acquire()
    _failure += num_f
    _count_lock.release()


def add_error(num_e):
    global _error
    _count_lock.acquire()
    _error += num_e
    _count_lock.release()


def parse_options():
    """
    Handle command-line options with optparse.OptionParser.

    Return list of arguments, largely for use in `parse_arguments`.
    """

    # Initialize
    parser = OptionParser(usage="apirun [options] [ApiRunClass [ApiRunClass2 ... ]]")

    parser.add_option(
        '-f', '--testcasefile',
        dest='testcasefile',
        help="Testcase to run, e.g. '../testcase.xls'."
    )

    parser.add_option(
        '-F', '--testcasefolder',
        dest='testcasefolder',
        help="all testcase in the foler to run.",
        default=""
    )

    parser.add_option(
        '--report',
        action='store',
        type='str',
        dest='report',
        default='report',
        help="Store the reports.",
    )

    # Version number (optparse gives you --version but we have to do it
    # ourselves to get -V too. sigh)
    parser.add_option(
        '-V', '--version',
        action='store_true',
        dest='show_version',
        default=False,
        help="show program's version number and exit"
    )

    parser.add_option(
        '--demo',
        action='store_true',
        dest='make_demo',
        default=False,
        help="make demo xls in working folder"
    )

    # Finalize
    # Return three-tuple of parser + the output from parse_args (opt obj, args)
    opts, args = parser.parse_args()
    return parser, opts, args


def run_test(title, filename, report_path, description, testcase):
    test = unittest.TestLoader().loadTestsFromTestCase(testcase)
    suit = unittest.TestSuite([test])
    runner, fp = html_report(title=title, filename=filename, report_path=report_path, description=description)
    results = runner.run(suit)
    fp.close()
    e = results.error_count
    f = results.failure_count
    s = results.success_count
    add_success(s)
    add_failure(f)
    add_error(e)


def get_apirun_path():
    if 'win' in sys.platform:
        python3_path = os.getenv('PYTHON')
        if not python3_path:
            python3_path = os.getenv('PYTHON3')
        if python3_path:
            if 'python3' in python3_path.lower():
                if 'scripts' in python3_path.lower():
                    apirun_path = os.path.join(os.path.dirname(os.path.dirname(python3_path)), 'Lib\\site-packages\\apirun\\')
                else:
                    apirun_path = os.path.join(python3_path, 'Lib\\site-packages\\apirun\\')
        else:
            sys_path = os.getenv('path').split(';')
            for each in sys_path:
                if 'python3' in each.lower() and 'scripts' not in each.lower():
                    python3_path = each
                    break
            apirun_path = os.path.join(python3_path, 'Lib\\site-packages\\apirun\\')
    elif 'linux' in sys.platform:
        with os.popen('find /usr/local/ -name apirun -type d') as lp:
            apirun_path = lp.read().strip()
    return apirun_path


def str_to_json(data):
    data = str(data).replace('\'', '"')
    j = json.loads(data, encoding='utf-8')
    return j


def start_test(testcasefile):
    testcase_data = HandleExcel(testcasefile)

    token_url, token_body, token_para, token_locate = testcase_data.auth_info()
    token_body = str_to_json(token_body)
    try:
        token = get_token(token_url, token_body, token_locate)
    except KeyError:
        logger.error('Please check your auth info, cannot get correct response.')
        sys.exit(1)
    except Exception as e:
        logger.error('{}'.format(e))
        sys.exit(1)
    global headers
    headers[token_para] = token

    testcase_list = testcase_data.testcase_list()
    report_title, report_description = testcase_data.report_info()

    @ddt.ddt
    class ApiRun(unittest.TestCase):

        @classmethod
        def setUpClass(cls):
            cls.headers = headers

        @classmethod
        def tearDownClass(cls):
            pass

        @ddt.idata(testcase_list)
        @ddt.unpack
        def test_api(self, title, url, auth, method, query, request_data, expect_status, expect_str):
            print('用例标题：' + title + 'END')  # 死活别删这一段，正则匹配这段内容，将标题添加到HTML报告中
            method = method.upper()
            if query:
                query = str_to_json(query)
            if request_data:
                request_body = str_to_json(request_data)
            else:
                request_body = None
            exp_status_code = int(expect_status)

            _headers = self.headers
            if auth == 'FALSE':
                _headers = {"Content-Type": "application/json"}

            if method == 'GET':  # GET
                response_actual = requests.get(url=url, headers=_headers, params=query)
            elif method == 'POST':  # POST
                response_actual = requests.post(url=url, headers=_headers, json=request_body, params=query)
            elif method == 'DELETE':  # DELETE
                response_actual = requests.delete(url=url, headers=_headers, params=query)
            elif method == 'PUT':  # PUT
                response_actual = requests.put(url=url, headers=_headers, params=query, json=request_body)
            elif method == 'PATCH':  # patch
                response_actual = requests.patch(url=url, headers=_headers, params=query, json=request_body)
            elif method == 'HEAD':
                response_actual = requests.head(url=url, headers=_headers, params=query)
            elif method == 'OPTIONS':
                response_actual = requests.options(url=url, headers=_headers, params=query)
            else:  # Other method, such as TRACE
                response_actual = requests.request(method=method, url=url, headers=_headers, params=query, json=request_body)

            actual_status_code = int(response_actual.status_code)
            if actual_status_code == exp_status_code:
                print('Status code is same: {sc}'.format(sc=actual_status_code))
                if expect_str:
                    expect_str = expect_str.strip()
                    act_response = response_actual.json()
                    print('Actual response: {}'.format(act_response))
                    if expect_str.endswith(';'):
                        expect_str = expect_str.strip(';')
                    if expect_str.endswith('；'):
                        expect_str = expect_str.strip('；')
                    if ';' and '；' not in expect_str:
                        self.assertIn(expect_str, str(act_response), msg='{} is not in response'.format(expect_str))
                    else:
                        if ';' in expect_str:
                            expect_str_list = expect_str.split(';')
                        else:
                            expect_str_list = expect_str.split('；')
                        for each_str in expect_str_list:
                            each_str = each_str.strip()
                            self.assertIn(each_str, str(act_response), msg='{} is not in response'.format(each_str))
            else:
                try:
                    act_response = response_actual.json()
                    print('Actual response: {}'.format(act_response))
                except JSONDecodeError:
                    act_response = response_actual.text
                    print('Not json response: {}'.format(act_response))
                self.fail('Status code is different! Actual code is {}'.format(actual_status_code))

    report_filename = testcasefile.replace('\\', '-')
    run_test(title=report_title, filename=report_filename, report_path=report_dir, description=report_description,
             testcase=ApiRun)


def main():
    parser, options, arguments = parse_options()

    # setup logging
    # logger = logging.getLogger(__name__)

    if options.show_version:
        print("Apirun %s" % (version,))
        sys.exit(0)

    if options.make_demo:
        pwd = os.getcwd()
        apirun_path = get_apirun_path()
        if not apirun_path:
            logger.error('''Cannot locate Python path, make sure it is in right place. If windows add it to sys PATH,
            if linux make sure python is installed in /usr/local/lib/''')
            sys.exit(1)
        demo_path = os.path.join(apirun_path, 'demo', 'demo_testcase.xls')
        new_demo = os.path.join(pwd, 'demo.xls')
        shutil.copyfile(demo_path, new_demo)
        sys.exit(0)

    if options.report:
        global report_dir
        report_dir = options.report
        apirun_path = get_apirun_path()
        if not apirun_path:
            logger.error('''Cannot locate Python path, make sure it is in right place. If windows add it to sys PATH,
            if linux make sure python is installed in /usr/local/lib/''')
            sys.exit(1)
        try:
            os.makedirs(os.path.join(report_dir, 'js'))
            js_file = os.path.join(apirun_path, 'js', 'echarts.common.min.js')
            shutil.copyfile(js_file, os.path.join(report_dir, 'js', 'echarts.common.min.js'))
        except FileExistsError:
            pass

    if options.testcasefile:
        if options.testcasefolder:
            logger.error('Cannot use -f and -F together.')
            sys.exit(1)
        testcasefile = options.testcasefile
        if not testcasefile.endswith('.xls'):
            logger.error("Testcasefile must ends in '.xls' and see --help for available options.")
            sys.exit(1)
        if not os.path.isfile(testcasefile):
            logger.error('Testcasefile is not exist, please check it.')
            sys.exit(1)

        start_test(testcasefile=testcasefile)

    if options.testcasefolder:
        if options.testcasefile:
            logger.error('Cannot use -f and -F together.')
            sys.exit(1)
        testcase_folder = options.testcasefolder
        if testcase_folder:
            if not os.path.isdir(testcase_folder):
                logger.error('Testcasefolder is not exist, please check it.')
                sys.exit(1)
            _dir, _subdir, files = list(os.walk(testcase_folder))[0]
        else:
            _dir, _subdir, files = list(os.walk(os.getcwd()))[0]
        testcase_file_list = []
        for each in files:
            if each.endswith('.xls'):
                testcase_file_list.append(os.path.join(testcase_folder, each))
        if len(testcase_file_list) == 0:
            logger.error('There is no testcase file in Testcasefolder.')
            sys.exit(1)
        for testcasefile in testcase_file_list:
            t = Thread(target=start_test, args=(testcasefile,))
            print(t)
            print('+++++++++++++++ ' + testcasefile)
            t.start()
            t.join()

    print('==================')
    print('''
    Results:
    Total: {t}
    Success: {s}
    Failure: {f}
    Error: {e}
    '''.format(t=(_success + _failure + _error), s=_success, f=_failure, e=_error))


if __name__ == '__main__':
    main()
