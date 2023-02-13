#!/usr/bin/python3

"""
This script runs a QA test on a newly provision-replaced
Brain Control Module that is online under prod ROC.
It saves the results to a file in addition to printing 
results to the screen.
Copyright 2020 Sid Laurens
"""

import sys
import time
import shutil
import argparse
from pathlib import Path
from bcm_test import colors
from bcm_test import BcmTest

def get_user():
    """
    Gets username from the expected path.
    Prompts the user to create the file path if it does not exist.

    Parameters:
            None

    Returns:
            username (str): User name of person running the test.
    """
    user_path = Path("~/.bin/username").expanduser()

    try:
        with open(user_path, "r") as file:
            username = file.read().replace("\n", "")
    except FileNotFoundError:
        sys.exit(f"{colors.WARNING}{colors.BOLD}USERNAME NOT FOUND.{colors.ENDC}\nPlease set username by\n\n{colors.BOLD}echo YOUR_ROC_USERNAME >~/.bin/username\n\n{colors.ENDC}\n\nThen run this script again.")
        
    return username

def mov_doc(rin, date):
    """
    Moves the created test summary file to a fixed location.

    Parameters:
            rin  (str): The DUT (device under test) ID
            date (str): The date the test is being run 

    Returns:
            None
    """
    result_path = Path("~/Desktop/Test_Results").expanduser()
    result_path.mkdir(parents=False, exist_ok=True)
    dest_file = result_path / f"{rin}_{date}.txt"
    shutil.move(f"{rin}_{date}.txt", dest_file.resolve())

def tabulate(verbose, test_result):
    """
    Displays test results in tabulated format.

    Parameters:
            verbose      (str): Option for verbose output
            test_result (dict): Results of the QA test

    Returns:
            None
    """
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
        if (verbose and result=="PASS"):
            print (f"{test:<{col1_format}} {colors.PASS}{result:<{col2_format}}{colors.ENDC}")
        elif (result=="FAIL"):
            comments = values[2]
            print (f"{test:<{col1_format}} {colors.FAIL}{result:<{col2_format}}{colors.ENDC} {comments:<{col3_format}}")

def print_sys(system_list):
    """
    Displays system information of specified rin.

    Parameters:
            system_list (list): List of main system components

    Returns:
            None
    """
    print(f"\n\n{colors.BOLD}{colors.UNDERLINE}SYSTEM INFORMATION{colors.ENDC}")

    for item in system_list:
        part_item=item.split("- ")
        sys_item=part_item[1]
        print("-> " + sys_item)

def get_args():
    """
    Defines the list of arugments for script usage.

    Parameters:
            None

    Returns:
            args (argparse.Namespace): arguments to run the script
    """
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

    date_stamp = time.strftime("%Y%m%d")

    ARGS = get_args()

    user = get_user()

    test = BcmTest(user, date_stamp, ARGS.rin, ARGS.bundle)

    rin_status = test.check_status()
    if rin_status != 0:
        sys.exit(f"{colors.BOLD}UNABLE TO CONNECT TO {ARGS.rin} / CONNECTION TERMINATED.{colors.ENDC}\n")

    end_result = test.run_test()

    result_dict, system_list = test.analyze_results()

    mov_doc(ARGS.rin, date_stamp)

    if ARGS.quiet:
        sys.exit(f"{colors.BLUE}Test completed.{colors.ENDC}")

    #Print out test results.
    print(f"{colors.BOLD}{colors.UNDERLINE}{colors.HEADER}SUMMARY{colors.ENDC}\n")

    if ARGS.verbose:
        tabulate(ARGS.verbose, result_dict)
    else:
        if end_result == 1:
            print(f"{colors.FAIL}{colors.BOLD}TEST FAILED{colors.ENDC}\n")
            tabulate(ARGS.verbose, result_dict)
        else:
            print(f"{colors.PASS}{colors.BOLD}TEST PASSED{colors.ENDC}")
    
    print_sys(system_list)

    print()
