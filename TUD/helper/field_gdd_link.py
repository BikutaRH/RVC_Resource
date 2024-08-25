#!/usr/bin/python
import sys
import re
import json

REF_DB = {}
DEBUG = 0

def creat_db(gddFile):
    global REF_DB
    # parsing field_gdd.json
    try:
        if gddFile is not '':
            with open(gddFile, "r") as rfile:
                REF_DB = json.load(rfile)
    except:
        pass
            
           
def add_tsdd(line, field, current_cls, class_name):
    try: 
        class_ref = REF_DB[current_cls]
        gdd = class_ref[field]
    except Exception as e:
        gdd = None
    if gdd is None:
        for cls in class_name:
            try: 
                class_ref = REF_DB[cls]
                gdd = class_ref[field]
                if gdd is not None:
                    break
            except:
                gdd = None
                
    if gdd is not None:
        print ("    [-] Link field: %s to GDD: %s in class %s") %(field, gdd, class_name)
        imp = line.rstrip().replace(line.strip(), '') + "// Implementation: " + gdd
        line = line.rstrip() + "\r\n" + imp
    return line
    
def parsing_cs(file):
    global REF_DB
    has_change = 0
    context = ""
    field = ''
    class_name = []
    current_cls = ''
    with open(file, 'r') as lines:
        for line in lines:
            matches = re.findall('^(public|private|internal)*\s*[partial]*[abstract]*\s*class\s*(\w*).*$', line.strip())
            if len(matches):
                for match in matches:
                    current_cls = match[1]
                    class_name.append(current_cls)
                    print (class_name)
            if re.match(r'^\/\/\sImplementation\:\s*[\w<>]*$', line.strip()):
                continue
            line = re.sub(r'[^\x00-\x7f]+', '', line)
            try:
                for field in REF_DB[current_cls].keys():
                    tmp = line.split('=')[0]
                    lll = len(tmp.split())
                    l = line.replace(' ', '')
                    if (lll >= 2 and (field + ';' in l or field + '=' in l or field + '{get;set;}=' in l or field + '{get;set;}' in l) and 
                    '==' not in line and ' for ' not in line and '///' not in line):
                        print ("[+] found field: %s in class %s") % (field, class_name)
                        line = add_tsdd(line, field, current_cls, class_name)
                        has_change = 1
					
            except:
                pass
            context += line.rstrip() + "\r\n"

    if has_change == 1:
        with open(file, 'w') as outF:
            outF.write(context)

def usage():
    print ("=============================================================================")
    print ("Script help to add link from field to GDD number")
    print ("Field should start with protected|private|public and declare in one line")
    print ("Execute as below syntax:")
    print (" %s field_gdd.json source.cs") % sys.argv[0]
    print ("=============================================================================")
def main(argv):
    creat_db(argv[1])
    parsing_cs(argv[2])

if __name__ == '__main__':
    if len (sys.argv) == 3:
        main(sys.argv)
    else:
        usage()

