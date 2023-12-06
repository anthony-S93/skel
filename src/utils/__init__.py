# Initializes the application state

import os, os.path

# Global variabls
UTILS_PACKAGE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
SRC_DIRECTORY = os.path.dirname(UTILS_PACKAGE_DIRECTORY)
SKEL_HOME = os.path.dirname(SRC_DIRECTORY) 
TEMPLATES_DIRECTORY = os.path.join(SKEL_HOME, "resources/templates")
FILE_SRC_DIRECTORY  = os.path.join(SKEL_HOME, "resources/filesrc")
VALID_TAGS          = {
    # Valid tags and their required attributes
    "root": tuple(),
    "dir" : ("name",),
    "file": ("name",)
}

# Create templates and filesrc directories if missing
for d in (TEMPLATES_DIRECTORY, FILE_SRC_DIRECTORY):
    try:
        if not os.path.exists(d):
            os.makedirs(d)
    except Exception as err:
        print("Unable to create directory: \"{}\"".format(d))
        print("Cause: ", err)
        print("Aborting.")
        os._exit(1)


# Make sure that all dependencies are installed
import importlib.util
DEPENDENCIES = ("lxml",)
for pkg in DEPENDENCIES:
    if not importlib.util.find_spec(pkg):
        print("Missing dependency: '{}'".format(pkg))
        print("Please run the setup script first.")
        os._exit(1)
