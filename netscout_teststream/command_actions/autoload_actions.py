from __future__ import annotations

import re
from collections import defaultdict

from cloudshell.cli.command_template.command_template_executor import (
    CommandTemplateExecutor,
)
from cloudshell.cli.service.cli_service import CliService
from cloudshell.layer_one.core.helper.logger import get_l1_logger

import netscout_teststream.command_actions.actions_helper as helper
import netscout_teststream.command_templates.autoload as command_template

logger = get_l1_logger(name=__name__)


class PortInfoDTO:
    def __init__(self, name: str, address: str, protocol_id: str):
        self.name = name
        self.address = address
        self.protocol_id = protocol_id


class AutoloadActions:
    """Autoload actions."""

    SW_INFORM = "sw_inform"
    SW_COMPONENTS = "sw_components"

    def __init__(self, switch_name: str, cli_service: CliService):
        self._switch_name = switch_name
        self._cli_service = cli_service
        self.__switch_info_table = {}

    @property
    def _switch_info_table(self) -> dict:
        if not self.__switch_info_table:
            output = CommandTemplateExecutor(
                self._cli_service, command_template.SHOW_SWITCH_INFO, remove_prompt=True
            ).execute_command(switch_name=self._switch_name)
            info_match = re.search(
                r"\s*\*+\s+PHYSICAL\sINFORMATION\s\*+\s*(?P<physical_info>.*)"
                r"\s*\*+\s+SWITCH\sCOMPONENTS\s\*+\s*(?P<switch_components>.*)",
                output,
                re.DOTALL,
            )

            self.__switch_info_table[self.SW_INFORM] = info_match.group("physical_info")
            self.__switch_info_table[self.SW_COMPONENTS] = info_match.group(
                "switch_components"
            )
        return self.__switch_info_table

    def switch_model_name(self) -> str:
        return re.search(
            r"Switch Model:[ ]*(.*?)\n",
            self._switch_info_table[self.SW_INFORM],
            re.DOTALL,
        ).group(1)

    def switch_ip_addr(self) -> str:
        return re.search(
            r"IP Address:[ ]*(.*?)\n",
            self._switch_info_table[self.SW_INFORM],
            re.DOTALL,
        ).group(1)

    def chassis_table(self) -> dict:
        controller_ids = re.findall(
            r"chassis\scontroller\s(\d+):",
            self._switch_info_table[self.SW_COMPONENTS],
            flags=re.IGNORECASE | re.DOTALL,
        )

        controller_table_match = re.search(
            r"chassis\scontroller\s\d+:\s*(.*)" * len(controller_ids),
            self._switch_info_table[self.SW_COMPONENTS],
            flags=re.IGNORECASE | re.DOTALL,
        )
        chassis_table = {}
        for index in range(len(controller_ids)):
            controller_id = int(controller_ids[index])
            chassis_table[controller_id] = self._parse_blade_data(
                controller_table_match.group(index + 1)
            )
        return chassis_table

    def _parse_blade_data(self, blades_data: str) -> dict:
        blade_dict = {}
        for line in blades_data.splitlines():
            match = re.match(r"^\s*pim:\s+(\d+)\s+(.+)\s*$", line, re.IGNORECASE)
            if match:
                blade_id = match.group(1).strip()
                blade_type = match.group(2).strip()
                blade_dict[int(blade_id)] = blade_type
        return blade_dict

    def port_table(self) -> dict:
        output = CommandTemplateExecutor(
            self._cli_service, command_template.SHOW_PORTS_RAW, remove_prompt=True
        ).execute_command(switch_name=self._switch_name)
        port_table = {}
        for line in output.strip().splitlines():
            (
                address,
                protocol_id,
                port_mode,
                connected,
                connected_dir,
                subport_tx,
                subport_rx,
                alarm,
                name,
            ) = line.strip().split(",")
            if int(port_mode) != 16:
                port_table[address] = PortInfoDTO(name.strip("'"), address, protocol_id)
        return port_table

    def mapping_table(self) -> dict:
        """Get mappings for all multi-cast/simplex/duplex port connections."""
        output = CommandTemplateExecutor(
            self._cli_service, command_template.SHOW_CONNECTIONS, remove_prompt=True
        ).execute_command(switch_name=self._switch_name)
        mapping_info = defaultdict(list)

        if "connection not found" in output.lower():
            return mapping_info

        connections_data = helper.parse_table(
            parsable_str=output,
            header_column_names=[
                "src_addr",
                "src_name",
                "src_rx",
                "connection_type",
                "dst_addr",
                "dst_name",
                "dst_rx",
                "speed",
                "protocol",
            ],
        )

        for conn_info in connections_data:
            conn_type = conn_info.get("connection_type").lower()
            src = conn_info.get("src_addr")
            dst = conn_info.get("dst_addr")

            if conn_type in ("simplex", "mcast", "unknown"):
                mapping_info[src].append(dst)
            elif conn_type == "duplex":
                mapping_info[src].append(dst)
                mapping_info[dst].append(src)
            else:
                logger.warning(
                    f"Can't set mapping for unhandled connection type."
                    f"Connection info: {conn_info}"
                )

        return mapping_info
