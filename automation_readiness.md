# Automation Readiness

Automation Readiness is a playbook developed by us to help you determine how prepared your environment is to run CCA for Splunk. The playbook checks for a list of CCA for Splunk prerequisites, such as:

* OS version
* Ansible version
* Python version
* Ansible environment variables
* CCA for Splunk variables

The playbook outputs a score, referred as Automation Readiness Score. The score tells you how well your environment will handle CCA for Splunk, as well as required steps to increase the Automation Readiness Score.

**Automation Readiness Score**

To assess the Automation Readiness of the environment, we have developed a Readiness score that determines how well the environment is prepared to run CCA for Splunk from 0 (not at all) to 2398 (fully!). When you reach a Readiness score above 2000 you should be ready to execute `./cca_ctrl --setup` from the main *cca_for_splunk* repo. See [Setup Wizard](#setup-wizard)

![Automation Readiness Score](media/automation_readiness_score_viz.png)

CCA for Splunk typically need at least 2000 in Readiness score to be able to run (with some hard requirements of course)
We have also described installation steps according to our best practices, following these steps will increase your Automation Readiness Score.
 * [Python installation](#install-python-39)
 * [Virtual env and Ansible Installation](#create-python-virtual-env-and-install-ansible-with-collections)

## Optional: CCA Manager setup (recommended)

We recommend that you designate a central server that will have access to your Splunk infrastructure and that this server has a technical user that you access via `sudo`. The current fully supported OS's for running `cca_for_splunk` framework are RedHat 8, CentOS 8 Stream, Amazon Linux 2 and Ubuntu 20.
Machine minimum requirements:
* CPU: 2 CPU
* RAM: 4GB RAM (Onboarding repository size depends on the apps you have stored in it)
* Disk: 40 GB

Feel free to try and run these playbooks elsewhere but on your own responsibility.

A remote user that has SSH key based login enabled and has `sudo ALLl NO PASSWD` configured is also required on the Splunk Infrastructure servers you are going to manage.

Let's get started with automation readiness test.

## Step 1: Clone cca_for_splunk repository

Logon to a server where you will setup the CCA Manager.

Prepare your account with a directory where you will host your cloned `cca_for_splunk` repository. See example below.
```
mkdir ~/master ~/secrets
cd ~/master
git clone https://github.com/innovationfleet/cca_for_splunk.git
cd cca_for_splunk
```

## Step 2: Execute Automation Readiness Playbook

```
cd ~/master/cca_for_splunk

ansible-playbook -i localhost, playbooks/automation_readiness_cca_manager.yml -v
```

The playbook will test and assert that your account and server is setup as it should.
For every successful assertion, points will be added to your readiness score. At the
end you will see how far you have come on your readiness journey.

# Correct Automation Readiness issues

Here will list the different checks that we perform and what should be configured to correct them if they don't pass in your playbook.

## Install Python 3.9
As a user with sudo privileges execute `sudo yum install python39`

## Create Python virtual env and Install Ansible with collections
As the same user that runs the readiness playbook, execute the following commands to setup Python virtual env and Ansible.

```
cd
alias python='/usr/bin/python3.9'
mkdir -p ~/tools/python-venv/ansible2.12
cd ~/tools/python-venv
python -m venv ansible2.12
source ansible2.12/bin/activate
~/tools/python-venv/ansible2.12/bin/python3.9 -m pip install --upgrade pip
pip install ansible-core==2.12.5
ansible-galaxy collection install community.general
ansible-galaxy collection install ansible.posix

```
Add this line to your user profile to activate the Python virtual environment every time you login.

```
source ~/tools/python-venv/ansible2.12/bin/activate
```
Test it by logging out and in again and execute this command
```
if [[ -v VIRTUAL_ENV ]] ; then ansible --version ; else echo "VIRTUAL_ENV is not configured" ;  fi
 ```

If you get an output similar to this you are ok.

```
ansible [core 2.12.5]
  config file = /etc/ansible/ansible.cfg
  configured module search path = ['/opt/cca_builder/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /opt/cca_builder/tools/python-venv/ansible2.12/lib64/python3.9/site-packages/ansible
  ansible collection location = /opt/cca_builder/.ansible/collections:/usr/share/ansible/collections
  executable location = /opt/cca_builder/tools/python-venv/ansible2.12/bin/ansible
  python version = 3.9.7 (default, Sep 21 2021, 00:13:39) [GCC 8.5.0 20210514 (Red Hat 8.5.0-3)]
  jinja version = 3.1.2
  libyaml = True
  ```


## Required Environment variables

Experience have proven that we have much more control and less errors using environment variables instead of a managed ansible.cfg. This readiness playbook will check that all necessary and some optional environment variables are configured. Add missing environment variables to your user profile. When completed, source the user profile and execute `env` to validate that they are set correctly.

### ANSIBLE_PRIVATE_KEY_FILE

Ansible needs a reference to the private ssh key file that shall be used to access Splunk infrastructure servers. Add `export ANSIBLE_PRIVATE_KEY_FILE="path_to_private_key_file"` to your user profile and source it when you are done and before next automation readiness run.

### ANSIBLE_ROLES_PATH

Ansible needs how to find roles, this is required for `cca_for_splunk` where the playbooks are called from outside the repository. Verify that the directory below match your setup. Add
`export ANSIBLE_ROLES_PATH="./roles:~/master/cca_for_splunk/roles"` to your user profile and source it when you are done and before next automation readiness run.

### ANSIBLE_VAULT_PASSWORD_FILE

Use `openssl rand -hex 32` to output a random string that you then add to your `ANSIBLE_VAULT_PASSWORD_FILE` file. See proposed file name below.

Add `export ANSIBLE_VAULT_PASSWORD_FILE="~/secrets/cca_splunk_ansible_vault.secret"` to your user profile and source it when you are done and before next automation readiness run.


## Recommended Environment variables

### ANSIBLE_STRATEGY

The default strategy in Ansible is called linear and doesn't need to be specified separately. In `cca_for_splunk` the opposite is true, here we specify which playbooks that needs to run the linear strategy, for the rest we can control it with the environment variable `ANSIBLE_STRATEGY`.

If we set it to `mitogen_linear` the playbooks will run much faster, up 4X.

To use it your self, read up on [Ansible Mitogen](https://github.com/mitogen-hq/mitogen). Currently the package from github is needed, download and install it in the directory referenced by [ANSIBLE_STRATEGY_PLUGINS](#"ansiblestrategyplugins"-"internalccaforsplunktoolsmitogen-masteransiblemitogenpluginsstrategy")

Add `epxport ANSIBLE_STRATEGY="mitogen_linear"`
to start using the highly recommended strategy plugin.

### ANSIBLE_STRATEGY_PLUGINS

Add `export ANSIBLE_STRATEGY_PLUGINS="~/tools/mitogen-0.3.2/ansible_mitogen/plugins/strategy"` and set it to the directory where you have installed the mitogen package.

## Optional Environment variables

### ANSIBLE_CALLBACKS_ENABLED

Get useful summary information at the end of each task as well time spend per executed task. Add
`export ANSIBLE_CALLBACKS_ENABLED="ansible.posix.profile_tasks"` to your user profile and source it when you are done and before next automation readiness run.

### ANSIBLE_STDOUT_CALLBACK

Increased readability of Ansible terminal output, yaml formatted. Add
`export ANSIBLE_STDOUT_CALLBACK="yaml"` to your user profile and source it when you are done and before next automation readiness run.


## Summary of configured variables in your user profile

```
export ANSIBLE_PRIVATE_KEY_FILE="~/secrets/splunk_cca_ansible_gcp.pem"
export ANSIBLE_ROLES_PATH="./roles:~/master/cca_for_splunk/roles"
export ANSIBLE_STRATEGY_PLUGINS="~/tools/mitogen-0.3.2/ansible_mitogen/plugins/strategy"
export ANSIBLE_STRATEGY="mitogen_linear"
export ANSIBLE_CALLBACKS_ENABLED="ansible.posix.profile_tasks"
export ANSIBLE_STDOUT_CALLBACK="yaml"
export ANSIBLE_VAULT_PASSWORD_FILE="~/secrets/cca_splunk_ansible_vault.secret

source ~/tools/python-venv/ansible2.12/bin/activate
```
Wait with ANSIBLE_VAULT_PASSWORD_FILE until it exists.

### Splunk Enterprise Package

`cca_for_splunk` uses Splunk Enterprise tgz files for installing Splunk on target Splunk servers. The tgz files is also used by the setup wizard to temporary install.
Store the Splunk Enterprise for Linux tar file in `/tmp/splunk_tmp/`. If you are missing the directory, create it and it will later on be used during the setup wizard.

# Setup Wizard
When you have reached a automation readiness score above 2000 then you are ready to run the setup wizard. Read up on what the setup_wizard playbook does [here](/README.md) and **step 2b.**

In short it configures the two companion directories where custom settings and apps are stored. In the playbook you will be questioned to set names on the companion directories, the environment, the general pass4SymmKey and admin password.

If you have an existing environment that your are transforming, you have to update the pass4SymmKeys for the different cluster and shcluster id's.

## Inventory file
When the wizard is completed, CCA for Splunk needs a few hosts to configure. All hosts are configured in the inventory file, the file is found in the companion directory `environments/ENVIRONMENT_NAME/hosts`

At first the hosts file can seem complicated, be assured, it's not. All Splunk's Validated Architecture components are listed in the file. It also have 3 availability groups pre-configured. Find your group name, locate it in the hosts file. Add your host to one of the pre-configured availability groups.

## Environment Specific Variables

Look for all variables that needs to be updates. `grep -R UPDATE environments` will list all of them if you are in the root of the companion directories.

