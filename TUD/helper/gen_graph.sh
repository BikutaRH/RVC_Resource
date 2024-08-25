#!/usr/bin/sh
base_dir=`dirname $0`
dot_tool="$base_dir/graphviz-2.38/bin/dot.exe"

name="\n `echo $1 | sed s/####/'\\\n'/g ` \n\n"
#name=$1

dot_file="${2}.dot"
png_file="${2}.png"



echo "digraph \"{2}\"" > $dot_file
echo "{" >> $dot_file
echo "  edge [fontname=\"Helvetica\",fontsize=\"10\",labelfontname=\"Helvetica\",labelfontsize=\"10\"];" >> $dot_file
echo "  node [fontname=\"Helvetica\",fontsize=\"10\",shape=record];" >> $dot_file
echo "  Node2 [label=\"${name}\",height=0.2,width=0.4,color=\"black\", fillcolor=\"grey75\", style=\"filled\", fontcolor=\"black\"];" >> $dot_file
echo "}" >> $dot_file

$dot_tool -Tpng $dot_file -o $png_file
rm -f $dot_file
echo "${PWD}/$png_file"
