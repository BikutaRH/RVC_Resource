#!/usr/bin/sh

work=$PWD
base_dir=`dirname $0`
doc_gen_tool=$base_dir/doc_gen.py
doxy_file=$base_dir/Doxyfile
doxy_tool=$base_dir/doxygen-1.8.16.windows.x64.bin/doxygen.exe
check_docx=$base_dir/check_docx.py
config_parser=$base_dir/config_parser.py
gdd_link=$base_dir/gdd_link.py
field_gdd_link=$base_dir/field_gdd_link.py
dot_path=$base_dir/graphviz-2.38/bin
check_mapping=$base_dir/check_mapping_result.py
check_mapping_result=$work/doc

config_file=`ls /cygdrive/u/internal/Module/mem/04_AD/01_WorkProduct/R-Car_U5x_MEMACC_Configuration.xlsx`
error_list_file=`ls /cygdrive/u/internal/Module/mem/04_AD/01_WorkProduct/R-Car_U5x_MEMACC_GenTool_ErrorList.xlsx`

module_specific="MEMACC_TUD_CLS_\d+_\d+"
source_code_path="MEMACC\\"

# Initialize
mkdir -p $work/doc
touch $work/doc/configuration.json
cd $work/doc

export PATH=$PATH:$dot_path

#Step 1. config_parser , output "configuration.json" file
if [[ -f $config_file ]]; then
    $config_parser $config_file
    echo "Huy1 - config_parser"
fi
#Step 2. DocGen
check_docx_result=`$check_docx`
if [ ! "$check_docx_result" == "OK" ]
then
    echo "Huy2 - DocGen"
	cd $base_dir
	echo "Install python docx"
	tar xf python-docx-0.8.6.tar.gz
	cd python-docx-0.8.6
	python setup.py install
	cd $work/doc
fi

#Remove old output DD
if [[ -f $detail_design_file ]]; then
    rm $detail_design_file
fi

#back up resource .cs
find $work -name "*Design*.cs" | while read line;
do
    echo "[+] Back up ${line}"
    new_name="${line}.bk"
    mv "${line}" "${new_name}"
done

cp $doxy_file .
$doxy_tool
$doc_gen_tool xml

#restore resource .cs
find $work -name "*Design*.cs.bk" | while read line;
do
    bk=".bk"
    nf="`echo $line | sed s/${bk}//`"
    echo "[+] Restore ${nf}"
    mv "${line}" "${nf}"
done

# Step 3. Add GDD link
find $work -name "*.cs" | while read line; 
do 
    # Remove old Implementation
    # sed -i 's/^\/\/ Implementation: MEMACC_TUD_FST_001/\/\/GENTOOL_DD_DOCX/' $line
    # sed -i '/^ *\/\/ Implementation: MEMACC_TUD_CLS_/d' $line
	# sed -i '/^ *\/\/Implementation: MEMACC_TUD_CLS_/d' $line
    
    $gdd_link "gdd.json" $line

    # sed -i 's/Implementation/Method_Implementation/g' $line

    $field_gdd_link "field_gdd.json" $line

    # sed -i 's/Method_Implementation/Implementation/g' $line

    # Revert to old generic Id
    # sed -i 's/\/\/GENTOOL_DD_DOCX/\/\/ Implementation: MEMACC_TUD_FST_001/' $line
    
    unix2dos $line
done

cd $work

# Step 4. Check ID mapping result
detail_design_file=`ls $work/doc/output_dd.docx`

if [[ -f $config_file ]] && [ -f $error_list_file ] && [ -f $detail_design_file ]; then
    $check_mapping $module_specific $config_file $error_list_file $detail_design_file $source_code_path $check_mapping_result 
fi



