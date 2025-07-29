import os
import glob
import configparser
import json
from collections import defaultdict, OrderedDict
import sys
import fnmatch

class CaseSensitiveConfigParser(configparser.ConfigParser):
    def __init__(self, *args, **kwargs):
        super(CaseSensitiveConfigParser, self).__init__(*args, **kwargs, dict_type=OrderedDict)
        self._duplicates = defaultdict(list)
        self._duplicate_sections = defaultdict(list)
        self._duplicate_lines = defaultdict(list)

    def optionxform(self, optionstr):
        return optionstr

    def _read(self, fp, fpname):
        current_section = None
        for lineno, line in enumerate(fp, start=1):
            comment_start = line.find('#')
            if comment_start == -1:
                comment_start = line.find(';')
            if comment_start != -1:
                line = line[:comment_start]

            line = line.strip()
            if not line:
                continue

            if line.startswith('['):
                section = line.strip('[]')
                if not self.has_section(section):
                    self.add_section(section)
                else:
                    self._duplicate_sections[section].append(fpname)
                current_section = section
                continue

            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                if key in self[current_section]:
                    self._duplicates[(current_section, key)].append(fpname)
                    self._duplicate_lines[(fpname, lineno, current_section, key)].append(value)
                else:
                    self[current_section][key] = value

    def get_duplicates(self):
        return self._duplicates

    def get_duplicate_sections(self):
        return self._duplicate_sections

    def get_duplicate_lines(self):
        return self._duplicate_lines

def traverse_and_parse(directory, filter_dir_pattern=None):
    serverclass_data = OrderedDict()
    duplicates = defaultdict(list)
    duplicate_sections = defaultdict(list)
    duplicate_lines = defaultdict(list)

    for filepath in glob.glob(os.path.join(directory, '**', 'serverclass.conf'), recursive=True):
        if 'search/local/' in filepath.replace('\\', '/'):
            continue

        # Apply directory filter with wildcard support if provided
        if filter_dir_pattern:
            path_components = filepath.split(os.sep)
            if not any(fnmatch.fnmatch(component, filter_dir_pattern) for component in path_components):
                continue

        config = CaseSensitiveConfigParser()
        with open(filepath, 'r') as f:
            config._read(f, filepath)

        for section in config.sections():
            if section not in serverclass_data:
                serverclass_data[section] = OrderedDict()
            for option in config.options(section):
                serverclass_data[section][option] = config.get(section, option)

        file_duplicates = config.get_duplicates()
        file_duplicate_sections = config.get_duplicate_sections()
        file_duplicate_lines = config.get_duplicate_lines()

        for (section, key), files in file_duplicates.items():
            duplicates[(section, key)].extend(files)

        for section, files in file_duplicate_sections.items():
            duplicate_sections[section].extend(files)

        for (fpname, lineno, section, key), values in file_duplicate_lines.items():
            duplicate_lines[(fpname, lineno, section, key)] = values

    combined_duplicates = {
        'duplicate_sections': {f"{section}": files for section, files in duplicate_sections.items()},
        'duplicate_keys': {f"{section}::{key}": files for (section, key), files in duplicates.items()}
    }

    for (fpname, lineno, section, key), values in duplicate_lines.items():
        print(f"{fpname},{lineno},{section}")

    return serverclass_data, combined_duplicates

def save_to_json(data, output_file):
    with open(output_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def save_to_ini(data, output_directory):
    os.makedirs(output_directory, exist_ok=True)
    section_counter = 0
    file_counter = 0

    ini_file = None
    for section in data.keys():
        if section.startswith('serverClass:') and ':app:' not in section and section_counter % 1000 == 0:
            if ini_file:
                ini_file.close()
            dir_name = f"cca_merged_serverclass_{str(file_counter).zfill(5)}-{str(file_counter + 999).zfill(5)}/local"
            dir_path = os.path.join(output_directory, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            ini_file = open(os.path.join(dir_path, 'serverclass.conf'), 'w')
            file_counter += 1000

        ini_file.write(f"[{section}]\n")
        for key, value in data[section].items():
            ini_file.write(f"{key} = {value}\n")
        if section.startswith('serverClass:') and ':app:' not in section:
            section_counter += 1

    if ini_file:
        ini_file.close()

if __name__ == "__main__":
    if len(sys.argv) < 4 or len(sys.argv) > 6:
        print("Usage: script.py <directory_to_traverse> <output_json_file> <duplicates_json_file> [output_directory] [filter_directory_pattern]")
        sys.exit(1)

    directory_to_traverse = sys.argv[1]
    output_json_file = sys.argv[2]
    duplicates_json_file = sys.argv[3]
    output_directory = sys.argv[4] if len(sys.argv) >= 5 else None
    filter_directory_pattern = sys.argv[5] if len(sys.argv) == 6 else None

    parsed_data, combined_duplicates = traverse_and_parse(directory_to_traverse, filter_directory_pattern)
    save_to_json(parsed_data, output_json_file)
    save_to_json(combined_duplicates, duplicates_json_file)

    if output_directory:
        save_to_ini(parsed_data, output_directory)
