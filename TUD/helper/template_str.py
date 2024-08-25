import time
diagram_comment = '''
<< In section 4.X, parent class is defined. In section 4.X.X, class fields and methods which belong to 4.X parent class is defined>>
This section contains class diagram and list of the function for <MSN> Generation Tool.
'''

heading = {
    'classname': 1,
    'classnamespace': 2,
    'fieldstopic': 3,
    'methodstopic': 3,
    'fileds': 4,
    'methods': 4
}

template_filepath = r'template.docx'
#output_filepath = r'output%d.docx' % int(time.time())
output_filepath = r'output_dd.docx'

class_disigned_id = "MEMACC_TUD_CLS_%03d_%03d:"
class_ref_req = '{Ref: [x] <Requirement number>}'
class_ref_config = '{Ref: [3] %s}'   #5 : Index of configuration file in DD file
class_ref_configBase = '{Ref: [3] %s, %s}'
class_ref_errList = '{Ref: [1] MEMACC_TAD_%s_%s}'   #2 : Index of error list file in DD file
class_ref_NA = '{Ref: N/A}'
class_ref_dd_old = '{Ref: %s}'  # Reused ref in old DD