import re

from common.configuration_parser import ConfigurationParser
from common.driver_handler_base import DriverHandlerBase
from common.resource_info import ResourceInfo


class NetscoutDriverHandler(DriverHandlerBase):
    def __init__(self):
        DriverHandlerBase.__init__(self)
        self.force_duplex = ConfigurationParser.get("common_variable", "force_duplex")
        self.connection_mode = ConfigurationParser.get("common_variable", "connection_mode")
        self.standalone_tap = ConfigurationParser.get("common_variable", "standalone_tap")
        self.switch_name = ConfigurationParser.get("common_variable", "switch_name")

    def login(self, address, username, password, command_logger=None):
        self._session.connect(address, username, password, re_string=self._prompt)
        command = 'logon {} {}'.format(username, password)
        self._session.send_command(command, re_string='is now logged on')

    def logout(self, command_logger=None):
        command = 'logoff'
        self._session.send_command(command, re_string='is now logged off')

    def _select_switch(self, command_logger=None):
        command = 'select switch {}'.format(self.switch_name)
        self._session.send_command(command, re_string='has been selected')

    def _get_device_data(self):
        pass

    def get_resource_description(self, address, command_logger=None):
        # todo: handle incoming MAP
        depth = 0
        resource_info = ResourceInfo()
        resource_info.set_depth(depth)
        resource_info.set_address(address)

        command = "display information switch {}".format(self.switch_name)
        device_info = self._session.send_command(command, re_string=self._prompt)

        info_match = re.search(
            r"PHYSICAL INFORMATION(?P<physical_info>.*)"
            r"SWITCH COMPONENTS(?P<switch_components>.*)",
            device_info, re.DOTALL)

        model_name = re.search(r"Switch Model:[ ]*(.*?)\n", info_match.group("physical_info"), re.DOTALL).group(1)
        resource_info.set_model_name(model_name)
        resource_info.set_index(model_name)
        ip_addr = re.search(r"IP Address:[ ]*(.*?)\n", info_match.group("physical_info"), re.DOTALL).group(1)
        resource_info.add_attribute("Switch Address", ip_addr)

        command = "display status".format(self.switch_name)
        device_status = self._session.send_command(command, re_string=self._prompt)
        soft_version = re.search(r"Version[ ]?(.*?)\n", device_status, re.DOTALL).group(1)
        resource_info.add_attribute("Software Version", soft_version)

        info_list = info_match.group("switch_components").split("\n")

        command = "show port info * swi {}".format(self.switch_name)
        ports_info = self._session.send_command(command, re_string=self._prompt)

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
                    port_resource = ResourceInfo()
                    port_resource.set_model_name(blade_type)
                    port_resource.set_depth(depth + 3)
                    port_resource.set_index(str(port_no))
                    port_resource.add_attribute("Protocol Type", 0)

                    # if port_data["status"].lower() == "not connected":
                    #     port_resource.add_attribute("State", "Enable")
                    # else:
                    #     port_resource.add_attribute("State", "Disable")
                    blade_resource.add_child(port_no, port_resource)

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

    def _map_bidi_duplex(self, src_port, dst_port):
        command = "connect duplex prtn {} to {} force".format(src_port, dst_port)
        return self._session.send_command(command, re_string="successful")

    def _map_bidi_multicast(self, src_port, dst_port, command_logger):
        command = "con multi {} to {} for"
        src_cmd = command.format(src_port, dst_port)
        dst_cmd = command.format(dst_port, src_port)

        for cmd in (src_cmd, dst_cmd):
            self._session.send_command(cmd, re_string=self._prompt)

    def _convert_port_names(self, src_port, dst_port):
        return [
            '.'.join(map(lambda x: x.zfill(2), port[1:]))
            for port in (src_port, dst_port)]

    def map_bidi(self, src_port, dst_port, command_logger):
        self._select_switch(command_logger=command_logger)
        src_port_name, dst_port_name = self._convert_port_names(src_port, dst_port)

        if self.force_duplex or self.connection_mode == "DUPLEX_TAP":
            self._map_bidi_duplex(src_port_name, dst_port_name)

        elif self.connection_mode == "MULTICAST":
            self._map_bidi_multicast(src_port_name, dst_port_name)

    def map_clear_to(self, src_port, dst_port, command_logger):
        pass

    def map_clear(self, src_port, dst_port, command_logger):
        pass

    def map_uni(self, src_port, dst_port, command_logger):
        pass

    def set_speed_manual(self, command_logger):
        command_logger.info("EXECUTE 'set_speed_manual' command")
