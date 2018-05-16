import re

from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor
import netscout_teststream.command_templates.mappings as command_template


class MappingActions(object):
    """
    Autoload actions
    """

    def __init__(self, switch_name, cli_service, logger):
        """
        :param cli_service: default mode cli_service
        :type cli_service: CliService
        :param logger:
        :type logger: Logger
        :return:
        """
        self._switch_name = switch_name
        self._cli_service = cli_service
        self._logger = logger

    def connect_simplex(self, src_port, dst_port, new_command_format=False):
        if new_command_format:
            template = command_template.MAP_SIMPLEX_NEW
        else:
            template = command_template.MAP_SIMPLEX_OLD

        output = CommandTemplateExecutor(self._cli_service, command_template.SELECT_SWITCH).execute_command(
            switch_name=self._switch_name)

        output += CommandTemplateExecutor(self._cli_service, template).execute_command(src_port=src_port,
                                                                                       dst_port=dst_port)
        return output

    def connect_duplex(self, src_port, dst_port, new_command_format=False):
        if new_command_format:
            template = command_template.MAP_DUPLEX_NEW
        else:
            template = command_template.MAP_DUPLEX_OLD

        output = CommandTemplateExecutor(self._cli_service, command_template.SELECT_SWITCH).execute_command(
            switch_name=self._switch_name)

        output += CommandTemplateExecutor(self._cli_service, template).execute_command(src_port=src_port,
                                                                                       dst_port=dst_port)
        return output
