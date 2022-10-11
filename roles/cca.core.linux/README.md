cca.core.linux
==============

This role is prepping an installed server with the settings that is required to run Splunk as a service as a non privileged user.

### Customization
Options exists to control which tasks that should be executed and to add multiple custom roles to configure the server as you like.

Requirements
------------

The servers OS and version needs to be one of the supported ones.
  - Centos 8 Steam
  - RHEL 8
  - Amazon Linux 2

Mount points needs to be created for the `splunk_path` on all Splunk servers, a separate filesystem is recommended but not enforced.
On Cluster Index peers two additional mount points are need, align with `splunk_volume_path_hot` and `splunk_volume_path_cold` defined in `environments/ENVIRONMENT_NAME/hosts`. Same here, separate file systems is highly recommended but not enforced.

The initial account that is used to setup the server with users and services needs to have SUDO ALL access to the server. If you don't have it at this point, the server team could possibly run the ansible playbook that include this role and handover the server when completed.

Role Variables
--------------

Description

### group_vars/all/linux
* `external_bootstrap_pre_roles`
  * Possibility to inject custom roles early in the server bootstrap configuration process. Add role names as lists and store them outside the cca_for_splunk repo. Configure ansible role search paths accordingly.
* `external_bootstrap_roles`
  * Possibility to inject custom roles in the middle of the server bootstrap configuration process. Add role names as lists and store them outside the cca_for_splunk repo. Configure ansible role search paths accordingly.
*  `external_bootstrap_post_roles`
   * Possibility to inject custom roles late in the server bootstrap configuration process. Add role names as lists and store them outside the cca_for_splunk repo. Configure ansible role search paths accordingly.
* `cca_splunk_manager_user`
  * Setup manager user on splunk servers during bootstrap. This user is used to connect to the server and from there ansible sudoes to splunk to perform required configuration.
* `cca_splunk_manager_user_uid`
  * Manager users UID
* `cca_splunk_manager_user_dir`
  * Manager users home dir
* `cca_splunk_manager_group_name`
  * Manager users group name
* `cca_splunk_manager_gid`
  * Manager users GID
* `splunk_user`
  * Name of splunk user, normally just `splunk`
* `splunk_user_uid`
  * Splunk users UID
* `splunk_user_dir`
  * Splunk users home is that same as `splunk_path`
* `splunk_user_group_name`
  * Splunk user group name is the same as `splunk_user`
* `splunk_user_gid`
  * Splunk users GID is normally the same as UID
* `cca_baseline_software`
  * Baseline software that is needed by CCA to perform the required work. Example of required software
    - 'rsync'
    - 'git'
    - 'bind-utils'
    - 'nc'

* `control`
  * `linux_configuration`
  * Controls wether these tasks should be executed or not. Read up on the tasks files to find if they should be disabled or not. Not all tasks are created. If a changed behaviour is wanted of one of the included tasks, disable them in this file by changing the value from true to false. Then add a custom role and the changed tasks in it and add it to the external_bootrap role list.

### group_vars/all/env_specific
* `filename`
  * Description

### group_vars/all/default
* `filename`
  * Description

### group_vars/all/general_settings
* `filename`
  * Description

### group_vars/GROUP_VARS_FILES
* `filename`
  * Description

### host_vars/INVENTORY_HOSTNAME
* `filename`
  * Description

### Configurable variables
* `filename`
  * Description


Vars
------------

Vars is used to specify OS dependent variables that can be override'd if needed.

* `default.yml`
  * Set default variables
* `Amazon-2`
  * Set specific variables for Amazon-2 Linux servers


Tasks
------------

### Main
* `validate_supported_os_versions.yml`
  * Validate ansible facts against CCA supported OS'es and versions
* `include_external_pre_roles.yml`
  * Execute external roles at the beginning of main
* `configure_splunk_user.yml`
  * Configure splunk user
* `include_external_roles.yml`
  * Execute external roles
* `dot_bootstrap.yml`
  * Mark this server instance as bootstrapped
* `configure_firewall.yml`
  * Not defined
* `configure_server_hardening.yml`
  * Not defined
* `configure_baseline_software.yml`
  * Execute external roles in the middle of main
* `configure_splunk_limits.yml`
  * Set ulimits for Splunk user
* `configure_splunk_service.yml`
  * Include systemd/main.yml
*  `systemd/spunkd_service.yml`
   * Template out Splunkd.service and Splunk.service.d/limits.conf
* `configure_polkit.yml`
  * Install polkit and includes polkit/polkit_rules.yml
* `polkit/polkit_rules.yml`
  * Template out polkit rule configuration for Splunk user
* `configure_thp.yml`
  * Disables THP by building and updating grub.cfg
* `configure_sudoers.yml`
  * Configure sudo all for Splunk manager user
* `include_external_post_roles.yml`
  * Execute external roles at last in the main

### Standalone tasks
* `server_reboot_handler.yml`
  * Calls `check_pending_actions.yml` reboots server and wait until it's up

Dependencies
------------
None

License
-------

MIT
