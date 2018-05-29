import re

from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor
import netscout_teststream.command_templates.mappings as command_template


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
        return CommandTemplateExecutor(self._cli_service, command_template.SELECT_SWITCH).execute_command(
            switch_name=self._switch_name)

    def connect_simplex(self, src_port, dst_port, software_version=NEW_MAJOR_VERSION):
        self.select_switch()
        if self._is_new_command_format(software_version):
            template = command_template.MAP_SIMPLEX_NEW
        else:
            template = command_template.MAP_SIMPLEX_OLD
        output = CommandTemplateExecutor(self._cli_service, template).execute_command(src_port=src_port,
                                                                                      dst_port=dst_port)
        return output

    def connect_duplex(self, src_port, dst_port, software_version=NEW_MAJOR_VERSION):
        self.select_switch()
        if self._is_new_command_format(software_version):
            template = command_template.MAP_DUPLEX_NEW
        else:
            template = command_template.MAP_DUPLEX_OLD
        output = CommandTemplateExecutor(self._cli_service, template).execute_command(src_port=src_port,
                                                                                      dst_port=dst_port)
        return output

    def disconnect_simplex(self, src_port, dst_port, software_version=NEW_MAJOR_VERSION):
        self.select_switch()
        if self._is_new_command_format(software_version):
            output = CommandTemplateExecutor(self._cli_service,
                                             command_template.DISCONNECT_SIMPLEX_NEW).execute_command(src_port=src_port,
                                                                                                      dst_port=dst_port)
        else:
            output = CommandTemplateExecutor(self._cli_service,
                                             command_template.DISCONNECT_SIMPLEX_OLD).execute_command(dst_port=dst_port)
        return output

    def disconnect_duplex(self, src_port, dst_port, software_version=NEW_MAJOR_VERSION):
        self.select_switch()
        if self._is_new_command_format(software_version):
            output = CommandTemplateExecutor(self._cli_service, command_template.DISCONNECT_DUPLEX_NEW).execute_command(
                src_port=src_port,
                dst_port=dst_port)
        else:
            output = CommandTemplateExecutor(self._cli_service, command_template.DISCONNECT_DUPLEX_OLD).execute_command(
                dst_port=dst_port)
        return output

    def disconnect_mcast(self, src_port, dst_port, software_version=NEW_MAJOR_VERSION):
        self.select_switch()

        output = CommandTemplateExecutor(self._cli_service, command_template.DISCONNECT_MCAST).execute_command(
            dst_port=dst_port)
        return output

    def connection_info(self, src_address):
        self.select_switch()
        template = command_template.SHOW_CONNECTION
        output = CommandTemplateExecutor(self._cli_service, template, remove_prompt=True).execute_command(
            port=src_address)
        # matched = re.search(r".*-\n(.*)\n\n", output, re.DOTALL)
        matched = re.search(r".*--\s+(.*)\s+", output, re.DOTALL)

        if matched is None:
            self._logger.warning("Trying to clear connection which doesn't exist for port {}".format(src_address))
            return None

        conn_info = matched.group(1)

        if re.search('connection\snot\sfound', conn_info, re.IGNORECASE | re.DOTALL):
            return
        
        connection_list = []
        for data in conn_info.strip().splitlines():
            conn_data = re.search(r"(?P<src_addr>.*?)[ ]{2,}"
                                  r"(?P<src_name>.*?)[ ]{2,}"
                                  r".*?[ ]{2,}"  # src Rx Pwr(dBm)
                                  r"(?P<connection_type>.*?)[ ]{2,}"
                                  r"(?P<dst_addr>.*?)[ ]{2,}"
                                  r"(?P<dst_name>.*?)[ ]{2,}"
                                  r".*?[ ]{2,}"  # dst Rx Pwr(dBm)
                                  r"(?P<speed>.*)"
                                  r"(?P<protocol>.*)",
                                  data)
            if not conn_data:
                self._logger.warning('Cannot parse connection data for port {}'.format(src_address))
                continue
            src_addr_info = conn_data.group("src_addr")
            dst_addr_info = conn_data.group("dst_addr")
            connection_type_info = conn_data.group("connection_type")
            # if src_addr_info == src_address:
            connection_list.append(ConnectionInfoDTO(src_addr_info, dst_addr_info, connection_type_info))
        return connection_list
