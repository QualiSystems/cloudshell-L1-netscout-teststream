from __future__ import annotations

import re

from cloudshell.cli.command_template.command_template_executor import (
    CommandTemplateExecutor,
)
from cloudshell.cli.service.cli_service import CliService

import netscout_teststream.command_templates.system as command_template


class SystemActions:
    """Autoload actions."""

    def __init__(self, switch_name: str, cli_service: CliService):
        self._switch_name = switch_name
        self._cli_service = cli_service

    def available_switches(self) -> list[str]:
        """Get available switches."""
        output = CommandTemplateExecutor(
            self._cli_service, command_template.SHOW_SWITCHES
        ).execute_command()
        switches_match = re.search(
            r"available\s+switches:(.*)", output, flags=re.IGNORECASE | re.DOTALL
        )
        return switches_match.group(1).strip().splitlines()

    def software_version(self) -> str:
        """Get software version."""
        output = CommandTemplateExecutor(
            self._cli_service, command_template.SHOW_STATUS
        ).execute_command()
        match = re.search(r"Version[ ]?(.*?)\n", output, re.DOTALL)
        if match:
            return match.group(1)
        else:
            raise Exception("Can not determine Software Version.")
