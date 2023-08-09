#!/usr/bin/python -B
# -*- coding: utf-8 -*-
'''
This class support for:
1) Creating *.cpr via command line:
    +++ ipg.cop: should contain --preprocessor_logging option 
        => create *.cpl files when sources are compiled by cantata
    +++ Tool to create *.ctr: "C:\qa_systems\cantata\bin\cppgetcov.exe" (
        detail how to use please refer --help option of cppgetcov.exe Tool)
    +++ option used in this class: cppgetcov.exe --cplSearchDir:Path search --output:Output Path
        --cplSearchDir      : Recursively searches the given directory for .cpl files.
        --output            : Path and file name of *.cpr file.

2) Design:
MCAL:
    +++ Input : path search, output path.
        basePath: root dir contain all *.cpl files.
        cprPath : cpr output location.
    +++ Output :
         Check : *.cpl exist
         Create: All_preprocessorMacros.cpr file
         Update: Excel file about Compiled Code status
CI:
    +++ python 3.8
    +++ output: error_C0_Measure.log (store at: D:/CI_ErrorLog)
    
'''

########################################################################################################################
### Module   = C0_Measure.py                                                                                         ###
### Author   = Anh Nhat Nguyen                                                                                       ###
### Date     = 12/27/2021                                                                                            ###
###                                               Revision History                                                   ###
###                                                                                                                  ###
###  1.0.0: 12/27/2021  : Initial version.                                                                           ###
########################################################################################################################
###                                                Import section                                                    ###
########################################################################################################################
import os
import string
import sys
import glob
import subprocess
import re
import io
import time

########################################################################################################################
###                                                Function definition                                               ###
########################################################################################################################


class C0_Measure():
    def __init__(self, basePath, cprPath):
        self.basePath = basePath.replace("\\", "/")
        self.cprPath = cprPath.replace("\\", "/")
        self.errorLog = []
        # decision point to make sure input is True
        self.checkUserInput()
        if not [] == self.errorLog:
            print("\n".join(self.errorLog))
            sys.exit()
        else:
            print("User Input has checked!")

    def checkUserInput(self):
        userInputCorrect = True
        # check base Path is a dirrectory
        if not os.path.isdir(self.basePath):
            contentLog = "Could not find path: {}".format(self.basePath)
            print(contentLog)
            self.errorLog = self.errorLog + [contentLog]
        else:
            # Check *cpl is exist or not
            cplPatern = self.basePath + "/**/*.cpl"
            anyCplFile = glob.glob(cplPatern, recursive=True)
            if not anyCplFile:
                contentLog = "Could not find any *.cpl files at: {}".format(
                    self.basePath)
                print(contentLog)
                self.errorLog = self.errorLog + [contentLog]
            else:
                # check cpr path file is exist or not
                if not os.path.isdir(self.cprPath):
                    print("Created path:", self.cprPath,
                          "As This output path is not exist!")
                    os.makedirs(self.cprPath)
                else:
                    pass

        return self.errorLog

    def create_CprFile(self):
        cantataTool = "C:/qa_systems/cantata/bin/cppgetcov.exe"
        cprFile = self.cprPath + "/All_preprocessorMacros"
        cmdCantata = cantataTool + \
            " --output:{} --cplSearchDir:{}".format(cprFile, self.basePath)
        outOfLicense = False
        print(cmdCantata)
        try:
            cprCreating = subprocess.check_output(cmdCantata, shell=True)
            print("Created All_preprocessorMacros.cpr successfully!")
            print("Your output at:", self.cprPath)
        except subprocess.CalledProcessError as cprCreating:
            exceptLog = cprCreating.output.decode("utf8")
            if ("All licensing tokens" in exceptLog):
                outOfLicense = True
                print("re-run until get cantata license")
            else:
                self.errorLog = self.errorLog + [cprCreating.output]
                print(cprCreating.returncode, exceptLog)
                return 1
        while (outOfLicense):
            # sleep 100s then check again Cantata cycle is 300s
            time.sleep(100)
            try:
                cprCreating = subprocess.check_output(cmdCantata, shell=True)
                outOfLicense = False  # if error occur in subprocess this line will not run
            except subprocess.CalledProcessError as cprCreating:
                exceptLog = cprCreating.output.decode("utf8")
                if ("All licensing tokens" in exceptLog):
                    outOfLicense = True
                else:
                    print("Can not contact license")
                    self.errorLog = self.errorLog + [cprCreating.output]
                    print(cprCreating.returncode, exceptLog)
                    outOfLicense = False
        return 0

    def extractLineToDict(self, line):
        loC = 0
        status = "No_Infor"
        paternSearch = "\.c \([0-9]+\) "
        lineOfCodeString = re.findall(paternSearch, line)
        if len(lineOfCodeString) == 1:
            loC = int(lineOfCodeString[0].replace(".c (", "").replace(")", ""))
            status = "Compiled"
            if ">> NOT INCLUDED" in line:
                status = "Not_Compiled"
        elif len(lineOfCodeString) > 1:
            errorContent = "Pattern '\.c \([0-9]+\) 'Search Found Multiple String For Line: " + line
            print(errorContent)
            self.errorLog = self.errorLog + [errorContent]
        else:
            pass
        return loC, status

    '''
    getUnCompiledCodeOnly filter dict intput to get only un-compiled codes.
    targetSources: [List of target source C files]
    rawData: Dict type with format {sourceName : {lineOfCode : [List status]}}
    return value: Dict type with format {sourceName : [List of lines Un-Compiled]}
    '''

    def getUnCompiledCodeOnly(self, rawData, targetSources):
        unCompiledCode = {}
        for source in targetSources:
            raw = rawData.get(source)
            if raw == None:
                outputStr = """
                ##################################################################
                source = {source}
                Total Un-Compiled Line Of Code = 0
                Please re-check this source if no pre-processor macro, it's ok!!!!
                ###########################!!!!!!!!!!!############################
                """
                print(outputStr)
                unCompiledCode[source] = []
                continue
            for loc, all_status in raw.items():
                if not "Compiled" in all_status:
                    if not source in unCompiledCode.keys():
                        unCompiledCode[source] = [loc]
                    else:
                        unCompiledCode[source] = unCompiledCode[source] + [loc]
                else:
                    continue
            if unCompiledCode == {}:
                unCompiledCode[source] = []
        # print(unCompiledCode)
        return unCompiledCode
    '''
    Get list line of code based on:
    ++ source file input
    ++ un-preprocessor macro line
    basic C code:
    comment:
        /* comment */     (1)     
        // comment     (2)
    reference: https://en.cppreference.com/w/c/comment
    Preprocessor Macros:
        if-line :
            #if constant-expression
            #ifdef identifier
            #ifndef identifier
        elif-line :
            #elif constant-expression
        else-line :
            #else
        endif-line :
            #endif
    reference: https://docs.microsoft.com/en-us/cpp/preprocessor/hash-if-hash-elif-hash-else-and-hash-endif-directives-c-cpp?view=msvc-170
    '''
    '''
    + Input: 
        logPath: log folder path of coverage merge tool with format path/to/log
        unCompiledMacroLines : Dict type with format sourceC : [list un-compiled macros]
    + output:
        source_C_notcomp.txt with format line (tap space) NOT COMPILED (if any)
    '''

    def listUnCompiledLineOfCode(self, logPath, source, locList):
        # Input
        sourceC = source
        unCompiledMacros = locList
        errorFlag = False
        sourcePath = logPath + \
            "/{}_c_code.txt".format(sourceC.replace(".c", ""))
        notCompiledTxt = logPath + \
            "/{}_c_notcomp.txt".format(sourceC.replace(".c", ""))
        # Check input notCompiledTxt and sourcePath should be exist at CMT path
        if not os.path.isfile(notCompiledTxt):
            errorContent = "Do not find log path of CMT Tool " + notCompiledTxt
            self.errorLog = self.errorLog + [errorContent]
            errorFlag = True
        if not os.path.isfile(sourcePath):
            errorContent = "Do not find source C code file of CMT Tool " + sourcePath
            self.errorLog = self.errorLog + [errorContent]
            errorFlag = True
        if errorFlag:
            print(self.errorLog)
            sys.exit()
        # read source C content for each line
        with open(sourcePath, 'r') as f:
            eachLineC = f.read().splitlines()
            f.close()
        # Preprocess
        '''
        Find out list of related lines from #if to #endif block
        example: 
        #if Target Block
            #if B
            #endif
        #endif /* end Target Block */ 
        '''
        startCheckpoint = "^\s*#if"  # check if find #if at the start string
        elCheckPoint = "^\s*#el"  # check if find #el at the start string
        endCheckpoint = "^\s*#end"  # check if find #end at the start string

        start = 0
        end = 0
        targetLoC = []
        # Loop all input list
        for lineIndex in unCompiledMacros:
            # comment line or preprocessor macros will be excluded
            commentLoc = []
            # count #if exist
            numberOfStartPoint = 0
            # Get start index after #if or #el
            start = lineIndex - 1
            # find end index
            countLoop = 0
            sliceLine = eachLineC[start::1]
            for eachLine in sliceLine:
                if re.match(startCheckpoint, eachLine):
                    # skip first index for checking #if
                    if countLoop > 0:
                        numberOfStartPoint = numberOfStartPoint + 1
                    commentLoc = commentLoc + [start + countLoop]
                # check for end block "#if to #el" or "#el to #el"
                if re.match(elCheckPoint, eachLine):
                    # skip first index for checking #el
                    if numberOfStartPoint == 0 and countLoop > 0:
                        end = start + countLoop + 1  # slice string will auto minor 1
                        commentLoc = commentLoc + [start + countLoop]
                        break
                    commentLoc = commentLoc + [start + countLoop]
                # check for end target block "#if to #end" or "#el to #end"
                if re.match(endCheckpoint, eachLine):
                    # never occur first index for checking #end
                    if numberOfStartPoint == 0:
                        end = start + countLoop + 1  # slice string will auto minor 1
                        commentLoc = commentLoc + [start + countLoop]
                        break
                    commentLoc = commentLoc + [start + countLoop]
                    numberOfStartPoint = numberOfStartPoint - 1
                countLoop = countLoop + 1
            # your block
            yourBlock = "\n".join(eachLineC[start:end:1])
            # print(yourBlock)
            # check how many lines support for condition of #if
            left = 0
            right = 0
            numberSkipLines = 0
            excludeConditionLine = []
            for macroLine in commentLoc:
                lineOfBlock = eachLineC[macroLine]
                left = left + len(re.findall("\(", lineOfBlock))
                if left > 0:
                    left = 0
                    excludeConditionLine = excludeConditionLine + \
                        [macroLine + numberSkipLines]
                    for nextLine in eachLineC[macroLine::1]:
                        left = left + len(re.findall("\(", nextLine))
                        right = right + len(re.findall("\)", nextLine))
                        if left == right:
                            left = 0
                            right = 0
                            break
                        numberSkipLines = numberSkipLines + 1
                        excludeConditionLine = excludeConditionLine + \
                            [macroLine + numberSkipLines]
            # exclude all lines support for condition
            commentLoc = commentLoc + excludeConditionLine
            contentOfBlock = eachLineC[start: end]
            # remove redundant comment line of code
            commentLeft = "^\s*\/\*"  # /* match start of string
            commentRight = "\w*\s*\*\/\s*$"  # */ match end of string
            generalComment = "^\s*\/\/"  # //
            nextIndex = 0
            # exclude for case /* */
            for lineOfBlock in contentOfBlock:
                left = left + len(re.findall(commentLeft, lineOfBlock))
                right = right + len(re.findall(commentRight, lineOfBlock))
                # support comment multiple lines
                if left > right:
                    commentLoc = commentLoc + [start + nextIndex]
                # if a pair /* and */ is found
                if left == right and left > 0:
                    commentLoc = commentLoc + [start + nextIndex]
                    left = 0
                    right = 0
                # if a comment occur in them same line of code
                if right > 0 and left == 0:
                    right = 0
                # next index
                nextIndex = nextIndex + 1
            commentPos = 0
            # exclude for case //
            for lineOfBlock in contentOfBlock:
                commentPos = commentPos + 1
                if len(re.findall(generalComment, lineOfBlock)) > 0:
                    cmtLoC = start + commentPos
                    if cmtLoC in commentLoc:
                        pass
                    else:
                        commentLoc = commentLoc + [cmtLoC]
            # Update target line of code to return list
            for loc in list(range(start, end)):
                if not loc in commentLoc:
                    # this line should contain a string
                    anyStringRegex = '\w+'
                    if [] != re.findall(anyStringRegex, eachLineC[loc]):
                        targetLoC = targetLoC + [loc + 1]
                    # else not care
        # print out some informations for user
        if [] == targetLoC:
            print(sourceC, "Compiled All")
        else:
            outputStr = """
            ############################################################
            source = {sourceC}
            Total Un-Compiled Line Of Code = {len(targetLoC)}
            Un-Compiled Lines = {targetLoC}
            ############################################################
            """
            print(outputStr)
        # write to *_notcomp.txt in log path
        targetLoC = ''.join(
            list(map(lambda x: "{}\tNOT COMPILED\n".format(x), targetLoC)))
        with io.open(notCompiledTxt, "w", newline='\n') as notCompiledText:
            notCompiledText.write(targetLoC)
            notCompiledText.close()
        return targetLoC
    '''
    This function support to remove redundant information, it is included:
    + header files
    + C sources are not in targe.txt files
    '''

    def getLoCUnCompiledMacros(self):
        cprFile = self.cprPath + "/All_preprocessorMacros.cpr"
        targetTxt = self.cprPath + "/target.txt"
        with open(cprFile, 'r') as file:
            cprContent = file.read().splitlines()
            file.close()
        targetInformation = []
        # get only C source in target.txt
        # ["Gpt_OSTM_Irq.c", "Gpt_TAUD_Irq.c", "Gpt_OSTM_LLDriver.c", "Gpt.c"]
        targetC_Sources = []
        with open(targetTxt, 'r') as targetC:
            targetC_Sources = targetC.read().splitlines()
            targetC_Sources = list(set(targetC_Sources))
        # convert list to .c at tail name
        targetC_Sources = list(
            map(lambda x: x.replace(".c", "") + ".c", targetC_Sources))
        sourceStatus = {}
        # loop all lines in cprContent to check status, line of code
        # Get only line contain source C name and should find .c (line of code) in line by 1 time.
        for line in cprContent:
            if (".cpl" in line):
                continue
            for cSource in targetC_Sources:
                if f'/{cSource} (' in line.replace("\\", "/"):
                    loC, status = self.extractLineToDict(line)
                    if "No_Infor" == status:
                        continue
                    targetInformation = targetInformation + [line]
                    if not sourceStatus.get(cSource):
                        sourceStatus[cSource] = {loC: [status]}
                    else:
                        if not sourceStatus.get(cSource).get(loC):
                            sourceStatus[cSource][loC] = [status]
                        else:
                            sourceStatus[cSource][loC] = sourceStatus[cSource][loC] + [status]
        # write to text file to create tool evidence
        targetSources = self.cprPath + "/targetSourcesOnly.txt"
        with open(targetSources, 'w') as f:
            content = "\n".join(targetInformation)
            f.write(content)
            f.close()
        ''' check status the same length for all line of code in the same source
        This error is not true: as nest macros (pre-processor macro inside pre-processor macros)
        '''
        unCompiledCodes = self.getUnCompiledCodeOnly(
            sourceStatus, targetC_Sources)
        # Confirm stage
        if [] != self.errorLog:
            print("Error: ", "\n".join(self.errorLog))
        # end of this method
        return unCompiledCodes


########################################################################################################################
###                                                MAIN FUNCTION                                                     ###
########################################################################################################################
# Sequence called
# Get user input : This path the same as target.txt path
baseDir = sys.argv[1]  # "D:/sendToVendor/CantataWS/CantataWS/X2x/U2Ax/gpt"
baseDir = baseDir.replace("\\", "/")
# Init C0 class
C0_Init = C0_Measure(baseDir, baseDir)
# Create Cpr File All_preprocessorMacros.cpr
C0_Init.create_CprFile()
# Filter to get un-complied macros via C
unCompiledPerSource = C0_Init.getLoCUnCompiledMacros()
# update un-compiled line of codes to *_notcomp.txt in log path of CMT
logPath = "{}/log".format(baseDir)
for source, locList in unCompiledPerSource.items():
    print(source, locList)
    linePerSource = C0_Init.listUnCompiledLineOfCode(logPath, source, locList)
# re-confirm stage to check any errors
if [] == C0_Init.errorLog:
    print("Update *_notcomp.txt successfull!")
else:
    errorLogContent = "\n".join(C0_Init.errorLog)
    # print to jenkin log
    print("Error: Please re-check error log\n", errorLogContent)
    errorLogFile = "{}/error_C0_Measure.log".format(baseDir)
    # Print to error log file
    with open(errorLogFile, 'w') as log:
        log.write(errorLogContent)
        log.close()
sys.exit()
