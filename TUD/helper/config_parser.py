#!/usr/bin/python
from xlrd import open_workbook
import re
import  sys
import json

start_column = 0

def showHelp():
    print ("This tool is ...")

def read_xml_file(xlsFile):
    MAP_CONFIG = {}
    wb = open_workbook(xlsFile)
    for sheet in wb.sheets():
        #print sheet.name
        #print sheet.ncols
        #print sheet.nrows
        
        # Don't check sheet not used
        if sheet.name == "Cover" or sheet.name == "Reference":
            continue
        
        number_of_rows = sheet.nrows
        # print("number_of_rows", number_of_rows)

        start_column = 1
        for row in range(1, number_of_rows):
            if sheet.cell(row, 0).value != '':
                start_column = 0
        
        for row in range(1, number_of_rows):
            try:
                value1 = (sheet.cell(row, start_column).value).strip()
                # print("v1 = ", value1)
                # Handle for STATIC structure
                value2 = ""
                valueTemp = sheet.cell(row, start_column + 1).value.strip()
                # print("v Temp = ", valueTemp)
                if "STATIC" in valueTemp:
                    value2 = re.findall(r'^(\w*)', valueTemp[7:len(valueTemp)-6])
                else:
                    value2 = re.findall(r'^(\w*)', valueTemp)
                    # print("v2 = ", value2)
                # Try next cell
                if len(value2[0].strip()) == 0:
                    value2 = re.findall(r'^(\w*)', sheet.cell(row, start_column + 2).value.strip())
                    # print("v2 strip = ", value2)
                
                if len(value1) > 0 and len(value2[0].strip()) > 0:
                    MAP_CONFIG[value1] = value2[0]
                    
            except:
                pass
    # print(MAP_CONFIG)            
    return MAP_CONFIG

def main():
    if len(sys.argv) < 2:
        showHelp()
    else:
        map_config = read_xml_file(sys.argv[1])
        
    with open("configuration.json", 'w') as cjson:
        json.dump(map_config, cjson, indent=2)

if __name__ == '__main__':
    main()