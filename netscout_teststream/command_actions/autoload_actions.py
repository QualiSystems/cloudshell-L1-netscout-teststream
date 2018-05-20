#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor
import netscout_teststream.command_templates.autoload as command_template


class PortKeys():
    PROTOCOL_ID = 'protocol_id'
    NAME = 'name'
    ADDRESS = 'address'


# class BladeKeys():
#     BLADE_ID = 'blade_id'
#     BLADE_TYPE = 'blade_type'


class AutoloadActions(object):
    """
    Autoload actions
    """
    SW_INFORM = 'sw_inform'
    SW_COMPONENTS = 'sw_components'

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
        self.__switch_info_table = {}

    @property
    def _switch_info_table(self):
        if not self.__switch_info_table:
            output = CommandTemplateExecutor(self._cli_service, command_template.SHOW_SWITCH_INFO).execute_command(
                switch_name=self._switch_name)
            info_match = re.search(
                r'\s*\*+\s+PHYSICAL\sINFORMATION\s\*+\s*(?P<physical_info>.*)'
                r'\s*\*+\s+SWITCH\sCOMPONENTS\s\*+\s*(?P<switch_components>.*)',
                output, re.DOTALL)

            self.__switch_info_table[self.SW_INFORM] = info_match.group("physical_info")
            self.__switch_info_table[self.SW_COMPONENTS] = info_match.group("switch_components")
        return self.__switch_info_table

    def switch_model_name(self):
        return re.search(r"Switch Model:[ ]*(.*?)\n", self._switch_info_table[self.SW_INFORM], re.DOTALL).group(1)

    def switch_ip_addr(self):
        return re.search(r"IP Address:[ ]*(.*?)\n", self._switch_info_table[self.SW_INFORM], re.DOTALL).group(1)

    def chassis_table(self):
        controller_ids = re.findall(r'chassis\scontroller\s(\d+):', self._switch_info_table[self.SW_COMPONENTS],
                                    flags=re.IGNORECASE | re.DOTALL)

        controller_table_match = re.search(r'chassis\scontroller\s\d+:\s*(.*)' * len(controller_ids),
                                           self._switch_info_table[self.SW_COMPONENTS], flags=re.IGNORECASE | re.DOTALL)
        chassis_table = {}
        for index in xrange(len(controller_ids)):
            controller_id = int(controller_ids[index])
            chassis_table[controller_id] = self._parse_blade_data(controller_table_match.group(index + 1))
        return chassis_table

    def _parse_blade_data(self, blades_data):
        blades_id_type = re.findall(r'pim:\s+(\d+)\s+([\w-]+)', blades_data, flags=re.IGNORECASE)
        # blade_dict = {}
        # blade_pattern = r'pim:\s+\d+\s+[\w-]+s*(.*)' * len(blades_id_type)
        # blade_table_match = re.search(blade_pattern, blades_data,
        #                               flags=re.IGNORECASE | re.DOTALL)
        # for index in xrange(len(blades_id_type)):
        #     blade_id = int(blades_id_type[index][0])
        #     blade_type = blades_id_type[index][1]
        #     data = blade_table_match.group(index + 1)
        #     blade_info = re.search(
        #         r"(?P<vendor>.*),(?P<model>.*),(?P<uboot_rev>.*),(?P<serial_number>.*)", data.strip(), re.DOTALL)
        #
        #     if not blade_info:
        #         blade_info = re.search(
        #             r"(?P<model>.*?)\s{2,}(?P<uboot_rev>.*?)\s{2,}(?P<serial_number>.*?)(\s{2,}|$)",
        #             data.strip(),
        #             re.DOTALL)
        #     blade_dict[blade_id] = blade_info.groupdict()
        #     blade_dict[blade_id]['blade_type'] = blade_type
        # return blade_dict
        blade_dict = {}
        for blade_id, blade_type in blades_id_type:
            blade_dict[int(blade_id)] = blade_type
        return blade_dict

    def port_table(self):
        output = CommandTemplateExecutor(self._cli_service, command_template.SHOW_PORTS_RAW).execute_command(
            switch_name=self._switch_name)
        port_table = {}
        for line in output.strip().splitlines():
            address, protocol_id, normal, connected, connected_dir, subport_tx, subport_rx, alarm, name = line.strip(
            ).split(',')
            port_table[address] = {
                PortKeys.ADDRESS: address,
                PortKeys.PROTOCOL_ID: protocol_id,
                PortKeys.NAME: name.strip("'")
            }

        return port_table

    def mapping_table(self):
        """Get mappings for all multi-cast/simplex/duplex port connections

        :param command_logger: logging.Logger instance
        :return: (dictionary) destination sub-port => source sub-port
        """
        output = CommandTemplateExecutor(self._cli_service, command_template.SHOW_CONNECTIONS).execute_command(
            switch_name=self._switch_name)
        mapping_info = {}

        if "connection not found" in output.lower():
            return mapping_info

        connections_data = re.search(r".*-\s+(.*)\s+", output, re.DOTALL)
        if not connections_data:
            return mapping_info

        connections_list = connections_data.group(1).strip().splitlines()
        for conn_info in connections_list:
            conn_data = re.search(r"(?P<src_addr>.*?)[ ]{2,}"
                                  r"(?P<src_name>.*?)[ ]{2,}"
                                  r".*?[ ]{2,}"  # src Rx Pwr(dBm)
                                  r"(?P<connection_type>.*?)[ ]{2,}"
                                  r"(?P<dst_addr>.*?)[ ]{2,}"
                                  r"(?P<dst_name>.*?)[ ]{2,}"
                                  r".*?[ ]{2,}"  # dst Rx Pwr(dBm)
                                  r"(?P<speed>.*)"
                                  r"(?P<protocol>.*)",
                                  conn_info)
            conn_type = conn_data.group('connection_type').lower()
            src = conn_data.group('src_addr')
            dst = conn_data.group('dst_addr')

            if conn_type in ('simplex', 'mcast'):
                mapping_info[dst] = src
            elif conn_type == 'duplex':
                mapping_info[dst] = src
                mapping_info[src] = dst
            else:
                self._logger.warning("Can't set mapping for unhandled connection type. "
                                     "Connection info: {}".format(conn_data))
        return mapping_info
