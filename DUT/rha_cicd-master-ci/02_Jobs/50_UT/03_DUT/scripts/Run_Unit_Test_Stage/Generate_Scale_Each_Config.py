import os.path

from scripts.Global_Properties import Global_Properties
from jinja2 import Environment, FileSystemLoader
import json
import shutil
from pathlib import Path
# Global params
jobProperties = Global_Properties()
allProjects = {}
class Scale():
    def __init__(self, projectConfigPath, countIndex):
        self.projectConfigPath = projectConfigPath
        self.countIndex = countIndex
    def copyTemplateToConfig(self):
        """
        Copy all Scale Template File to Target Config Then Call Render.
        """
        targetPath = os.path.join(self.projectConfigPath, "Scale")
        if os.path.isdir(targetPath):
            shutil.rmtree(targetPath)
        shutil.copytree(jobProperties.scaleTemplatePath, targetPath)
        return 0

    def renderBatchTemplate(self):
        global allProjects
        """
        This method will re-generate template to target value,
        please note that the output should be inside the config
        loop through the configs, each 2(two) configs will have
        same batch script name. To support multiple threads!
        Example:
            V4H_CFG01 : + Cantata
                        + Scale :
                            - RunScale_1.bat
            V4H_CFG02 : + Cantata
                        + Scale :
                            - RunScale_1.bat
            V4H_CFG03 : + Cantata
                        + Scale :
                            - RunScale_2.bat
        """
        # For batch script
        """
        1, 2, 3, 4,
        --> 1, 1, 2, 2"""
        batchTemplate = os.path.join(self.projectConfigPath, "Scale")
        # this setting will support for parralel mode when using multiple threads
        if 0 == self.countIndex % 2:
            subIndex = int(self.countIndex / 2)
        else:
            subIndex = int((self.countIndex + 1) / 2)
        batchOutput = os.path.join(self.projectConfigPath, "Scale", f"RunScale_{subIndex}.bat")
        env = Environment(loader=FileSystemLoader(batchTemplate))
        template = env.get_template("Run_One_Project.bat")
        autoTestCantataPath = os.path.join(self.projectConfigPath, "Scale")
        # Format for batch script
        autoTestCantataPath = autoTestCantataPath.replace("/", "\\")
        outputParsed = template.render(Cantata_AutoTest_File=".\\Cantata_AutoTest_CLI.py", Batch_Script_Path=autoTestCantataPath)
        with open(batchOutput, "w") as f:
            f.write(outputParsed)
        os.remove(os.path.join(batchTemplate, "Run_One_Project.bat"))
        return batchOutput

    def renderPythonTemplate(self):
        pythonTemplatePath = os.path.join(self.projectConfigPath, "Scale")
        pythonOutput = os.path.join(pythonTemplatePath, "Cantata_AutoTest_CLI.py")
        env = Environment(loader=FileSystemLoader(pythonTemplatePath))
        template = env.get_template("Cantata_AutoTest_CLI.py")
        cantataProjectRootPath = os.path.join(self.projectConfigPath)
        # Format for python file
        cantataProjectRootPath = cantataProjectRootPath.replace("\\", "/")
        outputParsed = template.render(PROJECT_PATH_CONFIG=cantataProjectRootPath)
        with open(pythonOutput, "w") as f:
            f.write(outputParsed)
        return 0

class modifyIpgCopFile():
    def __init__(self, moduleRunning, project, microSubVar, configNumber) -> None:
        self.moduleRunning = moduleRunning.lower()
        self.project = project.upper() # X2x, Gen4, SML, ...
        self.microSubVar = microSubVar.upper() # micro sub variant S4_G4MH, U2A16, ...
        self.configNumber = configNumber.upper()
        self.dumpJsonToConfig()

    def readJsonTargetConfig(self):
        manualRecordFile = os.path.join(jobProperties.jobWorkSpace,'scripts', 'Run_Unit_Test_Stage', 'manualUpdateIPG_COP.json')
        with open(manualRecordFile, 'r') as f:
            jsonDataBase = json.loads(f.read())
        currentProject = jsonDataBase.get(self.project)
        if None == currentProject:
            return {}
        currentSubVar = currentProject.get(self.microSubVar)
        if None == currentSubVar:
            return {}
        currentModule = currentSubVar.get(self.moduleRunning, {})
        currentConfig = currentModule.get(self.configNumber, {})
        return currentConfig
    
    def dumpJsonToConfig(self):
        rootWorkSpace = jobProperties.cantataDUT_RootWorkspace
        projectPath = os.path.join(rootWorkSpace, f"{self.microSubVar}_{self.configNumber}")
        configPath = os.path.join(projectPath, "manual_IpgCop.json")
        manualData = self.readJsonTargetConfig()
        with open(configPath, 'w') as f:
            json.dump(manualData, f)
        return


def main():
    """
    This function will execute the workflow.
    """
    # record dict
    recordDic = {}
    # Get all target value, which is used in current job
    jsonDataFile = jobProperties.targetCantataDir
    with open(jsonDataFile, 'r') as f:
        dataOfCurrentJob = json.loads(f.read())
    targetConfig = dataOfCurrentJob['hw_ip'][jobProperties.moduleRunning.capitalize()]
    rootWorkSpace = jobProperties.cantataDUT_RootWorkspace
    # Loop all values and execute target value
    count = 1
    # Copy scale and render template
    for microSubName, configDic in targetConfig.items():
        for configName in list(configDic.keys()):
            projectPath = os.path.join(rootWorkSpace, f"{microSubName}_{configName}")
            copyScale = Scale(projectPath, count)
            copyScale.copyTemplateToConfig()
            batFile = copyScale.renderBatchTemplate()
            batchName = os.path.basename(batFile)
            currentValue = recordDic.get(batchName)
            if None == currentValue:
                currentValue = []
            currentValue.append(batFile)
            recordDic[batchName] = currentValue
            copyScale.renderPythonTemplate()
            modifyIpgCopFile(jobProperties.moduleRunning, jobProperties.projectName, microSubName, configName)
            count = count + 1
    # Dump record dict to record file.
    jsonRecordFile = os.path.join(jobProperties.jobWorkSpace, "All_Scale.json")
    with open(jsonRecordFile, 'w') as f:
        json.dump(recordDic, f)
    return 0

# Call Main Function only
if __name__ == "__main__":
    main()