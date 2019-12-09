#!/bin/bash
# patch translations

filespath="../icon-themes/ossii/translations/online"

echo patch translations....
cd translations

if test $1 = "9" ; then
    for filename in $filespath/*.patch;
    do 
        if test -e $filename.done; then
            echo ${filename##*/} patched!
        else
            echo ${filename##*/} patching...;
            git am $filename > /dev/null 2>&1
            touch $filename.done
        fi
    done
fi

cd -
