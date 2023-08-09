import glob
from scripts.Global_Properties import Global_Properties
import InitWorkspace
import json
import os
import traceback
import shutil
from pathlib import Path
jobProperties = Global_Properties()
class DUT_Preparation():
    def __init__(self):
        self.initalCantataWorkspace()
        self.removeRedundantSourceEachConfig()

    def readCanttDir(self):
        """
        Read CanttDir.json -> Dic
        """
        # This line just record for your understanding only
        templateOfDic = jobProperties.templateCantataDir
        jsonDataFile = jobProperties.targetCantataDir
        with open(jsonDataFile, 'r') as f:
            allConfigs = json.load(f)
        return allConfigs

    def cloneTableDrivenToConfig(self, configNumber, microSubVariant):
        targetProjectPath = os.path.join(jobProperties.cantataDUT_RootWorkspace, f"{microSubVariant}_{configNumber}", "TableDriven")
        tableDrivenPath = f"{jobProperties.cantataDUT_RootWorkspace}/TableDriven"
        if os.path.isdir(targetProjectPath):
            shutil.rmtree(tableDrivenPath)
        all_atestFiles = glob.glob(f"{tableDrivenPath}/**/atest_*.c", recursive=True)
        relatedAtest = [Path(x).parent.parent for x in all_atestFiles if
                        configNumber.lower() in x.lower() and microSubVariant.lower() in x.lower()]
        relatedAtest = list(set(relatedAtest))
        if len(relatedAtest) == 1:
            shutil.copytree(relatedAtest[0], targetProjectPath)


    def getDriverSourceOfConfig(self, configNumber, microSubVariant):
        """
        This method will extract driver source under 1 config
        """
        tableDrivenPath = f"{jobProperties.cantataDUT_RootWorkspace}/TableDriven"
        all_atestFiles = glob.glob(f"{tableDrivenPath}/**/atest_*.c", recursive=True)
        relatedAtest = [os.path.basename(x) for x in all_atestFiles if configNumber.lower() in x.lower() and microSubVariant.lower() in x.lower()]
        return [x.replace("atest_", "") for x in relatedAtest]

    def removeRedundantSourceEachConfig(self):
        jsonData = self.readCanttDir()
        allConfigs = jsonData["hw_ip"][jobProperties.moduleRunning.capitalize()]
        for microSub, configDic in allConfigs.items():
            for configName in list(configDic.keys()):
                projectPath = os.path.join(jobProperties.cantataDUT_RootWorkspace, f"{microSub}_{configName}")
                relatedSource = self.getDriverSourceOfConfig(configName, microSub)
                driverCFile = glob.glob(f"{projectPath}/src/*.c")
                for file in driverCFile:
                    fileName = os.path.basename(file)
                    if fileName not in relatedSource:
                        os.remove(file)
                self.cloneTableDrivenToConfig(configName, microSub)
        return 0

    def initalCantataWorkspace(self):
        """
        Return: List of DUT project path of each config
        This function will remove all folder which is used for running this job
        Clone Cantata template to each config
        Clone Coverage source to workspace
        """
        jsonData = self.readCanttDir()
        rootProject = jsonData["Cantata"]["Workspace"]
        allConfigs = jsonData["hw_ip"][jobProperties.moduleRunning.capitalize()]
        # Prepare step for coverage report
        input_Cfg_Path = f"{jobProperties.cantataDUT_RootWorkspace}/{jobProperties.moduleRunning}_TestLog"
        if os.path.isdir(input_Cfg_Path):
            shutil.rmtree(input_Cfg_Path, ignore_errors=True)
        shutil.copytree(jobProperties.coverageReportSource, input_Cfg_Path)
        # Loop all target value, remove folder if exist and create an empty target dirrectory
        for microSub, configDic in allConfigs.items():
            for configName in list(configDic.keys()):
                Project_Name = f"{microSub}_{configName}"
                projectPath = os.path.join(rootProject, f"{microSub}_{configName}")
                if os.path.isdir(projectPath):
                    shutil.rmtree(projectPath, ignore_errors=True)
                os.makedirs(projectPath)
                self.copyProjectTemplate(projectPath)
                print(f">>> Current Project is: {Project_Name}")
                # ## Update Cantata option file
                if os.path.exists(f"{jobProperties.cantataDUT_RootWorkspace}/{Project_Name}/ipg.cop"):
                    Cantata_Workspace = InitWorkspace.workspace(jobProperties.targetCantataDir, projectPath, jobProperties.moduleRunning, Project_Name)
                    Cantata_Workspace.generate_cantata_option_file()
                    Cantata_Workspace.generate_makefile_targets()
                    Cantata_Workspace.copy_project_source_file(microSub, configName)
                    print(">>> Add Project to Coverage Test Result Workspace.")
                    ## Add CFGxx to input in CTR WorkspaceWorkspace
                    self.init_cmt_cfg(Project_Name)
                else:
                    print("Please Add Workspace Before Add Project. Thank you!")
        return 0

    def copyProjectTemplate(self, projectPath):
        cantataTemplate = jobProperties.templateCantataProject
        for file in glob.glob(f'{cantataTemplate}/*'):
            shutil.copy(file, projectPath)
        for file in glob.glob(f'{cantataTemplate}/.*'):
            shutil.copy(file, projectPath)
        return 0

    def init_cmt_cfg(self, CfgName):
        ## Create folder CFGxx to contain .doc and .ctr file
        envRootPath = f"{jobProperties.cantataDUT_RootWorkspace}/{jobProperties.moduleRunning}_TestLog/Env"
        input_Cfg_Path = f"{envRootPath}/{jobProperties.moduleRunning}/input/{CfgName}"
        if os.path.exists(input_Cfg_Path):
            try:
                shutil.rmtree(input_Cfg_Path, ignore_errors=True)
            except:
                traceback.print_exc()
                exit()
        try:
            os.makedirs(input_Cfg_Path)
            print(f">>> Create folder {input_Cfg_Path} Successfully.")
        except:
            traceback.print_exc()

        input_Cfg_Path = f"{envRootPath}/{jobProperties.moduleRunning}/ctr_log"
        try:
            os.makedirs(input_Cfg_Path)
            print(f">>> Create folder {input_Cfg_Path} Successfully.")
        except:
            print("ctr_log folder is already exist!")

        input_Cfg_Path = f"{envRootPath}/{jobProperties.moduleRunning}/log"
        try:
            os.makedirs(input_Cfg_Path)
            print(f">>> Create folder {input_Cfg_Path} Successfully.")
        except:
            print("log folder is already exist!")

        input_Cfg_Path = f"{envRootPath}/{jobProperties.moduleRunning}/result"
        try:
            os.makedirs(input_Cfg_Path)
            print(f">>> Create folder {input_Cfg_Path} Successfully.")
        except:
            print("result folder is already exist!")
        return 0

def main():
    # Only call this class.
    # The init stage will do kind of works!
    DUT_Preparation()
    # Done
    return 0

if __name__ == '__main__':
    main()
