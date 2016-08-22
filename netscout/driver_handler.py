import re
from collections import OrderedDict

from common.configuration_parser import ConfigurationParser
from common.driver_handler_base import DriverHandlerBase
from common.resource_info import ResourceInfo


class NetscoutDriverHandler(DriverHandlerBase):
    TX_SUBPORT_INDEX = 'TX'
    RX_SUBPORT_INDEX = 'RX'

    GENERIC_ERRORS = OrderedDict([
        ("[Ii]nvalid", "Command is invalid"),
        ("[Nn]ot [Ll]ogged", "User is not logged in"),
        ("error|ERROR", "Failed to perform command"),
    ])

    def __init__(self):
        DriverHandlerBase.__init__(self)
        self._port_mode = ConfigurationParser.get("driver_variable", "port_mode")
        self._switch_name = None

    def login(self, address, username, password, command_logger):
        """Perform login operation on the device

        :param address: (str) address in the format <host>:<port>?Horizon=<switch_name> (port is optional)
        :param username: (str) username for horizon
        :param password: (str) password for horizon
        :param command_logger: logging.Logger instance
        :return: None
        """
        address_data = re.search(
            r"(?P<host>[^:]*)"
            r":?(?P<port>[0-9]*?)"
            r"\?horizon=(?P<switch_name>.*)",
            address,
            re.IGNORECASE)

        host = address_data.group("host")
        port = address_data.group("port")
        port = int(port) if port else None

        self._session.connect(host, username, password, port, re_string=self._prompt)
        command = 'logon {} {}'.format(username, password)
        error_map = OrderedDict([
            ("[Aa]ccess [Dd]enied", "Invalid username/password for login"),
        ])
        error_map.update(self.GENERIC_ERRORS)
        self._session.send_command(command, re_string=self._prompt, error_map=error_map)
        self._switch_name = address_data.group("switch_name")

    def logout(self, command_logger):
        """Perform logout operation on the device

        :param command_logger: logging.Logger instance
        :return: None
        """
        command = 'logoff'
        error_map = OrderedDict([
            ("[Nn]o [Uu]ser", "User is not logged in"),
        ])
        error_map.update(self.GENERIC_ERRORS)
        self._session.send_command(command, re_string=self._prompt, error_map=error_map)

    @property
    def is_logical_port_mode(self):
        """Returns True if port is "logical" model, otherwise returns False"""
        return self._port_mode.lower() == "logical"

    def _disp_switch_info(self):
        """Execute display switch info command on the device

        :return: (str) output for switch info command from the device
        """
        command = "display information switch {}".format(self._switch_name)
        error_map = OrderedDict([
            ("[Nn]ot [Ff]ound", "Switch {} was not found".format(self._switch_name)),
        ])
        error_map.update(self.GENERIC_ERRORS)
        return self._session.send_command(command, re_string=self._prompt, error_map=error_map)

    def _disp_status(self):
        """Execute display status command on the device

        :return: (str) output for display status command from the device
        """
        command = "display status"
        return self._session.send_command(command, re_string=self._prompt, error_map=self.GENERIC_ERRORS)

    def _show_ports_info(self):
        """Execute show port info by switch command on the device

        :return: (str) output for show port info command from the device
        """
        command = "show port info * swi {}".format(self._switch_name)
        error_map = OrderedDict([
            ("[Nn]ot [Ff]ound", "Switch {} was not found".format(self._switch_name)),
        ])
        error_map.update(self.GENERIC_ERRORS)
        return self._session.send_command(command, re_string=self._prompt, error_map=error_map)

    def _show_connections(self):
        """Execute show connections by switch command on the device

        :return: (str) output for show connections command from the device
        """
        command = "show connection switch {}".format(self._switch_name)
        return self._session.send_command(command, re_string=self._prompt, error_map=self.GENERIC_ERRORS)

    def _get_port_mappings(self, command_logger):
        """Get mappings for all multi-cast/simplex/duplex port connections

        :param command_logger: logging.Logger instance
        :return: (dictionary) destination sub-port => source sub-port
        """
        connections = self._show_connections()
        mapping_info = {}

        if "connection not found" in connections.lower():
            return mapping_info

        connections_list = re.search(r".*-\n(.*)\n\n", connections, re.DOTALL).group(1).split('\n')
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
                command_logger.warning("Can't set mapping for unhandled connection type. "
                                       "Connection info: {}".format(conn_data))
        return mapping_info

    def get_resource_description(self, address, command_logger):
        """Auto-load function to retrieve all information from the device

        :param address: (str) address in the format <host>:<port>?Horizon=<switch_name> (port is optional)
        :param command_logger: logging.Logger instance
        :return: common.resource_info.ResourceInfo instance with all switch sub-resources (chassis, blades, ports)
        """
        depth = 0
        resource_info = ResourceInfo()
        resource_info.set_depth(depth)
        resource_info.set_address(address)

        device_info = self._disp_switch_info()

        info_match = re.search(
            r"PHYSICAL INFORMATION(?P<physical_info>.*)"
            r"SWITCH COMPONENTS(?P<switch_components>.*)",
            device_info, re.DOTALL)

        model_name = re.search(r"Switch Model:[ ]*(.*?)\n", info_match.group("physical_info"), re.DOTALL).group(1)
        resource_info.set_model_name(model_name)
        resource_info.set_index(model_name)
        ip_addr = re.search(r"IP Address:[ ]*(.*?)\n", info_match.group("physical_info"), re.DOTALL).group(1)
        resource_info.add_attribute("Switch Address", ip_addr)

        device_status = self._disp_status()
        soft_version = re.search(r"Version[ ]?(.*?)\n", device_status, re.DOTALL).group(1)
        resource_info.add_attribute("Software Version", soft_version)

        info_list = info_match.group("switch_components").split("\n")

        ports_info = self._show_ports_info()

        ports_list = re.search(r".*-\n(.*)\n\n", ports_info, re.DOTALL).group(1).split("\n")
        all_ports = {}

        port_mappings = self._get_port_mappings(command_logger)

        for port in ports_list:
            info = re.search(r"(?P<phys_addr>.*?)[ ]{2,}"
                             r"(?P<status>.*?)[ ]{2,}"
                             r"(?P<name>.*?)[ ]{2,}"
                             r".*?[ ]{2,}"  # Lock*/Rx Pwr(dBm)
                             r".*?[ ]{2,}"  # Tx Pwr(dBm)
                             r".*?[ ]{2,}"  # Rx Pwr(dBm)
                             r"(?P<speed>.*?)[ ]{2,}"
                             r"(?P<protocol>.*)", port)

            chassis, blade, port_no = info.group("phys_addr").split('.')
            chassis_ports = all_ports.setdefault(int(chassis), {})
            blade_ports = chassis_ports.setdefault(int(blade), [])
            blade_ports.append(info.groupdict())

        for info_str in info_list:
            if info_str.lower().startswith("chassis"):
                chassis_no = int(re.search(r"(\d+):", info_str).group(1))
                chassis_resource = ResourceInfo()
                chassis_resource.set_depth(depth + 1)
                chassis_resource.set_index(str(chassis_no))
                resource_info.add_child(info_str, chassis_resource)

            elif info_str.startswith(" " * 4):
                # add ports
                blade_info = re.search(
                    r"(?P<vendor>.*),(?P<model>.*),(?P<uboot_rev>.*),(?P<serial_number>.*)", info_str, re.DOTALL)

                # blade_resource.add_attribute("Vendor", blade_info.group("vendor"))
                # blade_resource.add_attribute("Uboot Rev.", blade_info.group("uboot_rev"))
                blade_resource.set_serial_number(blade_info.group("serial_number"))

                chassis_ports = all_ports.get(chassis_no, {})
                blade_ports = chassis_ports.get(blade_no, [])

                for port_data in blade_ports:
                    phys_addr = port_data["phys_addr"]
                    port_no = int(phys_addr.split(".")[-1])

                    if self.is_logical_port_mode:
                        port_resource = ResourceInfo()
                        port_resource.set_model_name(blade_type)
                        port_resource.set_depth(depth + 3)
                        port_resource.set_index(str(port_no))
                        port_resource.add_attribute("Protocol Type", 0)

                        connected_resource = self._get_connected_resource(phys_addr, port_mappings)
                        if connected_resource:
                            port_resource.set_mapping("{}/{}".format(address, connected_resource))

                        # if port_data["status"].lower() == "not connected":
                        #     port_resource.add_attribute("State", "Enable")
                        # else:
                        #     port_resource.add_attribute("State", "Disable")

                        blade_resource.add_child(port_no, port_resource)
                    else:
                        for subport in (self.TX_SUBPORT_INDEX, self.RX_SUBPORT_INDEX):
                            subport_idx = "{}-{}".format(port_no, subport)
                            subport_resource = ResourceInfo()
                            subport_resource.set_model_name(blade_type)
                            subport_resource.set_depth(depth + 3)
                            subport_resource.set_index(subport_idx)
                            subport_resource.add_attribute("Protocol Type", 0)
                            blade_resource.add_child(subport_idx, subport_resource)

                            if subport == self.RX_SUBPORT_INDEX:
                                connected_resource = self._get_connected_resource(phys_addr, port_mappings)
                                if connected_resource:
                                    subport_resource.set_mapping("{}/{}".format(address, connected_resource))

            elif info_str.startswith(" " * 2):
                # blade type is the last word in the sequence
                blade_type = info_str.rstrip().rsplit(' ')[-1]
                blade_no = int(re.search(r"(\d+)", info_str).group(1))

                blade_resource = ResourceInfo()
                blade_resource.set_model_name(blade_type)
                blade_resource.set_depth(depth + 2)
                blade_resource.set_index(str(blade_no))
                chassis_resource.add_child(info_str, blade_resource)

        return resource_info.convert_to_xml()

    def _get_connected_resource(self, phys_addr, port_mappings):
        """Get connected port to the given one if such connection exists

        :param phys_addr: (str) address of the port in format "<chassis>.<blade>.<port>"
        :param port_mappings: (dictionary) connection mappings between destination and source port
        :return: (str) resource address of the connected port or None
        """
        if phys_addr not in port_mappings:
            return None

        resource_addr = port_mappings[phys_addr]
        # remove leading zero from the address ("1.1.1" instead of "01.01.01")
        resource_addr = "/".join([str(int(part)) for part in resource_addr.split(".")])
        if not self.is_logical_port_mode:
            resource_addr = "{}-{}".format(resource_addr, self.TX_SUBPORT_INDEX)

        return resource_addr

    def _convert_port_names(self, src_port, dst_port):
        """Convert source and destination ports to the correct addresses

        Example:
            src ["192.168.29.10", "1", "1", "10"] => "01.01.10"
            dst ["192.168.29.10", "1", "2", "5"] => "01.02.05"

        :param src_port: (list) source port data
        :param dst_port: (list) destination port data
        :return: (list) converted src and dst port in format "<chassis>.<blade>.<port>"
        """
        return [
            '.'.join(map(lambda x: x.zfill(2), port[1:]))
            for port in (src_port, dst_port)]

    def _select_switch(self, command_logger):
        """Perform select switch operation on the device

        :param command_logger: logging.Logger instance
        :return: None
        """
        command = 'select switch {}'.format(self._switch_name)
        error_map = OrderedDict([
            ("[Nn]ot [Ff]ound", "Switch {} was not found".format(self._switch_name)),
        ])
        error_map.update(self.GENERIC_ERRORS)
        self._session.send_command(command, re_string=self._prompt, error_map=error_map)

    def _con_simplex(self, src_port, dst_port, command_logger):
        """Perform simplex connection between source and destination ports

        :param src_port: (str) source port in format "<chassis>.<blade>.<port>"
        :param dst_port: (str) destination port in format "<chassis>.<blade>.<port>"
        :param command_logger: logging.Logger instance
        :return: (str) output for the connect command from the device
        """
        command = "connect simplex prtnum {} to {} force".format(src_port, dst_port)
        error_map = OrderedDict([
            ("[Nn]ot [Ff]ound", "Subport was not found"),
        ])
        error_map.update(self.GENERIC_ERRORS)
        return self._session.send_command(command, re_string=self._prompt, error_map=error_map)

    def _con_duplex(self, src_port, dst_port, command_logger):
        """Perform duplex connection between source and destination ports

        :param src_port: (str) source port in format "<chassis>.<blade>.<port>"
        :param dst_port: (str) destination port in format "<chassis>.<blade>.<port>"
        :param command_logger: logging.Logger instance
        :return: (str) output for the connect command from the device
        """
        if not self.is_logical_port_mode:
            raise Exception("Bidirectional port mapping could be done only in logical port_mode "
                            "current mode: {}".format(self._port_mode))
        error_map = OrderedDict([
            ("[Nn]ot [Ff]ound", "Subport was not found"),
        ])
        error_map.update(self.GENERIC_ERRORS)
        command = "connect duplex prtnum {} to {} force".format(src_port, dst_port)
        return self._session.send_command(command, re_string=self._prompt, error_map=error_map)

    def _discon_simplex(self, src_port, dst_port, command_logger):
        """Perform disconnection of a simplex connection between source and destination ports

        :param src_port: (str) source port in format "<chassis>.<blade>.<port>"
        :param dst_port: (str) destination port in format "<chassis>.<blade>.<port>"
        :param command_logger: logging.Logger instance
        :return: (str) output for the disconnect command from the device
        """
        command = "disconnect simplex {} force".format(dst_port)
        error_map = OrderedDict([
            ("[Nn]ot [Ss]implex", "Subport is not simplex connected"),
        ])
        error_map.update(self.GENERIC_ERRORS)
        return self._session.send_command(command, re_string=self._prompt, error_map=error_map)

    def _discon_duplex(self, src_port, dst_port, command_logger):
        """Perform disconnection of a duplex connection between source and destination ports

        :param src_port: (str) source port in format "<chassis>.<blade>.<port>"
        :param dst_port: (str) destination port in format "<chassis>.<blade>.<port>"
        :param command_logger: logging.Logger instance
        :return: (str) output for the disconnect command from the device
        """
        command = "disconnect duplex prtnum {} force".format(dst_port)
        return self._session.send_command(command, re_string=self._prompt, error_map=self.GENERIC_ERRORS)

    def _discon_multi(self, src_port, dst_port, command_logger):
        """Perform disconnection of a multi-cast connection between source and destination ports

        :param src_port: (str) source port in format "<chassis>.<blade>.<port>"
        :param dst_port: (str) destination port in format "<chassis>.<blade>.<port>"
        :param command_logger: logging.Logger instance
        :return: (str) output for the disconnect command from the device
        """
        command = "disconnect multicast destination {} force".format(dst_port)
        return self._session.send_command(command, re_string=self._prompt, error_map=self.GENERIC_ERRORS)

    def _show_port_connection(self, port):
        """Perform show port connection command on the device

        :param port: (str) source/destination port in format "<chassis>.<blade>.<port>"
        :return: (str) output for the show port connection command
        """
        command = "show prtnum {}".format(port)
        error_map = OrderedDict([
            ("[Ii]ncorrect", "Incorrect port number format"),
            # ("[Nn]ot [Ff]ound", "Connection not found"),
        ])
        error_map.update(self.GENERIC_ERRORS)
        return self._session.send_command(command, re_string=self._prompt, error_map=error_map)

    def _validate_rx_subport(self, subport):
        """Validate if given sub-port is a correct receiver sub-port, return logical port part

        Example:
            sub-port "1.1.1-Rx" => port "1.1.1"
            sub-port "1.1.1-Tx" => raise Exception

        :param subport: (str) sub-port in format "<chassis>.<blade>.<port>-Rx"
        :return: (str) logical port part for the given sub-port
        """
        port, sub_idx = subport.split('-')
        if sub_idx.upper() != self.RX_SUBPORT_INDEX.upper():
            raise Exception("Transmitter sub-port can't be used as a destination")
        return port

    def _validate_tx_subport(self, subport):
        """Validate if given sub-port is a correct transceiver sub-port, return logical port part

        Example:
            sub-port "1.1.1-Tx" => port "1.1.1"
            sub-port "1.1.1-Rx" => raise Exception

        :param subport: (str) sub-port in format "<chassis>.<blade>.<port>-Tx"
        :return: (str) logical port part for the given sub-port
        """
        port, sub_idx = subport.split('-')
        if sub_idx.upper() != self.TX_SUBPORT_INDEX.upper():
            raise Exception("Receiver sub-port can't be used as a source")
        return port

    def map_bidi(self, src_port, dst_port, command_logger):
        """Create a bidirectional connection between source and destination ports

        :param src_port: (list) source port in format ["<address>", "<chassis>", "<blade>", "<port>"]
        :param dst_port: (list) destination port in format ["<address>", "<chassis>", "<blade>", "<port>"]
        :param command_logger: logging.Logger instance
        :return: None
        """
        src_port_name, dst_port_name = self._convert_port_names(src_port, dst_port)
        self._select_switch(command_logger=command_logger)
        self._con_duplex(src_port_name, dst_port_name, command_logger)

    def map_uni(self, src_port, dst_port, command_logger):
        """Create a unidirectional connection between source and destination ports

        :param src_port: (list) source port in format ["<address>", "<chassis>", "<blade>", "<port>"]
        :param dst_port: (list) destination port in format ["<address>", "<chassis>", "<blade>", "<port>"]
        :param command_logger: logging.Logger instance
        :return: None
        """
        if not self.is_logical_port_mode:
            src_port[-1] = self._validate_tx_subport(src_port[-1])
            dst_port[-1] = self._validate_rx_subport(dst_port[-1])

        src_port_name, dst_port_name = self._convert_port_names(src_port, dst_port)
        self._select_switch(command_logger=command_logger)
        self._con_simplex(src_port_name, dst_port_name, command_logger)

    def map_clear_to(self, src_port, dst_port, command_logger):
        """Remove simplex/multi-cast/duplex connection ending on the destination port

        :param src_port: (list) source port in format ["<address>", "<chassis>", "<blade>", "<port>"]
        :param dst_port: (list) destination port in format ["<address>", "<chassis>", "<blade>", "<port>"]
        :param command_logger: logging.Logger instance
        :return: None
        """
        if not self.is_logical_port_mode:
            src_port[-1] = self._validate_tx_subport(src_port[-1])
            dst_port[-1] = self._validate_rx_subport(dst_port[-1])

        src_port_name, dst_port_name = self._convert_port_names(src_port, dst_port)
        self._select_switch(command_logger=command_logger)
        conn_info = self._show_port_connection(dst_port_name)

        if "connection not found" in conn_info.lower():
            command_logger.warning("Trying to clear connection which doesn't exist for port {}".format(dst_port_name))
            return

        conn_info = re.search(r".*-\n(.*)\n\n", conn_info, re.DOTALL).group(1)
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

        disconn_type_map = {
            "simplex": self._discon_simplex,
            "duplex": self._discon_duplex,
            "mcast": self._discon_multi,
        }
        try:
            disconn_handler = disconn_type_map[conn_data.group("connection_type").lower()]
        except KeyError:
            command_logger.warning("Can't disconnect unhandled connection type. Connection info: {}".format(conn_info))
        else:
            # conn_info string output contains correct order for src/dst addresses
            disconn_handler(conn_data.group("src_addr"), conn_data.group("dst_addr"), command_logger)

    def map_clear(self, src_port, dst_port, command_logger):
        """Remove simplex/multi-cast/duplex connection ending on the destination port

        :param src_port: (list) source port in format ["<address>", "<chassis>", "<blade>", "<port>"]
        :param dst_port: (list) destination port in format ["<address>", "<chassis>", "<blade>", "<port>"]
        :param command_logger: logging.Logger instance
        :return: None
        """
        self.map_clear_to(src_port, dst_port, command_logger)

    def set_speed_manual(self, command_logger):
        """Set speed manual - skipped command

        :param command_logger: logging.Logger instance
        :return: None
        """
        command_logger.info("EXECUTE 'set_speed_manual' command")
