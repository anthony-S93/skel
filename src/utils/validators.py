# This module contains specific handlers to validate the values of attributes

import os
from .error_handling import *
from lxml.etree import _Element as Element
from typing import Callable, Dict


def _check_name_attribute(elem: Element) -> None:
    # Ignore anything other than a <dir> or <file>
    if elem.tag == "dir" or elem.tag == "file":
        if os.sep in elem.get("name"):
            descriptions = [
                "The value assigned to 'name' cannot contain any path separators (only basenames are allowed)",
                "E.g: On UNIX systems, name=\"fname\" is valid, but not name=\"/fname\" or name=\"fname/\""
            ]
            issue = InvalidAttributeValue(affected_element=elem, attribute_name="name", attribute_value=elem.get("name"))
            issue.add_descriptions(desc=descriptions)
            log_issue(issue)

        if not elem.get("name"):
            descriptions = [
                "The value assigned to 'name' cannot be empty",
                "The value of 'name' should refer to the basename of the {} to be created".format("directory" if (elem.tag == "dir") else elem.tag)
            ]
            issue = InvalidAttributeValue(affected_element=elem, attribute_name="name", attribute_value="")
            issue.add_descriptions(desc=descriptions)
            log_issue(issue)


def _check_src_attribute(elem: Element) -> None:
    # Ignore the src attribute for any element other than <file>
    if elem.tag == "file":
        src = elem.get("src")
        if not src:
            descriptions = [
                "The value assigned to 'src' cannot be empty",
                "The value of 'src' should point to an existing file whose contents you want to replicate inside the skeleton project"
            ]
            issue = InvalidAttributeValue(affected_element=elem, attribute_name="src", attribute_value="")
            issue.add_descriptions(desc=descriptions)
            log_issue(issue)
        else:
            src_path = resolve_src_attribute(src=src)
            if not os.path.isfile(src_path):
                if os.path.isdir(src_path):
                    descriptions = [
                        "The value of 'src' must point to an existing file",
                        "The path \"{}\" belongs to a directory".format(src_path)
                    ]
                else:
                    descriptions = [
                        "The file \"{}\" does not exist".format(src_path),
                        "Relative paths assigned to 'src' will be resolved relative to the filesrc directory",
                        "To use a file outside the filesrc directory, provide an absolute path instead",
                    ]
                issue = InvalidAttributeValue(affected_element=elem, attribute_name="src", attribute_value=src_path)
                issue.add_descriptions(desc=descriptions)
                log_issue(issue)


REGISTERED_ATTRIBUTE_CHECKERS: Dict[str, Callable[[Element, str], None]]
REGISTERED_ATTRIBUTE_CHECKERS = {
    "name": _check_name_attribute,
    "src" : _check_src_attribute,
}
