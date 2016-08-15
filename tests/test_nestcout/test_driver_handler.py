import unittest

from netscout import driver_handler
import mock


class TestNetscoutDriverHandler(unittest.TestCase):
    def setUp(self):
        super(TestNetscoutDriverHandler, self).setUp()
        self.src_port = "01.01.01"
        self.dst_port = "02.02.02"
        with mock.patch('netscout.driver_handler.DriverHandlerBase'):
            with mock.patch('netscout.driver_handler.ConfigurationParser'):
                self.tested_instance = driver_handler.NetscoutDriverHandler()
                self.tested_instance._session = mock.MagicMock()
                self.tested_instance._prompt = mock.MagicMock()

    def tearDown(self):
        super(TestNetscoutDriverHandler, self).tearDown()
        del self.tested_instance

    def test_init(self):
        with mock.patch('netscout.driver_handler.DriverHandlerBase'):
            with mock.patch('netscout.driver_handler.ConfigurationParser') as conf_parser_class:
                driver_handler.NetscoutDriverHandler()
                conf_parser_class.get.assert_any_call("common_variable", "force_duplex")
                conf_parser_class.get.assert_any_call("common_variable", "connection_mode")
                conf_parser_class.get.assert_any_call("common_variable", "standalone_tap")
                conf_parser_class.get.assert_any_call("common_variable", "switch_name")

    def test_convert_port_names(self):
        expected_src_port, expected_dst_port = "01.01.121", "01.10.01"
        src_port_name, dst_port_name = self.tested_instance._convert_port_names(
            src_port=["192.168.1.10", "1", "1", "121"],
            dst_port=["192.168.1.10", "1", "10", "1"])

        self.assertEquals(expected_src_port, src_port_name)
        self.assertEquals(expected_dst_port, dst_port_name)

    def test_select_switch(self):
        self.tested_instance._select_switch()
        self.tested_instance._session.send_command(
            'select switch {}'.format(self.tested_instance.switch_name), re_string='has been selected')

    def test_con_simplex(self):
        self.tested_instance._con_simplex(src_port=self.src_port, dst_port=self.dst_port)
        self.tested_instance._session.send_command.assert_called_once_with(
            "connect simplex prtnum {} to {} force".format(self.src_port, self.dst_port), re_string="successful")

    def test_con_duplex(self):
        self.tested_instance._con_duplex(src_port=self.src_port, dst_port=self.dst_port)
        self.tested_instance._session.send_command.assert_called_once_with(
            "connect duplex prtnum {} to {} force".format(self.src_port, self.dst_port), re_string="successful")

    def test_con_multicast(self):
        self.tested_instance._con_multicast(src_port=self.src_port, dst_port=self.dst_port)
        self.tested_instance._session.send_command.assert_called_once_with(
            "connect multicast prtnum {} to {} force".format(self.src_port, self.dst_port), re_string="successful")

    def test_discon_simplex(self):
        self.tested_instance._discon_simplex(src_port=self.src_port, dst_port=self.dst_port)
        self.tested_instance._session.send_command.assert_called_once_with(
            "disconnect simplex {} force".format(self.dst_port), re_string="successful")

    def test_discon_duplex(self):
        self.tested_instance._discon_duplex(src_port=self.src_port, dst_port=self.dst_port)
        self.tested_instance._session.send_command.assert_called_once_with(
            "disconnect duplex prtnum {} force".format(self.src_port), re_string="successful")

    def test_discon_multicast(self):
        self.tested_instance._discon_multicast(src_port=self.src_port, dst_port=self.dst_port)
        self.tested_instance._session.send_command.assert_called_once_with(
            "disconnect multicast destination prtnum {} force".format(self.dst_port), re_string="successful")

    def test_login(self):
        address, username, password = "address", "username", "password"
        self.tested_instance.login(address=address, username=username, password=password)
        self.tested_instance._session.connect.assert_called_once_with(address, username, password,
                                                                      re_string=self.tested_instance._prompt)
        self.tested_instance._session.send_command.assert_called_once_with('logon {} {}'.format(username, password),
                                                                           re_string='is now logged on')

    def test_logout(self):
        self.tested_instance.logout()
        self.tested_instance._session.send_command.assert_called_once_with('logoff', re_string='is now logged off')

    def test_set_speed_manual(self):
        command_logger = mock.MagicMock()
        self.tested_instance.set_speed_manual(command_logger)
        command_logger.info.assert_called_once()

#     def test_get_resource_description(self):
#         disp_switch_info_out = """
#         INFORMATION ON OS-192:
#
# *** PHYSICAL INFORMATION ***
# Switch Model: OS-192
# IP Address:   10.88.37.103
#
#
# *** SWITCH COMPONENTS ***
# Chassis Controller 1:
#
#   PIM: 01  O-Blade
#     Netscout,N-OST-192x192-LU1-DSHNV-017,002020,6.3.3.16
#   PIM: 02  O-Blade
#     Netscout,N-OST-192x192-LU1-DSHNV-017,002020,6.3.3.16
# """
#         disp_status_out = """OnPATH Universal Connectivity Server Version 02.05.01.15
# Port Alarm Count:    0
# System Alarm Count:  10
#
# """
#         show_ports_info_out = """
#
# Port summary for switch OS-192:
#
# Phys Addr  Status         Name                     Lock*  Tx Pwr(dBm)  Rx Pwr(dBm)  Speed    Protocol
# ---------  -------------  -----------------------  -----  -----------  -----------  -------  ---------
# 01.01.01   Not Connected  OS-192 01.01.01                 N/A          N/A          Unknown  Unknown
# 01.01.02   Not Connected  OS-192 01.01.02                 N/A          N/A          Unknown  Unknown
# 01.01.03   Not Connected  OS-192 01.01.03                 N/A          N/A          Unknown  Unknown
# 01.01.04   Not Connected  OS-192 01.01.04                 N/A          N/A          Unknown  Unknown
# 01.01.05   Not Connected  OS-192 01.01.05                 N/A          N/A          Unknown  Unknown
# 02.01.01   Not Connected  OS-192 02.01.01                 N/A          N/A          Unknown  Unknown
# 02.02.01   Not Connected  OS-192 02.02.01                 N/A          N/A          Unknown  Unknown
# 03.01.01   Not Connected  OS-192 03.01.01                 N/A          N/A          Unknown  Unknown
#
# """
#         self.tested_instance._disp_switch_info = mock.MagicMock(return_value=disp_switch_info_out)
#         self.tested_instance._disp_status = mock.MagicMock(return_value=disp_status_out)
#         self.tested_instance._show_ports_info = mock.MagicMock(return_value=show_ports_info_out)
#         self.tested_instance.get_resource_description(address="10.88.37.103")

    # def test_map_bidi(self):
    #     command_logger = mock.MagicMock()
    #     self.tested_instance.map_bidi(src_port=[], dst_port=[], command_logger=command_logger)
    #     self.tested_instance.
    #     self.tested_instance._select_switch.assert_called_once()
    #
    # def test_map_uni(self):
    #     pass
    #
    # def test_map_clear_to(self):
    #     pass
    #
    # def test_map_clear(self):
    #     pass
    #
