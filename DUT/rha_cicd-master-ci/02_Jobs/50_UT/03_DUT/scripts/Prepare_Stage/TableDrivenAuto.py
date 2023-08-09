import win32com.client
import os
import os.path
from os import path
import sys
import re
import openpyxl
import subprocess
from scripts.Global_Properties import Global_Properties
import glob
import psutil
import shutil
########### Global Param ###########
jobProperties = Global_Properties()
table_svn_path = "http://172.29.44.209/automotive/autosar/svnASG_D008633/project/external/RVC/Training/Coverage/UT_Cantata/Auto_TS_to_TP/TableDriven.xlsm"
def callTableDriven(tbDrivenFile, testSpecPath, OutputPath):
    # Check file exist
    try:
        wb = None
        excel = win32com.client.gencache.EnsureDispatch('Excel.Application')
        # excel.Visible = True
        # Check reopen workbook

        wb = excel.Workbooks.Open(tbDrivenFile)

        ws = wb.Worksheets('Export')
        path_result = OutputPath
        ws.Cells(6, 2).Value = testSpecPath
        ws.Cells(9, 2).Value = path_result
        svn_rev = str(ws.Cells(2, 3).Value).replace(".0", '')

        if path.exists(path_result):
            print('>>> Remove ' + path_result)
            os.system('rmdir /s /q ' + path_result)

        if not path.isfile(testSpecPath):
            print('>>> File: ' + testSpecPath + ' does not exist')
            wb.Close(SaveChanges=False)
            excel.Application.Quit()
            del excel

        if not path.isdir(OutputPath):
            os.makedirs(OutputPath)
        # check the update for table driven
        svn_latest_rev = subprocess.getoutput(f'svn info --username lmndu --password o1KDh9B --show-item last-changed-revision {table_svn_path}')
        if svn_rev != svn_latest_rev:
            print(f">>> TableDriven on SVN got updated to rev {svn_latest_rev}. Please update the TableDriven for CI!")
            excel.Application.Quit()
            del excel
    except Exception:
        print('>>> ' + tbDrivenFile + " does not exist")
    try:
        # Run VBA macro
        excel.Application.Run("TableDriven.xlsm!Sheet1.ExportClick")
        print(">>> Export completed")
    except Exception:
        print(">>> Error(s) occurred during export")
    # Close current working workbook
    excel.Application.Quit()
    del excel

def kill_excel():
    for proc in psutil.process_iter():
        if proc.name() == "EXCEL.EXE":
            proc.kill()
def merge_all_output(listOutputPath):
    # Root Path Store All Output of multile test spec
    for index, path in enumerate(listOutputPath):
        if index == 0:
            mergePath = listOutputPath[0]
            mergePath = mergePath.replace("/", "\\")
            continue
        cmdPath = path.replace("/", "\\")
        cmdCommand = f"xcopy {cmdPath} {mergePath} /e /y"
        subprocess.run(cmdCommand, check=True, stdout=False)
    return 0

def checkLenSheetName(testSpecPath):
    testSpecPath = testSpecPath.replace("\\","/")
    if not os.path.isfile(testSpecPath):
        print("JK_ERROR: Could not find your test spec path: ", testSpecPath)
        sys.exit(1)
    wb = openpyxl.load_workbook(testSpecPath)
    moreThan3 = []
    for sheetName in wb.sheetnames:
        patern = "^\s*\d+[a-zA-Z]*" # like " 123a" or "123"
        if re.match(patern, sheetName):
            if len(sheetName) > 3:
                moreThan3.append(sheetName)
    wb.close()
    if len(moreThan3) > 0:
        print("JK_ERROR: Your Sheet Name Must Be Less Than 4 chars (example: '12a' or '123' only),\n\t As Coverage Report Will Wrong", testSpecPath)
        print("*"*80)
        print("-"*10,"JK_INFO: PLEASE RENAME OF FOLLOWING SHEETS:\n", moreThan3)
        print("*"*80)
        sys.exit(1)
    return 0


def main():
    kill_excel()
    testPlanPath = jobProperties.TestPlanPath
    allTestPlan = glob.glob(f"{testPlanPath}/**/*.xlsm", recursive=True)
    tableDrivenFile = jobProperties.tableDrivenFile
    outputPath = []
    rootProject = jobProperties.cantataDUT_RootWorkspace
    if os.path.isdir(rootProject):
        shutil.rmtree(rootProject)
    # Make sure remove tree correctly
    os.makedirs(rootProject, exist_ok=False)
    unifyOutputPath = os.path.join(rootProject, "TableDriven")
    for index, tesplan in enumerate(allTestPlan):
        if index > 0:
            unifyOutputPath = unifyOutputPath + f'_{index}'
        outputPath.append(unifyOutputPath)
        checkLenSheetName(tesplan)
        callTableDriven(tableDrivenFile, tesplan, unifyOutputPath)
        kill_excel()
    merge_all_output(outputPath)
    return 0

if __name__ == "__main__":
    main()

