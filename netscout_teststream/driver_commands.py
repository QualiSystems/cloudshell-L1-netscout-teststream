from __future__ import annotations

import re
from collections import defaultdict

from cloudshell.layer_one.core.driver_commands_interface import DriverCommandsInterface
from cloudshell.layer_one.core.helper.logger import get_l1_logger
from cloudshell.layer_one.core.helper.runtime_configuration import RuntimeConfiguration
from cloudshell.layer_one.core.response.response_info import (
    AttributeValueResponseInfo,
    GetStateIdResponseInfo,
    ResourceDescriptionResponseInfo,
)

from netscout_teststream.cli.netscout_cli_handler import NetscoutCliHandler

# from netscout_teststream.cli.simulator.cli_simulator import CLISimulator  # noqa: E800
from netscout_teststream.command_actions.autoload_actions import AutoloadActions
from netscout_teststream.command_actions.mapping_actions import MappingActions
from netscout_teststream.command_actions.system_actions import SystemActions
from netscout_teststream.model.netscout_blade import NetscoutBlade
from netscout_teststream.model.netscout_chassis import NetscoutChassis
from netscout_teststream.model.netscout_port import NetscoutPort

logger = get_l1_logger(name=__name__)


class DriverCommands(DriverCommandsInterface):
    """Driver commands implementation."""

    LOGICAL_PORT_MODE = "LOGICAL"
    TX_SUBPORT_INDEX = "TX"
    RX_SUBPORT_INDEX = "RX"
    SUFFIX_SEPARATOR = "-"
    CHASSIS_ID = 1

    def __init__(self, runtime_config: RuntimeConfiguration):
        self._runtime_config = runtime_config
        self._driver_port_mode = runtime_config.read_key(
            "DRIVER.PORT_MODE", self.LOGICAL_PORT_MODE
        )
        self._cli_handler = NetscoutCliHandler()
        """
        self._cli_handler = CLISimulator(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "cli",
                         "simulator",
                         "data"),
            logger)
        """  # noqa: E800
        self._switch_name = None
        self.__software_version = None

    def _software_version(self, session):
        if not self.__software_version:
            system_actions = SystemActions(self._switch_name, session)
            self.__software_version = system_actions.software_version()
        return self.__software_version

    @property
    def _is_logical_port_mode(self):
        return self._driver_port_mode.lower() == self.LOGICAL_PORT_MODE.lower()

    def login(self, address: str, username: str, password: str):
        """Perform login operation on the device.

        Example:
            # Define session attributes
            self._cli_handler.define_session_attributes(address, username, password)

            # Obtain cli session
            with self._cli_handler.default_mode_service() as session:
                # Executing simple command
                device_info = session.send_command("show version")
                logger.info(device_info)
        """
        address_data = re.search(
            r"(?P<host>[^:]*)"
            r":?(?P<port>[0-9]*?)"
            r"\?teststream=(?P<switch_name>.*)",
            address,
            re.IGNORECASE,
        )

        if not address_data:
            raise Exception(
                "Switch name was not found. Make sure resource address is in format: "
                "host[:port]?teststream=switch_name"
            )
        host = address_data.group("host")
        port = address_data.group("port")
        try:
            port = int(port)
        except Exception:  # noqa: E722
            port = None

        self._switch_name = address_data.group("switch_name")

        logger.debug(f"Defined switch: {self._switch_name}")

        self._cli_handler.define_session_attributes(host, username, password, port)
        with self._cli_handler.default_mode_service() as session:
            system_actions = SystemActions(self._switch_name, session)
            available_switches = system_actions.available_switches()
            logger.debug(f"Available Switches: {', '.join(available_switches)}")
            if self._switch_name.lower() not in (s.lower() for s in available_switches):
                raise Exception(f"Switch {self._switch_name} is not available")

    def get_state_id(self) -> GetStateIdResponseInfo:
        """Check if CS synchronized with the device."""
        return GetStateIdResponseInfo(-1)

    def set_state_id(self, state_id: str):
        """Set synchronization state id to the device."""
        pass

    def _convert_port_address(self, port_address: str) -> str:
        ip_addr, blade_id, port_id = port_address.split("/")
        port_id = port_id.split(self.SUFFIX_SEPARATOR)[0]
        return f"{str(self.CHASSIS_ID).zfill(2)}.{blade_id.zfill(2)}.{port_id.zfill(2)}"

    def map_bidi(self, src_port: str, dst_port: str):
        """Create a bidirectional connection between source and destination ports."""
        if not self._is_logical_port_mode:
            raise Exception(
                f"Bidirectional port mapping could be done only in LOGICAL port_mode. "
                f"Current port mode: {self._driver_port_mode}"
            )
        with self._cli_handler.default_mode_service() as session:
            mapping_action = MappingActions(self._switch_name, session)
            mapping_action.connect_duplex(
                self._convert_port_address(src_port),
                self._convert_port_address(dst_port),
                self._software_version(session),
            )

    def map_uni(self, src_port: str, dst_ports: list[str]):
        """Unidirectional mapping of two ports."""
        if not self._is_logical_port_mode:
            self._validate_tx_port(src_port)
            map(lambda x: self._validate_rx_subport(x), dst_ports)  # noqa: C417

        with self._cli_handler.default_mode_service() as session:
            mapping_action = MappingActions(self._switch_name, session)
            src_address = self._convert_port_address(src_port)
            exception_messages = []
            for dst_port in dst_ports:
                try:
                    mapping_action.connect_simplex(
                        src_address,
                        self._convert_port_address(dst_port),
                        self._software_version(session),
                    )
                except Exception as e:
                    if len(e.args) > 1:
                        exception_messages.append(e.args[1])
                    elif len(e.args) == 1:
                        exception_messages.append(e.args[0])

            if exception_messages:
                raise Exception(", ".join(exception_messages))

    def get_resource_description(self, address: str) -> ResourceDescriptionResponseInfo:
        """Auto-load function to retrieve all information from the device."""
        with self._cli_handler.default_mode_service() as session:
            chassis_dict = {}
            autoload_actions = AutoloadActions(self._switch_name, session)
            switch_model_name = autoload_actions.switch_model_name()
            software_version = self._software_version(session)
            switch_address = autoload_actions.switch_ip_addr()
            ports_table = autoload_actions.port_table()
            blades_dict = {}
            for chassis_id, chassis_data in autoload_actions.chassis_table().items():
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

    def _build_blades(self, chassis_id, chassis, chassis_data: dict) -> dict:
        logger.debug("Build Blades")
        blades_dict = {}
        for blade_id, blade_type in chassis_data.items():
            blade_instance = NetscoutBlade(blade_id, blade_type)
            blade_instance.set_parent_resource(chassis)
            blades_dict[(chassis_id, blade_id)] = blade_instance
        return blades_dict

    def _build_ports(self, blades_dict: dict, ports_table: dict):
        logger.debug("Build Ports")
        port_dict = defaultdict(list)
        for address, port_info in ports_table.items():
            chassis_id, blade_id, port_id = address.split(".")
            blade = blades_dict.get((int(chassis_id), int(blade_id)))
            if blade:
                if self._is_logical_port_mode:
                    port = NetscoutPort(port_id, port_info.name, port_info.protocol_id)
                    port.set_parent_resource(blade)
                    port_dict[address].append(port)
                else:
                    for suffix in (self.TX_SUBPORT_INDEX, self.RX_SUBPORT_INDEX):
                        subport_id = f"{port_id}-{suffix}"
                        port = NetscoutPort(
                            subport_id, port_info.name, port_info.protocol_id
                        )
                        port.set_parent_resource(blade)
                        port_dict[address].append(port)
        return port_dict

    def _build_mappings(self, mapping_table: dict, port_dict: dict):
        logger.debug("Build mappings")
        for src_addr, dst_addr_list in mapping_table.items():
            self._map_ports(src_addr, dst_addr_list, port_dict)

    def _map_ports(self, src_addr: str, dst_addr_list: list[str], port_dict: dict):
        src_port = port_dict.get(src_addr, [])[0]
        for dst_addr in dst_addr_list:
            if self._is_logical_port_mode:
                dst_port = port_dict.get(dst_addr, [])[0]
            else:
                dst_port = port_dict.get(dst_addr, [])[1]
            dst_port.add_mapping(src_port)

    def map_clear(self, ports: list[str]):
        """Remove simplex/multi-cast/duplex connection ending on the destination port.

        ports - ["192.168.42.240/1/21", "192.168.42.240/1/22"]
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
            raise Exception(", ".join(exception_messages))

    def map_clear_to(self, src_port: str, dst_ports: list[str]):
        """Remove simplex/multi-cast/duplex connection ending on the dst port."""
        if not self._is_logical_port_mode:
            self._validate_tx_port(src_port)
            map(lambda x: self._validate_rx_subport(x), dst_ports)  # noqa: C417

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
            raise Exception(", ".join(exception_messages))

    def _disconnect_ports(self, src_port: str, dst_port: str = None):
        with self._cli_handler.default_mode_service() as session:
            mapping_action = MappingActions(self._switch_name, session)
            connection_info_list = mapping_action.connection_info(src_port)
            if not connection_info_list:
                logger.debug(f"Port {src_port} is not connected")
                return
            for connection_info in connection_info_list:
                if dst_port and connection_info.dst_address != dst_port:
                    continue

                if connection_info.connection_type.lower() in ["simplex", "unknown"]:
                    mapping_action.disconnect_simplex(
                        connection_info.src_address,
                        connection_info.dst_address,
                        self._software_version(session),
                    )
                elif connection_info.connection_type.lower() == "duplex":
                    mapping_action.disconnect_duplex(
                        connection_info.src_address,
                        connection_info.dst_address,
                        self._software_version(session),
                    )
                elif connection_info.connection_type.lower() == "mcast":
                    mapping_action.disconnect_mcast(connection_info.dst_address)
                else:
                    raise Exception(
                        f"Connection type {connection_info.connection_type} "
                        f"is no supported by the driver."
                    )

    def _validate_tx_port(self, port_address: str):
        """Validate if given sub-port is a correct transceiver sub-port.

        Sub-port in format "<chassis>.<blade>.<port>-Tx"
        Example:
            sub-port "1.1.1-Tx" => port "1.1.1"
            sub-port "1.1.1-Rx" => raise Exception
        """
        ip_addr, blade_id, port_id = port_address.split("/")
        port, sub_idx = port_id.split(self.SUFFIX_SEPARATOR)
        if sub_idx.upper() != self.TX_SUBPORT_INDEX.upper():
            raise Exception("Receiver sub-port can't be used as a source")

    def _validate_rx_subport(self, port_address: str):
        """Validate if given sub-port is a correct receiver sub-port.

        Sub-port in format "<chassis>.<blade>.<port>-Rx"
        Example:
            sub-port "1.1.1-Rx" => port "1.1.1"
            sub-port "1.1.1-Tx" => raise Exception
        """
        ip_addr, blade_id, port_id = port_address.split("/")
        port, sub_idx = port_id.split(self.SUFFIX_SEPARATOR)
        if sub_idx.upper() != self.RX_SUBPORT_INDEX.upper():
            raise Exception("Transmitter sub-port can't be used as a destination")

    def get_attribute_value(
        self, cs_address: str, attribute_name: str
    ) -> AttributeValueResponseInfo:
        """Retrieve attribute value from the device.

        Example:
            with self._cli_handler.config_mode_service() as session:
                command = AttributeCommandFactory.get_attribute_command(
                                                                    cs_address,
                                                                    attribute_name
                                                                    )
                value = session.send_command(command)
                return AttributeValueResponseInfo(value)
        """
        pass

    def set_attribute_value(
        self, cs_address: str, attribute_name: str, attribute_value: str
    ) -> AttributeValueResponseInfo:
        """Set attribute value to the device.

        Example:
            with self._cli_handler.config_mode_service() as session:
                command = AttributeCommandFactory.set_attribute_command(
                                                                    cs_address,
                                                                    attribute_name,
                                                                    attribute_value
                                                                    )
                session.send_command(command)
                return AttributeValueResponseInfo(attribute_value)
        """
        pass

    def map_tap(self, src_port: str, dst_ports: list[str]):
        """Add TAP connection.

        Example:
            return self.map_uni(
                        "192.168.42.240/1/21",
                        ["192.168.42.240/1/22", "192.168.42.240/1/23"]
                        )
        """
        return self.map_uni(src_port, dst_ports)

    def set_speed_manual(self, src_port: str, dst_port: str, speed, duplex):
        """Set connection speed."""
        raise NotImplementedError
