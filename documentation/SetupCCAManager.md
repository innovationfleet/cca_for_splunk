![alt text](/media/CCAforSplunk_orange.png)
## Setup the CCA Manager

### Use the docker image
To use the docker image for CCA for Splunk follow the instruction in
[CCA for Splunk - Docker Repo](https://github.com/innovationfleet/docker).
When completed you can jump to setup the environment.

### Install the Manager and pull CCA for Splunk
Machine minimum requirements:
```
 CPU: 2core
 RAM: 4GB
 Disk: 40GB
 preferred OS: RHEL 8 or higher, CentOS 8 stream or higher
```
**Manual Setup**
The easiest way to setup a CCA manager from scratch is to use the `setup_cca_manager.yml` playbook from a device that is suitable. The following perquisites is needed:
* Access to a server where you would like to deploy CCA Manager.
* Python 3.9 installed on that server.
* Ansible locally installed on your device from where you run the setup playbook, any recent ansible version should be good to use.
* Preferably a dedicated user account e.g. `cca_manager` created on the server, accessible either directly of via sudo. The `cca_manager` user don't need any sudo rights.
* Authentication via SSH key to a account on the server, the account needs sudo right to switch to `cca_manager` if it's not already authenticated as the `cca_manager` user.
* Internet access to download pip packages, ansible-core, ansible collections, mitogen framework and cca_for_splunk repository.

Follow the instructions in [README - Setup CCA Manager](/roles/cca.setup.cca-manager/README.md) on how to run the standalone playbook.

To validate the basic requirements, follow instructions provided in [Automation Readiness](/automation_readiness.md). If you have used the `setup_cca_manager.yml` to setup your environment you should be good to continue to next step. If not, then follow the instructions in the [Automation Readiness](/automation_readiness.md) file and continue when you have reached an appropriate readiness score.

## Setup the environment 
**a)** from the cca_for_splunk repo, run the Readiness playbooks to ensure that you have the prerequisites and install missing tools/packages:
Follow the instructions in [Setup CCA Manager](#prerequisites)
Read up on our [Automation Readiness](/automation_readiness.md) page.

These playbooks will check your automation readiness of both the Manager server, and your Splunk infrastructure in simple assert tasks. When you have passed all assert checks, your environment is ready for the automation journey to start.

**b**) run `./cca_ctrl --setup` from the **cca_for_splunk** repo. The wizard will ask you to provide the following information:

* Name of your environment (cca_lab)

When this information is collected, template files will be copied from the **cca_for_splunk/templates** directory to build the base for the two required repositories, when this is completed you will be asked to provide the following information:

* Splunk Secret, this is the key used to encrypt and decrypt Splunk Passwords and secrets. Accept the generated key or provide your own.
* The name of the admin user (admin)
* The password for the admin user, a random password is generated. Store it if you choose to use it.
* The general pass4SymmKey that is used by Splunk for S2S communication, like communication to license managers. If you have an existing infrastructure, use that pass4SymmKey. If not keep the random key.

Next comes a generation of 4 different sslpasswords, server, web, inputs and outputs. CCA for Splunk can deploy 4 unique certificates to the infrastructure. If you already have certificates that can be used, use the password that correlates to the respective private key. Read more about [certificates](/roles/cca.splunk.ssl-certificates/README.md). Otherwise use the given passwords when generating the encrypted private keys.

* Password for Server Certificate
* Password for Inputs Certificate
* Password for Outputs Certificate
* Password for Web Certificate

The wizard assumes that you have 1 index and 1 search head cluster and will prompt for pass4SymmKeys for those clusters. If you have an existing cluster, add the existing pass4SymmKey instead of the pre-generated one.

* Cluster C1 pass4SymmKey
* Search Head Cluster C1 pass4SymmKey

In the background 8 more pass4SymmKeys for respective cluster is generated and stored in the Splunk Infrastructure repo at environments/ENVIRONMENT_NAME/group_vars/all/cca_splunk_secrets

To access the cleartext value of one of the ansible secrets, run the following command from the relevant repo. Replace the variable specified for `var`.
```
ansible -i environments/cca_lab -m debug -a "var=cca_splunk_certs_server_default_sslpassword" localhost
```

**c**) Verification: Verify that two companion repos has been created and staged with the correct information.

## Update ansible inventory files and variable values
In the following files in your environment directory make the nessesary changes with your values. 

### Variables
* group_vars/all/env_specific
  * cca_splunk_license_manager_uri: 'https://UPDATE_LICENSE_MANAGER_FQDN:8089'
  * domain_name: 'UPDATE_DOMAIN.NAME'
  * cca_splunk_alert_action_smtp: 'UPDATE_SMTP_SERVER_FQDN'
  * cca_splunk_health_alert_action_email_to: 'UPDATE_ALERT_EMAIL_ADDRESS'
  * cca_splunk_extension_cert_rootca: 'UPDATE_ROOT_CA_EXPIRE_DATE_Issuing_CA_EXPIRE_DATE.pem'
  * cca_splunk_extension_server_cert: 'splunk-server_UPDATE_EXPIRE_DATE.cer'
  * cca_splunk_extension_server_key: 'splunk-server_UPDATE_EXPIRE_DATE.key'
  * cca_splunk_extension_inputs_cert: 'splunk-inputs_UPDATE_EXPIRE_DATE.cer'
  * cca_splunk_extension_inputs_key: 'splunk-inputs_UPDATE_EXPIRE_DATE.key'
  * cca_splunk_extension_outputs_cert: 'splunk-outputs_UPDATE_EXPIRE_DATE.cer'
  * cca_splunk_extension_outputs_key: 'splunk-outputs_UPDATE_EXPIRE_DATE.key'
  * cca_splunk_extension_web_cert: 'splunk-web_UPDATE_EXPIRE_DATE.cer'
  * cca_splunk_extension_web_key: 'splunk-web_UPDATE_EXPIRE_DATE.key'
  * 'UPDATE_LICENSE_FILE.lic'
* group_vars/all/linux
  * splunk_user_uid: 'UPDATE_SPLUNK_UID'
  * splunk_user_gid: 'UPDATE_SPLUNK_GID'
  * firewall_zone_name: 'UPDATE_ZONE_NAME'
  * firewall_zone_description: 'UPDATE_ZONE_DESCRIPTION'

### Inventory file
* hosts
  * UPDATE Splunk S2S ports if the default don't match your environment.
  * UPDATE Splunk enterprise version to your desired version.
  * ansible_ssh_user="UPDATE_SSH_REMOTE_USER"
  * UPDATE search and replication factor to match your environment
  * UPDATE available sites to match your environment
  * UPDATE hot and cold volume path to match your environment
  * maxVolumeDataSizeMB_hot="UPDATE_HOT_VOLUME_SIZE_MB"
  * maxVolumeDataSizeMB_cold="UPDATE_COLD_VOLUME_SIZE_MB"

  