# CCA Splunk conf flatten

from ansible.errors import AnsibleFilterError

def splunk_conf_flatten(conf_groups):
    try:
        flattened_data = []
        for group in conf_groups:
            filepath = group.get('filepath')
            filename = group.get('filename')
            for section in group.get('sections', []):
                section_name = section.get('section')
                if section_name != '':
                    for option in section.get('options', []):
                        flattened_data.append({
                            'path': filepath + '/' + filename,
                            'section': section_name,
                            'option': option.get('option'),
                            'value': option.get('value'),
                            'state': option.get('state','present'),
                            'comment': option.get('comment', ''),
                        })
        return flattened_data
    except Exception as e:
        raise AnsibleFilterError('Error flattening configuration data: {}'.format(e))

class FilterModule(object):
    ''' Ansible custom filter plugin for flattening Splunk configuration data '''

    def filters(self):
        return {
            'splunk_conf_flatten': splunk_conf_flatten
        }
