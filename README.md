# BCM-TEST
_Please note: this repository is a replica of my private project on GitHub. This open-source version is slightly modified, thus will not build. The scripts are no longer maintained and are for reference only._

Script to run a standardized QA test on newly replace-provisioned BCMs prior to field replacement.

This repo contains scripts that check file integrity of an embedded computer called a "BCM".  Specifically, it is an embedded computer that is a field replacement of a decommissioned BCM model.  It should have already gone through provisioning prior to running this script.  This test should be run prior to deployment.
## Setup

Two shell scripts are used within the python script, and must exist in the same directory as the python script.  They will need proper access permissions to be run:
```bash
-rwxr-xr-x
```
If they do not have the correct permissions, they can be set by entering this command in the terminal:
```bash
chmod a+x <script-name>.sh
```
Python 3 (version 3.6.9 or greater) is required to run the python script.

## Usage

You can enter `-h` or `--help` when running the script to learn about proper usage.

Note that when the script has completed execution a Test Result file (identified by the given rin number and date stamp when the test was run) will be created and moved to a fixed directory on your Ubuntu VM (~/Desktop/Test_Results).  These are text files and can be used as a reference to verify the test results, and for the future after the BCM is in the field.
