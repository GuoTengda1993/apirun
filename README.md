# apirun
A simple API test framework for doing api test easy.
## How to Use It?
Open Console, type `apirun --help`, you will see some parameters
>-f TESTCASEFILE, --testcasefile=TESTCASEFILE
>>TESTCASEFILE is .xls format, you can write testcases in it.

> -F TESTCASEFOLDER, --testcasefolder=TESTCASEFOLDER
>>TESTCASEFOLDER contains TESTCASEFILEs, you need write `folder` or `folder\\`, never `\\folder`; default is None, which means to scan the current work dir.

>--report=REPORT
>>Folder to store test results, default is `report`.

>--demo
>>Make demo xls in working dir.

>-V, --version
>>Show the version.

>--email
>>sending email after finishing api test

>--from
>>the user who sends email, will cover the info in email.json

>--to
>>the user(s) who receive email, will cover the info in email.json

>--subject
>>the email subject, will cover the info in email.json, default is `API Test Result`

>--host
>>the email host, will cover the info in email.json, is required no metter in json file or in parameter

>--pt, --pressuretest
>>run pressure test according to the xls, supported by locustio; `Ctrl + C`, if you want to stop it.

>--pt-demo
>>make PT demo file in current folder

>--pt-not-run
>>just make locustfile according to the xls

>--master
>>Set locust to run in distributed mode with this process as master, use this parameter with --pt; `Ctrl + Break`, if you want to stop it.

## Pending
* More api test situations
