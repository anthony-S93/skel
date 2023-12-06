# This module contains the tools required to detect errors and issues with the template xml files

from . import *
from .helpers import *
from lxml.etree import _Element as Element
from typing import List


class TemplateFileIssue:
    def __init__(self, *, affected_element: Element) -> None:
        self.title = "Invalid template file"
        self.elems = [affected_element]  # A list of all the elements with the issue
        self.desc  = []  # A list of descriptions (to be added by subclasses)

    def __str__(self) -> str:
        self.elems: List[Element]
        affected_lines = [str(line) for line in sorted(set([elem.sourceline for elem in self.elems]))]
        if affected_lines:
            header = self.title + " " + "(line: {})".format(", ".join(affected_lines))
        else:
            header = self.title
        self.desc: List[str]
        # The descriptions are indented by one level relative to the header
        formatted_desc = [indent(text=add_bullet(text=desc)) for desc in self.desc]
        printed_lines = [header]
        printed_lines.extend(formatted_desc)
        return "\n".join(printed_lines)

    def __eq__(self, __value: object) -> bool:
        return type(__value) == type(self)

    def merge_with(self, other: "TemplateFileIssue") -> None:
        self.elems.extend(e for e in other.elems if e not in self.elems)

    def add_descriptions(self, desc: List[str]) -> None:
        self.desc.extend(desc)


class UnrecognizedTag(TemplateFileIssue):
    def __init__(self, *, affected_element: Element) -> None:
        super().__init__(affected_element=affected_element)

    def __str__(self) -> str:
        # Customize title and descriptions first
        problematic_tagnames = sorted(set([elem.tag for elem in self.elems]))
        if (len(problematic_tagnames) > 1):
            be      = "are"        
            suffix  = "s"
            article = ""
        else:
            be      = "is"
            suffix  = ""
            article = "a "

        taglist = ["<{}>".format(tagname) for tagname in problematic_tagnames]
        taglist = ", ".join(taglist)
        
        self.title = "Unrecognized tag{suffix}".format(suffix=suffix)
        self.desc  = [
            "{taglist} {be} not {article}valid tag{suffix}".format(taglist=taglist, be=be, article=article, suffix=suffix),
            "Only <root>, <dir>, and <file> tags are allowed"
        ]
        return super().__str__()


class NestedRootTag(TemplateFileIssue):
    def __init__(self, *, affected_element: Element) -> None:
        super().__init__(affected_element=affected_element)
        self.desc  = [
            "The <root> tag can only be used as the top-level element of the template file",
        ]

    def __str__(self) -> str:
        if len(self.elems) > 1:
            suffix = "s"
        else:
            suffix = ""
        self.title = "Nested <root> tag{suffix} detected".format(suffix=suffix)
        return super().__str__()


class InvalidRootElement(TemplateFileIssue):
    def __init__(self, *, affected_element: Element) -> None:
        super().__init__(affected_element=affected_element)
        self.title = "Invalid root element"
        self.desc  = [
            "<{}> is not a valid root element".format(affected_element.tag),
            "The template file should have <root> as its top-level element"
        ]


class MissingRequiredAttribute(TemplateFileIssue):
    def __init__(self, *, affected_element: Element, attribute: str) -> None:
        super().__init__(affected_element=affected_element)
        self.__affected_tag = affected_element.tag
        self.__missing_attributes = [attribute]

    def __eq__(self, other: "MissingRequiredAttribute") -> bool:
        # Same tag, same issue
        return super().__eq__(other) and (self.__affected_tag == other.__affected_tag)

    def __str__(self) -> str:
        # Update title based on affected tag
        if len(self.__missing_attributes) > 1:
            suffix = "s"
            be = "are"
        else:
            suffix = ""
            be = "is"
        missing_attr_names = ["'{}'".format(attr) for attr in self.__missing_attributes]
        missing_attr_names = ", ".join(missing_attr_names)
        self.title = "Missing required attribute{suffix}".format(suffix=suffix)
        self.desc = [
            "{attr_list} {be} required for <{tag}>".format(attr_list=missing_attr_names, be=be, tag=self.__affected_tag),
            " e.g. <{tag} {attr}=\"foo\"></{tag}> or <{tag} {attr}=\"foo\"/>".format(tag=self.__affected_tag, attr=self.__missing_attributes[0])
        ]
        return super().__str__()

    def merge_with(self, other: "MissingRequiredAttribute") -> None:
        super().merge_with(other) # Add the elements first to track the line numbers
        self.__missing_attributes.extend([attr for attr in other.__missing_attributes if attr not in self.__missing_attributes])


class InvalidAttributeValue(TemplateFileIssue):
    def __init__(self, *, affected_element: Element, attribute_name: str, attribute_value: str) -> None:
        super().__init__(affected_element=affected_element)
        self.__affected_tag       = affected_element.tag
        self.__affected_attribute = attribute_name
        self.__problematic_value  = attribute_value
        self.title  = "Invalid '{attr}' in <{tag}>".format(
                attr=self.__affected_attribute,
                tag=self.__affected_tag
        )

    def __eq__(self, other: "InvalidAttributeValue") -> bool:
        if super().__eq__(other):
            # For two issues to be equal, the affected_tag, affected_attribute, and problematic value must be the same
            return (
                (self.__affected_tag == other.__affected_tag) and
                (self.__affected_attribute == other.__affected_attribute) and
                (self.__problematic_value == other.__problematic_value)
            )
        else:
            return False


ALL_ISSUES: List[TemplateFileIssue] = []


def log_issue(issue: TemplateFileIssue) -> None:
    for iss in ALL_ISSUES:
        if iss == issue:
            iss.merge_with(issue)
            break
    else:
        ALL_ISSUES.append(issue)


class InvalidTemplateFile(Exception):
    def __init__(self, *, template_file: str, issues: List[TemplateFileIssue]=[]) -> None:
        self.__template_file = template_file
        self.__all_issues    = issues
        self.header_line     = "\nInvalid template file: \"{}\"\n".format(self.__template_file)

    def __str__(self) -> str:
        issue_reports = [indent_block(textblock=str(issue)) + "\n" for issue in self.__all_issues]
        printed_lines = [self.header_line]
        printed_lines.extend(issue_reports)
        return "\n".join(printed_lines)


class NotWellFormedXML(InvalidTemplateFile):
    def __init__(self, *, template_path: str) -> None:
        super().__init__(template_file=template_path)

    def __str__(self) -> str:
        subtitle = indent("The XML file is not well-formed")
        details  = [
            "A well-formed XML document must have a root element",
            "Please include a <root> element at the document's top level"
        ]
        details = [indent(text=add_bullet(text=d), level=2) for d in details]
        printed_lines = [self.header_line]
        printed_lines.append(subtitle)
        printed_lines.extend(details)

        return "\n".join(printed_lines) + "\n"


class UnableToParse(NotWellFormedXML):
    def __init__(self, *, template_path: str, trigger: Exception) -> None:
        super().__init__(template_path=template_path)
        self.__trigger = trigger

    def __str__(self) -> str:
        subtitle = "Failed to parse the template file"
        details  = [
            "An exception was raised by lxml.etree.parse() with the following error message:",
            "\"{}\"".format(str(self.__trigger)),
        ]
        details = [indent(text=add_bullet(text=d), level=2) for d in details]
        printed_lines = [self.header_line]
        printed_lines.append(subtitle)
        printed_lines.extend(details)
        return "\n".join(printed_lines) + "\n"

class BadCmdlineArgument(Exception): pass
class DirPathBelongsToExistingFile(Exception): pass
