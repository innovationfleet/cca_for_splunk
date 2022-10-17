cca.setup.cca-manager
=========

This role is fully standalone and can be used to setup the prerequisites for running and setting up CCA in a easy way. It will assist with creating a directory structure, install a python virtual environment, install the correct version of Ansible and set required Environment variables.

The versions listed in this role matches the requirements for CCA.

When the playbook `playbooks/setup_cca_manager.yml` has been completed the server and account is ready to run CCA. Next step is to verify all settings following the instructions in automation_readiness.md

Requirements
------------

The role require ssh access to a server with an account where it's ok to create directories and alter the login profile. Bash is a required login shell.
Python 3.9 needs to be installed with a package manager or built from source.

Role Variables
--------------

All variables are defined in `vars/main.yml`. If custom variables are needed they be added via playbook arguments using `--extra-vars`.

After completion of this role, CCA will manage all variables in an `environments` directory structure in the 2 companion repos that are generated post the execution of `./cca_ctrl --setup`.


Instruction
---------

Run this command after updating ssh config file. Note the comma after the host name in the ansible-playbook command, it instructs ansible to treat the host as the inventory source.

`ansible-playbook -i <destination_host>, playbooks/setup_cca_manager.yml -v --become --become-user=<cca_manager_user> --become-method=sudo`

### Example for remote cca manager with sudo to a cca_manager user ###
`ansible-playbook -i splunk-prod-mgr-101, playbooks/setup_cca_manager.yml -v --become --become-user=cca_manager --become-method=sudo`

### Example for remote cca manager with the logged-in user ###
`ansible-playbook -i splunk-prod-mgr-101, playbooks/setup_cca_manager.yml -v`


### Example for settings up current user on localhost ###
`ansible-playbook -i localhost, playbooks/setup_cca_manager.yml --connection=local -v`


To simplify the required parameters for ansible connections configuration can easily be added to your local `~/.ssh/config`

### ~/.ssh/config ###

```
Host splunk-prod-mgr-101
  HostName 10.11.12.13
  IdentityFile ~/.ssh/id_rsa
  User rlinq
```

Tasks
------------
### Main
* `python_check.yml`
  * Checks if the required python version is available on the server
* `configure_cca_manager_user.yml`
  * Create directories, installs ansible in python virtual environment.
* `create_python_venv.yml`
  * Create a virtual python environment for ansible
* `install_ansible_venv.yml`
  * Install ansible in the virtual environment
* `install_mitogen.yml`
  * Install the mitogen framework to speed up playbook execution
* `install_cca_for_splunk.yml`
  * Clone cca_for_splunk repository from github.com/innovationfleet/cca_for_splunk

Dependencies
------------

None

License
-------

MIT
