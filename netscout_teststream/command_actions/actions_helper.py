import re


def parse_table(
        parsable_str,
        header_column_names,
        header_border_separator="-",
        separator="  ",
):
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

    """
    res = []
    match = re.search(
        r"(?P<header_border>({hbs}{{2,}}({sep})*)+)\s+(?P<info>.*)".format(
            hbs=header_border_separator,
            sep=separator
        ),
        parsable_str,
        re.DOTALL
    )
    if match:
        border_list = map(len, match.group("header_border").strip().split())

        if len(border_list) != len(header_column_names):
            raise Exception("Parsing error")

        for line in match.group("info").splitlines():
            line = line.strip()
            if not line:
                continue
            data = {}
            for i, name in enumerate(header_column_names):
                info_len = border_list[i]
                data.update({name: line[:info_len].strip()})
                line = line[info_len + len(separator):]

            if data:
                res.append(data)

    return res
