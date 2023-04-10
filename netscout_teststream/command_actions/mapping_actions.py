import re

from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor
import netscout_teststream.command_templates.mappings as command_template
import netscout_teststream.command_actions.actions_helper as helper


class ConnectionInfoDTO:
    def __init__(self, src_address, dst_address, connection_type):
        """
        :type src_address: str
        :type dst_address: str
        :type connection_type: str
        """
        self.src_address = src_address
        self.dst_address = dst_address
        self.connection_type = connection_type


class MappingActions(object):
    """
    Mapping actions
    """
    NEW_MAJOR_VERSION = 3

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

    def _is_new_command_format(self, software_version):
        major_version = int(re.search(r"(\d+)", software_version).group(1))
        return major_version >= self.NEW_MAJOR_VERSION

    def select_switch(self):
        return CommandTemplateExecutor(
            self._cli_service,
            command_template.SELECT_SWITCH
        ).execute_command(switch_name=self._switch_name)

    def connect_simplex(self, src_port, dst_port, software_version=NEW_MAJOR_VERSION):
        self.select_switch()
        if self._is_new_command_format(software_version):
            template = command_template.MAP_SIMPLEX_NEW
        else:
            template = command_template.MAP_SIMPLEX_OLD
        output = CommandTemplateExecutor(
            self._cli_service,
            template
        ).execute_command(src_port=src_port, dst_port=dst_port)
        return output

    def connect_duplex(self, src_port, dst_port, software_version=NEW_MAJOR_VERSION):
        self.select_switch()
        if self._is_new_command_format(software_version):
            template = command_template.MAP_DUPLEX_NEW
        else:
            template = command_template.MAP_DUPLEX_OLD
        output = CommandTemplateExecutor(
            self._cli_service,
            template
        ).execute_command(src_port=src_port, dst_port=dst_port)
        return output

    def disconnect_simplex(self, src_port, dst_port, software_version=NEW_MAJOR_VERSION):
        self.select_switch()
        if self._is_new_command_format(software_version):
            output = CommandTemplateExecutor(
                self._cli_service,
                command_template.DISCONNECT_SIMPLEX_NEW
            ).execute_command(src_port=src_port, dst_port=dst_port)
        else:
            output = CommandTemplateExecutor(
                self._cli_service,
                command_template.DISCONNECT_SIMPLEX_OLD
            ).execute_command(dst_port=dst_port)
        return output

    def disconnect_duplex(self, src_port, dst_port, software_version=NEW_MAJOR_VERSION):
        self.select_switch()
        if self._is_new_command_format(software_version):
            output = CommandTemplateExecutor(
                self._cli_service,
                command_template.DISCONNECT_DUPLEX_NEW
            ).execute_command(src_port=src_port, dst_port=dst_port)
        else:
            output = CommandTemplateExecutor(
                self._cli_service,
                command_template.DISCONNECT_DUPLEX_OLD
            ).execute_command(dst_port=dst_port)
        return output

    def disconnect_mcast(self, src_port, dst_port, software_version=NEW_MAJOR_VERSION):
        self.select_switch()

        output = CommandTemplateExecutor(
            self._cli_service,
            command_template.DISCONNECT_MCAST
        ).execute_command(dst_port=dst_port)
        return output

    def connection_info(self, src_address):
        self.select_switch()
        template = command_template.SHOW_CONNECTION
        output = CommandTemplateExecutor(
            self._cli_service,
            template,
            remove_prompt=True
        ).execute_command(port=src_address)

        connections_data = helper.parse_table(
            parsable_str=output,
            header_column_names=[
                "src_addr",
                "src_name",
                "src_rx",
                "connection_type",
                "dst_addr",
                "dst_name",
                "dst_rx",
                "speed",
                "protocol"
            ],
        )

        connection_list = []
        for conn_info in connections_data:
            src_addr_info = conn_info.get("src_addr")
            dst_addr_info = conn_info.get("dst_addr")
            connection_type_info = conn_info.get("connection_type")
            connection_list.append(
                ConnectionInfoDTO(src_addr_info, dst_addr_info, connection_type_info)
            )

        if not connection_list:
            self._logger.warning("There is no connection info.")

        return connection_list
