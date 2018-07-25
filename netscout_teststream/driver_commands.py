#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
from collections import defaultdict

from cloudshell.layer_one.core.driver_commands_interface import DriverCommandsInterface
from cloudshell.layer_one.core.response.response_info import GetStateIdResponseInfo
from cloudshell.layer_one.core.response.response_info import ResourceDescriptionResponseInfo
from netscout_teststream.cli.netscout_cli_handler import NetscoutCliHandler
from netscout_teststream.cli.simulator.cli_simulator import CLISimulator
from netscout_teststream.command_actions.autoload_actions import AutoloadActions
from netscout_teststream.command_actions.mapping_actions import MappingActions
from netscout_teststream.command_actions.system_actions import SystemActions
from netscout_teststream.model.netscout_blade import NetscoutBlade
from netscout_teststream.model.netscout_chassis import NetscoutChassis
from netscout_teststream.model.netscout_port import NetscoutPort


class DriverCommands(DriverCommandsInterface):
    """
    Driver commands implementation
    """
    LOGICAL_PORT_MODE = 'LOGICAL'
    TX_SUBPORT_INDEX = 'TX'
    RX_SUBPORT_INDEX = 'RX'
    SUFFIX_SEPARATOR = '-'
    CHASSIS_ID = 1

    def __init__(self, logger, driver_port_mode=LOGICAL_PORT_MODE):
        """
        :param logger:
        :type logger: logging.Logger
        """
        self._logger = logger
        self._driver_port_mode = driver_port_mode
        self._cli_handler = NetscoutCliHandler(logger)
        # self._cli_handler = CLISimulator(
        #     os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cli', 'simulator', 'data'),
        #     logger)
        self._switch_name = None
        self.__software_version = None

    def _software_version(self, session):
        if not self.__software_version:
            system_actions = SystemActions(self._switch_name, session, self._logger)
            self.__software_version = system_actions.software_version()
        return self.__software_version

    @property
    def _is_logical_port_mode(self):
        return self._driver_port_mode.lower() == self.LOGICAL_PORT_MODE.lower()

    def login(self, address, username, password):
        """
        Perform login operation on the device
        :param address: resource address, "192.168.42.240"
        :param username: username to login on the device
        :param password: password
        :return: None
        :raises Exception: if command failed
        Example:
            # Define session attributes
            self._cli_handler.define_session_attributes(address, username, password)

            # Obtain cli session
            with self._cli_handler.default_mode_service() as session:
                # Executing simple command
                device_info = session.send_command('show version')
                self._logger.info(device_info)
        """
        address_data = re.search(
            r"(?P<host>[^:]*)"
            r":?(?P<port>[0-9]*?)"
            r"\?teststream=(?P<switch_name>.*)",
            address,
            re.IGNORECASE)

        if not address_data:
            raise Exception("Switch name was not found. "
                            "Make sure resource address is in format host[:port]?teststream=switch_name")
        host = address_data.group("host")
        port = address_data.group("port")
        try:
            port = int(port)
        except:
            port = None

        self._switch_name = address_data.group("switch_name")

        self._logger.debug('Defined switch: ' + self._switch_name)

        self._cli_handler.define_session_attributes(host, username, password, port)
        with self._cli_handler.default_mode_service() as session:
            system_actions = SystemActions(self._switch_name, session, self._logger)
            available_switches = system_actions.available_switches()
            self._logger.debug('Available Switches: ' + ", ".join(available_switches))
            if self._switch_name.lower() not in map(lambda x: x.lower(), available_switches):
                raise Exception('Switch {} is not available'.format(self._switch_name))

    def get_state_id(self):
        """
        Check if CS synchronized with the device.
        :return: Synchronization ID, GetStateIdResponseInfo(-1) if not used
        :rtype: cloudshell.layer_one.core.response.response_info.GetStateIdResponseInfo
        :raises Exception: if command failed

        Example:
            # Obtain cli session
            with self._cli_handler.default_mode_service() as session:
                # Execute command
                chassis_name = session.send_command('show chassis name')
                return chassis_name
        """
        return GetStateIdResponseInfo(-1)

    def set_state_id(self, state_id):
        """
        Set synchronization state id to the device, called after Autoload or SyncFomDevice commands
        :param state_id: synchronization ID
        :type state_id: str
        :return: None
        :raises Exception: if command failed

        Example:
            # Obtain cli session
            with self._cli_handler.config_mode_service() as session:
                # Execute command
                session.send_command('set chassis name {}'.format(state_id))
        """
        pass

    def _convert_port_address(self, port_address):
        """
        :type port_address: str
        """
        ip_addr, blade_id, port_id = port_address.split('/')
        port_id = port_id.split(self.SUFFIX_SEPARATOR)[0]
        return '.'.join(map(lambda x: x.zfill(2), [str(self.CHASSIS_ID), blade_id, port_id]))

    def map_bidi(self, src_port, dst_port):
        """
        Create a bidirectional connection between source and destination ports
        :param src_port: src port address, '192.168.42.240/1/21'
        :type src_port: str
        :param dst_port: dst port address, '192.168.42.240/1/22'
        :type dst_port: str
        :return: None
        :raises Exception: if command failed

        Example:
            with self._cli_handler.config_mode_service() as session:
                session.send_command('map bidir {0} {1}'.format(convert_port(src_port), convert_port(dst_port)))

        """
        if not self._is_logical_port_mode:
            raise Exception("Bidirectional port mapping could be done only in LOGICAL port_mode "
                            "current mode: {}".format(self._driver_port_mode))
        with self._cli_handler.default_mode_service() as session:
            mapping_action = MappingActions(self._switch_name, session, self._logger)
            mapping_action.connect_duplex(self._convert_port_address(src_port),
                                          self._convert_port_address(dst_port), self._software_version(session))

    def map_uni(self, src_port, dst_ports):
        """
        Unidirectional mapping of two ports
        :param src_port: src port address, '192.168.42.240/1/21'
        :type src_port: str
        :param dst_ports: list of dst ports addresses, ['192.168.42.240/1/22', '192.168.42.240/1/23']
        :type dst_ports: list
        :return: None
        :raises Exception: if command failed

        Example:
            with self._cli_handler.config_mode_service() as session:
                for dst_port in dst_ports:
                    session.send_command('map {0} also-to {1}'.format(convert_port(src_port), convert_port(dst_port)))
        """
        if not self._is_logical_port_mode:
            self._validate_tx_port(src_port)
            map(lambda x: self._validate_rx_subport(x), dst_ports)

        with self._cli_handler.default_mode_service() as session:
            mapping_action = MappingActions(self._switch_name, session, self._logger)
            src_address = self._convert_port_address(src_port)
            exception_messages = []
            for dst_port in dst_ports:
                try:
                    mapping_action.connect_simplex(src_address, self._convert_port_address(dst_port),
                                                   self._software_version(session))
                except Exception as e:
                    if len(e.args) > 1:
                        exception_messages.append(e.args[1])
                    elif len(e.args) == 1:
                        exception_messages.append(e.args[0])

            if exception_messages:
                raise Exception(self.__class__.__name__, ', '.join(exception_messages))

    def get_resource_description(self, address):
        """
        Auto-load function to retrieve all information from the device
        :param address: resource address, '192.168.42.240'
        :type address: str
        :return: resource description
        :rtype: cloudshell.layer_one.core.response.response_info.ResourceDescriptionResponseInfo
        :raises cloudshell.layer_one.core.layer_one_driver_exception.LayerOneDriverException: Layer one exception.

        Example:

        from cloudshell.layer_one.core.response.resource_info.entities.chassis import Chassis
        from cloudshell.layer_one.core.response.resource_info.entities.blade import Blade
        from cloudshell.layer_one.core.response.resource_info.entities.port import Port
        from cloudshell.layer_one.core.response.response_info import ResourceDescriptionResponseInfo

        chassis_resource_id = 1
        chassis_model_name = "Netscout Teststream Chassis"
        chassis_serial_number = 'NA'
        chassis = Chassis(chassis_resource_id, address, chassis_model_name, chassis_serial_number)

        blade1 = Blade('1')
        blade1.set_parent_resource(chassis)
        blade2 = Blade('2')
        blade2.set_parent_resource(chassis)

        for port_id in range(1, 11):
            port = Port(port_id)
            port.set_parent_resource(blade1)

        for port_id in range(1, 11):
            port = Port(port_id)
            port.set_parent_resource(blade2)

        return ResourceDescriptionResponseInfo([chassis])
        """
        with self._cli_handler.default_mode_service() as session:
            chassis_dict = {}
            autoload_actions = AutoloadActions(self._switch_name, session, self._logger)
            switch_model_name = autoload_actions.switch_model_name()
            software_version = self._software_version(session)
            switch_address = autoload_actions.switch_ip_addr()
            ports_table = autoload_actions.port_table()
            blades_dict = {}
            for chassis_id, chassis_data in autoload_actions.chassis_table().iteritems():
                chassis = NetscoutChassis(chassis_id, address)
                chassis.set_ip_address(switch_address)
                chassis.set_model_name(switch_model_name)
                chassis.set_os_version(software_version)
                chassis_dict[chassis_id] = chassis
                blades_dict = self._build_blades(chassis_id, chassis, chassis_data)
            port_dict = self._build_ports(blades_dict, ports_table)
            mapping_table = autoload_actions.mapping_table()
            self._build_mappings(mapping_table, port_dict)
        return ResourceDescriptionResponseInfo(chassis_dict.values())

    def _build_blades(self, chassis_id, chassis, chassis_data):
        self._logger.debug('Build Blades')
        blades_dict = {}
        for blade_id, blade_type in chassis_data.iteritems():
            blade_instance = NetscoutBlade(blade_id, blade_type)
            blade_instance.set_parent_resource(chassis)
            blades_dict[(chassis_id, blade_id)] = blade_instance
        return blades_dict

    def _build_ports(self, blades_dict, ports_table):
        self._logger.debug('Build Ports')
        port_dict = defaultdict(list)
        for address, port_info in ports_table.iteritems():
            """:type port_info: netscout_teststream.command_actions.autoload_actions.PortInfoDTO"""
            chassis_id, blade_id, port_id = address.split('.')
            blade = blades_dict.get((int(chassis_id), int(blade_id)))
            if blade:
                if self._is_logical_port_mode:
                    port = NetscoutPort(port_id, port_info.name, port_info.protocol_id)
                    port.set_parent_resource(blade)
                    port_dict[address].append(port)
                else:
                    for suffix in (self.TX_SUBPORT_INDEX, self.RX_SUBPORT_INDEX):
                        subport_id = "{}-{}".format(port_id, suffix)
                        port = NetscoutPort(subport_id, port_info.name, port_info.protocol_id)
                        port.set_parent_resource(blade)
                        port_dict[address].append(port)
        return port_dict

    def _build_mappings(self, mapping_table, port_dict):
        """
        :type mapping_table: dict
        :type port_dict: dict
        """
        self._logger.debug("Build mappings")
        for src_addr, dst_addr_list in mapping_table.iteritems():
            self._map_ports(src_addr, dst_addr_list, port_dict)

    def _map_ports(self, src_addr, dst_addr_list, port_dict):
        src_port = port_dict.get(src_addr, [])[0]
        """:type src_port: netscout_teststream.model.netscout_port.NetscoutPort"""
        for dst_addr in dst_addr_list:
            if self._is_logical_port_mode:
                dst_port = port_dict.get(dst_addr, [])[0]
            else:
                dst_port = port_dict.get(dst_addr, [])[1]
                """:type dst_port: netscout_teststream.model.netscout_port.NetscoutPort"""
            dst_port.add_mapping(src_port)

    def map_clear(self, ports):
        """
        Remove simplex/multi-cast/duplex connection ending on the destination port
        :param ports: ports, ['192.168.42.240/1/21', '192.168.42.240/1/22']
        :type ports: list
        :return: None
        :raises Exception: if command failed

        Example:
            exceptions = []
            with self._cli_handler.config_mode_service() as session:
                for port in ports:
                    try:
                        session.send_command('map clear {}'.format(convert_port(port)))
                    except Exception as e:
                        exceptions.append(str(e))
                if exceptions:
                    raise Exception('self.__class__.__name__', ','.join(exceptions))
        """
        exception_messages = []
        for port in ports:
            try:
                port_addr = self._convert_port_address(port)
                self._disconnect_ports(port_addr)
            except Exception as e:
                if len(e.args) > 1:
                    exception_messages.append(e.args[1])
                elif len(e.args) == 1:
                    exception_messages.append(e.args[0])

        if exception_messages:
            raise Exception(self.__class__.__name__, ', '.join(exception_messages))

    def map_clear_to(self, src_port, dst_ports):
        """
        Remove simplex/multi-cast/duplex connection ending on the destination port
        :param src_port: src port address, '192.168.42.240/1/21'
        :type src_port: str
        :param dst_ports: list of dst ports addresses, ['192.168.42.240/1/21', '192.168.42.240/1/22']
        :type dst_ports: list
        :return: None
        :raises Exception: if command failed

        Example:
            with self._cli_handler.config_mode_service() as session:
                _src_port = convert_port(src_port)
                for port in dst_ports:
                    _dst_port = convert_port(port)
                    session.send_command('map clear-to {0} {1}'.format(_src_port, _dst_port))
        """
        if not self._is_logical_port_mode:
            self._validate_tx_port(src_port)
            map(lambda x: self._validate_rx_subport(x), dst_ports)

        exception_messages = []
        src_port_addr = self._convert_port_address(src_port)
        for dst_port in dst_ports:
            try:
                dst_port_addr = self._convert_port_address(dst_port)
                self._disconnect_ports(src_port_addr, dst_port_addr)
            except Exception as e:
                if len(e.args) > 1:
                    exception_messages.append(e.args[1])
                elif len(e.args) == 1:
                    exception_messages.append(e.args[0])

        if exception_messages:
            raise Exception(self.__class__.__name__, ', '.join(exception_messages))

    def _disconnect_ports(self, src_port, dst_port=None):
        with self._cli_handler.default_mode_service() as session:
            mapping_action = MappingActions(self._switch_name, session, self._logger)
            connection_info_list = mapping_action.connection_info(src_port)
            if not connection_info_list:
                self._logger.debug('Port {} is not connected'.format(src_port))
                return
            for connection_info in connection_info_list:
                if dst_port and connection_info.dst_address != dst_port:
                    continue

                if connection_info.connection_type.lower() in ['simplex', 'unknown']:
                    mapping_action.disconnect_simplex(connection_info.src_address, connection_info.dst_address,
                                                      self._software_version(session))
                elif connection_info.connection_type.lower() == 'duplex':
                    mapping_action.disconnect_duplex(connection_info.src_address, connection_info.dst_address,
                                                     self._software_version(session))
                elif connection_info.connection_type.lower() == 'mcast':
                    mapping_action.disconnect_mcast(connection_info.src_address, connection_info.dst_address,
                                                    self._software_version(session))
                else:
                    raise Exception(self.__class__.__name__, 'Connection type {} is no supported by the driver'.format(
                        connection_info.connection_type))

    def _validate_tx_port(self, port_address):
        """Validate if given sub-port is a correct transceiver sub-port, return logical port part

        Example:
            sub-port "1.1.1-Tx" => port "1.1.1"
            sub-port "1.1.1-Rx" => raise Exception

        :param port_address: (str) sub-port in format "<chassis>.<blade>.<port>-Tx"
        :return: (str) logical port part for the given sub-port
        """
        ip_addr, blade_id, port_id = port_address.split('/')
        port, sub_idx = port_id.split(self.SUFFIX_SEPARATOR)
        if sub_idx.upper() != self.TX_SUBPORT_INDEX.upper():
            raise Exception("Receiver sub-port can't be used as a source")

    def _validate_rx_subport(self, port_address):
        """Validate if given sub-port is a correct receiver sub-port, return logical port part

        Example:
            sub-port "1.1.1-Rx" => port "1.1.1"
            sub-port "1.1.1-Tx" => raise Exception

        :param port_address: (str) sub-port in format "<chassis>.<blade>.<port>-Rx"
        :return: (str) logical port part for the given sub-port
        """
        ip_addr, blade_id, port_id = port_address.split('/')
        port, sub_idx = port_id.split(self.SUFFIX_SEPARATOR)
        if sub_idx.upper() != self.RX_SUBPORT_INDEX.upper():
            raise Exception("Transmitter sub-port can't be used as a destination")

    def get_attribute_value(self, cs_address, attribute_name):
        """
        Retrieve attribute value from the device
        :param cs_address: address, '192.168.42.240/1/21'
        :type cs_address: str
        :param attribute_name: attribute name, "Port Speed"
        :type attribute_name: str
        :return: attribute value
        :rtype: cloudshell.layer_one.core.response.response_info.AttributeValueResponseInfo
        :raises Exception: if command failed

        Example:
            with self._cli_handler.config_mode_service() as session:
                command = AttributeCommandFactory.get_attribute_command(cs_address, attribute_name)
                value = session.send_command(command)
                return AttributeValueResponseInfo(value)
        """
        pass

    def set_attribute_value(self, cs_address, attribute_name, attribute_value):
        """
        Set attribute value to the device
        :param cs_address: address, '192.168.42.240/1/21'
        :type cs_address: str
        :param attribute_name: attribute name, "Port Speed"
        :type attribute_name: str
        :param attribute_value: value, "10000"
        :type attribute_value: str
        :return: attribute value
        :rtype: cloudshell.layer_one.core.response.response_info.AttributeValueResponseInfo
        :raises Exception: if command failed

        Example:
            with self._cli_handler.config_mode_service() as session:
                command = AttributeCommandFactory.set_attribute_command(cs_address, attribute_name, attribute_value)
                session.send_command(command)
                return AttributeValueResponseInfo(attribute_value)
        """
        pass

    def map_tap(self, src_port, dst_ports):
        """
        Add TAP connection
        :param src_port: port to monitor '192.168.42.240/1/21'
        :type src_port: str
        :param dst_ports: ['192.168.42.240/1/22', '192.168.42.240/1/23']
        :type dst_ports: list
        :return: None
        :raises Exception: if command failed

        Example:
            return self.map_uni(src_port, dst_ports)
        """
        return self.map_uni(src_port, dst_ports)

    def set_speed_manual(self, src_port, dst_port, speed, duplex):
        """
        Set connection speed. It is not used with new standard
        :param src_port:
        :param dst_port:
        :param speed:
        :param duplex:
        :return:
        """
        raise NotImplementedError
