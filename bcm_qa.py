#!/usr/bin/python3

"""
This script runs a QA check on a newly provision-replaced
Brain Control Module that is online under prod ROC.
"""
# ============================================================================
# Copyright 2020 Sid Laurens
# ============================================================================

import sys
import time
import shutil
import argparse
import subprocess
from pathlib import Path

class colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    PASS = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#Get username from the expected path.
def get_user():
    user_path = Path("~/.bin/username").expanduser()

    try:
        with open(user_path, "r") as file:
            username = file.read().replace("\n", "")
    except FileNotFoundError:
        print(f"{colors.WARNING}{colors.BOLD}USERNAME NOT FOUND.{colors.ENDC}\nPlease set username by\n\n{colors.BOLD}echo YOUR_ROC_USERNAME >~/.bin/username\n\n{colors.ENDC}\n\nThen run this script again.")
        sys.exit()

    return username

#Call shell script to check connectivity of the specified rin.
def check_status(user, rin):
    status=subprocess.Popen([f"./bcm_status.sh {user} {rin}"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    
    for line in status.stdout:
        sys.stdout.write(line)

    status.wait()
    
    get_status = status.returncode

    return get_status

#Call shell script to run test on the specified rin. Pipe output to text file.
def run_test(user, rin, bundle):
    with open(f"{rin}_{date_stamp}.txt", "w") as test_summary:
        test_summary.write(f"Tested by: {user}\n") 
        test=subprocess.Popen([f"./bcm_qa.sh {user} {rin} {bundle}"], stdout=test_summary, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)

    test.wait()

    test_status = test.returncode

    return test_status

#Create a new dictionary containing results from the test summary file.
def analyze_results(rin, test_plan, test_result, system_list):
    result_list=[]

    with open(f"{rin}_{date_stamp}.txt", "r") as file:
        for line in file:
            check_line = line.strip()

            if "PASS" in check_line:
                result_list.append(check_line)
            elif "FAIL" in check_line:
                result_list.append(check_line)
            elif "SYS" in check_line:
                system_list.append(check_line)
    
    for (num, data) in test_plan.items():
        try:
            step=data[0]
            notes=data[1]
            if "PASS" in result_list[num]:
                test_result[num]=(step, result_list[num])
            elif "FAIL" in result_list[num]:
                test_result[num]=(step, result_list[num], notes)
        except IndexError:
            print(f"{colors.BOLD}TEST DID NOT COMPLETE.  PLEASE RETEST.{colors.ENDC}\n")
            sys.exit()

#Move the created test summary file to a fixed location.
def mov_doc(rin):
    result_path = Path("~/Desktop/Test_Results").expanduser()
    result_path.mkdir(parents=False, exist_ok=True)
    dest_file = result_path / f"{rin}_{date_stamp}.txt"
    shutil.move(f"{rin}_{date_stamp}.txt", dest_file.resolve())

#Display test results in tabulated format.
def tabulate(verbose, test_result):
    col1_format = 26
    col2_format = 10
    col3_format = 15
    col1_head = "TITLE"
    col2_head = "RESULT"
    col3_head = "COMMENTS"

    print(f"{colors.BOLD}{colors.UNDERLINE}{col1_head:<{col1_format}} {col2_head:<{col2_format}} {col3_head:<{col3_format}}{colors.ENDC}") 
    for (key, values) in test_result.items(): 
        test = values[0]
        result = values[1]
        if (ARGS.verbose and result=="PASS"):
            print (f"{test:<{col1_format}} {colors.PASS}{result:<{col2_format}}{colors.ENDC}")
        elif (result=="FAIL"):
            comments = values[2]
            print (f"{test:<{col1_format}} {colors.FAIL}{result:<{col2_format}}{colors.ENDC} {comments:<{col3_format}}")

#Display system information of specified rin.
def print_sys(system_list):
    print(f"\n\n{colors.BOLD}{colors.UNDERLINE}SYSTEM INFORMATION{colors.ENDC}")

    for item in system_list:
        part_item=item.split("- ")
        sys_item=part_item[1]
        print("-> " + sys_item)

#Define the list of arugments for script usage.
def get_args():
    parser = argparse.ArgumentParser(description="Run QA test on a newly provisioned BCM replacement")

    requiredArgs = parser.add_argument_group("required arguments")
    requiredArgs.add_argument("-r", "--rin", metavar="", required=True, help="input rin to analyze")
    requiredArgs.add_argument("-b", "--bundle", metavar="", required=True, help="bundle ID of route/config package used")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-q", "--quiet", action="store_true", help="runs the test without printing out a result")
    group.add_argument("-v", "--verbose", action="store_true", help="print pass / fail details of each sub-test")

    args = parser.parse_args()

    return args


if __name__ == "__main__":

    test_plan = { 
0: ["HOME DIR. CONTENTS", "FILE(S) PRESENT IN HOME DIRECTORY"],
1: ["F/W_UPDATED FILE", "FIRMWARE_UPDATED FILE FOUND"],
2: ["MACHINE FILE-EXIST", "MACHINE FILE NOT FOUND"],
3: ["MACHINE FILE-CONTENT", "FILE NOT READABLE OR EMPTY (OR FAILED DUE TO FILE NOT FOUND)"],
4: ["MACHINE TYPE", "MACHINE FILE / MACHINE TYPE MISMATCH (OR FAILED DUE TO FILE NOT FOUND)"],
5: ["BUNDLE ID-EXIST", "NO BUNDLE ID MATCH"],
6: ["BUNDLE ID-RESTORE", "RESTORE DID NOT COMPLETE (OR WAS NOT DONE)"],
7: ["ROUTE DATABASE-EXIST", "NO DIRECTORY FOUND"],
8: ["ROUTE DATABASE-OWN", "WRONG ROUTE DB OWNERSHIP (OR DIRECTORY NOT FOUND)"],
9: ["ROUTE DATABASE-CONTENT", "ROUTE DB DIRECTORY EMPTY (OR DIRECTORY NOT FOUND)"],
10: ["ROUTE STORE-EXIST", "NO DIRECTORY FOUND"],
11: ["ROUTE STORE-CONTENT", "DIRECTORY EMPTY (OR BAD FILE OWNERSHIP)"],
12: ["ROUTE INDEX-EXIST", "NO DIRECTORY FOUND"],
13: ["ROUTE INDEX-CONTENT", "DIRECTORY EMPTY (OR BAD FILE OWNERSHIP)"],
14: ["CURRENT LINK-EXIST", "<CURRENT> SYMBOLIC LINK NOT FOUND"],
15: ["CURRENT LINK-CONTENT", "<CURRENT> LINK IS EMPTY (OR LINK NOT FOUND)"],
16: ["VER.ROBOT PARAMS-EXIST", "DIRECTORY NOT FOUND"],
17: ["VER.ROBOT PARAMS-OWN", "BAD DIRECTORY OWNERSHIP (OR DIRECTORY NOT FOUND)"],
18: ["VER.ROBOT PARAMS-CONTENT", "DIRECTORY EMPTY (OR BAD FILE OWNERSHIP)"],
19: ["VER.ROBOT PARAMS-SUBDIR", "SUBDIRECTORY EMPTY (OR CONTAINS BAD FILE OWNERSHIP)"]
}
    test_result = {}
    system_list = []
    date_stamp = time.strftime("%Y%m%d")
    

    ARGS = get_args()

    user = get_user()

    rin_status = check_status(user, ARGS.rin)
    #Connection exception.
    if rin_status != 0:
        sys.exit(f"{colors.BOLD}UNABLE TO CONNECT TO {ARGS.rin} / CONNECTION TERMINATED.{colors.ENDC}\n")

    end_result = run_test(user, ARGS.rin, ARGS.bundle)

    analyze_results(ARGS.rin, test_plan, test_result, system_list)

    mov_doc(ARGS.rin)


    if ARGS.quiet:
        sys.exit(f"{colors.BLUE}Test completed.{colors.ENDC}")

    #Print out test results.
    print(f"{colors.BOLD}{colors.UNDERLINE}{colors.HEADER}SUMMARY{colors.ENDC}\n")

    if ARGS.verbose:
        tabulate(ARGS.verbose, test_result)
    else:
        if end_result == 1:
            print(f"{colors.FAIL}{colors.BOLD}TEST FAILED{colors.ENDC}\n")
            tabulate(ARGS.verbose, test_result)
        else:
            print(f"{colors.PASS}{colors.BOLD}TEST PASSED{colors.ENDC}")
    
    print_sys(system_list)

    print()
