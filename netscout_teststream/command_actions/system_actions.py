import re

from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor
import netscout_teststream.command_templates.system as command_template


class SystemActions(object):
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

    def available_switches(self):
        output = CommandTemplateExecutor(self._cli_service, command_template.SHOW_SWITCHES).execute_command()
        switches_match = re.search(r'available\s+switches:(.*)', output, flags=re.IGNORECASE | re.DOTALL)
        return switches_match.group(1).strip().splitlines()

    def software_version(self):
        output = CommandTemplateExecutor(self._cli_service, command_template.SHOW_STATUS).execute_command()
        match = re.search(r"Version[ ]?(.*?)\n", output, re.DOTALL)
        if match:
            return match.group(1)
        else:
            raise Exception(self.__class__.__name__, "Can not determine Software Version.")
