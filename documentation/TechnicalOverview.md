![alt text](/media/CCAforSplunk_orange.png)
# Technically what is CCA for Splunk ?

CCA for Splunk is powered by Ansible. There's multiple playbooks used to interact with your operating system (OS) & Splunk to apply configurations and maintain a desired & approved state of your Splunk platform. All of the Splunk configurations performed by CCA for Splunk resides in Git, allowing for a single point of truth, increasing tracking ability of performed changed and handle everything with speed and efficiency.

No need to spend unnecessary hours on troubleshooting your Splunk platform where the root cause is mismatched configurations between your servers, simply apply your configuration changes in Git & Ansible takes care of the rest.

# Design philosophy

Building an automation framework that scale from the smallest Splunk test server up to 9 parallel index and search head clusters in any number of environments is a challenge of it's own. At your fingertips, this is the power you will get by using **Continuous Configuration Automation (CCA) for Splunk**

Our design principles behind the project are:
* Security Everywhere
* No hands on servers
* Make data valuable
* Sharing is caring

We base our configuration and naming standard on [Splunk Validated Architecture](https://www.splunk.com/pdfs/technical-briefs/splunk-validated-architectures.pdf) description. See [Ansible Inventory File](/templates/infrastructure_template/environments/ENVIRONMENT_NAME/hosts) for naming convention and Ansible groups layout.

# Architecture
## Prerequisites
Before you can initiate CCA for Splunk, the environments needs to fulfil some basic requirements.

### Docker - cca_for_splunk

To use the docker image for 'CCA for Splunk' by following the instruction in
[CCA for Splunk - Docker Repo](https://github.com/innovationfleet/docker).



## The Manager server
Let CCA run under a technical user e.g. `cca_manager` on the manager server and have users `sudo` to this user from their personal ones.

CCA for Splunk uses 3 repositories:
One original repo `cca_for_splunk` and two that will be automatically created first time `./cca_ctrl --setup` is executed from the within the `cca_for_splunk` repo.

All the repositories sits on the Manager server. Recommendation is to use a central git server where all Splunk configurations is stored and kept up to date the local repositories. This is a really good start for a successful and secure management of your Splunk infrastructure.

**CCA for Splunk**

Original repo that don't have any user or environment changes in it, don't need to be stored centrally. Always safe to pull the latest version from github.

**Infrastructure Repo**

The repository that holds all infrastructure configurations and the ansible hosts inventory file. This repo has user specific configuration and should be connected to a central remote repository. Secrets are stored in ansible vaults and can thus be safely store in the repo.

**Onboarding Repo**

The repository holds all data onboarding related configuration and apps. This repo has user specific configurations and apps and should be connected to a central remote repository. Secrets are stored in ansible vaults and can thus be safely store in the repo.


### Repository overview

![CCA Overview](https://github.com/innovationfleet/cca_for_splunk/blob/main/media/cca_overview.png)

- **CORE - cca_for_splunk** : This is the main repository where the core code of CCA for Splunk is stored. Treat this repository as read-only, do not store any custom playbooks or roles in this repo as that will break future updates. Custom roles and playbooks can easily be added to the below repositories in their respective `roles` and `playbooks` directory. Inclusion of the custom playbooks are automatic in `cca_ctrl`

- **Mandatory - cca_splunk_infrastructure**: This repository holds all Splunk infrastructure configurations, files and Ansible inventory information that is needed to correctly install and configure Splunk on an infrastructure server. You will also be able to import custom roles to the framework using this repository. It supports any number of environments and have pre-configured directories to manage up to 9 different index and search head clusters per environment, equipped for giant Splunk installations.

- **Mandatory - cca_splunk_onboardings**: This repository holds all Apps, Deployment Apps, Master Apps and Search Head Cluster Apps in a version controlled manner. It supports any number of environments and have pre-configured directories to manage up to 9 different index and search head cluster per environment.

- **Mandatory - cca_ctrl**: This executable is the operational centre of CCA for Splunk! We´ve developed a UI using Whiptail that is as old-school as it is well supported by basically any terminal. From cca_ctrl you instruct CCA for Splunk what to run, where and how from all from a central menu.

- **Optional - Custom Roles & Playbooks**: If you want to create your own custom Roles & Playbooks it´s easy to do so, and they will operate together with the default from within CCA for Splunk.

- **Optional - Custom Extension**: If you want to extend the functionality of CCA for Splunk to cover a completely new capability, that´s also possible - the extensions instructs custom Roles & Playbooks and gets picked up by CCA for Splunk.