import re

from common.configuration_parser import ConfigurationParser
from common.driver_handler_base import DriverHandlerBase
from common.resource_info import ResourceInfo


class NetscoutDriverHandler(DriverHandlerBase):
    TX_SUBPORT_INDEX = 'TX'
    RX_SUBPORT_INDEX = 'RX'

    def __init__(self):
        DriverHandlerBase.__init__(self)
        self._port_mode = ConfigurationParser.get("driver_variable", "port_mode")

        # todo(A.Piddubny): find where to get it
        self.switch_name = "OS-192"

    def login(self, address, username, password, command_logger=None):
        self._session.connect(address, username, password, re_string=self._prompt)
        command = 'logon {} {}'.format(username, password)
        self._session.send_command(command, re_string='is now logged on')

    def logout(self, command_logger=None):
        command = 'logoff'
        self._session.send_command(command, re_string='is now logged off')

    @property
    def is_logical_port_mode(self):
        return self._port_mode.lower() == "logical"

    def _disp_switch_info(self, switch_name):
        command = "display information switch {}".format(switch_name)
        return self._session.send_command(command, re_string=self._prompt)

    def _disp_status(self):
        command = "display status"
        return self._session.send_command(command, re_string=self._prompt)

    def _show_ports_info(self, switch_name):
        command = "show port info * swi {}".format(switch_name)
        return self._session.send_command(command, re_string=self._prompt)

    def get_resource_description(self, address, command_logger=None):
        # todo(A.Piddubny): handle incoming MAP
        depth = 0
        resource_info = ResourceInfo()
        resource_info.set_depth(depth)
        resource_info.set_address(address)

        device_info = self._disp_switch_info(self.switch_name)

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

        ports_info = self._show_ports_info(self.switch_name)

        ports_list = re.search(r".*-\n(.*)\n\n", ports_info, re.DOTALL).group(1).split("\n")
        all_ports = {}

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
                    port_no = int(port_data["phys_addr"].split(".")[-1])

                    if self.is_logical_port_mode:
                        port_resource = ResourceInfo()
                        port_resource.set_model_name(blade_type)
                        port_resource.set_depth(depth + 3)
                        port_resource.set_index(str(port_no))
                        port_resource.add_attribute("Protocol Type", 0)

                        # todo(A.Piddubny): will not show simplex connections ! use separate command for this
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

    def _convert_port_names(self, src_port, dst_port):
        return [
            '.'.join(map(lambda x: x.zfill(2), port[1:]))
            for port in (src_port, dst_port)]

    def _select_switch(self, command_logger=None):
        command = 'select switch {}'.format(self.switch_name)
        self._session.send_command(command, re_string='has been selected')

    def _con_simplex(self, src_port, dst_port, command_logger=None):
        command = "connect simplex prtnum {} to {} force".format(src_port, dst_port)
        return self._session.send_command(command, re_string="successful")

    def _con_duplex(self, src_port, dst_port, command_logger=None):
        if not self.is_logical_port_mode:
            raise Exception("Bidirectional port mapping could be done only in logical port_mode "
                            "current mode: {}".format(self._port_mode))

        command = "connect duplex prtnum {} to {} force".format(src_port, dst_port)
        return self._session.send_command(command, re_string="successful")

    def _discon_simplex(self, src_port, dst_port, command_logger=None):
        command = "disconnect simplex {} force".format(dst_port)
        return self._session.send_command(command, re_string="successful")

    def _discon_duplex(self, src_port, dst_port, command_logger=None):
        command = "disconnect duplex prtnum {} force".format(dst_port)
        return self._session.send_command(command, re_string="successful")

    def _discon_multi(self, src_port, dst_port, command_logger=None):
        command = "disconnect multicast destination {} force".format(dst_port)
        return self._session.send_command(command, re_string="successful")

    def _show_port_connection(self, port):
        command = "show prtnum {}".format(port)
        return self._session.send_command(command, re_string=self._prompt)

    def _validate_rx_subport(self, subport):
        port, sub_idx = subport.split('-')
        if sub_idx.upper() != self.RX_SUBPORT_INDEX.upper():
            raise Exception("Transmitter sub-port can't be used as a destination")
        return port

    def _validate_tx_subport(self, subport):
        port, sub_idx = subport.split('-')
        if sub_idx.upper() != self.TX_SUBPORT_INDEX.upper():
            raise Exception("Receiver sub-port can't be used as a source")
        return port

    def map_bidi(self, src_port, dst_port, command_logger):
        src_port_name, dst_port_name = self._convert_port_names(src_port, dst_port)
        self._select_switch(command_logger=command_logger)
        self._con_duplex(src_port_name, dst_port_name, command_logger)

    def map_uni(self, src_port, dst_port, command_logger):
        if not self.is_logical_port_mode:
            src_port[-1] = self._validate_tx_subport(src_port[-1])
            dst_port[-1] = self._validate_rx_subport(dst_port[-1])

        src_port_name, dst_port_name = self._convert_port_names(src_port, dst_port)
        self._select_switch(command_logger=command_logger)
        self._con_simplex(src_port_name, dst_port_name, command_logger)

    def map_clear_to(self, src_port, dst_port, command_logger):
        if not self.is_logical_port_mode:
            src_port[-1] = self._validate_tx_subport(src_port[-1])
            dst_port[-1] = self._validate_rx_subport(dst_port[-1])

        src_port_name, dst_port_name = self._convert_port_names(src_port, dst_port)
        self._select_switch(command_logger=command_logger)
        conn_info = self._show_port_connection(dst_port_name)
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
        return self.map_clear_to(src_port, dst_port, command_logger)

    def set_speed_manual(self, command_logger):
        command_logger.info("EXECUTE 'set_speed_manual' command")
