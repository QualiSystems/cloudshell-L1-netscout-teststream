#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
from collections import OrderedDict

from cloudshell.layer_one.core.driver_commands_interface import DriverCommandsInterface
from cloudshell.layer_one.core.response.response_info import GetStateIdResponseInfo
from cloudshell.layer_one.core.response.resource_info.entities.chassis import Chassis
from cloudshell.layer_one.core.response.resource_info.entities.blade import Blade
from cloudshell.layer_one.core.response.resource_info.entities.port import Port
from cloudshell.layer_one.core.response.response_info import ResourceDescriptionResponseInfo
from netscout_teststream.cli.netscout_cli_handler import NetscoutCliHandler
from netscout_teststream.cli.simulator.cli_simulator import CLISimulator
from netscout_teststream.command_actions.autoload_actions import AutoloadActions
from netscout_teststream.command_actions.system_actions import SystemActions
from netscout_teststream.model.hs_bank import HSBank
from netscout_teststream.model.o_blade import OBlade
from netscout_teststream.model.s_blade import SBlade
from netscout_teststream.model.s_blade_pro import SBladePro
from netscout_teststream.model.t_blade import TBlade


class DriverCommands(DriverCommandsInterface):
    """
    Driver commands implementation
    """
    REGISTERED_BLADES = {
        OBlade.MODEL_NAME.lower(): OBlade,
        HSBank.MODEL_NAME.lower(): HSBank,
        SBlade.MODEL_NAME.lower(): SBlade,
        SBladePro.MODEL_NAME.lower(): SBladePro,
        TBlade.MODEL_NAME.lower(): TBlade

    }

    def __init__(self, logger):
        """
        :param logger:
        :type logger: logging.Logger
        """
        self._logger = logger
        # self._cli_handler = NetscoutCliHandler(logger)
        self._cli_handler = CLISimulator(
            '/Users/yar/Projects/Quali/Github/LayerOne/cloudshell-L1-netscout-teststream/netscout_teststream/cli/simulator/data',
            logger)
        self._switch_name = None

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
        pass

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
        pass

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
            software_version = autoload_actions.software_version()
            switch_address = autoload_actions.switch_ip_addr()
            ports_table = autoload_actions.ports_table()
            blades_dict = {}
            for chassis_id, chassis_data in autoload_actions.chassis_table().iteritems():
                chassis = Chassis(chassis_id, switch_address, 'Netscout Teststream Chassis', None)
                chassis.set_model_name(switch_model_name)
                chassis.set_os_version(software_version)
                chassis_dict[chassis_id] = chassis
                blades_dict = self._build_blades(chassis_id, chassis, chassis_data)
            self._build_ports(blades_dict, ports_table)
        return ResourceDescriptionResponseInfo(chassis_dict.values())

    def _build_blades(self, chassis_id, chassis, chassis_data):
        blades_dict = {}
        for blade_id, blade_data in chassis_data.iteritems():
            blade_type = blade_data.get('blade_type')
            blade_class = self.REGISTERED_BLADES.get(blade_type.lower())
            if not blade_class:
                raise Exception(self.__class__.__name__, 'Blade type {} is not registered'.format(blade_type))
            model_name = blade_data.get('model')
            serial_number = blade_data.get('serial_number')
            blade_instance = blade_class(blade_id)
            blade_instance.set_model_name(model_name)
            blade_instance.set_serial_number(serial_number)
            blade_instance.set_parent_resource(chassis)
            blades_dict[(chassis_id, blade_id)] = blade_instance
        return blades_dict

    def _build_ports(self, blades_dict, ports_table):
        for address, port_data in ports_table.iteritems():
            chassis_id, blade_id, port_id = address.split('.')
            blade = blades_dict.get((int(chassis_id), int(blade_id)))
            if blade:
                port = Port(port_id)
                port.set_parent_resource(blade)
                port.set_model_name(port_data.get('name'))

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
        pass

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
        pass

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
        raise NotImplementedError

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
