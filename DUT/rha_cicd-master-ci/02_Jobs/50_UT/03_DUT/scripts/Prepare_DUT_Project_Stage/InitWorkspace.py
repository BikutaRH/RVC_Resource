# -*- coding: utf-8 -*-
""" '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Author    : Tin Nguyen
# Email     : tin.nguyen.uf@renesas.com
# Editor    : Tu Nguyen
# Email     : tu.nguyen.jg@renesas.com
# Date      : 29-10-2020
# Filename  : InitWorkspace.py
# Project   : Auto DUT CI
# Todo      : Init ipg.cop file and copy source code from repo to Cantata Worksapce
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """

""" ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''Begin Import libarary header file'''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """
import logging
import os
import shutil
import json
import glob
from zipfile import ZipFile
from pathlib import Path
# import subprocess
import traceback

""" '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''End Import libarary header file'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """

""" ''''''''''''''''''''''''''''''''''''''''''''''''''''Begin declare variable and necessary path''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """


""" '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''End declare variable''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """

""" ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''Begin main class'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """
class workspace:
    __ipg_cop_content_file = [

        "#",
        "# Cantata Project-Level Options",
        "#",
        "# The options set in this file will be inherited by each test in the project.",
        "#",
        "# WARNING: Do not alter this file manually.",
        "#",
        "#tool.use=true",
        "#tool.tests=Cantata",
        "#tool.version=2",
        "\"--analyse\"",
        "\"--ci:--instr:stmt;func;rel;loop;call;decn;block;log;\"",
        "\"--parse:--line_directives\"",
        "\"--parse:-W2\"",
        "\"--preprocessor_logging\"",
        "\"--sm:--call_seq_code\"",
        "\"--comp:x86-Win32-gcc8.2-bundled\"",
        "",
        "#User Section",
        "\"--ci:--instr_macros:?*DEM?*\"",
        "\"--ci:--instr_macros:?*DET?*\"",
        "\"--ci:--instr_macros:?*ENTER?*\"",
        "\"--ci:--instr_macros:?*EXIT?*\"",
        "\"--ci:--instr_macros:?*EXECUTE?*\"",
        "\"--ci:--instr_macros:?*RH850_SV?*\"",
        "\"--ci:--instr_macros:?*RSCAN?*\"",
        "\"--ci:--instr_macros:?*PACK_ADDRESS?*\"",
        "\"--ci:--instr_macros:?*COPY_MAC_ADDRESS?*\"",
        "\"--ci:--instr_macros:?*DF_WRITE32?*\"",
        "\"--ci:--instr_macros:?*_SYNCP?*\"",
        "\"--ci:--instr_macros:?*ASM_HALT?*\"",
        "\"--ci:--instr_macros:?*RESET_CALLOUT?*\"",
        "\"--ci:--instr_macros:?*DMA_ISR_TEMPLATE?*\"",
        "\"--ci:--instr_macros:?*MCU_CLKKCPROT?*\"",
        "\"--ci:--instr_macros:?*MCU_CLKD_PLLC?*\"",
        "\"--ci:--instr_macros:?*SPI_REG_VERIFY?*\"",
        "\"--ci:--instr_macros:?*SPI_REG_WRITE_ONLY?*\"",
        "\"--ci:--instr_macros:?*SPI_REG_OR?*\"",
        "\"--ci:--instr_macros:?*SPI_REG_AND?*\"",
        "\"--ci:--instr_macros:?*SPI_WRITE_VERIFY_REG?*\"",
        "\"--ci:--instr_macros:?*SPI_WRITE_VERIFY_AND_REG?*\"",
        "\"--ci:--instr_macros:?*SPI_WRITE_VERIFY_OR_REG?*\"",
        "\"--ci:--instr_macros:?*SPI_WRITE_VERIFY_AND_OR_REG?*\""

    ]
    __makefile_targets = [
        "$(OBJS) : ../ipg.cop"
    ]
    def __init__(self, CanttDirJsonFile, projectPath, Msn, microsub_Config):
        self.file_get_wp = CanttDirJsonFile
        self.projectPath = projectPath
        self.Msn = Msn.capitalize()
        self.Cfg = microsub_Config

################################################################### Begin write_file_ipg function ############################################################
    def __generate_file_ipg(self,ipg_cop_ofProjectFile):
        _readed_file = open(ipg_cop_ofProjectFile,"w")
        for row in self.__ipg_cop_content_file:
            _readed_file.write(row + '\n')
        ## Add User Selection option
        _readed_file.write(f"\"--ci:--static_info_file:{self.projectPath}\Debug\"\n")
        _readed_file.close()

################################################################## End write_file_ipg function ###############################################################

############################################################## Begin get_path_workspace function #############################################################
    def __read_file_json(self,filename):
        dict_json = {}
        try:
            with open(filename,"r") as json_file:
                dict_json = json.load(json_file)
                json_file.close()
        except FileNotFoundError:
            print(">>> File does not exist.")
        return dict_json    
############################################################## End get_path_workspace function ################################################################

################################################################ Clone Source code from repo ##################################################################
    def __clone_src(self,_CanttDir_json,_Device,_Config:str,_Path_Project):
        print(">>> Begin copying source .......................................................")
        Include_Path_Common = _CanttDir_json["hw_ip"][self.Msn][_Device][_Config.split('_')[-1].upper()]["CC_Include_Path"]
        Source_Path_Common = _CanttDir_json["hw_ip"][self.Msn][_Device][_Config.split('_')[-1].upper()]["CC_Source_Path"]

        Include_Path_Arr =str(Include_Path_Common).split(' ')
        Source_Path_Arr =str(Source_Path_Common).split(' ')
        
        ## Check folder include and clear if it exist
        if os.path.exists(f"{_Path_Project}/include/") is False:
            os.mkdir(f"{_Path_Project}/include/")
        else:
            # shutil.rmtree(f"{_Path_Project}/inc/")
            os.system(f"rmdir /s /q \"{_Path_Project}/include/\"")
            os.mkdir(f"{_Path_Project}/include/")
        ## Copy Header file to workspace
        for Include_Path in Include_Path_Arr:
            if os.path.exists(Include_Path):
                if (".zip" in Include_Path):
                    parrent = Path(Include_Path).parent.absolute()
                    zipFolder = Include_Path.replace(".zip","")
                    zipFolder = Path(zipFolder).absolute()
                    print(zipFolder)
                    if os.path.isdir(zipFolder):
                        shutil.rmtree(zipFolder)
                    # opening the zip file in READ mode
                    with ZipFile(Include_Path, 'r') as zip:
                        # extracting all the files
                        print('Extracting all the files now...')
                        zip.extractall(parrent)
                        print('Done!')
                        continue
                os.chdir(Include_Path)
                print('+ ' + Include_Path)
                Inc_File_List = glob.glob("**/*.h", recursive=True)
                for Inc_File in  Inc_File_List:
                    print('  |- '+ Inc_File)
                    shutil.copy(Inc_File,f"{_Path_Project}/include/")
            else:
                print(f'WARNING!!! Include path {Include_Path} is not exist!')

        ## Check folder and clear if it exist
        if os.path.exists(f"{_Path_Project}/src/") is False:
            os.mkdir(f"{_Path_Project}/src/")
        else:
            # shutil.rmtree(f"{_Path_Project}/src/")
            os.system(f"rmdir /s /q \"{_Path_Project}/src/\"")
            os.mkdir(f"{_Path_Project}/src/")
        ## Copy Source file to workspace
        for Source_Path in Source_Path_Arr:
            if os.path.exists(Source_Path):
                os.chdir(Source_Path)
                print('+ ' + Source_Path)
                Src_File_List = glob.glob("**/*.c", recursive=True)
                for Src_File in  Src_File_List:
                    if not ("atest_" in Src_File):
                        print('  |- '+ Src_File)
                        shutil.copy(Src_File,f"{_Path_Project}/src/")
            else:
                 print(f'WARNING!!! Source path {Source_Path} is not exist!')
        print(">>> Finish copy source.")

###############################################################################################################################################################
    def copy_project_source_file(self, _Device, _Cfg):
        #Get path of workspace and project#
        dict_json = self.__read_file_json(f"{self.file_get_wp}")
        ## Argument processing
        # argument_process(argv)
        ## Copy source code from reposistory to workspace CANTATA
        self.__clone_src(dict_json, _Device, _Cfg, self.projectPath)

    def generate_cantata_option_file(self):
        # profile_list_ipg = read_file(f"{Path_Project}/ipg.cop", profile_list_ipg)
        self.__generate_file_ipg(f"{self.projectPath}/ipg.cop")
        ##End write to ipg.cop ##
        
    def generate_makefile_targets(self):
        ## Create file ##
        _readed_file = open(f"{self.projectPath}/makefile.targets","w")
        for row in self.__makefile_targets:
            _readed_file.write(row)
        _readed_file.close()


""" ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''End main class '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' """
# if __name__ == "__main__":
#     main(sys.argv[1:])
    
