import glob
import re

class Correct_Ctr_File():
    def __int__(self, repairPath):
        self.repairPath = repairPath
    def extractLongFunctionName(self, linesContent):
        """
        :param linesContent: String type
        :return: List of function name string more than 30 chars
        """
        allFunction = re.findall("\.c\(\d*\).*_.*\n?.*\(",
                                 linesContent)  # 'Msn.c:Fr_59_Renesas_AbortCommunication(uint8 )entry point coverage details ('
        allFunction = [x.replace("\r\n", "") for x in
                       allFunction]  # Unify end of line format is \r\n - windows style
        allFunction = [re.search('.*:(.*_.*\(.*).*', x).group(1) for x in
                       allFunction]  # 'Fr_59_Renesas_AbortCommunication(uint8 )entry point coverage details ('
        allFunction = [x.split("(")[0] for x in allFunction]  # Fr_59_Renesas_AbortCommunication
        allFunction = [x for x in allFunction if len(x) > 30]  # Only Function Name More Than 30 chars
        allFunction = list(set(allFunction))
        return allFunction

    def extractCFileName(self, linesContent):
        """
        :param linesContent: String type
        :return: List of file name string more than 15 chars, decision point (bool type), list of cut file name
        """
        fastAction = True
        allFileName = re.findall("\r\n\w*\.c\(\d*\)", linesContent)  # \r\nFr_59_Renesas_LLDriver.c(
        allFileName = [x.replace("\r\n", "") for x in allFileName]  # #Fr_59_Renesas_LLDriver.c(line of code)
        allLongFileName = [x for x in allFileName if len(x) > 21]  # Only File Name More Than 21 chars
        allCutFileName = [x for x in allFileName if len(x) == 21]  # Only File Name Equal 21 chars
        allCutFileName = list(set(allCutFileName))
        allFileName = list(set(allFileName))

        # Init Compare Data
        fileNameOnly = [x.split("(")[0] for x in allLongFileName]  # Fr_59_Renesas_AbortCommunication
        cutNameOnly = [x.split("(")[0] for x in allCutFileName]  # Fr_59_Renesas_AbortCommunication
        fileNameOnly = list(set(fileNameOnly))
        cutNameOnly = list(set(cutNameOnly))
        # Decision to run fast algorithm or slow algorithm
        for cutFileName in cutNameOnly:
            count = 1
            for longFileName in fileNameOnly:
                """
                example: 
                TAUD_HWUNIT_LLDRiver.c(123)
                TAUJ_HWUNIT_LLDRiver.c(123)
                longFileName = ["TAUD_HWUNIT_LLDRiver.c(123)", "TAUJ_HWUNIT_LLDRiver.c(123)"]
                cutFileName = "WUNIT_LLDRiver.c(123)"
                ==> Tool need to start slow algorithm to make sure no wrong data. 
                """
                if cutFileName in longFileName:  # Make sure not any file name same as each other
                    if (count == 1):
                        count = count + 1
                    else:
                        fastAction = False
                        break
        return fileNameOnly, fastAction, cutNameOnly, allLongFileName, allCutFileName

    def replaceSlowAction(self, linesContent, allLongFileName, allCutFileName):
        """
        :param linesContent, allLongFileName, allCutFileName
        :return: linesContent has been replaced short name which is replaced by Cantata tool to real value.
        :algorithm: Find min string length between short name contain line of code and real file name contain line of code.
        """
        for shortNameAndLoc in allCutFileName:
            minLenght = 20000 * 120
            targetString = ""
            replaceString = ""
            for fileNameAndLoc in allLongFileName:
                fileNameLoc = fileNameAndLoc.replace("(", "\\(").replace(")", "\\)")  # convert to regex string
                shortNameLoc = shortNameAndLoc.replace("(", "\\(").replace(")", "\\): ")  # convert to regex string
                searchRegex = f"{fileNameLoc}[\s\S]*coverage details[\s\S]*?(?={shortNameLoc})"
                allSubString = re.findall(searchRegex, linesContent)
                for subString in allSubString:
                    if len(subString) < minLenght:
                        fileNameOnly = fileNameAndLoc.split("(")[0]
                        Loc = shortNameAndLoc.split("(")[1]
                        targetString = subString + f"{fileNameOnly}({Loc}"
                        replaceString = subString + shortNameAndLoc
                        minLenght = len(subString)
            if len(targetString) > 0:
                linesContent = linesContent.replace(replaceString, targetString)
            else:
                print("JK_Warning: Tool can not auto fix file name for short name (name replaced by Cantata):",
                      shortNameAndLoc)
        return linesContent

    def posix2win(self, path):
        """
        :param path is string
        :return: If cygdrive path will convert to os path automatically else return as input path.
        """
        path = "/".join(re.split(r"[\\/]+", path))
        cygpath_pattern_path = re.match(r'^/cygdrive/([A-Za-z])', path, re.IGNORECASE)
        if cygpath_pattern_path:
            path = re.sub(r'^/cygdrive/([A-Za-z])', cygpath_pattern_path.group(1).upper() + ':', path, re.IGNORECASE)
        else:
            pass
        return path

    def repairCtrFiles(self, repairPath):
        """
        :param repairPath is path string
        :return: linesContent has been replaced short name which is replaced by Cantata tool to real value.
        """
        searchPath = self.posix2win(repairPath)
        all_crtFile = glob.glob(f"{searchPath}/**/*.ctr", recursive=True)
        for ctrFile in all_crtFile:
            linesContent = ""
            with open(ctrFile, 'r', newline='\r\n') as ctrContent:
                linesContent = ctrContent.read()
                linesContent = linesContent.replace("\r", "")
                linesContent = linesContent.replace("\n", "\r\n")
                ctrContent.close()
            # End Unify end of line
            allLongFunction = self.extractLongFunctionName(linesContent)  # Get function name more than 30 chars
            # Due to length of string value so short we need to determine which algorithm to be used.
            # Return Parameter: fastAction -> If True: Fast Algoritm, If False: Slow Algorithm.
            fileNameOnly, fastAction, cutNameOnly, allLongFileName, allCutFileName = self.extractCFileName(
                linesContent)  # Get function name more than 15 chars
            # Replace wrong name to correct Name
            for longFuncName in allLongFunction:
                wrongName = f"\"{longFuncName[-30:]}\""
                toCorrectName = f"\"{longFuncName[:]}\""
                linesContent = linesContent.replace(wrongName, toCorrectName)
            if fastAction:
                # Fast algorithm
                for shortName in cutNameOnly:
                    for longFileName in fileNameOnly:
                        if shortName in longFileName:
                            stringToBeReplaced = f"\r\n{shortName}"
                            toCorrectName = f"\r\n{longFileName[:]}"
                            linesContent = linesContent.replace(stringToBeReplaced, toCorrectName)
            else:
                linesContent = self.replaceSlowAction(linesContent, allLongFileName, allCutFileName)
            del fileNameOnly, fastAction, cutNameOnly, allLongFileName, allCutFileName
            # Write to target file
            linesContent = linesContent.replace("\r", "")
            with open(ctrFile, 'w', newline='\r\n') as ctrContent:
                ctrContent.writelines(linesContent)
                ctrContent.close()
        # Process Next File
        # End
        return 0
