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

## Pending
* More api test situations
* Easy and better installation
