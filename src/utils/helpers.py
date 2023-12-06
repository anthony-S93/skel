# Helper functions that encapsulate basic but frequently-used tasks

from . import *
import os.path

def indent(*, text: str, level: int=1) -> str:
    indentation = " " * level * 2
    return indentation + text

def indent_block(*, textblock:str, level: int=1) -> str:
    # Applies indentation to a string of newline-separated text
    lines = textblock.splitlines(keepends=True)
    lines = [indent(text=line, level=level) for line in lines]
    return "".join(lines)

def add_bullet(*, text: str) -> str:
    bullet_point = "• "
    return bullet_point + text

def resolve_src_attribute(*, src: str) -> str:
    if not os.path.isabs(src):
        # Relative paths are resolved relative to SKEL_HOME/resources/filesrc
        return os.path.join(FILE_SRC_DIRECTORY, src)
    else:
        return src
