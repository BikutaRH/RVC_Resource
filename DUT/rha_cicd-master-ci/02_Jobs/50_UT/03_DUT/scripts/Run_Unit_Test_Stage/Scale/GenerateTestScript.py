# -*- coding: utf-8 -*-
""" '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Author:   Tin Nguyen
# Email:    tin.nguyen.uf@renesas.com
# Date:     27-10-2020
# Filename: GenerateTestScript.py
# Project:  Auto DUT CI
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """

""" ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''Begin Import libarary header file'''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """
import logging
import os
import shutil
import json
import glob
import re
from os import sys
from argparse import ArgumentParser
""" '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''End Import libarary header file'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """

""" ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' Begin declare variable ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """


""" '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''End declare variable''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """

""" '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' Begin main class '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """
class testscript:

    File_Get_Wp = "CanttDir.json"
    Path_Cantata = os.getcwd()
    # Path_Workspace_Testapp = "D:/New_repo/internal/Module/pwm/07_UT/01_WorkProduct_D/app/RH850_X2x_PWM_DUT_TestApp" 
    # Project_Testapp = "cfg01"
    def __init__(self, currentProjectPath):
        self.currentProjectPath = currentProjectPath
###################################################################### Begin read_file function ##############################################################
    def read_file(self,Filename):
        Readed_File = open(Filename,"r")
        Text = Readed_File.read()
        Profile_List = Text.split("\n")
        Readed_File.close()
        return Profile_List
####################################################################### End read_file function ###############################################################

################################################################# Begin remove_folder_trash function #########################################################
    def __remove_irrelevant_folders(self,Path_to_Test_Folder,Test_Suite,All_Folder_Cantata):
        print(">>> Begin remove redundant folder ........................................")
        for Folder in All_Folder_Cantata:
            if Folder in Test_Suite:
                None
            else:
                os.system(f"rmdir /s /q \"{Path_to_Test_Folder}/{Folder}\"")
                print("{:<62}{:}".format(f"Deleting {Folder}","Done"))
        print(">>> Remove Done \n")
        return 0
################################################################## End remove_folder_trash function ##########################################################

################################################################ Begin get_source_code_name function #########################################################
    def get_source_code_name(self,Path_to_Testapp,Test_Suite):
        Dict_Source_Code = {}
        List_Source_Code = []
        for Item in Test_Suite:
            for (Dirpath, Dirnames, Filenames) in os.walk(f"{Path_to_Testapp}/{Item}"):
                for Filename in Filenames:
                    if Filename.endswith(".h") or Filename.endswith(".c"):
                        List_Source_Code.append(Filename)
            Dict_Source_Code[Item] = List_Source_Code
            List_Source_Code = []
        return Dict_Source_Code
############################################################## Start Add_Isolate_To_Atest_Generate_By_TableDriven_#############################################    
    def __addIsolateToAtestDriven(self, projectPath):
        atestGenByCantata = f"{projectPath}/Cantata/tests"
        if not os.path.isdir(atestGenByCantata):
            print("JK_ERROR: Cantata Wp is Wrong! No folder Cantata/tests")
            return 0
        def findIsolateComplex(textContent, leftPattern, rightPattetn):
            complexIsolate = re.search(".* ISOLATE_.*\(", textContent)
            listSubString = []
            end_position = 0
            start_position = 0
            while (None != complexIsolate):
                start_position = end_position + complexIsolate.span()[0]
                index = slice(start_position,len(textContent)) # equivalent to [1:] indexing
                subString = textContent[index]
                endIsolate = re.search(rightPattetn, subString)
                if endIsolate:
                    end_position = start_position + endIsolate.span()[1]
                else:
                    pass
                    #print(index)
                listSubString.append((start_position, end_position))
                index = slice(end_position,len(textContent)) # equivalent to [1:] indexing
                subString = textContent[index]
                complexIsolate = re.search(".* ISOLATE_.*\(", subString)
            #print(listSubString)
            listTarget = []
            for indexStr in listSubString:
                index = slice(indexStr[0],indexStr[1])
                ispair = textContent[index]
                leftside = re.findall(leftPattern,ispair)
                rightside = re.findall(rightPattetn,ispair)
                nextSide = indexStr[1]
                flagControll = False
                while(len(leftside) != len(rightside)):
                    newindex = slice(nextSide,len(textContent)) # equivalent to [1:] indexing
                    subString = textContent[newindex]
                    if re.search(rightPattetn, subString):
                        flagControll = True
                        break
                    else:
                        nextSide = nextSide + re.search(rightPattetn, subString).span()[1]
                    index = slice(indexStr[0],nextSide)
                    ispair = textContent[index]
                    leftside = re.findall(leftPattern,ispair)
                    rightside = re.findall(rightPattetn,ispair)
                # Remove all ISOLATE Gen by Table Driven
                if flagControll:
                    continue
                indexRemove = slice(indexStr[0],nextSide)
                contentRemove = textContent[indexRemove]
                listTarget.append(contentRemove)
            return listTarget        
        allFiles = list(os.listdir(atestGenByCantata))
        allFolders = [x for x in allFiles if os.path.isdir(f"{atestGenByCantata}/{x}")]
        currentDir = os.getcwd()
        os.chdir(atestGenByCantata)
        valueDeclareCantata = []
        valueVoidCantata = []
        for atestFolder in allFolders:
            defaultSearch = "#pragma qas cantata ignore off"
            isolateGenByCantata = ''
            with open(f"./{atestFolder}/{atestFolder}.c", 'r', encoding = 'utf-8') as f:
                #print(f.read())
                atest_text = f.read()
                valueDeclareCantata = findIsolateComplex(atest_text, "\(", "\) *;")
                for isolateRemove in valueDeclareCantata:
                    if isolateRemove:
                        atest_text = atest_text.replace(isolateRemove,"")
                    else:
                        pass # Not care null
                #valueVoidCantata = findIsolateComplex(atest_text, "{", "}")
                isolateGenByCantata = valueVoidCantata + valueDeclareCantata
                #print(isolateGenByCantata)
                f.close()
            atestTableDrivenContent = ''
            with open(f"{projectPath}/TableDriven/{atestFolder}/{atestFolder}.c", 'r', encoding = 'utf-8') as f:
                #print(f.read())
                atestTableDrivenContent = f.read()
                f.close
            if len(isolateGenByCantata) > 1:
                valueDeclare = findIsolateComplex(atestTableDrivenContent, "\(", "\) *;")
                simpleIsolateTableDriven = valueDeclare
                
                for isolateRemove in simpleIsolateTableDriven:
                    if isolateRemove:
                        print(f"Removed in {atestFolder}.c Gen By Table Driven: \n",isolateRemove)
                        atestTableDrivenContent = atestTableDrivenContent.replace(isolateRemove,"")
                        pass
                    else:
                        pass # Not care null
                #valueVoid = findIsolateComplex(atestTableDrivenContent, "{", "}")
                simpleIsolateTableDriven = []#valueVoid
                for isolateRemove in simpleIsolateTableDriven:
                    if isolateRemove:
                        print(f"Removed in {atestFolder}.c Gen By Table Driven: \n",isolateRemove)
                        atestTableDrivenContent = atestTableDrivenContent.replace(isolateRemove,"")
                    else:
                        pass # Not care null
                voidList = [defaultSearch] + valueVoidCantata
                print(f"Added in {atestFolder}.c:",'\n'.join(voidList))
                atestTableDrivenContent = atestTableDrivenContent.replace(defaultSearch, '\n'.join(voidList), 1)
                defaultGlobal = "/* Function Call & Dummy Functions */"
                def sortlistViaLoC(listIsolateName):
                    atestTBDriven = atestTableDrivenContent
                    def mapLoc(strValue):
                        searchStr = strValue.split("(")[0]
                        location = re.search(f"{searchStr}\(", atestTBDriven)
                        if None != location:
                            return {strValue:location.span()[0]}
                        else: 
                            return {strValue:1}
                    maptoDict = list(map(lambda x: mapLoc(x), listIsolateName))
                    mergeDict = {}
                    for eachLoc in maptoDict:
                        mergeDict = {**mergeDict, **eachLoc}
                    sortViaLoC = dict(sorted(mergeDict.items(), key=lambda item: item[1]))
                    listSortViaLoC = []
                    for func,LoC in sortViaLoC.items():
                        listSortViaLoC = listSortViaLoC + [func]
                    return listSortViaLoC
                # Group of target lines
                globalList = [defaultGlobal] + valueDeclareCantata
                print(f"Added in {atestFolder}.c Gen By Table Driven:",'\n'.join(globalList))
                atestTableDrivenContent = atestTableDrivenContent.replace(defaultGlobal, '\n'.join(globalList), 1)
                startString = re.search("/\* Function Call & Dummy Functions \*/", atestTableDrivenContent)
                endString = re.search("/\* Global Functions \*/", atestTableDrivenContent)
                if (None != startString and None != endString):
                    startIndex = startString.span()
                    endIndex = endString.span()
                    stringTarget = atestTableDrivenContent[startIndex[1] : endIndex[0]]
                    atestTableDrivenContent = atestTableDrivenContent.replace(stringTarget, "")
                    listOfLines = stringTarget.split("\n")
                    sortedLoc = sortlistViaLoC(listOfLines)
                    globalList = [defaultGlobal] + sortedLoc
                    atestTableDrivenContent = atestTableDrivenContent.replace(defaultGlobal, '\n'.join(globalList), 1)
            else:
                pass
            with open(f"{projectPath}/TableDriven/{atestFolder}/{atestFolder}.c", 'w', encoding = 'utf-8') as f:
                #print(f.read())
                f.write(atestTableDrivenContent)
                f.close        
        return 0
############################################################### End Add_Isolate_To_Atest_Generate_By_TableDriven_#############################################


################################################################ Begin get_source_code_name function ##############################################################
    def copy_source_to_cantata_wp(self,Dict_Source_Code,Path_to_Testapp,Path_to_Cantata_Folder):
        for Folder, Files in Dict_Source_Code.items():
            for Item in Files:
                shutil.copy2(f"{Path_to_Testapp}/{Folder}/{Item}", f"{Path_to_Cantata_Folder}/{Folder}")
                print("{:<62}{:}".format(f"Copying {Item}",f"to {Folder}"))
        print(">>> Copy Done.")
        return 0
################################################################# End get_source_code_name function ################################################################

################################################################# Begin create_testsuite function ##################################################################
    def create_testsuite(self,Test_Suite):
        textfile = os.path.join(self.currentProjectPath, "CanttTestSuite.txt")
        with open(textfile, "w") as Txt_File:
            Test_Suite = list(Test_Suite)
            for Count in range(0,len(Test_Suite)-1):
                Txt_File.write(f"{Test_Suite[Count]}\n")
            Txt_File.write((f"{Test_Suite[-1]}"))
            print(">>> File CanttTestSuite.txt is updated.")
        return 0
################################################################## End create_testsuite function ###################################################################

################################################################ Begin get_dirname_folder function #################################################################
    def get_dirname_in_folder(self,Path_to_Test_Folder):
        Dirnames=[]
        for (Dirpath, Dirnames, Filenames) in os.walk(Path_to_Test_Folder):
            break
        return Dirnames
        
################################################################# End get_dirname_folder function ##################################################################

############################################################# Begin get_path_project_folder function ###############################################################
    def get_path_project_folder(self,Dict_Json):
        for Keys, Values in Dict_Json.items():
            if Keys == "Cantata":
                for Key, Value in Values.items():
                    if Key == "Workspace":
                        Path_Workspace = Value
                    if Key == "Project":
                        Project_Folder = Value
        Path_to_Project_Folder = f"{Path_Workspace}/{Project_Folder}"
        return Path_Workspace , Path_to_Project_Folder
############################################################ End get_path_project_folder function ##################################################################

################################################################# Begin read_file_json function ####################################################################
    def __read_file_json(self,Filename):
        Dict_Json = {}
        try:
            with open(Filename,"r") as Json_File:
                Dict_Json = json.load(Json_File)
                Json_File.close()
        except FileNotFoundError:
            print(f">>> File {Filename} does not exist.")
            exit()
        return Dict_Json
################################################################# End read_file_json function #################################################################

############################################################### Begin modify_makefile function ################################################################
    def modify_makefile(self, Path_to_Cantata_Folder,Test_Suite):
        Profile_List_Makefile = []
        Count = 0
        try:
            with open(f"{Path_to_Cantata_Folder}/Makefile","r") as Makefile: 
                print(">>> Begining generate Makefile ..................................................")
                Makefile.close()
            Profile_List_Makefile = self.read_file(f"{Path_to_Cantata_Folder}/Makefile")
            ## Find top and bottom ##
            List_Boundary_TS = []
            for Count in range(0,len(Profile_List_Makefile)):
                if Profile_List_Makefile[Count].rfind("ALL_TESTS :=",0,len(Profile_List_Makefile[Count])-1) != -1 or \
                    Profile_List_Makefile[Count].rfind("NUMBER_OF_TESTS :=",0,len(Profile_List_Makefile[Count])-1) != -1:
                    List_Boundary_TS.append(Count)
            # print(List_Boundary_TS)

            ## List contains new information to modify into Makefile ##
            List_New_to_Modify = []
            for Count in range(0,len(Test_Suite)):
                if Count == 0 or Count == len(Test_Suite) - 1:
                    if Count == 0:
                        List_New_to_Modify.append(f"ALL_TESTS := {Test_Suite[Count]} \\")
                    else:
                        List_New_to_Modify.append(f"             {Test_Suite[Count]}\n")
                        List_New_to_Modify.append(f"NUMBER_OF_TESTS := {len(Test_Suite)}")
                else:
                    List_New_to_Modify.append(f"             {Test_Suite[Count]} \\")
            ## Write to Makefile ##
            with open(f"{Path_to_Cantata_Folder}/Makefile","w") as Makefile:
                for Count in range(0,List_Boundary_TS[0]):
                    Makefile.write(f"{Profile_List_Makefile[Count]}\n")
                for Item in List_New_to_Modify:
                    Makefile.write(f"{Item}\n")
                for Count in range(List_Boundary_TS[1] + 1, len(Profile_List_Makefile)-1):
                    Makefile.write(f"{Profile_List_Makefile[Count]}\n")
                Makefile.close()
            print(">>> Generate Makefile DONE!")
            ## End write ##
        except FileNotFoundError:
            print("Makefile does not exist or accessible.")
        return 0

############################################################## Begin Generate TestSuit Function ###############################################################
    def generate_testsuite_file(self):
        File_Test = "Cantata/tests"
        print(">>> Begining generate test suite list file ......................................")
        ## Get all folder in Cantata Workspace folder ##
        Path_to_Cantata_Folder = f"{self.currentProjectPath}/{File_Test}"

        ## Find test suite in Cantata/tests of Project
        Test_Suite = self.get_dirname_in_folder(Path_to_Cantata_Folder)

        ## create TestSuite.txt ##
        self.create_testsuite(Test_Suite)

        ## Modify makefile ##
        #self.modify_makefile(Path_to_Cantata_Folder,Test_Suite)

    def generate_test_app(self, Path_to_Project_Folder):
        File_Test = "Cantata/tests"
        ## Get all folder in Cantata Workspace folder ##
        Path_to_Cantata_Folder = f"{Path_to_Project_Folder}/{File_Test}"
        All_Folder_Cantata = self.get_dirname_in_folder(Path_to_Cantata_Folder)
        
        ## Get all folder in Testapp ##
        # Split due to config name format <device>_<config_number>
        Path_to_Testapp = f"{Path_to_Project_Folder}/TableDriven"
        All_Folder_Testapp = self.get_dirname_in_folder(Path_to_Testapp)
        ## Get same folder and remove trash folder ##
        Same_Folder = set(All_Folder_Testapp) & set(All_Folder_Cantata)
        Same_Folder = list(Same_Folder)

        ## delete redundant folder ##
        #self.__remove_irrelevant_folders(Path_to_Cantata_Folder,Same_Folder,All_Folder_Cantata)
        print(">>> Begin copy ISOLATE_FUNC_Generated_By_Cantata To Atest Table Driven....")
        self.__addIsolateToAtestDriven(Path_to_Project_Folder)
        ## Copy testapp is generated from TableDriven to Cantata test
        print(">>> Begin copy test app to Cantata Workspace..............................")
        Dict_Source_Code = self.get_source_code_name(Path_to_Testapp, Same_Folder)
        self.copy_source_to_cantata_wp(Dict_Source_Code, Path_to_Testapp, Path_to_Cantata_Folder)



    

############################################################### End Generate TestSuit Function ################################################################

############################################################## End modify_makefile function ###################################################################

""" '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' End main class ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """

""" ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''Begin main function'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """
# def main():
#     ## Declare list and variable ##
#     Dict_Json = {}
#     Path_to_Project_Folder = ""
#     Profile_List_Ipg = []
#     Test_Suite = []
#     File_Test = "Cantata/tests"
#     All_Folder_Cantata = []
#     Dict_Source_Code = {}

#     #Get path of workspace and project#
#     Dict_Json = read_file_json(f"{Path_Cantata}/{File_Get_Wp}")
#     Path_to_Project_Folder = get_path_project_folder(Dict_Json)
#     ##End path of workspace and project ##

#     ## Get all folder in Cantata Workspace folder ##
#     Path_to_Cantata_Folder = f"{Path_to_Project_Folder}/{File_Test}"
#     All_Folder_Cantata = get_dirname_in_folder(Path_to_Cantata_Folder)

#     ## Get all folder in Testapp ##
#     Path_to_Testapp = f"{Path_Workspace_Testapp}/{Project_Testapp}/{File_Test}" 
#     All_Folder_Testapp = get_dirname_in_folder(Path_to_Testapp)

#     ### Step 1: copy from TDB to Cantata and Remove irrelevant folder ###
#     ## Get same folder and remove trash folder ##
#     Same_Folder = set(All_Folder_Testapp) & set(All_Folder_Cantata)
#     Same_Folder = list(Same_Folder)
#     ### ---> remove irrelevant folder ###
#     remove_irrelevant_folders(Path_to_Cantata_Folder,Same_Folder,All_Folder_Cantata)   
#     ## copy to Cantata WorkSpace ##
#     Dict_Source_Code = get_source_code_name(Path_to_Testapp,Same_Folder)
#     copy_to_cantata_wp(Dict_Source_Code,Path_to_Testapp,Path_to_Cantata_Folder)
#     ## End copy ##
#     ### End Step 1 ###

#     ### Step 2: Export testsuite.txt file ###
#     ## Find test suite ---> read all folder in Cantata/tests of Project ##
#     Test_Suite = get_dirname_in_folder(Path_to_Cantata_Folder)
#     ## create TestSuite.txt ##
#     create_testsuite(Test_Suite)
#     ## end create ##
#     ### End Step 2 ###

#     ### Step 3: Modify Makefile in Cantata folder ###
#     ## Modify makefile ##
#     modify_makefile(Path_to_Cantata_Folder,Test_Suite)
#     ## End modify ##
#     ### End Step 3 ###
""" ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''End main function''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """
# if __name__ == "__main__":
#     main()
# testscript = testscript()
# testscript.generate_test_app("U2A16","CFG01")
