from collections import OrderedDict

from cloudshell.cli.command_template.command_template import CommandTemplate
from netscout_teststream.command_templates.ERRORS import GENERIC_ERRORS

ACTION_MAP = OrderedDict()
ERROR_MAP = GENERIC_ERRORS

SHOW_SWITCH_INFO = CommandTemplate('show information switch {switch_name}', ACTION_MAP, ERROR_MAP)
SHOW_PORTS = CommandTemplate('show port info * swi {switch_name}', ACTION_MAP, ERROR_MAP)
SHOW_PORTS_RAW = CommandTemplate('show port rawinfo * swi {switch_name}', ACTION_MAP, ERROR_MAP)
SHOW_CONNECTIONS = CommandTemplate('show connection switch {switch_name}', ACTION_MAP, ERROR_MAP)
