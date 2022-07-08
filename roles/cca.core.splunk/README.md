cca.core.splunk
=========

This role are a central part of CCA as it holds tasks to check statuses, control notification handlers and manage Splunk configuration settings.

Let's start with describing Splunk configuration settings, which is the main reason why you would like to automate your Splunk Infrastructure. Without creating and manage a lot of settings a initial setup of Splunk will be impossible to up and running. Continuously over time settings are crucial to be update, for example, when new SSL certificates are configured or just to tune settings to optimize performance in Splunk.


DRY (Don't repeat yourself) has been an important design philosophy and with so many options to configure in Splunk we have introduced 3 levels of settings in Ansible, General, Group and Host level. These levels are a perfect match between Ansible and Splunk.

An important note is that these settings are not squashed together. Playbook tasks starts with configuring general settings, then group settings and finally host settings. Be careful not to configure conflicting values on different levels. Effectively what happen is that Ansible will set one value and trigger a change notification then just after set another and trigger a new change notification. Probably your expected value will concur but with the side affect that a Splunkd restart or rolling restart is triggered every time the playbook is run. If this happens, review your config and make sure to correct the logics.

One important feature to keep in mind is that all settings are managed with the Ansible `ini_file` module. It does a great job managing the settings that is configured. However it can't do anything for settings that it don't now about. If there is a need to remove a setting or Splunk stanza, it's not enough to just delete it from the configuration file in Ansible. Before it's removed from the configuration the state need to be set to `absent` and playbooks needs to run towards all affected servers.

We take a closer look at the different levels.

## Ansible general level

Settings in the general level covers the common settings that is used to configure Splunk across all types of instances. Settings are found in `environments/ENVIRONMENT_NAME/group_vars/all/general_settings`

Logics has been added to variable settings to be able to dynamically update configurations, when for example, SSL certificates have been configured or updated.

## Ansible group level

Group level settings deals with all settings that are specific for an Ansible group (e.g Splunk role). All values that are different between environments have been parameterized and specified in either the `hosts` or `env_specific` file. Settings are found in `environments/ENVIRONMENT_NAME/group_vars/GROUP_VARS` files.

## Ansible host level

Rarely used in an ordinary working configuration but invaluable when cleaning up deprecated settings, incorrect values or migrated settings.
Settings are found in `environments/ENVIRONMENT_NAME/host_vars/INVENTORY_HOSTNAME` files.


Requirements
------------

The role will ensure that when Splunk already installed, that the _splunk.secret_ file has a checksum that matches the variable _cca_splunk_secret_sha256_ that you find in the ansible inventory at `environments/ENVIRONMENT_NAME/group_vars/all/cca_splunk_secrets`


Role Variables
--------------

The below variables are defined per environment in `environments/ENVIRONMENT_NAME/`

### group_vars/all/cca_splunk_secrets
* `cca_splunk_admin_user`
  * Configured name for Splunk amin user
* `cca_splunk_admin_password_hash`
  * Hashed admin user password. Can be created using methods described in https://docs.splunk.com/Documentation/Splunk/8.2.6/Security/Secureyouradminaccount
* `cca_splunk_admin_email`
  * Admin user email
* `cca_splunk_local_users`
  * Additional users to be added to local passwd file
* `cca_splunk_secret`
  * Splunk secret file stored in a Ansible vault

### group_vars/all/env_specific
* `cca_splunk_extension_licenses`
  * List of license files to be deployed to license manager
* `preflight_command_retries`
  * Number of retries for Cluster preflight checks

### group_vars/all/default
* `dot_managed_by_ansible`
  * Reference a hidden state file, used to mark a CCA managed host
* `file_managed_by_ansible`
  * Text string added to each Splunk .conf file managed by CCA
* `hide_password`
  * Default value is `true`, suppress log out put where defined
* `invalid_config_regex`
  * List of invalid characters to search for when validating the .conf settings.
* `splunk_path`
  * Install path for Splunk Enterprise

### group_vars/all/general_settings
* `splunk_conf_general_settings`
  * Holds all general settings for Splunk .conf files

### group_vars/GROUP_VARS_FILES
* `splunk_conf_group_settings`
  * Holds all inventory group related settings for Splunk .conf files

### host_vars/INVENTORY_HOSTNAME
* `splunk_conf_host_settings`
  * Holds all host specific settings for Splunk .conf files

### Configurable variables
* `cca_wait_for_connection_timeout`
  * Connection timeout can be changed if the default value is not sufficient. Add updated values to your env_specific file.
* `cluster_bundle_status_command_retries`
  * Bundle status retries be changed if the default value is not sufficient. Add updated values to your env_specific file.
* `cluster_peer_rolling_restart_preflight_retries`
  * Preflight retries can be changed if the default value is not sufficient. Add updated values to your env_specific file.
* `wait_time_cluster_peers_report`
  * Wait time for cluster peer report, can be changed if default value is not sufficient. Add updated values to your env_specific file.
* `prompt_rolling_restart`
  * Prompt for user confirmation if a rolling restart is detected. Defaults to `false`.


Tasks
------------

### Main
* `check_init.yml`
  * Checks if current instance has a .ansible_managed file
* `check_splunk_secret.yml`
  * Checks and validates splunk.secret file
* `local_users.yml`
  * Adds local users to Splunk instance, minimum that admin user is added
  * `../../cca.splunk.ssl-certificates/tasks/validate_certificates.yml`
  * Runs checks to validate currently installed certificates
* `precheck_settings.yml`
  * Scan for invalid characters before applying Splunk .conf settings
* `set_splunk_general_settings.yml`
  * Sets general Splunk .conf settings
* `set_splunk_group_settings.yml`
  * Sets group Splunk .conf settings
* `set_splunk_host_settings.yml`
  * Sets host Splunk .conf settings
* `add_license.yml`
  * Configure Splunk license files

### Standalone tasks
* `ansible_managed.yml`
  * Creates a state file to tell that the Splunk is managed by ansible
* `apply_cluster_bundle.yml`
  * Validates and applies cluster bundle
* `apply_shcluster_bundle.yml`
  * Applies shcluster bundle on deployer
* `assert/validate_parameters.yml`
  * Lists all variables that are required to run CCA.
* `check_pending_actions.yml`
  * Checks for pending actions stored as state files on Splunk hosts after configuring settings and run actions.
* `check_preflight_status.yml`
  * Check Pre-flight status of Cluster Manager. If check time exceeds 90 minutes the output is hidden as credentials needs to be added on command line.
* `cleanup_shcluster_rolling_restart_file.yml`
  * Remove state file after shcluster rolling restart is started
* `cluster/get_cluster_status.yml`
  * Collect splunk version and cluster status
* `cluster/precheck_upgrade_status.yml`
  * Assert that status is as expected before starting upgrade.
* `cluster/splunk_offline.yml`
  * Stops Splunk process with offline command
* `cluster_peers_rolling_restart.yml`
  * Performs a rolling restart of a index cluster
* `get_splunk_status.yml`
  * Get running status of Splunk
* `notify_splunk.yml`
  * Call notification handlers depending on scope of the splunk settings that has been updated.
* `restart_splunkd.yml`
  * Restart Splunk process
* `shcluster/get_shcluster_status.yml`
  * Collect shcluster status from member nodes
* `shcluster/precheck_upgrade_status.yml`
  * Assert that shcluster status is as expected
* `shcluster_members_rolling_restart.yml`
  * Perform a rolling restart of Search head members
* `splunk_login.yml`
  * Login to Splunk before running an authenticated command. This allows us to keep log output from the authenticated commands and see failures or stdout of the commands.
* `splunk_logout.yml`
  * Log out from an authenticated sessions.
* `wait_for_connection.yml`
  * Wait until host is reachable

Dependencies
------------

cca.splunk.ssl-certificates

License
-------

MIT
