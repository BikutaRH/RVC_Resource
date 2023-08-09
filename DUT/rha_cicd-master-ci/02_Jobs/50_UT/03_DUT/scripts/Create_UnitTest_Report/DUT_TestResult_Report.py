import win32com.client as win32
import json
import os
import shutil
from Global_Properties import Global_Properties
import glob

def rep(link):
    for root, _, files in os.walk(link, topdown=False):
        for name in files:
            if ".ctr" in name:
                filee = open(f'{root}/{name}', 'r')
                data = filee.readlines()
                new_data = ""
                for i in data:
                    new_data += i.replace("\n", "\r")
                with open(f"{root}/{name}",'w') as f:
                    f.write(new_data)

def callTestReportMacro(testPlan_filePath, testReport_FilePath, macroCode, inputPath):
    shutil.copy(testPlan_filePath, testReport_FilePath)
    with open (macroCode, "r") as myfile:
        macro = myfile.read()
    macro = macro.replace("INPUTLINKPATH", inputPath)

    
    excel = win32.Dispatch("Excel.Application")
    excel.Visible = False
    workbook = excel.Workbooks.Open(testReport_FilePath)
    

    excelModule = workbook.VBProject.VBComponents.Add(1)
    
    excelModule.Name = 'CICDReport'
    excelModule.CodeModule.AddFromString(macro)

    print("Clear Test case Info")
    excel.Application.Run('CICDReport.Clear_All_Button_news')

    print("Fill Test case Info")
    excel.Application.Run('CICDReport.Insert_TCs_Button_news')

    print("Import CTR Result")
    excel.Application.Run('CICDReport.ImportCTR_Button_news')

    print("Fill Test Result")
    excel.Application.Run('CICDReport.Insert_Result_Button_news')

    print("finish")

    excel.Workbooks(1).Close(SaveChanges=1)
    print("Close")
    excel.Application.Quit()
    del excel

def main():
    jobProperties = Global_Properties()
    Msn = jobProperties.moduleRunning.capitalize()
    jsonData = jobProperties.targetCantataDir
    with open(jsonData, 'r') as f:
        data = json.load(f)
    macroCodePath = f"{jobProperties.jobWorkSpace}/scripts/Create_UnitTest_Report/code.txt"
    glbCantataWS = data["Cantata"]["Workspace"]
    rootReport = f'{glbCantataWS}/{Msn}_TestLog/Env/{Msn}/report'
    inputPath = f'{glbCantataWS}/{Msn}_TestLog/Env/{Msn}/input'
    rep(inputPath)
    testPlanPath = jobProperties.TestPlanPath
    testPlanFile = glob.glob(f'{testPlanPath}/*.xlsm')
    for tsfile in testPlanFile:
        reportName = os.path.basename(tsfile)
        reportName = reportName.replace("_TS", "_TR")
        reportFilePath = os.path.join(rootReport, reportName)
        # Generate Passed/Failed result
        callTestReportMacro(tsfile, reportFilePath, macroCodePath, inputPath)
    return 0

main()
