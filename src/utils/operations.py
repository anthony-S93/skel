import os, os.path, shutil

from . import *
from .error_handling import *
from . import validators

from lxml import etree
from lxml.etree import _Element as Element

def display_help() -> None:
    print("Usage: skel <template> [targets...]")
    print()
    display_available_templates()


def display_available_templates() -> None:
    print("Available templates:")
    for template in _get_available_templates():
        print("→ {}".format(template))


def parse_template(template: str) -> Element:
    # Check whether the template file exists
    template_file = os.path.join(TEMPLATES_DIRECTORY, "{}.xml".format(template)) 
    if (template not in _get_available_templates()):
        raise BadCmdlineArgument("The template file \"{}\" doesn't exist".format(template_file))

    # Perform the actual parsing
    try:
        root_xml_element = etree.parse(template_file).getroot()
    except etree.ParseError as e:
        raise UnableToParse(template_path=template_file, trigger=e) 

    # Validate the root element
    _validate_xml_element(root_xml_element, template_file, is_root=True)

    if ALL_ISSUES:
        # Raise an exception if at least one issue with the template file is detected
        raise InvalidTemplateFile(template_file=template_file, issues=ALL_ISSUES)

    # All good
    return root_xml_element


def generate_skeleton(*, inside: List[str], based_on: Element):
    root_element = based_on
    target_dirs = inside

    if not target_dirs:
        target_dirs = [os.getcwd()]
    else:
        # Expand all paths to absolute paths
        target_dirs = [os.path.realpath(d) for d in target_dirs]

    # Create every target dirs if they don't exist
    # Set up the dir structure as specified by the root element
    for dir in target_dirs:
        try:
            _make_paths(path_type="directory", path=dir)
            _create_dir_entries(inside=dir, based_on=root_element)
        except DirPathBelongsToExistingFile:
            remarks = [
                    "Unable to create the target directory",
                    "The path belongs to an existing file",
            ]
            _report_path_creation_status(path_type="directory", path=dir, skipping=True, remarks=remarks)
        except PermissionError:
            _report_permission_error(path_type="directory", path=dir)


def check_cli_arguments(args: List[str]) -> None:
    # Only accepts a non-empty list of strings
    template_name = args[0]
    if os.sep in template_name:
        raise BadCmdlineArgument("Template names cannot contain path separators ({})".format(os.sep))


def _get_available_templates() -> List[str]:
    return [os.path.splitext(t)[0] for t in os.listdir(TEMPLATES_DIRECTORY) if t.endswith(".xml")]


def _validate_xml_element(element: Element, template_path: str, is_root: bool):
    # Make sure that the tag is valid
    if element.tag == "noroot":
        raise NotWellFormedXML(template_path=template_path)
    if is_root and (element.tag != "root"):
        # The root element of the document cannot be something other than <root>
        log_issue(InvalidRootElement(affected_element=element))
    if element.tag not in VALID_TAGS:
        log_issue(UnrecognizedTag(affected_element=element))

    # Make sure that mandatory attributes are present for all valid tags
    if element.tag in VALID_TAGS:
        for attr in VALID_TAGS[element.tag]:
            if attr not in element.attrib:
                log_issue(MissingRequiredAttribute(affected_element=element, attribute=attr))

    # Invoke the appropriate handlers to validate the values of all registered attributes
    for attr in element.attrib:
        if attr in validators.REGISTERED_ATTRIBUTE_CHECKERS:
            validators.REGISTERED_ATTRIBUTE_CHECKERS[attr](element)

    # Validate the element's children unless it is a <file> element
    if (element.tag == "file"): return
    if (element.tag == "root") and not is_root:
        # <root> must be the top level in the template file
        log_issue(NestedRootTag(affected_element=element))

    # Check all the children of the element recursively
    for child in element:
        _validate_xml_element(element=child, template_path=template_path, is_root=False)


def _create_dir_entries(*, inside: str, based_on: Element):
    containing_directory = inside
    template_element     = based_on

    for child in template_element:
        # Child elements can only be either <dir> or <file>; a nested <root> will trigger an exception early on
        if child.tag == "file":
            file_path = os.path.join(containing_directory, child.get("name"))
            if "src" in child.attrib:
                src = resolve_src_attribute(src=child.get("src"))
            else:
                src =""
            _make_paths(path_type="file", path=file_path, src=src)
            if len(child): # Print warning if <file> has children
                _report_ignoring_children_of_file_tag(file_elem=child)

        if child.tag == "dir":
            # Child element is a <dir>
            # The element represents a subdirectory of the current directory
            dir_path = os.path.join(containing_directory, child.get("name"))
            try:
                _make_paths(path_type="directory", path=dir_path)
            except DirPathBelongsToExistingFile:
                # Skip the element entirely
                # Do not attempt to create the entries of its children
                remarks = [
                        "A file already exists at {}".format(dir_path),
                        "Make sure that no <file> and <dir> under the same parent has the same 'name'"
                ]
                _report_path_creation_status(path_type="directory", path=dir_path, skipping=True, remarks=remarks)
                continue
            except PermissionError:
                _report_permission_error(path_type="directory", path=dir_path)
                continue
            _create_dir_entries(inside=dir_path, based_on=child)


def _make_paths(*, path_type:str, path: str, src: str="") -> None:
    if path_type == "file":
        if os.path.exists(path):
            # Path already exists. Skip
            if os.path.isdir(path):
                remarks = [
                        "A directory already exists at that path",
                        "Make sure that no <file> and <dir> under the same parent has the same 'name'"
                ]
            else:
                remarks = [
                        "A file already exists at that path",
                        "Make sure that the <file> tag isn't specified more than once in the same parent"
                ]
            _report_path_creation_status(path_type=path_type, path=path, skipping=True, remarks=remarks)
        else:
            if src: # Source file provided
                # Copy the source file to the new location
                shutil.copy(src=src, dst=path)
            else:
                # Create an empty file
                open(path, "w").close()
            _report_path_creation_status(path_type=path_type, path=path)
    if path_type == "directory":
        if os.path.exists(path):
            if os.path.isdir(path):
                # A directory already exists at that path.
                # Skip
                _report_path_creation_status(path_type=path_type, path=path, skipping=True)

            if os.path.isfile(path):
                # A file already exists at that path. 
                # Skip.
                # Signal the caller to ignore all the <dir> element's children
                raise DirPathBelongsToExistingFile()
        else:
            # Path doesn't exist yet. Safe to create dir
            dirs_to_be_created = _list_dirs_that_makedirs_will_create(path)
            os.makedirs(path)
            # Report successful creation
            for dir in dirs_to_be_created:
                _report_path_creation_status(path_type=path_type, path=dir)


def _list_dirs_that_makedirs_will_create(path) -> List[str]:
    # Input : An absolute path that points to a directory to be created
    # Output: A list of all directories (including intermediate dirs) that will be created by os.makedirs()
    result: List[str] = []
    while path:
        if os.path.exists(path):
            # Reached a parent directory that already exists
            path = ""  # Terminate the loop
        else:
            result.append(path)
            path = os.path.dirname(path)
    result.reverse() # Make sure that the higher level directories are listed first
    return result


def _report_path_creation_status(*, path_type: str, path: str, skipping: bool = False, remarks: List[str] = []) -> None:
    successful_creation_msg_format = "✔ Created  {entry_type:<10}: \"{path}\""
    skipping_creation_msg_format   = "✘ Skipping {entry_type:<10}: \"{path}\""
    remark_format                  = "  {branch} {remark}"
    if not skipping:
        msg = successful_creation_msg_format.format(entry_type=path_type, path=path)
    else:
        msg = skipping_creation_msg_format.format(entry_type=path_type, path=path)
    print(msg)
    if remarks:
        normal_branch         = "┣━"
        last_branch           = "┗━"
        remarks_to_be_printed = []
        for num, remark in enumerate(remarks):
            branch = last_branch if (num == (len(remarks) - 1)) else normal_branch
            remarks_to_be_printed.append(remark_format.format(branch=branch, remark=remark))
        print("\n".join(remarks_to_be_printed))


def _report_permission_error(*, path_type: str, path: str) -> None:
    msg = "✘ Skipping {entry_type:<10}: \"{path}\"".format(entry_type=path_type, path=path)
    branch = "┗━"
    text = "Do not have permission to create {entry_type}".format(entry_type=path_type)
    remark = "  {branch} {text}".format(branch=branch, text=text)
    print(msg + "\n" + remark)


def _report_ignoring_children_of_file_tag(*, file_elem: Element): 
    msg = "❗Ignoring the child elements of <file name=\"{}\">".format(file_elem.get("name"))
    print(msg)
