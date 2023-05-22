from __future__ import annotations

import re


def parse_table(
    parsable_str: str,
    header_column_names: list[str],
    header_border_separator: str = "-",
    separator: str = "  ",
) -> list[dict]:
    """Parse formatted table.

    :param parsable_str: list of column names
    :type parsable_str: str
    :param header_column_names: list of column names
    :type header_column_names: list
    :param header_border_separator:
    :type header_border_separator: str
    :param separator: column separator
    :type separator: str

    Example:
    GEO addr  Name (>20 ..)            Rx Pwr(dBm)  Conn Type  GEO addr  Name (>20 ..)            Rx Pwr(dBm)  Speed    Protocol

    --------  -----------------------  -----------  ---------  --------  -----------------------  -----------  -------  --------

    01.01.09  02 01.01.03-1 - 10G  ..  Not Present  Duplex     01.01.11  02 01.01.03-3 - 10G  ..  Not Present  10000    Ethernet
    01.05.23  03 01.05.23              -2.800889    Duplex     01.03.05  03 01.03.05 - 10G To ..  Not Present  10000    Ethernet

    """  # noqa: E501
    res = []
    match = re.search(
        r"(?P<header_border>({hbs}{{2,}}({sep})*)+)\s+(?P<info>.*)".format(
            hbs=header_border_separator, sep=separator
        ),
        parsable_str,
        re.DOTALL,
    )
    if match:
        border_list = list(map(len, match.group("header_border").strip().split()))

        if len(border_list) != len(header_column_names):
            raise Exception("Parsing table error")

        for line in match.group("info").splitlines():
            line = line.strip()
            if not line:
                continue
            data = {}
            for i, name in enumerate(header_column_names):
                info_len = border_list[i]

                temp = line[:info_len].strip()
                while len(line) > info_len and line[info_len] != " ":
                    temp += line[info_len]
                    info_len += 1

                data.update({name: temp})
                line = line[info_len + len(separator) :]

            if data:
                res.append(data)

    return res
