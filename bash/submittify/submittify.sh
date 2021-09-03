#!/bin/bash
# submittify.sh - cleans up a .tex file for its submission on the arXiv
# or to a journal. Bundles the bibliography, removes comments, and renames 
# the figures. 
# To run it, start from the folder where you have *freshly compiled* your 
# manuscript PREFIX.tex, then run
# $ submittify.sh PREFIX DESTINATION/
# The prettifyied files will be generated in the DESTINATION/ folder

PREFIX="${1%.tex}"
DEST="$2"
if [ -z "$DEST" ]; 
then
    DEST="./submit"
fi

if [ ! -d "$DEST" ]
then
    mkdir "$DEST"
fi

echo Modifying project "$PREFIX" for APS submit. Output in "$DEST"

function get_lines
{
    (( nlines=$2-$1+1 ))
    head -n $2 | tail -n $nlines
}


cp "${PREFIX}.tex" __sb_tmp1

#encapsulates macro definitions and include files in general

MACROS=`grep \\\input\{ __sb_tmp1 | sed -e '{s/.*input[^{]*{ *\([^}]*\) *}.*/\1/}'`
while [ "$MACROS" ]; do  # iteratively includes inputs
  for a in $MACROS
  do
    echo "INCLUDING MACRO $a"
    LN=`grep -n \\\input"{$a}" __sb_tmp1`
    LN=${LN%%[^0-9]*}
    ((PRE=$LN-1))
    ((POST=$LN+1))
    head -n $PRE __sb_tmp1 > __sb_tmp2
    if [ -e "$a" ]; then cat "$a" >> __sb_tmp2
    else if [ -e "$a.tex" ]; then cat "$a.tex" >> __sb_tmp2
    fi;fi;
    echo "" >> __sb_tmp2
    tail -n +$POST __sb_tmp1 >> __sb_tmp2
    mv __sb_tmp2 __sb_tmp1
  done
  MACROS=`grep \\\input\{ __sb_tmp1 | sed -e '{s/.*input[^{]*{ *\([^}]*\) *}.*/\1/}'`
  echo "NEW MACROS " $MACROS
done

#removes comments from file
sed -i 's/\(^\|[^\\]\)%.*$/\1%/' __sb_tmp1
sed -i 's/\(^.*\)\\begin{comment}.*$/\1\n\\begin{comment}/' __sb_tmp1
sed -i 's/^.*\\end{comment}\(.*$\)/\\end{comment}\n\1/' __sb_tmp1
awk 'BEGIN{icmd=0} /\\begin{comment}/{icmd+=1} {if (icmd==0) print $0} /\\end{comment}/{icmd-=1}' __sb_tmp1 > __sb_tmp2
mv __sb_tmp2 __sb_tmp1 

#replaces and renames figures according to the figNUMBER.sub PRX scheme
S_FLOATS=( $(grep -n -e "\\\\begin{\(figure\|SCfigure\|sidewaysfigure\|table\)[*]*}" __sb_tmp1 | sed -e '{s/\(^[0-9]*\):.*$/\1/}') )
E_FLOATS=( $(grep -n -e "\\\\end{\(figure\|SCfigure\|sidewaysfigure\|table\)[*]*}" __sb_tmp1 | sed -e '{s/\(^[0-9]*\):.*$/\1/}') )

k=0
for (( i=0; i< ${#S_FLOATS[@]}; i++ ));
do
  FIGS=( $(cat __sb_tmp1 | get_lines ${S_FLOATS[$i]} ${E_FLOATS[$i]} | grep includegraphic | sed -e '{s/.*includegraphics[^{]*{ *\([^{]*\) *}.*/\1/}') )
  echo "FLOAT $i:" ${S_FLOATS[$i]} ${E_FLOATS[$i]}
  echo "${#FIGS[@]} FIGURES:" ${FIGS[@]}
  if [  ${#FIGS[@]} -gt 0 ]; then (( k++ )); fi
  for (( j=0; j< ${#FIGS[@]}; j++ ))
  do
    ao=${FIGS[$j]}
    a=$(echo "$ao" | sed -e '{s/\//\\\//g}')
    EXT=${ao#${ao%???}} 
    ((b=$j+1))
    if [  ${#FIGS[@]} -eq 1 ]; then c=$k; else c=${k}_${b}; fi
    cp "$ao" "$DEST/fig$c.$EXT"    
    sed -e "{s/\(includegraphics[^{]*{ *\)$a *}/\1fig$c.$EXT}/}"  __sb_tmp1 > __sb_tmp2
    mv __sb_tmp2 __sb_tmp1
  done
done

#if a bibtex bibliography file is present, it is included into the file
if [ -e "${PREFIX}.bbl" ]
then
	LN=`grep -n "bibliography{" __sb_tmp1`
	LN=${LN%%[^0-9]*}
	TOTL=`cat __sb_tmp1 | wc -l `
        echo "LINES " $LN  " " $TOTL 
	(( PRE=$LN-1 ))
	(( POST=$TOTL-$LN ))
	head -n $PRE __sb_tmp1 > "$DEST/text.tex"
	cat "${PREFIX}.bbl" >> "$DEST/text.tex"
	tail -n $POST __sb_tmp1 >> "$DEST/text.tex"
else
	echo "${PREFIX}.bbl file does not exist. Resulting tex file will lack included BiBTeX bibliography";
fi

rm __sb_tmp[12] -f 2> /dev/null
