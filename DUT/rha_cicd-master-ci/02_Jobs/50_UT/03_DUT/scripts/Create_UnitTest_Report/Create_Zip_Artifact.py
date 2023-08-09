import shutil
import os
import sys
import re
import json
import subprocess
from Global_Properties import Global_Properties
import glob
from pathlib import Path
import shutil

# Get related input
jobProperties = Global_Properties()
jsonData = jobProperties = Global_Properties()
jsonData = jobProperties.targetCantataDir
Msn = jobProperties.moduleRunning.capitalize()
with open(jsonData, 'r') as f:
    data = json.load(f)
glbCantataWS = data["Cantata"]["Workspace"]
rootReport = f'{glbCantataWS}/{Msn}_TestLog/Env'
glbMergeWS = f'{rootReport}/{Msn}'
jobWorkspace = jobProperties.jobWorkSpace


# Test Report ( include test result and coverage report)
zipFile = f'{jobWorkspace}/DUT_Test_Report.zip'
if os.path.isfile(zipFile):
    os.remove(zipFile)
subprocess.call(f'7z a {zipFile} {glbMergeWS}')

# Test config
testConfigZip = f'{jobWorkspace}/DUT_Test_CONFIG.zip'
if os.path.isfile(testConfigZip):
    os.remove(testConfigZip)
allConfigs = glob.glob(f"{glbCantataWS}/*/manual_IpgCop.json")
deleteInsideConfig = ["manual_IpgCop.json", "CanttTestSuite.txt", "Scale", "TableDriven"]
for detectedConfig in allConfigs:
    parentPath = Path(detectedConfig).parent
    for delete in deleteInsideConfig:
        deletePath = os.path.join(parentPath, delete)
        if os.path.isdir(deletePath):
            shutil.rmtree(deletePath)
        else:
            os.remove(deletePath)
    subprocess.call(f'7z a {testConfigZip} {parentPath}')