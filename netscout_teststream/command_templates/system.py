from collections import OrderedDict

from cloudshell.cli.command_template.command_template import CommandTemplate

from netscout_teststream.command_templates.errors import GENERIC_ERRORS

ACTION_MAP = OrderedDict()
ERROR_MAP = GENERIC_ERRORS

SHOW_SWITCHES = CommandTemplate("show switches", ACTION_MAP, ERROR_MAP)
SHOW_STATUS = CommandTemplate("show status", ACTION_MAP, ERROR_MAP)
