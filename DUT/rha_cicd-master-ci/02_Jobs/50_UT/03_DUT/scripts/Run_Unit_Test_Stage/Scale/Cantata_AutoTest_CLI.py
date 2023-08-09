import glob
import os
import subprocess
import time
from GenerateTestScript import testscript
from updateIPG_COP import updateManualDataOfIpgCop

class CantataCLI():
    def __init__(self, ProjectPath, Project_Name):
        self.Project_Name = Project_Name
        self.ProjectPath = ProjectPath

    def cleanCantataProject(self):
        # python38 -u CanttCmd.py -c all
        print('>>> Processing clean file ...................................................')
        if os.path.exists(f"{self.ProjectPath}/Debug/src"):
            List_File = glob.glob(f"{self.ProjectPath}/Debug/src/*")
            for File in List_File:
                os.remove(File)
                print(f">>> Clean {os.path.basename(File):<62} Done")
            print('>>> Clean Project Done!')
        else:
            print('>>> Folder "src" does not exits!')
        return 0

    def buildCantataProject(self):
        # check_canttdir()
        ## Get current direction and change to cantata
        Src_File_List = glob.glob(f"{self.ProjectPath}/src/*.c")
        print('>>> Processing Build Project ....................................................')
        ## Create folder Debug
        if os.path.exists(f"{self.ProjectPath}/Debug"):
            if os.path.exists(f"{self.ProjectPath}/Debug/src") is False:
                os.mkdir((f"{self.ProjectPath}/Debug/src"))
        else:
            os.mkdir((f"{self.ProjectPath}/Debug"))
            os.mkdir((f"{self.ProjectPath}/Debug/src"))

        ##
        for Src_File in Src_File_List:
            # Get name of file from char '\' to char '.' , dont't get extern file
            # print( Src_File)
            Name_File = Src_File[Src_File.rfind('\\', 0, len(Src_File)) + 1: len(Src_File)].split('.', 1)
            ##
            commandOutput = subprocess.getoutput(f"ipg_comp --optfile {self.ProjectPath}/ipg.cop gcc -D__interrupt= \
                       -IC:/qa_systems/cantata/inc -I{self.ProjectPath}/include \
                           -I{self.ProjectPath}/src -O0 -g3 -Wall -c -fmessage-length=0 \
                               -o {self.ProjectPath}/Debug/src/{Name_File[0]}.o {Src_File}")
            while ("All licensing tokens" in commandOutput):
                print("On-going check Cantata license is exist or not!")
                time.sleep(100)  # sleep 100s then check again Cantata cycle is 300s
                commandOutput = subprocess.getoutput(f"ipg_comp --optfile {self.ProjectPath}/ipg.cop gcc -D__interrupt= \
                           -IC:/qa_systems/cantata/inc -I{self.ProjectPath}/include \
                               -I{self.ProjectPath}/src -O0 -g3 -Wall -c -fmessage-length=0 \
                                   -o {self.ProjectPath}/Debug/src/{Name_File[0]}.o {Src_File}")
            print(commandOutput)
        print('>>> Build Project Done!')

    def generateTestScriptAuto(self):
        """
        :: Generate Auto Test Script With Source Name is Defined By TB Driven
        :: Limit Function Test Time is 120s
        python38 -u CanttCmd.py -g test_script_sourceC_NameBy_TBDriven  %%d
        """
        workSpace = self.ProjectPath
        allCFiles = glob.glob(f"{workSpace}/src/*.c")
        allCFileName = [os.path.basename(x) for x in allCFiles]
        for cName in allCFileName:
            cName = cName.replace(".c", "")
            print(f'>>> Processing Generating Test Script For {cName} ........')
            # -Dosgi.locking=None is used to resolve locking resource of Java Framwork!
            cmdCall = f"cantppc.exe -Duser.home={workSpace}_metadata -Xmx2G\
                        -application com.ipl.products.eclipse.cantpp.testscript.CommandLineTestGenerator \
                        -noSplash -data {workSpace}_metadata sourceFile=\"src\\{cName}.c\" \
                        baseLocation=\"{workSpace}\" \
                        testscriptName=\"atest_{cName}\" makefileEnabled \
                        overwrite coverageRuleset=\"Report all Metrics\" \
                        timeLimit=1 \
                        testCases=AUTO_TESTS stubWrap"
            command_output = subprocess.getoutput(cmdCall)
            while ("All licensing tokens" in command_output):
                print("On-going check Cantata license is exist or not!")
                time.sleep(100)  # sleep 100s then check again Cantata cycle is 300s
                command_output = subprocess.getoutput(cmdCall)
            print(command_output)
        print('>> Generate Test Script Done!')
        return 0

    def rebuildCantataProject(self):
        print('>>> Processing Rebuild All Test Suite ..........................................')
        currentDir = os.getcwd()
        workSpace = self.ProjectPath.replace("\\", "/")
        os.chdir(f"{workSpace}/Cantata/tests")
        subprocess.getoutput("make CONFIG=x86-Win32-gcc8.2-bundled clean")
        command_output = subprocess.getoutput("make CONFIG=x86-Win32-gcc8.2-bundled EXECUTE=1 VERBOSE=2 OUTPUT_TO_CONSOLE=1 all")
        while ("All licensing tokens" in command_output):
                    print("On-going check Cantata license is exist or not!")
                    time.sleep(100) # sleep 100s then check again Cantata cycle is 300s
                    subprocess.getoutput("make CONFIG=x86-Win32-gcc8.2-bundled clean")
                    command_output = subprocess.getoutput(
                        "make CONFIG=x86-Win32-gcc8.2-bundled EXECUTE=1 VERBOSE=2 OUTPUT_TO_CONSOLE=1 all")
        print(command_output)
        print('>>> Rebuild All Test Suite Done!')

def main():
    # Test - This value will be changed by jinja2 tool
    projectFolder = '{{ PROJECT_PATH_CONFIG }}' #"C:\\Workspace\\CantataWorkspace\\V4H_CFG22"
    configNameOfCurrentProject = os.path.basename(projectFolder)
    # init main object
    cantata = CantataCLI(projectFolder, configNameOfCurrentProject)
    # Prepare DUT Project, which is generated automatically by Cantata
    #### Step 1: Clean Project - make clean only 
    cantata.cleanCantataProject()
    #### Step 2: Build Driver Source with target setting
    cantata.buildCantataProject()
    #### Step 2: generate automation test script with target setting
    cantata.generateTestScriptAuto()
    #Modify ipg.cop if any
    updateManualDataOfIpgCop(projectFolder)
    # Clone test script, which is generated by Table Driven (excel -> test script)
    ### Step 1: Create an initial object for target project
    testscriptManual = testscript(projectFolder)
    ### Step 2: Clone test script to Test project
    testscriptManual.generate_test_app(projectFolder)
    ### Step 3: Just generate an text file - for recording only!
    testscriptManual.generate_testsuite_file()
    ### Step 4: Call unit test and Get test report (*.ctr (check coverage result) and *.csi (build data), *.cpl (check pre-combine macro))
    cantata.rebuildCantataProject() 
    # Remove un-used objects
    del testscriptManual
    del cantata
    return 0
# Call main process
if __name__ == "__main__":
    main()
