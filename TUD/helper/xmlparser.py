import xml.etree.ElementTree as ET
import re
import ntpath

class ClassInfo:
    def __init__(self):
        self.Name = ''
        self.Description = 'None'
        # Fields
        self.PublicFields = []
        self.ProtectedFields = []
        self.PrivateFields = []
        # Methods
        self.PublicMethods = []
        self.ProtectedMethods = []
        self.PrivateMethods = []
        self.FileName = 'None'

    def getNameOnly(self):
        return self.Name.split(':')[-1]


class MethodInfo:
    def __init__(self):
        self.Name = ""
        self.Type = "None"
        self.Args = []
        self.ReturnStr = ["None", "None"]
        self.GeneatedValue = "None"
        self.Description = "None"
        self.Range = "None"
        self.Algorithm = "None"
        self.File = ""
        self.Line = 0
        #Huy
        self.Ref = "N/A"
        pass

    pass


def getfield(memberdef):
    return getmethod(memberdef)


def getmethod(memberdef):
    method = MethodInfo()
    # Name
    method.Name = memberdef.find('name').text
    
    # File & line
    for location in memberdef.iter('location'):
        print ((" [-] location: "), ntpath.basename(location.attrib['file']))
        method.File = location.attrib['file']
        method.Line = int(location.attrib['line'])
        break
    

    # Description
    briefdescription = memberdef.find('briefdescription')
    if briefdescription != None:
        para = briefdescription.find('para')
        if (para != None):
            ref = para.find('ref')
            if (ref != None):
                method.Description = para.text + ref.text
            else:   
                method.Description = para.text

    # Type
    t = memberdef.find('type')
    if t != None:
        method.Type = t.text.strip() if t.text is not None else ''
        for child in t:
            method.Type += ' ' + child.text
    method.Type = method.Type.strip()

    # Arguments
    args = []
    for param in memberdef.findall('param'):
        type = param.find('type').text if param.find('type') is not None else "None"
        declname = param.find('declname').text if param.find('declname') is not None else "None"

        type = type if type else ''
        declname = declname if declname else ''
        args.append([type + ' ' + declname])

    i = 0
    detaileddescription = memberdef.findall('detaileddescription')
    if len(detaileddescription) > 0:
        for parameterdescription in detaileddescription[0].iter("parameterdescription"):
            para = parameterdescription.find('para').text if parameterdescription.find('para') is not None else ''
            if para is not None and i < len(args):
                para = para.replace("<range>", "$").replace("</range>", "$")
                temp = para.split('$')
                desc = temp[0] if len(temp) > 0 else 'None'
                desc = desc.replace("<desc>", "").replace("</desc>", "") #Huy edit
                ran = temp[1] if len(temp) > 1 else 'None'
                args[i].append(desc)
                args[i].append(ran)
            elif  i < len(args):
                args[i].append('None')
                args[i].append('None')
            i += 1
            if i >= len(args):
                break
    method.Args = args

    # # generated_value, Reference == Huy Doan
    # ref = ''

    i = 0
    ref = 'N/A'
    detaileddescription = memberdef.findall('detaileddescription')
    if len(detaileddescription) > 0:
        paras = detaileddescription[0].findall("para")
        print("Huy - method name = ", method.Name)
        print("len of para = ", len(paras))
        if len(paras) > 1: 
            if paras[1].text != None:
                print("huy - parar1 = ",paras[1].text )
                if "<generated_value>" in paras[1].text and "</generated_value>" in paras[1].text and "<ref>" in paras[1].text and "</ref>":
                    paraContent = paras[1].text
                    print("Huy - paraContent = ",  paraContent)
                    generate = paraContent.replace('<generated_value>', '$').replace('</generated_value>', '$')
                    temp_generateValue = generate.split("$")
                    print("Huy - temp_generateValue = ", temp_generateValue)
                    method.GeneatedValue = temp_generateValue[1].strip() if len(temp_generateValue) > 0 else ""
                    print("Huy - GeneatedValue = ", method.GeneatedValue)
                    ref = temp_generateValue[2].replace('<ref>', '$').replace('</ref>', '$')
                    temp_ref = ref.split("$")
                    method.Ref = temp_ref[1].strip() if len(temp_ref) > 0 else ""
                    print("Huy - Ref = ", method.Ref)
                elif paras[2].text != None:
                    print("huy - parar2 = ",paras[2].text )
                    if "</generated_value>" in paras[2].text and "<ref>" in paras[2].text and "</ref>":
                        paraContent1 = paras[1].find('heading').text if paras[1].find('heading') is not None else ''
                        method.GeneatedValue = paraContent1.strip()
                        print("Huy - GeneatedValue = ", method.GeneatedValue)
                        paraContent2 = paras[2].text
                        print("Huy - paraContent2 = ",  paraContent2)
                        generate = paraContent2.replace('</generated_value>', '$')
                        temp_generateValue = generate.split("$")
                        print("Huy - temp_generateValue = ", temp_generateValue)
                        ref = temp_generateValue[1].replace('<ref>', '$').replace('</ref>', '$')
                        temp_ref = ref.split("$")
                        method.Ref = temp_ref[1].strip() if len(temp_ref) > 0 else ""
                else:
                    print("Error: check description in T-Code to get reference")

            # Format ref
            if "_DAD_" in method.Ref:
                method.Ref = "{Ref: [3] "+ method.Ref + '}'
            elif "_TAD_" in method.Ref:
                method.Ref = "{Ref: [1] "+ method.Ref + '}'
            else:
                method.Ref = "{Ref: "+ method.Ref + '}'
            
            print("Huy - Ref = ", method.Ref)
        
    # method.Args.append((type + ' ' + declname, range_val, description))

    # Return
    detaileddescription = memberdef.find('detaileddescription')
    if detaileddescription != None:
        para = detaileddescription.find('para')
        if para != None:
            simplesect = para.find('simplesect')
            if simplesect != None:
                para1 = simplesect.find('para')
                if para1 != None:
                    text = para1.text
                    if text is not None:
                        text = text.replace('<range>', '$').replace('</range>', '$')
                        temp = text.split("$")
                        method.ReturnStr[0] = temp[0].replace("<type>", "Type: ").replace("</type>", "").replace("<name>", "\nName: ").replace("</name>", "").replace("<section>", "\nSection: ").replace("</section>", "").replace("<desc>", "\nDesc: ").replace("</desc>", "").strip() if len(temp) > 0 else "" #Huy Edit
                        method.ReturnStr[1] = temp[1].strip() if len(temp) > 1 else ""
            
            text = str(simplesect.tail) if simplesect is not None else ''
            # print('Huy - tail')
            # print(text)
            try:
                # method.Ref = text.split('<ref>')[1].split('</ref>')[0]
                # method.GeneatedValue = text.split('<generated_value>')[1].split('</generated_value>')[0]
                algorithm = text.split('<algorithm>')[1].split('</algorithm>')[0]
                for line in para.findall('linebreak'):
                    algorithm += '\n' + line.tail
                algorithm = algorithm.replace('</algorithm>', '')
            except:
                # method.GeneatedValue = ''
                algorithm = ''
                pass
            if algorithm is not None: method.Algorithm = algorithm
    return method


def parse(filename):
    class_info = None
    tree = ET.parse(filename)
    root = tree.getroot()

    # Class Name
    for compounddef in root.iter('compounddef'):
        class_info = ClassInfo()
        class_info.FileName = ntpath.basename(filename)
        # Class Name
        for compoundname in compounddef.iter('compoundname'):
            class_info.Name = compoundname.text

        # Class description
        briefdescription = compounddef.find('briefdescription')
        if briefdescription != None:
            para = briefdescription.find('para')
            if para != None:
                class_info.Description = para.text

        #Huy - section
        ## Reference to AD

        #end Huy - section
        # location
        for location in compounddef.iter('location'):
            print ((" [-] location: "), ntpath.basename(location.attrib['file']))
            class_info.FileName = ntpath.basename(location.attrib['file'])
            break

        # Childs
        for sectiondef in compounddef.iter('sectiondef'):
            print ((" [-]"), sectiondef.tag, sectiondef.attrib)

            if sectiondef.attrib['kind'].endswith('attrib') :
                if sectiondef.attrib['kind'].startswith('public'):
                    childs = class_info.PublicFields
                elif sectiondef.attrib['kind'].startswith('protected'):
                    childs = class_info.ProtectedFields
                else:
                    childs = class_info.PrivateFields

                for memberdef in sectiondef.iter('memberdef'):
                    method = getfield(memberdef)
                    childs.append(method)
                    print("Huy - Method information 1")
                    print (('  [+] Huy: '), method.Name, method.Type, method.Description, method.Args, method.GeneatedValue, method.Ref, (method.ReturnStr))
            
            elif sectiondef.attrib['kind'].endswith('func'):
                if sectiondef.attrib['kind'].startswith('public'):
                    childs = class_info.PublicMethods
                elif sectiondef.attrib['kind'].startswith('protected'):
                    childs = class_info.ProtectedMethods
                else:
                    childs = class_info.PrivateMethods

                for memberdef in sectiondef.iter('memberdef'):
                    method = getmethod(memberdef)
                    childs.append(method)
                    print("Huy - Method information 2")
                    print (('  [+] Huy: '), method.GeneatedValue, method.Ref)
            
            elif sectiondef.attrib['kind'].endswith('property'):
                childs = class_info.PublicFields
                for memberdef in sectiondef.iter('memberdef'):
                    method = getmethod(memberdef)
                    childs.append(method)
                    print("Huy - Method information 3")
                    print (('  [+] Huy: '), method.Name, method.Type)
            
    return class_info


if __name__ == '__main__':
    pass
