from collections import OrderedDict

from cloudshell.cli.command_template.command_template import CommandTemplate
from netscout_teststream.command_templates.ERRORS import GENERIC_ERRORS

ACTION_MAP = OrderedDict()
ERROR_MAP = OrderedDict([("[Nn]ot compatible", "Ports\Subports not compatible"),
                         ("[Ee]rror|ERROR", "Error during command execution. See logs for more details"),
                         ("[Ii]ncorrect", "Incorrect port number format")])
ERROR_MAP.update(GENERIC_ERRORS)

SELECT_SWITCH = CommandTemplate('select switch {switch_name}', ACTION_MAP, ERROR_MAP)
MAP_SIMPLEX_OLD = CommandTemplate('connect simplex prtnum {src_port} to {dst_port} force', ACTION_MAP, ERROR_MAP)
MAP_SIMPLEX_NEW = CommandTemplate('CONNECT -s -F PRTNUM {src_port} PRTNUM {dst_port}', ACTION_MAP, ERROR_MAP)
MAP_DUPLEX_OLD = CommandTemplate('connect duplex prtnum {src_port} to {dst_port} force', ACTION_MAP, ERROR_MAP)
MAP_DUPLEX_NEW = CommandTemplate('CONNECT -d -F PRTNUM {src_port} PRTNUM {dst_port}', ACTION_MAP, ERROR_MAP)
SHOW_CONNECTION = CommandTemplate('show conn prtnum {port}', ACTION_MAP, OrderedDict(
    [("[Ee]rror|ERROR", "Error during command execution. See logs for more details")]))
DISCONNECT_SIMPLEX_NEW = CommandTemplate('DISCONNECT -s -F PRTNUM {src_port} PRTNUM {dst_port}', ACTION_MAP,
                                         OrderedDict(ERROR_MAP.items() + [
                                             ("[Nn]ot [Ss]implex", "Subport is not simplex connected")]))
DISCONNECT_SIMPLEX_OLD = CommandTemplate('disconnect simplex {dst_port} force', ACTION_MAP,
                                         OrderedDict(ERROR_MAP.items() + [
                                             ("[Nn]ot [Ss]implex", "Subport is not simplex connected")]))
DISCONNECT_DUPLEX_NEW = CommandTemplate('DISCONNECT -d -F PRTNUM {src_port} PRTNUM {dst_port}', ACTION_MAP, ERROR_MAP)
DISCONNECT_DUPLEX_OLD = CommandTemplate('disconnect duplex prtnum {dst_port} force', ACTION_MAP, ERROR_MAP)
DISCONNECT_MCAST = CommandTemplate('disconnect multicast destination {dst_port} force', ACTION_MAP, ERROR_MAP)
