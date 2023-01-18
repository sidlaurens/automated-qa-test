#!/bin/bash

#Test points.
file_mach="/etc/brain/machine"
file_firm="/etc/brain/firmware_updated"
dir_home="~"
dir_rdb="/var/lib/brain/route_database"
dir_rstore="/var/lib/brain/route_database/route_store"
dir_rindex="/var/lib/brain/route_database/route_index"
link_curr="/var/lib/brain/route_database/route_index/current"
dir_vrp="/var/lib/brain/versioned_robot_parameters"

#----------SESSION VARIABLES

#Get latest targeted version.
(rocp -r $2 --history updates | grep -i targetVersion | egrep -o '[0-9]+([.][0-9]+)+([.][0-9])?') > versions.txt
sort -Vro versions.txt versions.txt
target_os=$(head -n 1 versions.txt)
#Get current running O/S version from machine.
rem_sess=$(roc legacy session -u $1 connect -s $2)
remote_os=$($rem_sess "cat /etc/os-release | grep -i brainos_version | cut -d 'v' -f 2")

#----------FUNCTIONS
#Transform software version to make it comparable.
version () { echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }'; }

#Test if object is a directory.
dir_check () {
fail_check=false

if [[ ! -d $1 ]] ; then
    fail_check=true
fi

if [[ $fail_check = true ]] ; then
    return 1
fi
return 0
}

#Test directory ownership.
dir_chown () {
fail_check=false

if [[ ! -O $1 ]] || [[ ! -G $1 ]] ; then
    fail_check=true
fi

if [[ $fail_check = true ]] ; then
    return 1
fi
return 0
}

#Test if directory is empty, then test content ownership.
dir_contents () {
fail_check=false

if [[ $(ls -A $1) ]] ; then
    ls -hl $1
    for file in "$1"/*; do
        if [ ! -O "$file" ] || [ ! -G "$file" ] ; then
             fail_check=true
         fi
    done
else
    fail_check=true
fi

if [[ "$fail_check" = true ]] ; then
    return 1
fi
return 0
}

#Test if subdirectories are empty, then test each subdirectory ownership.
subdir_check () {
for dir in $(find $1 -mindepth 1 -type d); do
    if [ "$(ls -A $dir)" ] ; then
        printf "$dir\n"
        ls -hl $dir
        for file in "$dir"/*; do
            if [ ! -O "$file" ] || [ ! -G "$file" ] ; then
                fail_check=true
            fi
        done
    else
        fail_check=true
    fi
done

if [[ $fail_check = true ]] ; then
    return 1
fi
return 0
}

echo

#Start the test.
$rem_sess << EOF

echo

$(typeset -f version)
$(typeset -f dir_check)
$(typeset -f dir_chown)
$(typeset -f dir_contents)
$(typeset -f subdir_check)

test_fail=false

#========================================================================================
#                                     SYSTEM CHECKS
#========================================================================================
#--------O/S VERSION
echo "SYS- O/S: $remote_os"
if [ $(version $target_os) -gt $(version $remote_os) ]; then
    echo "SYS- **Target this rin to v$target_os before shipping.**"
fi

#--------BOARD VERSION
# Machine type file format: [uint16]version [unit16]str_length [ascii] robot_type_str
machine=\$(tail -c +5 $file_mach)
if [ \${machine:0:5} == "cert_" ]; then
    echo "SYS- Board version: 129"
else
    echo "SYS- Board version: 115"
fi

#--------MACHINE TYPE
mach_type=\$(journalctl -b | grep -i machinetype | head -1 | cut -d'"' -f 4)
echo "SYS- Machine type: \$mach_type"

#--------SSD DETAILS
ssd_detail=\$(journalctl -b -u smartd.service | egrep -i "SATA SSD" | tr -s ' ' | cut -d ',' -f 2,3,4)
if [ -z "\$ssd_detail" ]; then
    ssd_detail=\$(journalctl -b -u smartd.service | egrep -i "KINGSTON " | tr -s ' ' | cut -d ',' -f 2-6)
    if [ -z "\$ssd_detail" ]; then
        ssd_detail=\$(journalctl -b -u smartd.service | egrep -i "WDC " | cut -d ',' -f 2-6)
    fi
fi
echo "SYS- SSD Details:\$ssd_detail"
echo
#========================================================================================
#                                       TEST START
#========================================================================================
echo "--HOME DIRECTORY CONTENTS--"
ls -hl
if [ -z "\$(ls $dir_home)" ] ; then
    echo "PASS"
else
    echo "FAIL"
    test_fail=true
fi
echo


echo "--FIRMWARE UPDATED--"
ls -hl $file_firm
if [ -f $file_firm ] ; then
    echo "FAIL"
    test_fail=true
else
    echo "PASS"
fi
echo


echo "--MACHINE TYPE--"
if [ -e $file_mach ]; then
    cat $file_mach
    echo
    echo "PASS"
    if [ -s $file_mach ] || [ -r $file_mach ] ; then
        echo "PASS"
        if grep -qF "\$mach_type" $file_mach ; then
            echo "PASS"
        else
            echo "Machine type: \$mach_type"
            echo "FAIL"
            test_fail=true
        fi
    else
        echo "FAIL"
        test_fail=true
    fi
else
    echo "FAIL"
    echo "FAIL"
    echo "FAIL"
    test_fail=true
fi
echo


echo "--BUNDLE ID--"
if journalctl -u brain-machine-restore.service | egrep -i "restoring|$3"; then
    echo "PASS"
else
    echo "FAIL"
    test_fail=true
fi

if journalctl -u brain-machine-restore.service | egrep -i "finished restore"; then
    echo "PASS"
else
    echo "FAIL"
    test_fail=true
fi
echo


echo "--ROUTE DATABASE--"
dir_check $dir_rdb
fileck_val=\$?
if [[ \$fileck_val -ne 0 ]] ; then
    printf "FAIL"
    test_fail=true
else
    echo "PASS"
    dir_chown $dir_rdb
    fileck_val=\$?
    if [[ \$fileck_val -ne 0 ]] ; then
        echo "FAIL"
        test_fail=true
    else
        echo "PASS"
        dir_contents $dir_rdb
        fileck_val=\$?
        if [[ \$fileck_val -ne 0 ]] ; then
            echo "FAIL"
            test_fail=true
        else
            echo "PASS"
        fi
    fi
fi
echo


echo "--ROUTE STORE--"
dir_check $dir_rstore
fileck_val=\$?
if [[ \$fileck_val -ne 0 ]] ; then
    printf "FAIL"
    test_fail=true
else
    echo "PASS"
    dir_contents $dir_rstore
    fileck_val=\$?
    if [[ \$fileck_val -ne 0 ]] ; then
        echo "FAIL"
        test_fail=true
    else
        echo "PASS"
    fi
fi
echo


echo "--ROUTE INDEX--"
dir_check $dir_rindex
fileck_val=\$?
if [[ \$fileck_val -ne 0 ]] ; then
    printf "FAIL"
    test_fail=true
else
    echo "PASS"
    dir_contents $dir_rindex
    fileck_val=\$?
    if [[ \$fileck_val -ne 0 ]] ; then
        echo "FAIL"
        test_fail=true
    else
        echo "PASS"
    fi
fi
echo


echo "--CURRENT--" 
if [ -L $link_curr ]; then
    echo "$link_curr"
    cat $link_curr
    echo "PASS"
    if [ -s $link_curr ]; then
        echo "PASS"
    else
        echo "FAIL"
        test_fail=true
    fi
else
    echo "FAIL"
    echo "FAIL"
    test_fail=true
fi

echo


echo "--CALIBRATION FILES--"
dir_check $dir_vrp
fileck_val=\$?
if [[ \$fileck_val -ne 0 ]] ; then
    printf "FAIL"
    test_fail=true
else
    echo "PASS"
    dir_chown $dir_vrp
    fileck_val=\$?
    if [[ \$fileck_val -ne 0 ]] ; then
        echo "FAIL"
        test_fail=true
    else
        echo "PASS"
        dir_contents $dir_vrp
        fileck_val=\$?
        if [[ \$fileck_val -ne 0 ]] ; then
            echo "FAIL"
            test_fail=true
        else
            echo "PASS"
            subdir_check $dir_vrp
            fileck_val=\$?
            if [[ \$fileck_val -ne 0 ]] ; then
                echo "FAIL"
                test_fail=true
            else
                echo "PASS"
            fi
        fi
    fi
fi

echo
echo

#Exit session accordingly.
if [ "\$test_fail" = true ] ; then 
	exit 1
fi

exit 0

EOF


