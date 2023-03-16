cca.splunk.enterprise-install
=========

Start, stops, installs and upgrade Splunk Enterprise. Manage cluster specific commands for rolling upgrades.
The role supports Ansible check mode and will run through all tasks and validate all things that is possible to test without actually performing the upgrade.

Requirements
------------

Splunk tgz file needs to be stored in the infrastructure directory of `splunk/var/images/` where they will be matched by the `splunk_enterprise_version` specified in the hosts inventory file.

Role Variables
--------------

The variable `splunk_enterprise_version` controls what version of Splunk that should be initially installed and also target version during a Splunk upgrade. `splunk_enterprise_version` is set in the ansible inventory file `environments/ENVIRONMENT_NAME/hosts`. It can be set on group or host level. Let you control splunk version on a server basis if needed.

### group_vars/all/cca_splunk_secrets
* `filename`
  * Description

### group_vars/all/env_specific
* `absolute_infra_repo_path`
  * Description
* `splunk_cli_user`
  * Splunk cli user, can be different from Splunk admin user
* `splunk_cli_user_password`
  * Splunk cli user password, can be different from Splunk admin user password

### group_vars/all/default
* `hide_password`
  * Description
* `splunk_path`
  * Install path for Splunk Enterprise
* `start_command`
  * Command to start splunk and accept license
* `stop_command`
  * Command to stop splunk
* `cca_splunk_var_tmp`
   * Temp directory for CCA and Splunk files
* `systemd_enterprise_name`
 * Name of systemd service for splunk

### group_vars/hosts
* `splunk_enterprise_version`
  * Set the desired version of Splunk Enterprise

### group_vars/all/linux
* `splunk_user`
  * Defines the splunk user

### Configurable variables
* `synchronize_module_use_ssh_args`
  * Set synchronize arguments


Tasks
------------

### Main
* `splunk_status.yml`
  * Checks status of Splunk and set fact if enterprise_upgrade should be performed. Checks if the system is managed by CCA, if not then it fails the task by the assert in `prompt_unmanaged.yml`
* `stage_install_files.yml`
  * Copy files from CCA manager to each Splunk server.
* `ensure_splunk_version.yml`
  * When enterprise_upgrade is flagged, splunk is stopped, tar file extracted, redundant files removed and splunk started. On Cluster Peers a offline command is issued instead of a stop command.
* `ensure_splunk_status_started.yml`
  * Start splunk from command line


### Standalone tasks
* `prompt_unmanaged.yml`
  * Assert if the server is managed by CCA
* `cluster/init_upgrade.yml`
  * Start rolling upgrade of Splunk Index Cluster
* `cluster/finalize_upgrade.yml`
  * Finalize rolling upgrade of Splunk Index Cluster
* `shcluster_upgrade_handler.ym`
  * Selects shcluster upgrade task based on upgrade method.
* `shcluster/init_upgrade.yml`
  * Start rolling upgrade on Search Head Member
* `shcluster/shcluster_rolling_upgrade.yml`
  * Perform the steps to execute the rolling upgrade of a search head member.
* `shcluster/shcluster_member_by_member_upgrade.yml`
  * Not implemented, task file as place holder
* `shcluster/finalize_upgrade.yml`
  * Finalize rolling upgrade of Splunk Search Head Members

Files
------------

* `bin/splunk_upgrade_cleanup.sh`
  * Helper script to cleanup files added by older versions and no longer applicable.
* `sudo_ansible_helper.sh`
  * Placeholder, not developed yet.
* `dat/untracked_files_splunk_VERSION_Linux.diff`
  * One file per linux version that has a large diff of current and earlier splunk versions. If upgrading to a version that has no diff file, the cleanup will be skipped and can be executed later.

Dependencies
------------

cca.core.splunk

License
-------

MIT