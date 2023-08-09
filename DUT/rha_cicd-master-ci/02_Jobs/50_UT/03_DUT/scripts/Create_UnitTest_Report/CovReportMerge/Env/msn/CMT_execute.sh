#!/bin/sh

if [ ! -d "ctr_log" ]; then
  mkdir ctr_log
fi
if [ ! -d "log" ]; then
  mkdir log
fi

while read TARGET
do

  # Create ctr extraction file
  find . -name *.ctr -print -exec grep entry {} \; | grep ${TARGET}.c >& ctr_log/${TARGET}_ctr_entry.txt
  find . -name *.ctr -print -exec grep call  {} \; | grep ${TARGET}.c >& ctr_log/${TARGET}_ctr_call.txt
  find . -name *.ctr -print -exec grep stmnt {} \; | grep ${TARGET}.c >& ctr_log/${TARGET}_ctr_stmnt.txt
  find . -name *.ctr -print -exec grep -e decn -e switch {} \;  | grep ${TARGET}.c| sed -e '/decn[ 0-9]*\r/N;s/\r\n/ /g' > ctr_log/${TARGET}_ctr_decn.txt
  find . -name *.ctr -print -exec grep expr  {} \;  | grep ${TARGET}.c>& ctr_log/${TARGET}_ctr_expr.txt
  find . -name *.ctr -print -exec grep oper  {} \;  | grep ${TARGET}.c>& ctr_log/${TARGET}_ctr_oper.txt
  find . -name *.ctr | xargs grep expr -h | grep -e "effective" -e "NOT EFFECTIVE" -h  | grep ${TARGET}.c>& ctr_log/${TARGET}_ctr_efct.txt

  # Merge ctr file
  ../../CMT/exec/ctr_analysis.exe -id ctr_log/${TARGET}_ctr_entry.txt -target ${TARGET}.c -category entry -silent >& ctr_log/${TARGET}_ctr_entry_log.txt
  ../../CMT/exec/ctr_analysis.exe -id ctr_log/${TARGET}_ctr_call.txt -target ${TARGET}.c -category call -silent >& ctr_log/${TARGET}_ctr_call_log.txt
  ../../CMT/exec/ctr_analysis.exe -id ctr_log/${TARGET}_ctr_stmnt.txt -target ${TARGET}.c -category stmnt -silent >& ctr_log/${TARGET}_ctr_stmnt_log.txt
  ../../CMT/exec/ctr_analysis.exe -id ctr_log/${TARGET}_ctr_decn.txt -target ${TARGET}.c -category decn -silent >& ctr_log/${TARGET}_ctr_decn_log.txt
  ../../CMT/exec/ctr_analysis.exe -id ctr_log/${TARGET}_ctr_expr.txt -target ${TARGET}.c -category expr -silent >& ctr_log/${TARGET}_ctr_expr_log.txt
  ../../CMT/exec/ctr_analysis.exe -id ctr_log/${TARGET}_ctr_oper.txt -target ${TARGET}.c -category oper -silent >& ctr_log/${TARGET}_ctr_oper_log.txt
  ../../CMT/exec/ctr_analysis.exe -id ctr_log/${TARGET}_ctr_efct.txt -target ${TARGET}.c -category efct -silent >& ctr_log/${TARGET}_ctr_efct_log.txt

  # Create Coverage result file list
  find . -name ${TARGET}_c.doc > ${TARGET}_c_list.txt


# Loop for file list
done < ./target.txt

../../CMT/exec/CompileCheck.py $(cygpath -w $PWD)
