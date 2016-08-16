import unittest

from netscout import driver_handler
import mock


class TestNetscoutDriverHandler(unittest.TestCase):
    def setUp(self):
        super(TestNetscoutDriverHandler, self).setUp()
        self.src_port = "01.01.01"
        self.dst_port = "02.02.02"
        with mock.patch("netscout.driver_handler.DriverHandlerBase"):
            with mock.patch("netscout.driver_handler.ConfigurationParser"):
                self.tested_instance = driver_handler.NetscoutDriverHandler()
                self.tested_instance._session = mock.MagicMock()
                self.tested_instance._prompt = mock.MagicMock()

    def tearDown(self):
        super(TestNetscoutDriverHandler, self).tearDown()
        del self.tested_instance
        del self.src_port
        del self.dst_port

    def test_init(self):
        with mock.patch("netscout.driver_handler.DriverHandlerBase"):
            with mock.patch("netscout.driver_handler.ConfigurationParser") as conf_parser_class:
                port_mode = mock.MagicMock()
                conf_parser_class.get.return_value = port_mode
                tested_instance = driver_handler.NetscoutDriverHandler()
                conf_parser_class.get.assert_any_call("driver_variable", "port_mode")
                self.assertEquals(tested_instance._port_mode, port_mode)

    def test_convert_port_names(self):
        expected_src_port, expected_dst_port = "01.01.121", "01.10.01"
        src_port_name, dst_port_name = self.tested_instance._convert_port_names(
            src_port=["192.168.1.10", "1", "1", "121"],
            dst_port=["192.168.1.10", "1", "10", "1"])

        self.assertEquals(expected_src_port, src_port_name)
        self.assertEquals(expected_dst_port, dst_port_name)

    def test_select_switch(self):
        self.tested_instance._select_switch()
        self.tested_instance._session.send_command.assert_called_once_with(
            "select switch {}".format(self.tested_instance.switch_name), re_string="has been selected")

    def test_con_simplex(self):
        self.tested_instance._con_simplex(src_port=self.src_port, dst_port=self.dst_port)
        self.tested_instance._session.send_command.assert_called_once_with(
            "connect simplex prtnum {} to {} force".format(self.src_port, self.dst_port), re_string="successful")

    def test_con_duplex_for_logical_mode(self):
        self.tested_instance.is_logical_port_mode = True
        result = self.tested_instance._con_duplex(src_port=self.src_port, dst_port=self.dst_port)
        self.tested_instance._session.send_command.assert_called_once_with(
            "connect duplex prtnum {} to {} force".format(self.src_port, self.dst_port), re_string="successful")
        self.assertEquals(result, self.tested_instance._session.send_command())

    def test_con_duplex_raises_exception_for_physical_mode(self):
        self.tested_instance.is_logical_port_mode = False
        with self.assertRaises(Exception) as inst:
            self.tested_instance._con_duplex(src_port=self.src_port, dst_port=self.dst_port)
        self.assertEquals(str(inst.exception),
                          "Bidirectional port mapping could be done only in logical port_mode "
                          "current mode: {}".format(self.tested_instance._port_mode))

    def test_discon_simplex(self):
        result = self.tested_instance._discon_simplex(src_port=self.src_port, dst_port=self.dst_port)
        self.tested_instance._session.send_command.assert_called_once_with(
            "disconnect simplex {} force".format(self.dst_port), re_string="successful")
        self.assertEquals(result, self.tested_instance._session.send_command())

    def test_discon_duplex(self):
        result = self.tested_instance._discon_duplex(src_port=self.src_port, dst_port=self.dst_port)
        self.tested_instance._session.send_command.assert_called_once_with(
            "disconnect duplex prtnum {} force".format(self.dst_port), re_string="successful")
        self.assertEquals(result, self.tested_instance._session.send_command())

    def test_discon_multi(self):
        result = self.tested_instance._discon_multi(src_port=self.src_port, dst_port=self.dst_port)
        self.tested_instance._session.send_command.assert_called_once_with(
            "disconnect multicast destination {} force".format(self.dst_port), re_string="successful")
        self.assertEquals(result, self.tested_instance._session.send_command())

    def test_login(self):
        address, username, password = "address", "username", "password"
        self.tested_instance.login(address=address, username=username, password=password)
        self.tested_instance._session.connect.assert_called_once_with(address, username, password,
                                                                      re_string=self.tested_instance._prompt)
        self.tested_instance._session.send_command.assert_called_once_with("logon {} {}".format(username, password),
                                                                           re_string="is now logged on")

    def test_logout(self):
        self.tested_instance.logout()
        self.tested_instance._session.send_command.assert_called_once_with("logoff", re_string="is now logged off")

    def test_set_speed_manual(self):
        command_logger = mock.MagicMock()
        self.tested_instance.set_speed_manual(command_logger)
        command_logger.info.assert_called_once()

    def test_validate_tx_subport(self):
        port = self.tested_instance._validate_tx_subport("1.1.1-Tx")
        self.assertEquals(port, "1.1.1")

    def test_validate_tx_subport_raises_exception_for_incorrect_subport(self):
        with self.assertRaises(Exception) as inst:
            self.tested_instance._validate_tx_subport("1.1.1-Rx")
        self.assertEquals(str(inst.exception), "Receiver sub-port can't be used as a source")

    def test_validate_rx_subport(self):
        port = self.tested_instance._validate_rx_subport("1.1.1-Rx")
        self.assertEquals(port, "1.1.1")

    def test_validate_rx_subport_raises_exception_for_incorrect_subport(self):
        with self.assertRaises(Exception) as inst:
            self.tested_instance._validate_rx_subport("1.1.1-Tx")
        self.assertEquals(str(inst.exception), "Transmitter sub-port can't be used as a destination")

    def test_map_uni_with_logical_port_mode(self):
        logger = mock.MagicMock()
        converted_src_port = mock.MagicMock()
        converted_dst_port = mock.MagicMock()

        self.tested_instance.is_logical_port_mode = True
        self.tested_instance._select_switch = mock.MagicMock()
        self.tested_instance._con_simplex = mock.MagicMock()
        self.tested_instance._convert_port_names = mock.MagicMock(return_value=(converted_src_port, converted_dst_port))

        src_port_input = ['192.168.10.10', '1', '1', '1']
        dst_port_input = ['192.168.10.10', '1', '2', '2']
        self.tested_instance.map_uni(src_port=src_port_input, dst_port=dst_port_input, command_logger=logger)

        self.tested_instance._select_switch.assert_called_once_with(command_logger=logger)
        self.tested_instance._convert_port_names.assert_called_once_with(src_port_input, dst_port_input)
        self.tested_instance._con_simplex.assert_called_once_with(converted_src_port, converted_dst_port, logger)

    def test_map_uni_with_physical_port_mode(self):
        logger = mock.MagicMock()
        converted_src_port = mock.MagicMock()
        converted_dst_port = mock.MagicMock()
        converted_rx = mock.MagicMock()
        converted_tx = mock.MagicMock()

        self.tested_instance.is_logical_port_mode = False
        self.tested_instance._select_switch = mock.MagicMock()
        self.tested_instance._con_simplex = mock.MagicMock()
        self.tested_instance._validate_tx_subport = mock.MagicMock(return_value=converted_tx)
        self.tested_instance._validate_rx_subport = mock.MagicMock(return_value=converted_rx)
        self.tested_instance._convert_port_names = mock.MagicMock(return_value=(converted_src_port, converted_dst_port))

        src_port_input = ['192.168.10.10', '1', '1', '1-1']
        dst_port_input = ['192.168.10.10', '1', '2', '2-2']
        self.tested_instance.map_uni(src_port=src_port_input, dst_port=dst_port_input, command_logger=logger)

        self.tested_instance._validate_tx_subport.assert_called_once_with('1-1')
        self.tested_instance._validate_rx_subport.assert_called_once_with('2-2')
        self.assertEquals(src_port_input[-1], converted_tx)
        self.assertEquals(dst_port_input[-1], converted_rx)
        self.tested_instance._convert_port_names.assert_called_once_with(src_port_input, dst_port_input)
        self.tested_instance._select_switch.assert_called_once_with(command_logger=logger)
        self.tested_instance._con_simplex.assert_called_once_with(converted_src_port, converted_dst_port, logger)

    def test_map_bidi_with_logical_port_mode(self):
        self.tested_instance.is_logical_port_mode = True
        converted_src_port = mock.MagicMock()
        converted_dst_port = mock.MagicMock()
        logger = mock.MagicMock()
        self.tested_instance._select_switch = mock.MagicMock()
        self.tested_instance._con_duplex = mock.MagicMock()
        self.tested_instance._convert_port_names = mock.MagicMock(return_value=(converted_src_port, converted_dst_port))

        src_port_input = ['192.168.10.10', '1', '1', '1']
        dst_port_input = ['192.168.10.10', '1', '2', '2']
        self.tested_instance.map_bidi(src_port=src_port_input, dst_port=dst_port_input, command_logger=logger)

        self.tested_instance._convert_port_names.assert_called_once_with(src_port_input, dst_port_input)
        self.tested_instance._select_switch.assert_called_once_with(command_logger=logger)
        self.tested_instance._con_duplex.assert_called_once_with(converted_src_port, converted_dst_port, logger)

    def test_map_bidi_with_physical_port_mode(self):
        self.tested_instance.is_logical_port_mode = False
        converted_src_port = mock.MagicMock()
        converted_dst_port = mock.MagicMock()
        logger = mock.MagicMock()
        self.tested_instance._select_switch = mock.MagicMock()
        self.tested_instance._con_duplex = mock.MagicMock()
        self.tested_instance._convert_port_names = mock.MagicMock(return_value=(converted_src_port, converted_dst_port))

        src_port_input = ['192.168.10.10', '1', '1', '1-1']
        dst_port_input = ['192.168.10.10', '1', '2', '2-2']
        self.tested_instance.map_bidi(src_port=src_port_input, dst_port=dst_port_input, command_logger=logger)

        self.tested_instance._convert_port_names.assert_called_once_with(src_port_input, dst_port_input)
        self.tested_instance._select_switch.assert_called_once_with(command_logger=logger)
        self.tested_instance._con_duplex.assert_called_once_with(converted_src_port, converted_dst_port, logger)

    def _test_map_clear_by_connection_type(self, regex_found_connection_type,
                                           regexp_found_src, regexp_found_dst, logger):
        src_port_input = mock.MagicMock()
        dst_port_input = mock.MagicMock()
        converted_src_port = mock.MagicMock()
        converted_dst_port = mock.MagicMock()
        self.tested_instance.is_logical_port_mode = True
        self.tested_instance._select_switch = mock.MagicMock()
        self.tested_instance._convert_port_names = mock.MagicMock(return_value=(converted_src_port, converted_dst_port))
        self.tested_instance._show_port_connection = mock.MagicMock()
        port_info_re_match = mock.MagicMock()
        port_info_re_match.group.side_effect = [regex_found_connection_type, regexp_found_src, regexp_found_dst]

        with mock.patch("re.search", side_effect=[mock.MagicMock(), port_info_re_match]):
            self.tested_instance.map_clear_to(src_port=src_port_input, dst_port=dst_port_input, command_logger=logger)

    def test_map_clear_to_simplex_connection_type(self):
        logger = mock.MagicMock()
        regex_found_connection_type = "Simplex"
        regexp_found_src = "test_source"
        regexp_found_dst = "test_destination"
        self.tested_instance._discon_simplex = mock.MagicMock()

        self._test_map_clear_by_connection_type(regex_found_connection_type, regexp_found_src, regexp_found_dst, logger)
        self.tested_instance._discon_simplex.assert_called_once_with(regexp_found_src, regexp_found_dst, logger)

    def test_map_clear_to_duplex_connection_type(self):
        logger = mock.MagicMock()
        regex_found_connection_type = "Duplex"
        regexp_found_src = "test_source"
        regexp_found_dst = "test_destination"
        self.tested_instance._discon_duplex = mock.MagicMock()

        self._test_map_clear_by_connection_type(regex_found_connection_type, regexp_found_src, regexp_found_dst, logger)
        self.tested_instance._discon_duplex.assert_called_once_with(regexp_found_src, regexp_found_dst, logger)

    def test_map_clear_to_multicast_connection_type(self):
        logger = mock.MagicMock()
        regex_found_connection_type = "MCast"
        regexp_found_src = "test_source"
        regexp_found_dst = "test_destination"
        self.tested_instance._discon_multi = mock.MagicMock()

        self._test_map_clear_by_connection_type(regex_found_connection_type, regexp_found_src, regexp_found_dst, logger)
        self.tested_instance._discon_multi.assert_called_once_with(regexp_found_src, regexp_found_dst, logger)

    def test_map_clear_to_unhandled_connection_type(self):
        logger = mock.MagicMock()
        regex_found_connection_type = "UNHANDLED CONNECTION TYPE"
        regexp_found_src = "test_source"
        regexp_found_dst = "test_destination"
        self.tested_instance._discon_simplex = mock.MagicMock()
        self.tested_instance._discon_duplex = mock.MagicMock()
        self.tested_instance._discon_multi = mock.MagicMock()

        self._test_map_clear_by_connection_type(regex_found_connection_type, regexp_found_src, regexp_found_dst, logger)

        logger.warning.assert_called_once()
        self.tested_instance._discon_multi.assert_not_called()
        self.tested_instance._discon_duplex.assert_not_called()
        self.tested_instance._discon_multi.assert_not_called()

    def test_map_clear(self):
        logger = mock.MagicMock()
        src_port_input = mock.MagicMock()
        dst_port_input = mock.MagicMock()
        self.tested_instance.map_clear_to = mock.MagicMock()

        result = self.tested_instance.map_clear(src_port=src_port_input, dst_port=dst_port_input, command_logger=logger)

        self.tested_instance.map_clear_to.assert_called_once_with(src_port_input, dst_port_input, logger)
        self.assertEquals(result, self.tested_instance.map_clear_to())

    @mock.patch('netscout.driver_handler.ResourceInfo')
    def test_get_resource_description(self, resource_info_class):
        resource_info = mock.MagicMock()
        resource_info_class.return_value = resource_info
        self.tested_instance._disp_switch_info = mock.MagicMock()
        self.tested_instance._disp_status = mock.MagicMock()
        self.tested_instance._show_ports_info = mock.MagicMock()

        with mock.patch("re.search"):
            result = self.tested_instance.get_resource_description('test_address')

        self.tested_instance._disp_switch_info.assert_called_once()
        self.tested_instance._disp_status.assert_called_once()
        self.tested_instance._show_ports_info.assert_called_once()
        resource_info.convert_to_xml.assert_called_once()
        self.assertEquals(result, resource_info.convert_to_xml())
