# filter_plugins/splunk_config_changes.py

import re

class FilterModule(object):
    def filters(self):
        return {
            'analyze_splunk_changes': self.analyze_splunk_changes
        }

    def analyze_splunk_changes(self, results, rolling_restart_pending=False, splunkd_restart_pending=False, force_splunkd_restart=False, force_bundle_push=False):
        actions = {
            'splunkd_restart_pending': force_splunkd_restart or splunkd_restart_pending,
            'deploymentserver_reload': False,
            'deployer_push': force_bundle_push,
            'cluster_manager_push': False,
        }

        if rolling_restart_pending:
            actions['splunkd_restart'] = True

        for item in results:
            if item['changed']:
                path = item.get('path', '')
                if bool(re.search('.*/etc/(?!deployment-apps|shcluster|master-apps|manager-apps).*?$', path)):
                    actions['splunkd_restart_pending'] = True
                elif 'deployment-apps' in path:
                    actions['deploymentserver_reload'] = True
                elif 'shcluster' in path:
                    actions['deployer_push'] = True
                elif 'master-apps' in path or 'manager-apps' in path:
                    actions['cluster_manager_push'] = True

        return actions
