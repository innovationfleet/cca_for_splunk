# filter_plugins/splunk_conf_validate.py

from ansible.errors import AnsibleFilterError
import re

def validate_splunk_conf(data, invalid_config_regex, enable_precheck=True):
    errors = []

    for item in data:
        path, section, option, value, state = (
            item.get('path', ''),
            item.get('section', ''),
            item.get('option', ''),
            item.get('value', ''),
            item.get('state', 'present'),
        )

        # Perform the checks
        if re.search(invalid_config_regex, path) and state != 'absent':
            errors.append(f"Invalid path: {path}")
        if re.search(invalid_config_regex, section) and state != 'absent':
            errors.append(f"Invalid section: {section}")
        if re.search(invalid_config_regex, option) and state != 'absent':
            errors.append(f"Invalid option: {option}")
        if re.search(invalid_config_regex, value) and state != 'absent':
            errors.append(f"Invalid value: {value}")
        if enable_precheck and re.match(r'^(?!#).*', option) and value != '' and option == '' and state != 'absent':
            errors.append(f"Precheck failed for option: {option} with value: {value}")

    if errors:
        error_msg = "\n".join(errors)
        raise AnsibleFilterError(f"Validation failed with the following errors:\n{error_msg}")

    # If no errors, return a message indicating success
    return "Validation passed successfully."

class FilterModule(object):
    def filters(self):
        return {
            'validate_splunk_conf': validate_splunk_conf
        }
