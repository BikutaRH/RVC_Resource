#!/usr/bin/python
from xlrd import open_workbook
import re
import os
import docxpy
from importlib import reload
#> *.docx
#> pip install docxpy
# encoding=utf8
import  sys
reload(sys)
# sys.setdefaultencoding('utf8')

def showHelp():
    print ("This tool is compare id between FD and DD")


def write_value(input_file, value, print_value):
    file_out = open(input_file, "a+")
    file_out.write(value)
    file_out.write("\r\n")
    file_out.close
    if print_value:
        print (value)


def write_list_value(input_file, value):
    file_out = open(input_file, "a+")
    for item in value:
        file_out.write(item.rstrip())
        file_out.write("\r\n")
    file_out.close


def read_xlsx_file(xlsxFile):
    wb = open_workbook(xlsxFile)
    if "_ErrorList" in xlsxFile:
        for sheet in wb.sheets():
            if sheet.name == "Error" or sheet.name == "Warning" or sheet.name == "Information":
                number_of_rows = sheet.nrows
                for row in range(5, number_of_rows):
                    value = sheet.cell(row, 1).value
                    if value != '' and ' ' not in value and '-' not in value:
                        error_list_array.append(value)
                        
        write_value(result_file, "Completed parser error list file with: \"%d\" IDs." %len(error_list_array), True)
    else:
        for sheet in wb.sheets():
            if sheet.name == "Cover" or sheet.name == "Reference":
                continue
            else:
                number_of_rows = sheet.nrows
                for row in range(1, number_of_rows):
                    value = sheet.cell(row, 1).value
                    if value != '' and ' ' not in value:
                        if value[len(value)-3:] == "001":
                            config_array.append(value[:len(value)-4])
                            config_array.append(value)
                        else:
                            config_array.append(value)
        write_value(result_file, "Completed parser configuration file with: \"%d\" IDs." %len(config_array), True)

  
def read_docx_file(docxFile, module_specific):
    tmp_file = "dd_file_temp.txt"
    text = docxpy.process(docxFile)
    file = open(tmp_file, "w")
    file.write(text)
    file.close
    
    file = open(tmp_file, "r")
    for line in file: 
        if re.match(r"{Ref: \[\d\] ", line) is not None:
            value = line[10:len(line)-2]
            if ',' in value:
                sub_values = value.split(', ')
                for sub_index in range(0, len(sub_values)):
                    dd_ref_array.append(sub_values[sub_index])
            else:
                dd_ref_array.append(value)
        
        if re.match(module_specific, line) is not None:
            dd_id_array.append(line[0:len(line)-2])

    os.remove(tmp_file)
    file.close
    write_value(result_file, "Completed parser detail design file with: \"%d\" IDs of Ref and \"%d\" IDs of DD." %(len(dd_ref_array), len(dd_id_array)), True)


def read_c_sharp_file(sourch_path, module_specific):
    # Get Id in source code
    # Get traverse directory to ".cs"
    for root, dirs, files in os.walk(sourch_path):
        for file in files:
            if file.endswith(".cs"):
                file_cs = open(os.path.join(root, file), "r")
                for line in file_cs: 
                    temp = "^ *// Implementation: " + module_specific
                    if re.match(temp, line) is not None:
                        value = re.findall(module_specific, line)
                        tcode_id_array.append(value[0])
    write_value(result_file, "Completed parser id of source code with: \"%d\" IDs." %len(tcode_id_array), True)                    
    

def comapre_ID_file(config_array, error_list_array, dd_ref_array, dd_id_array, tcode_id_array, result_file):  
    flag_first = True
    id_unmapped_array = []
    
    # Check Configuration File <=> DD
    for item_config in config_array:
        if item_config not in dd_ref_array:
            if flag_first:
                write_value(result_file, "\r\n\r\nID Unmapped: Configuration ID <=> DD:", False)
                flag_first = False
            id_unmapped_array.append(item_config)

    id_unmapped_array.sort()
    write_list_value(result_file, id_unmapped_array)
    flag_first = True
    del id_unmapped_array[:]
    
    
    # Check Error List File <=> DD
    for item_error in error_list_array:
        if item_error not in dd_ref_array:
            if flag_first:
                write_value(result_file, "\r\n\r\nID Unmapped: Error List ID <=> DD:", False)
                flag_first = False
            id_unmapped_array.append(item_error)
            
    id_unmapped_array.sort()
    write_list_value(result_file, id_unmapped_array)
    flag_first = True
    del id_unmapped_array[:]
    
    
    # Check DD <=> TCODE
    for item_dd in dd_id_array:
        if item_dd not in tcode_id_array:
            if flag_first:
                write_value(result_file, "\r\n\r\nID Unmapped: DD <=> TCODE:", False)
                flag_first = False
            id_unmapped_array.append(item_dd)

    id_unmapped_array.sort()
    write_list_value(result_file, id_unmapped_array)
    flag_first = True
    del id_unmapped_array[:]
    
    
    # Check Ids duplicated in TCODE
    for item_tcode in tcode_id_array:
        count = tcode_id_array.count(item_tcode)
        if count > 1:
            if flag_first:
                write_value(result_file, "\r\n\r\nID duplicated in TCODE:", False)
                flag_first = False
            string = item_tcode + " appeared %d times." %count
            id_unmapped_array.append(string)
            for temp in range (1, count):
                tcode_id_array.remove(item_tcode)
    
    id_unmapped_array.sort()
    write_list_value(result_file, id_unmapped_array)
    del id_unmapped_array[:]

    write_value(result_file, "\r\n\r\nCompleted check mapping ID !!!", False)
    print ("Completed check mapping ID: \"%s\"" %result_file)

def main():
    if len(sys.argv) < 7:
        showHelp()
    else:
        print ("\r\nStart tool check mapping FD <=> DD <=> TCODE\r\n")
        global config_array, error_list_array, dd_ref_array, dd_id_array, tcode_id_array
        config_array = []
        error_list_array = []
        dd_ref_array = []
        dd_id_array = []
        tcode_id_array = []
        global result_file
        result_file = sys.argv[6] + "/Result_Map(FD_DD_TCODE).txt"
         
        try:
            os.remove(result_file)
        except:
            pass
        
        # parse id in config file
        read_xlsx_file(sys.argv[2])
        # parse id in error list file
        read_xlsx_file(sys.argv[3])
        # parse id in dd file
        read_docx_file(sys.argv[4], sys.argv[1])
        # parse id in source code 
        read_c_sharp_file(sys.argv[5], sys.argv[1])
        
        # Compare id mapping
        comapre_ID_file(config_array, error_list_array, dd_ref_array, dd_id_array, tcode_id_array, result_file)
        print ("\r\nEnd tool check mapping FD <=> DD <=> TCODE")

        
if __name__ == '__main__':
    main()