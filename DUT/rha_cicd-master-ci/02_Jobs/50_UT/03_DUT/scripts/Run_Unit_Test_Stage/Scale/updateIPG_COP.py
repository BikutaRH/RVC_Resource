"""
Algorithm:
Step 1:
Get input:
Manual Data(Json)
Step 2:
Process Input:
Json + Varaiable
Then:
add manual data to ipg.cop
"""
#Get Input Data
import os
import sys
import json

class updateManualDataOfIpgCop():
    def __init__(self, projectRootPath) -> None:
        self.projectRootPath = projectRootPath
        self.updateProcess()

    def readJsonFile(self):
        # Get Manual Data
        jsonDataFile = os.path.join(self.projectRootPath, 'manual_IpgCop.json')
        with open(jsonDataFile, 'r') as f:
            jsonData = json.loads(f.read())
        return jsonData
    
    def updateMethod(self, location, data):
        remove_pattern = "remove/"
        location = location.replace("\\","/")
        #data to write =
        with open(location,'r+') as ipg_cop:
            print(f">>> Modifying {location}")
            #read content
            content = ipg_cop.read()
            # Pointer to 0
            ipg_cop.seek(0)
            #empty file
            ipg_cop.truncate(0)
            #Content to write
            defaultData = "#User Section"
            addData = []
            removeData = []
            for smData in data:
                if remove_pattern not in smData:
                    if not smData in content:
                        addData = addData + [smData]
                        print(f"[+] Add: {addData}")
                else:
                    removeData = removeData +[smData.replace(remove_pattern,'')]
            addData = addData + [defaultData]
            dataStr = "\n".join(addData)
            content = content.replace(defaultData, dataStr)
            for removeLine in removeData:
                content = content.replace(removeLine,'')
                print(f"[-] Remove: {addData}")
            # write to file
            ipg_cop.write(content)
            #close
            ipg_cop.close()
            print(">>> Done")
        # end
        return 0

    def updateProcess(self):
        # Main Process
        manualData = self.readJsonFile()
        projectPath = self.projectRootPath
        for folderName, manualList in manualData.items():
            absPath = os.path.join(projectPath, "Cantata/tests", folderName, "ipg.cop")
            #convert to list instance
            if isinstance(manualList, list):
                pass
            else:
                manualList = [manualList]
            #Update data
            if os.path.isfile(absPath):
                self.updateMethod(absPath, manualList)
            else:
                pass #No Process
        print("End Of Process Modify ipg.cop ")
        return 0