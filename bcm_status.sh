#!/bin/bash

y_cor=2
x_cor=8

clear

printf "CHECKING CONNECTION STATUS OF $2\n\n"

printf "STATUS: "

tput cup $y_cor $x_cor
printf "\xe2\x97\xaf  CHECKING..."

status=$(rocp -r $2 -S | grep -i 'connectionstatus' | cut -d'"' -f 4)

if [ "$status" == "desynced" ] || [ "$status" == "online" ] ; then
    tput cup $y_cor $x_cor
    printf "\e[1m\e[32m\xe2\xac\xa4\e[0m\033[0K  ONLINE\n"
    printf "TESTING CONNECTION...\n"

    session=$(roc legacy session -u $1 connect -s $2 | cut -d ' ' -f 2,3,4)
    err_msg=$(ssh -o ConnectTimeout=60 $session exit 2>&1)
    value=$(printf "%d\n" $?)

    if [ $value -ne 0 ] ; then
        tput cup $y_cor $x_cor
        printf "\e[33m\xe2\xac\xa4\e[0m\033[0K  TIMED OUT\n\n"
        printf "EXIT STATUS: $value\n"
        printf "\xe2\x86\xb3 error details:\n"
        printf "  $err_msg\n\n"
    else
        printf "CONNECTION SUCCESSFUL.\n"
    fi

printf "TIME ELAPSED: $((SECONDS / 60))m $((SECONDS % 60))s\n\n"

else
    tput cup $y_cor $x_cor
    printf "\e[1m\e[31m\xe2\xac\xa4\e[0m\033[0K  OFFLINE\n\n"
    value=1
fi

exit $value
