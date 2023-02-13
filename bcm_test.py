import sys
import subprocess
from bcm_test import colors

class BcmTest:
    """ 
    The purpose of this class is to confirm a provisioned BCM can be connected to, run tests on it,
    and to analyze those test results.

    Attributes
    ----------
    test_plan : dict
        Dictionary of test cases.  Key = index, Value = list of test title & description
    user : str
        The person running the script
    date_stamp : str
        The date the test is being run
    rin : str
        The DUT (device under test) ID
    bundle : str
        ID of the config file

    Methods
    -------
    check_status:
        Confirms the DUT to ensure it can be connected to prior to running the test.
    run_test:
        Executes the bash test on the DUT.
    analyze_results:
        Parses result file for test results.
    """
    
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

    def __init__(self, user, date_stamp, rin, bundle):
        """
        Constructs the necessary attributes for the BcmTest object.

        Parameters
        ----------
        user : str
            The person running the script
        date_stamp : str
            The date the test is being run
        rin : str
            The DUT (device under test) ID
        bundle : str
            ID of the config file
        """
        self.user = user
        self.date_stamp = date_stamp
        self.rin = rin
        self.bundle = bundle

    def __str__(self):
        return "This class runs a diagnostic-QA test on a provisioned BCM and outputs/saves the results to a file."
    

    def check_status(self):
        """
        Calls shell script to check ssh connectivity of the specified rin.

        Parameters
        ----------
        Self

        Returns
        -------
        get_status (int): Return value of the execute shell script command.
        """
        status=subprocess.Popen([f"./bcm_status.sh {self.user} {self.rin}"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
        
        for line in status.stdout:
            sys.stdout.write(line)
            
        status.wait()
        
        get_status = status.returncode
        
        return get_status

    def run_test(self):
        """
        Calls shell script to run test on the specified rin. Pipe output to text file.

        Parameters
        ----------
        Self

        Returns
        -------
        test_status (int): Return value of the execute shell script command.
        """
        with open(f"{self.rin}_{self.date_stamp}.txt", "w") as test_summary:
            test_summary.write(f"Tested by: {self.user}\n") 
            test=subprocess.Popen([f"./bcm_qa.sh {self.user} {self.rin} {self.bundle}"], stdout=test_summary, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
            
        test.wait()
        
        test_status = test.returncode
        
        return test_status

    def analyze_results(self):
        """
        Creates a new dictionary containing results from the test summary file.

        Parameters
        ----------
        Self

        Returns
        -------
        test_result (dict): Dictionary of the test results
        system_list (list): List of main system components
        """
        result_list=[]
        system_list = []
        test_result = {}
        
        with open(f"{self.rin}_{self.date_stamp}.txt", "r") as file:
            for line in file:
                check_line = line.strip()
                
                if "PASS" in check_line:
                    result_list.append(check_line)
                elif "FAIL" in check_line:
                    result_list.append(check_line)
                elif "SYS" in check_line:
                    system_list.append(check_line)
                    
        for (num, data) in BcmTest.test_plan.items():
            try:
                step=data[0]
                notes=data[1]
                if "PASS" in result_list[num]:
                    test_result[num]=(step, result_list[num])
                elif "FAIL" in result_list[num]:
                    test_result[num]=(step, result_list[num], notes)
            except IndexError:
                sys.exit(f"{colors.BOLD}TEST DID NOT COMPLETE.  PLEASE RETEST.{colors.ENDC}\n")

        return test_result, system_list
    