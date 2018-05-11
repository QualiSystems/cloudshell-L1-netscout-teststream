#!/usr/bin/python
# -*- coding: utf-8 -*-
from cloudshell.cli.command_mode_helper import CommandModeHelper
from netscout_teststream.cli.l1_cli_handler import L1CliHandler
from netscout_teststream.cli.netscout_command_modes import DefaultCommandMode


class NetscoutCliHandler(L1CliHandler):
    def __init__(self, logger):
        super(NetscoutCliHandler, self).__init__(logger)
        self.modes = CommandModeHelper.create_command_mode()

    @property
    def _default_mode(self):
        return self.modes[DefaultCommandMode]

    def default_mode_service(self):
        """
        Default mode session
        :return:
        :rtype: cloudshell.cli.cli_service.CliService
        """
        return self.get_cli_service(self._default_mode)
