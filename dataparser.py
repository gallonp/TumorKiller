"""Methods for parsing MRS brain scan data."""

import re


def get_header_data(data_string):
    """Parses header from the given MRS data file.

    Args:
        data_string: MRS data file's string contents.

    Returns:
        Dictionary of header values keyed by field name.
    """
    header_data = dict()
    end_count = 0

    # Look at file contents line-by-line.
    for line in data_string.split('\n'):
        line = line.strip()
        if line[0] != '$':
            # Get name and value of this header field.
            match_obj = re.match(r"(.+)\s+=\s+'?(.+)'?,?", line)
            header_name = match_obj.group(1)
            header_value = match_obj.group(2).rstrip(',').rstrip("'")
            header_data[header_name] = header_value
        else:
            # Count header end tokens.
            if line == '$END':
                end_count += 1
                if end_count > 1:  # header has two end tokens
                    break
    return header_data


def get_xy_data(data_string):
    """Parses time-domain MRS values from the given file contents.

    Args:
        data_string: MRS data file's string contents.

    Returns:
        List of data points from the MRS data file. The data points are ordered
        by time (X-axis), and each element is the corresponding MRS value
        (Y-axis) at that time.
    """
    xy_data = list()
    file_lines = data_string.split('\n')
    xy_start_line = 0
    end_count = 0

    # Find line where header ends and xy data begins.
    for line in file_lines:
        xy_start_line += 1
        if line.strip() == '$END':
            end_count += 1
            if end_count > 1:  # header has two end tokens
                break

    # Parse complex number off of each line.
    for line in file_lines[xy_start_line:]:
        line = line.strip()
        match_obj = re.match(r"(.+)\s+(.+)", line)

        if match_obj is not None:
            data_point = complex(float(match_obj.group(1)), float(match_obj.group(2)))
            xy_data.append(data_point)

    return xy_data
