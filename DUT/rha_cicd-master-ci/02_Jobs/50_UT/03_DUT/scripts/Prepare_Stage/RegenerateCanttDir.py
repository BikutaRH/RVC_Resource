#!/usr/bin/env python38
#!c:/Python38/python38.exe
# -*- coding: utf-8 -*-

################################################################################
### Module   = RegenerateCanttDir.py                                         ###
### Author   = TruongPham                                                    ###
### Date     = 10/28/2021                                                    ###
###                     Revision History                                     ###
###                                                                          ###
###  1.0.0: 10/28/2021  : Initial version.                                   ###
################################################################################
###                       Import section                                     ###
################################################################################

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import traceback
from glob import glob
from pycicd.logger.ci_logger import ci_logger
import xml.etree.ElementTree as ET
from pathlib import Path
import pycicd
import shutil
from scripts.Global_Properties import Global_Properties

################################################################################
###                       Global Variables deffition                         ###
################################################################################
jobProperty = Global_Properties()
projectInfor = pycicd.ProjectInfo(jobProperty.projectNumberOption, jobProperty.subProjectOption, jobProperty.repoLocalPath)
glbWorkSpace = jobProperty.jobWorkSpace
CI_LOGGER = ci_logger('DUT Prepare Stage').logger
# Global var for variant name

################################################################################
###                       Classes deffition                                  ###
################################################################################
def recurse_tree_find_deviceName(node):
        """
        This function support to find elements contain short name as input.
        Using yield to reduce memory
        if not any you can not parse any value via next(obj)
        """
        module_Running = jobProperty.moduleRunning
        if "Cdd" in module_Running:
            module_Running = "Cdd" + module_Running.replace("Cdd", "").capitalize()
        detectedString = f"/{module_Running}DeviceName"
        for child in list(node):
            if detectedString.lower() in str(child.text).lower():
                yield node
            if (len(list(child)) > 0):
                yield from recurse_tree_find_deviceName(child)

def getDeviceName(arxml_file) -> str:
        """
        This function support to gererate a dict with format
        {tagName : value of tag} for entire node
        """
        arxmlPath = arxml_file
        deviceName = []
        autosarStandardXML = ET.parse(arxmlPath)
        nodeContainShortName = recurse_tree_find_deviceName(autosarStandardXML.getroot())
        specialString = '{http://autosar.org/schema/r4.0}'
        for value in nodeContainShortName:
            for tag in list(value):
                if not "/" in str(tag.text):
                    deviceName.append(tag.text)
        deviceName = list(set(deviceName))
        if len(deviceName) == 1:
            return deviceName[0]
        else:
            CI_LOGGER.error(f"JK_ERROR: Could not parse device name for arxml file {arxml_file} current value {deviceName}")
        return "Unknown"

def ArchiveTestApp(DirTestApp, DirZipFile):
    """Function to archive Test App"""
    try:
        subprocess.run(
            f'7z x -y {DirZipFile} -o{DirTestApp}', check=True)
    except subprocess.CalledProcessError as e:
        traceback.print_exc()
        print(e.stderr)
        CI_LOGGER.error('[x] JK_ERROR: Error when extract DUT .zip result')

def SearchDevice(File):
    """Function to search devicename in <msn>_Cfg.h file
        Return: Micro Sub Variant value
    """
    DeviceName = None
    try:
        with open(File, "r") as datafile:
            Data = datafile.read()
        # Expected value is: RTM8RC79FG or R7F7...
        targetValue = re.search(
            "/\*\s*Devices: +(\S*)\s*\*/", Data)
        if None != targetValue:
            DeviceName = targetValue.group(1)
    except Exception as e:
        print('[+] Exception: ', e)
        sys.exit(1)
    if None != DeviceName:
        # Expected: V4H, S4_CR52, U2A16, ....
        deviceInfor = projectInfor.get_sub_variant_data(DeviceName)
        if None != deviceInfor:
            return deviceInfor.SubVariantName
        else:
            return "Unknown"
    else:
        CI_LOGGER.error(f"JK_Error: Can not find your device name {DeviceName} in {File}")
        return "Unknown"

def getRelatedConfigs():
    """
    Get all config path which contain device name of Micro Sub Variant when job running.
    Micro Sub Get From: MICRO_SUB_VARIANT in jenkin interface
    """
    validConfigs = {}
    extractTestZip()
    userInputMicroSub = jobProperty.microSubOption
    listMicroSub = userInputMicroSub.split(',')
    # init dic with empty list value
    for microS in listMicroSub:
        validConfigs[microS] = []
    scanPath = jobProperty.TestAppPath
    Module_Running = jobProperty.moduleRunning
    if "Cdd" in Module_Running:
        Module_Running = "CDD_" + Module_Running.replace("Cdd", "").capitalize()
    allConfigs = glob(f'{scanPath}/**/{Module_Running}_Cfg.h', recursive=True)
    for config in allConfigs:
        microSubOfFile = SearchDevice(config)
        if microSubOfFile in listMicroSub:
            validConfigs[microSubOfFile].append(config)
    willExit = False
    for key,value in validConfigs.items():
        if len(value) > 0:
            pass
        else:
            CI_LOGGER.error(f"JK_ERROR: Can not find any config files at {scanPath} related to your input {key}")
            willExit = True
    if willExit:
        sys.exit(1)
    return validConfigs


def getRelatedArxmlConfigs():
    """
    get all arxml file which is using for target micro sub of user Input
    """
    validArxmlConfigs = {}
    userInputMicroSub = jobProperty.microSubOption
    listMicroSub = userInputMicroSub.split(',')
    # init dic with empty list value
    for microS in listMicroSub:
        validArxmlConfigs[microS] = []
    scanPath = jobProperty.TestConfigPath
    allConfigs = glob(f'{scanPath}/**/*.arxml', recursive=True)
    for config in allConfigs:
        deviceOfArxml = getDeviceName(config)
        # Expected: V4H, S4_CR52, U2A16, ....
        microSubOfFile = projectInfor.get_sub_variant_data(deviceOfArxml)
        if microSubOfFile.SubVariantName in listMicroSub:
            validArxmlConfigs[microSubOfFile.SubVariantName].append(config)
    willExit = False
    for key, value in validArxmlConfigs.items():
        if len(value) > 0:
            pass
        else:
            CI_LOGGER.error(f"JK_ERROR: Can not find any config files at {scanPath} related to your input {key}")
            willExit = True
    if willExit:
        sys.exit(1)
    return validArxmlConfigs

def convertToTargetPath(file):
    """
    This function will convert file path to target:
        + If arxml -> just get parrent path
        + If zip file -> return UT project path of config
    """
    if ".arxml" in file:
        return Path(file).parent.absolute()
    appPath = jobProperty.TestAppPath
    appPath = appPath.replace("\\", "/")
    filePath = file.replace("\\", "/")
    filePath = filePath.replace(appPath, "").split("/")
    # app/zipName/ProjectFolder
    return os.path.join(appPath, filePath[1], filePath[2])


def extractConfig(listValue):
    """
    Return format: {configNumber : path}
    """
    targetDic = {}
    # Pre-process format
    listValue_pre = [x.lower().replace("_", "") for x in listValue]
    # '.*(cfg\d+).*'
    configInList = [re.search(".*(cfg\d+).*", x).group(1) for x in listValue_pre if None != re.search(".*(cfg\d+).*", x)]
    if not len(configInList) == len(listValue_pre):
        strangeListIndex = [listValue_pre.index(x) for x in configInList if x not in listValue_pre]
        pathList = [listValue[i] for i in strangeListIndex]
        CI_LOGGER.error(f"JK_ERROR: Found Strange Config of Module Input {pathList}")
        sys.exit(1)
    # pre-format cfg \d\d
    onlyNumber = [x.replace('cfg', '') for x in configInList]
    formatNumber = [f'CFG{"{:0>2d}".format(int(x))}' for x in onlyNumber]
    # User Input
    targetConfigOfUser = jobProperty.dutConfigOption
    if not "ALL_CFG" in targetConfigOfUser:
        formatNumber = [x for x in formatNumber if x in targetConfigOfUser]
    # Retry value with format {CFG01: realPath}
    for index,cfgFormat in enumerate(formatNumber):
        # As we verify len of list will not change when convert to list of cfg string only
        realPath = listValue[index]
        targetDic[cfgFormat] = convertToTargetPath(realPath)
    return targetDic

def confirmationStep(zipConfig, arxmlConfig):
    """
    This method only confirm redundant input of user. And
    All config in zip file should exist an arxml path corresponding.
    """
    userTargetConfig = jobProperty.dutConfigOption.split(',')
    userTargetMicroSub = jobProperty.microSubOption.split(',')
    combineList = []
    for config in userTargetConfig:
        for subVar in userTargetMicroSub:
            combineList.append(f"{subVar}{config}")
    zipConfigFound = []
    anyError = False
    for microSub, cfgDic in zipConfig.items():
        currentCfg = [microSub + x for x in list(cfgDic.keys())]
        zipConfigFound.extend(currentCfg)
    # Create Uniqe List only
    zipConfigFound = list(set(zipConfigFound))
    # Get config of arxml which is prepared by MOs
    arxmlConfigFound = []
    for microSub, cfgDic in arxmlConfig.items():
        currentCfg = [microSub + x for x in list(cfgDic.keys())]
        arxmlConfigFound.extend(currentCfg)
    # Do not verify unique for arxml, If any config exist in test plan, MO need to prepare for each Micro Sub also.
    # Get Unique config of arxml
    arxmlConfigFound = list(set(arxmlConfigFound))

    # Check issue
    if not "ALL_CFG" in userTargetConfig:
        preCheckData = [str(re.search(".*(cfg\d+).*", x.lower()).group(1)).upper() for x in combineList if x in zipConfigFound]
        redundantInput = [x for x in userTargetConfig if x not in preCheckData]
        # Check user input redundants
        if len(redundantInput) > 0:
            CI_LOGGER.error(f"JK_ERROR: Please re-check your input, Jenkins could not find any related configs for {redundantInput} in zip files! Found: {zipConfigFound}")
            anyError = True
    # Check arxml should exist for any found configs
    redundantInput = [x for x in zipConfigFound if x not in arxmlConfigFound]
    if len(redundantInput) > 0:
        CI_LOGGER.error(
            f"JK_ERROR: Please re-check your input, Jenkins could not find any related arxml configs for {redundantInput}")
        anyError = True
    if anyError:
        sys.exit(1)
    return 0

def extractTestZip():
    """
    this function will scan test zip file and extract it
    """
    # Extract all zip files which is prepared by Module Owner
    for zip in jobProperty.dutTestZipPath:
        ArchiveTestApp(jobProperty.TestAppPath, zip)
    return 0

def dumpValueToCanttJson(zipDic, arxmlDic):
    # This line just support new member for easy reading
    templateRefer = jobProperty.templateCantataDir
    rootCanttDir = {"Cantata": {
            "Workspace": "C:/Workspace/CantataWorkSpace",
            "Project": "MicroSubVariant_CONFIG"
            }
    }
    # Structure will refer zip file
    # unify upper first char only
    moduleCaptial = jobProperty.moduleRunning.capitalize()
    subDic = {"hw_ip": {moduleCaptial : {}}}
    for microSub, configDic in zipDic.items():
        # init empty dict as target template
        subDic["hw_ip"][moduleCaptial][microSub] = {}
        # Get current address for reducing length
        getPointerToMicroSub = subDic["hw_ip"][moduleCaptial][microSub]
        for configNumber, projectPath in configDic.items():
            CI_LOGGER.info(f"[-]    Getting information for config number: {configNumber} of Micro Sub Variant {microSub}")
            headerPrepared_ByMO = projectPath.replace("\\", "/")
            # Currently it is empty directory, it will be copied latest source to here, via others sub-scripts!
            latestHeader = os.path.join(arxmlDic[microSub][configNumber], "include")
            latestSource = os.path.join(arxmlDic[microSub][configNumber], "src")
            # Converting value to target dict tempate
            includePath = {"CC_Include_Path" : f"{zipDic[microSub][configNumber]} {latestHeader}"}
            srcPath = {"CC_Source_Path": f"{latestSource}"}
            # subDic will get new value via this line
            getPointerToMicroSub[configNumber] = {**includePath, **srcPath}
    # Merge value to target dict
    canttDirContent = {**rootCanttDir, **subDic}
    # json file path
    canttDirFile = jobProperty.targetCantataDir
    # parse value to json file
    with open(canttDirFile, 'w') as f:
        json.dump(canttDirContent, f)
    # End
    return 0

def regenerateGentool(arxmlDic):
    for microSub, configDic in arxmlDic.items():
        for config, rootPath in configDic.items():
            outputPath = rootPath
            inputCdf = glob(f'{rootPath}/**/*.arxml', recursive=True)
            dettectString = f"{jobProperty.moduleRunning.lower()}general"
            if "cdd" in jobProperty.moduleRunning.lower():
                dettectString = f"cddgeneral"
            inputCdfOfGentool = ""
            # Assump only 1 cdf under 1 root
            for cdfPath in inputCdf:
                with open(cdfPath, 'r') as f:
                    cdfData = f.read()
                    cdfData = cdfData.lower()
                    if dettectString in cdfData:
                        inputCdfOfGentool = cdfPath
                        break
            if "" == inputCdfOfGentool:
                CI_LOGGER.error(f"Please self check your arxml file {inputCdf}. Jenkin can not find required string : {dettectString}")
            else:
                # Generate gentol output via common lib
                pycicd.tools.regen_gentool_output(inputCdfOfGentool, outputPath, projectInfor, jobProperty.moduleRunning, microSub)
                excludeHeader = jobProperty.headerSourceSpecific.get(microSub.lower(), [])
                for gentoolFile in excludeHeader:
                    gentoolOutput = f"{outputPath}/include/{gentoolFile}"
                    if os.path.isfile(gentoolOutput):
                        os.remove(gentoolOutput)
    return 0

def modifyCompilerHeader():
    CI_LOGGER.info('=============================== Modify Compiler Macros ==============================')
    externalRoot = os.path.join(jobProperty.repoLocalPath, "external")
    file_list = ['Compiler.h', 'Compiler_Cfg_dep.h', 'arm_cr.h', 'arm_cr_cp15.h', 'SchM_Common.h', 'arm_gic.h', 'arm_cr_mpu.h'] # List of file to modify
    for file_name in file_list:
            print(f"JK_Warning exception: Jenkin will use {file_name} which is prepared by MOs.")
            allFiles = glob(f"{externalRoot}/**/{file_name}", recursive=True)
            for filePath in allFiles:
                os.remove(filePath)
                #if str(os.path.basename(filePath)) == 'arm_cr.h':
                #    
                #else:
                #    pycicd.tools.CompilerMacroModify(filePath)

    return 0

def copyLatestSource_To_ArxmlConfigPath(arxmlConfigDic):
    # Scan and get the file list from checked out repo.
    for subVariant, configDic in arxmlConfigDic.items():
        module_data = projectInfor.get_module_data(jobProperty.moduleRunning, subVariant)
        ecode_c_files = module_data.FileDict['ECODE_C']
        ecode_h_files = module_data.FileDict['ECODE_H']
        # Unit test do not need sub C files. stub_c_files = module_data.FileDict['STUB_C']
        stub_h_files = module_data.FileDict['STUB_H']
        # clone latest driver source
        ### For Header ###
        headerFileList = ecode_h_files + stub_h_files
        # filter file
        excludeHeader = jobProperty.headerSourceSpecific.get(subVariant.lower(), [])
        headerFileList = [x for x in headerFileList if x.FileName not in excludeHeader]
        for configName, configPath in configDic.items():
            CI_LOGGER.info(f'Copy correspond latest file from repo...')
            headerPath = os.path.join(configPath, "include")
            # Clone latest source of header file to arxml config include path
            for fileInfo in headerFileList:
                shutil.copy2(fileInfo.FilePath, headerPath)
                CI_LOGGER.success(f"   [+] Copied {fileInfo.FilePath}")
            # Clone latest source of c driver file to arxml config src path
            driverPath = os.path.join(configPath, "src")
            for fileInfo in ecode_c_files:
                shutil.copy2(fileInfo.FilePath, driverPath)
                CI_LOGGER.success(f"   [+] Copied {fileInfo.FilePath}")
    return 0


def main():
    """Main function
        Function 1: Verify arxml config
        Function 2: Verify gentool output config. in *.zip file, which is self prepared by Module Owner (MO)
        Function 3: Re-generate Gentool output if any - via pycicd
        Function 4: Re-Generate Config File. Includes: {DeviceName : Config Number}
        Function 5: Modify related compiers file
        Function 6: Clone latest source as CanttDir.json file
    """
    # get input (include verify arxml and zip input)
    allValidConfigInZip = getRelatedConfigs()
    allValidArxml = getRelatedArxmlConfigs()
    # Convert value to target dict format
    # Micro_Sub
    #   CONFIG_NUMBER
    #       LIST_PATH
    for microSub, listPath in allValidConfigInZip.items():
        configZipDic = extractConfig(listPath)
        allValidConfigInZip[microSub] = configZipDic
    for microSub, listPath in allValidArxml.items():
        configArxmlDic = extractConfig(listPath)
        allValidArxml[microSub] = configArxmlDic
    # Confirmation Step, If any issue will raise exit 1
    confirmationStep(allValidConfigInZip, allValidArxml)
    # Dump Value to CanttDir.json file
    dumpValueToCanttJson(allValidConfigInZip, allValidArxml)
    # re-generate gentool output
    regenerateGentool(allValidArxml)
    # Modify related compiler header
    modifyCompilerHeader()
    # Clone latest source
    copyLatestSource_To_ArxmlConfigPath(allValidArxml)
    return 0



if __name__ == "__main__":
    main()
