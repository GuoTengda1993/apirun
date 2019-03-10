import shutil
from threading import Thread
from threading import Lock
import unittest
from optparse import OptionParser
import ddt
import requests
from requests.packages import urllib3
import json
from json import JSONDecodeError
import apirun

from .genReport import html_report
from .getToken import get_token
from .extractExcel import HandleExcel
from .mail import *
from .PressureTest import *
from .PtSlave import ConnectSlave


urllib3.disable_warnings()
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

    parser.add_option(
        '--email',
        action='store_true',
        dest='email',
        default=False,
        help='sending email after finishing api test'
    )

    parser.add_option(
        '--from',
        action='store_true',
        dest='email_from',
        default=False,
        help='the user who sends email'
    )

    parser.add_option(
        '--to',
        action='store_true',
        dest='email_to',
        default=False,
        help='the user(s) who receive email'
    )

    parser.add_option(
        '--subject',
        action='store_true',
        dest='email_subject',
        default=False,
        help='the email subject'
    )

    parser.add_option(
        '--host',
        action='store_true',
        dest='email_host',
        default=False,
        help='the email host'
    )

    parser.add_option(
        '--pt', '--pressuretest',
        dest='PtFile',
        help='run pressure test according to the xls, supported by locustio'
    )

    parser.add_option(
        '--pt-demo',
        action='store_true',
        dest='PtDemo',
        default=False,
        help='make PT demo file in current folder'
    )

    parser.add_option(
        '--pt-not-run',
        dest='PtNotRun',
        help='just make locustfile according to the xls'
    )

    parser.add_option(
        '--master',
        action='store_true',
        default=False,
        dest='master',
        help='Set locust to run in distributed mode with this process as master, use this parameter with --pt'
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
            if str(auth) == '0' or auth == 'FALSE':
                _headers = {"Content-Type": "application/json"}

            if method == 'GET':  # GET
                response_actual = requests.get(url=url, headers=_headers, params=query, verify=False)
            elif method == 'POST':  # POST
                response_actual = requests.post(url=url, headers=_headers, json=request_body, params=query, verify=False)
            elif method == 'DELETE':  # DELETE
                response_actual = requests.delete(url=url, headers=_headers, params=query, verify=False)
            elif method == 'PUT':  # PUT
                response_actual = requests.put(url=url, headers=_headers, params=query, json=request_body, verify=False)
            elif method == 'PATCH':  # patch
                response_actual = requests.patch(url=url, headers=_headers, params=query, json=request_body, verify=False)
            elif method == 'HEAD':
                response_actual = requests.head(url=url, headers=_headers, params=query, verify=False)
            elif method == 'OPTIONS':
                response_actual = requests.options(url=url, headers=_headers, params=query, verify=False)
            else:  # Other method, such as TRACE
                response_actual = requests.request(method=method, url=url, headers=_headers, params=query, json=request_body, verify=False)

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
                    if (';' not in expect_str) and ('；' not in expect_str):
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


def pt_slave(ip, username, password, ptfile, ptcommand):
    connect = ConnectSlave(ip, username, password)
    is_locust = connect.check_locust()
    if is_locust:
        dest = '/root/' + ptfile
        connect.trans_file(source=ptfile, dest=dest)
        connect.remote_command(command=ptcommand)
    else:
        logging.error('Slave {} cannot run locust.'.format(ip))


def main():
    parser, options, arguments = parse_options()

    # setup logging
    # logger = logging.getLogger(__name__)
    apirun_path = get_apirun_path()
    pwd = os.getcwd()
    _run = False
    _email_mark = False

    if options.show_version:
        print("Apirun %s" % (version,))
        sys.exit(0)

    if options.make_demo:
        if not apirun_path:
            logger.error('''Cannot locate Python path, make sure it is in right place. If windows add it to sys PATH,
            if linux make sure python is installed in /usr/local/lib/''')
            sys.exit(1)
        demo_path = os.path.join(apirun_path, 'demo', 'demo_testcase.xls')
        new_demo = os.path.join(pwd, 'demo.xls')
        shutil.copyfile(demo_path, new_demo)
        sys.exit(0)

    if options.PtDemo:
        if not apirun_path:
            logger.error('''Cannot locate Python path, make sure it is in right place. If windows add it to sys PATH,
            if linux make sure python is installed in /usr/local/lib/''')
            sys.exit(1)
        pt_demo_path = os.path.join(apirun_path, 'demo', 'demo_pressuretest.xls')
        pt_new_demo = os.path.join(pwd, 'PtDemo.xls')
        shutil.copyfile(pt_demo_path, pt_new_demo)
        sys.exit(0)

    if options.email:
        global yag, email_to, subject
        _email = []
        if not (options.email_from and options.email_to):
            if not os.path.isfile('email.json'):
                logger.error('It is your first time to use email function, please fill email.json and run it again.')
                demo_email = os.path.join(apirun_path, 'demo', 'email.json')
                new_email = os.path.join(pwd, 'email.json')
                shutil.copyfile(demo_email, new_email)
                sys.exit(0)
            else:
                with open('email.json', 'r') as ef:
                    email_info = json.load(ef)
                email_from = email_info['from']
                subject = email_info['subject']
                if subject == '': subject = 'API Test Result'
                receivers = email_info['receiver']
                email_to = []
                for _e in receivers.keys():
                    email_to.extend(receivers[_e])
                email_host = email_info['host']
            if options.email_host:
                email_host = options.email_host
            if options.email_from:
                email_from = options.email_from
            if options.email_to:
                _to = options.email_to
                if _to in receivers.keys():
                    email_to = receivers[_to]
                else:
                    email_to = email_in_cil(_to)
            if options.email_subject:
                subject = options.email_subject
        else:
            email_from = options.email_from
            email_to = options.email_to
            email_host = options.email_host
            if options.email_subject: subject = options.email_subject
            else: subject = 'API Test Result'

        _email.append(email_from)
        _email.extend(email_to)
        for _each in _email:
            if check_address(_each): pass
            else:
                logger.error('Email address is not correct: {}'.format(_each))
                sys.exit(1)

        yag = init_email(username=email_from, host=email_host)
        _email_mark = True

    if options.email_from:
        if not options.email:
            logger.error('Cannot use --from without --email.')
            sys.exit(1)

    if options.email_to:
        if not options.email:
            logger.error('Cannot use --to without --email.')
            sys.exit(1)

    if options.email_host:
        if not options.email:
            logger.error('Cannot use --host without --email.')
            sys.exit(1)

    if options.email_subject:
        if not options.email:
            logger.error('Cannot use --subject without --email.')
            sys.exit(1)

    if options.master:
        if not options.PtFile:
            logger.error('Cannot use --master without --pt.')
            sys.exit(1)

    if options.report:
        global report_dir
        report_dir = options.report
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
            logger.error("Testcasefile must be end with '.xls' and see --help for available options.")
            sys.exit(1)
        if not os.path.isfile(testcasefile):
            logger.error('Testcasefile is not exist, please check it.')
            sys.exit(1)

        start_test(testcasefile=testcasefile)
        _run = True

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
        _run = True

    if options.PtNotRun:
        if options.PtFile:
            logger.error('Cannot use --pt and --pt-not-run together.')
            sys.exit(1)
        pt_file = options.PtNotRun
        if not pt_file.endswith('.xls'):
            logger.error("PressureTest file must be end with '.xls' and see --help for available options.")
            sys.exit(1)
        if not os.path.isfile(pt_file):
            logger.error('PressureTest file is not exist, please check it.')
            sys.exit(1)
        make_locustfile(pt_file)
        logger.info('Generate locustfile success.')
        sys.exit(0)

    if options.PtFile:
        if options.PtNotRun:
            logger.error('Cannot use --pt and --pt-not-run together.')
            sys.exit(1)
        pt_file = options.PtFile
        if not pt_file.endswith('.xls'):
            logger.error("PressureTest file must be end with '.xls' and see --help for available options.")
            sys.exit(1)
        if not os.path.isfile(pt_file):
            logger.error('PressureTest file is not exist, please check it.')
            sys.exit(1)
        global _run_pt
        _run_pt = False
        make_locustfile(pt_file)
        ptpy = pt_file.replace('.xls', '.py')
        pt_report = pt_file.strip('.xls')
        if not options.master:
            locust_cli = 'locust -f {locustfile} --csv={ptReport}'.format(locustfile=ptpy, ptReport=pt_report)
            try:
                os.system(locust_cli)
            except KeyboardInterrupt:
                shutil.move(pt_report+'_distribution.csv', os.path.join(report_dir, pt_report+'_distribution.csv'))
                shutil.move(pt_report+'_requests.csv', os.path.join(report_dir, pt_report+'_requests.csv'))
                _run_pt = True
        else:
            pt_s = PtExcel(pt_file)
            master_ip, pt_slave_info = pt_s.pt_slave()
            if master_ip == '':
                logger.error('master IP cannot be None if you use --master')
                sys.exit(1)
            if 'win' in sys.platform.lower():
                locust_cli_master = 'locust -f {locustfile} --csv={ptReport} --master'.format(locustfile=ptpy, ptReport=pt_report)
            else:
                locust_cli_master = 'locust -f {locustfile} --csv={ptReport} --master'.format(locustfile=ptpy, ptReport=pt_report)
            try:
                locust_cli_slave = 'nohup locust -f /root/{locustfile} --slave --master-host={masteIP} > /dev/null 2>&1 &'.format(locustfile=ptpy, masteIP=master_ip)
                for slave in pt_slave_info:
                    slave_ip, slave_username, slave_password = slave
                    _t = Thread(target=pt_slave, args=(slave_ip, slave_username, slave_password, ptpy, locust_cli_slave))
                    logger.info('Prepare slave {}'.format(slave_ip))
                    _t.start()
                    _t.join()
                os.system(locust_cli_master)
            except KeyboardInterrupt:
                pass
            except Exception as e:
                logger.error('Must someting happend, collect Exceptions here: {}'.format(e))
            finally:
                shutil.move(pt_report + '_distribution.csv', os.path.join(report_dir, pt_report + '_distribution.csv'))
                shutil.move(pt_report + '_requests.csv', os.path.join(report_dir, pt_report + '_requests.csv'))
                _run_pt = True

    if _run or _run_pt:
        if _run:
            print('==================')
            results_message = '''
            Results:
            Total: {t}
            Success: {s}
            Failure: {f}
            Error: {e}
            '''.format(t=(_success + _failure + _error), s=_success, f=_failure, e=_error)
            print(results_message)
        else:
            results_message = 'Pressure Test Result.'

        if _email_mark:
            attachment = subject.replace(' ', '_') + '.zip'
            zip_report(report_dir, attachment)
            send_email(yag, subject=subject, to=email_to, msg=results_message, attachment=attachment)
        else:
            sys.exit(0)
    sys.exit(0)


if __name__ == '__main__':
    main()
