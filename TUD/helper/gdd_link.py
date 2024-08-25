#!/usr/bin/python
import sys
import re
import json

REF_DB = {}
DEBUG = 0

def creat_db(gddFile):
    global REF_DB
    # parsing gdd.json
    try:
        with open(gddFile, "r") as rfile:
            REF_DB = json.load(rfile)
    except:
        pass

def printState(state):
    if DEBUG == 0: return
    if state == 0:
        print ("RUN")
    elif state == 1:
        print ("FIND_FUNC")
    elif state == 2:
        print ("FIND_FUNC_END")
    else:
        print ("FUNC_END")


class StateEnum:
    def __init__(self):
        self.RUN = 0
        self.FIND_FUNC = 1
        self.FIND_FUNC_END = 2
        self.FUNC_END = 3


def parsing_cs(file):
    global REF_DB
    has_change = 0
    STATE = StateEnum()

    State = STATE.RUN

    quote_count = 0
    method  = ""
    printState(State)
    context = ""
    class_name = []
    current_cls = ''
    with open(file, 'r') as lines:
        for line in lines:
            matches = re.findall('^(public|private|internal)*\s*[partial]*[abstract]*\s*class\s*(\w*).*$', line.strip())
            if len(matches):
                for match in matches:
                    class_name.append(match[1])
                    current_cls = match[1]
            if line.strip().startswith("// Implementation:"):
                continue
            if State == STATE.RUN:
                matches = ""
                if line.strip().startswith("protected") or \
                    line.strip().startswith("public") or \
                    line.strip().startswith("override") or \
                    line.strip().startswith("private") and \
                    not "class" in line:
                    pattern = r'[\s*\w*]\s*\[*\]*(\w*)\('
                    matches = re.findall(pattern, line.strip())
                if len(matches):
                    quote_count = 0
                    method = matches[0]
                    State = STATE.FIND_FUNC
                    printState(State)
                    quote_count += line.count('{')
                    quote_count -= line.count('}')
            elif State == STATE.FIND_FUNC:
                if '{' in line:
                    State = STATE.FIND_FUNC_END
                    printState(State)

                quote_count += line.count('{')
                quote_count -= line.count('}')
            elif State == STATE.FIND_FUNC_END:

                quote_count += line.count('{')
                quote_count -= line.count('}')

                if quote_count == 0:
                    State = STATE.FUNC_END
                    printState(State)

            if State == STATE.FUNC_END:
                print (("[+] found method %s in class %s") % (method, class_name))
                line = add_tsdd(line, method, current_cls, class_name)
                has_change = 1
                State = STATE.RUN
                printState(State)
                
            ascii = re.sub(r'[^\x00-\x7f]+', '', line)
            context += ascii.rstrip() + "\r\n"
    if has_change == 1:
        with open(file, 'w') as outF:
            outF.write(context)

def add_tsdd(line, method, current_cls, class_name):
    gdd = None
    try: 
        class_ref = REF_DB[current_cls]
        gdd = class_ref[method]
    except Exception as e:
        print(e)
        gdd = None
    if gdd is None:
        for cls in class_name:
            try: 
                class_ref = REF_DB[cls]
                gdd = class_ref[method]
                if gdd is not None:
                    break
            except:
                gdd = None
    
    if gdd is not None:
        print (("class_name: %s   gdd: %s") %(class_name, gdd))
        print (("    [-] Link method: %s to GDD: %s in class %s") %(method, gdd, class_name))
        imp = line.rstrip().replace('}', "// Implementation: " + gdd)
        line = line + imp
    return line

def usage():
    print ("=============================================================================")
    print ("Script help to add link from method to GDD number")
    print ("Method should start with protected|private|public")
    print ("Execute as below syntax:")
    print (" %s gdd.json source.cs") % sys.argv[0]
    print ("=============================================================================")

def main(argv):
    creat_db(argv[1])
    parsing_cs(argv[2])

if __name__ == '__main__':
    if len (sys.argv) == 3:
        main(sys.argv)
    else:
        usage()

