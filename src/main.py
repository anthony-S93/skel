import sys
from utils.operations import *

cli_args = sys.argv[1:]

try:
    if len(cli_args) == 0:
        display_help()
    else:
        check_cli_arguments(cli_args)
        chosen_template = cli_args[0]
        target_directories = cli_args[1:]
        root_element = parse_template(chosen_template)
        generate_skeleton(inside=target_directories, based_on=root_element)
except BadCmdlineArgument as error:
    print(error)
    print()
    display_help()
except Exception as error:
    print(error)
