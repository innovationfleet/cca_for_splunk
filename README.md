![alt text](/media/CCAforSplunk_orange.png)
<br>
<img align="right" src="https://badgen.net/badge/Latest%20Premium%20Version/2025.3.1/green?icon=github"><img align="right" src="https://badgen.net/badge/Latest%20Release/2025.3.1/green?icon=github"><img align="right" src="https://badgen.net/badge/License/MIT/blue">
<br>
### A full lifecycle management interface for Splunk

Ever wished you had a central interface to interact with all aspects of Splunk architecture and administration?
Let's be honest, running Splunk is all about finding an efficient and scalable way to manage all .conf files and the other magic under the hood. At scale, the complexity often gives way to either speed or quality - if you don't find a way to automate it.

That is precisely what we've done for years, and now it's time to share how you can do it to. Our solution enables a full lifecycle management of Splunk using a **C**ontinuous **C**onfiguration **A**utomation framework powered by Ansible.

>[!NOTE]
> This is a free read-only open-source project, a fully working but limited and unsupported version based on the full enterprise solution hence the low amount of commits in this repo. For a better overview of all improvements check out [release notes](https://github.com/innovationfleet/cca_for_splunk/blob/main/RELEASE_NOTES.txt). For enterprise use, we recommend our subscription service which includes an expanded feature set, full end user support and optional premium extensions to expand the frameworks capabilities. For subscribing customers we also offer additional services including strategic advisory, implementation- and custom feature development projects.

## Table of Contents
- [Table of Contents](#table-of-contents)
- [What is CCA for Splunk?](#what-is-cca-for-splunk)
  - [Where does CCA for come from and who supports it?](#where-does-cca-for-come-from-and-who-supports-it)
- [Commercial version of CCA for Splunk?](#commercial-version-of-cca-for-splunk)
- [Features](#features)
- [How to get started](#how-to-get-started)

## What is CCA for Splunk?
The templates that we provide for configuring Splunk roles are used in our own Multisite Cluster implementations. After you have configured your project, the control is in your hands when it comes to deciding your settings. Adding or modifying parameters has no impact on the framework and are localized under your control.

Playbooks are DRY (Don't Repeat Yourself), with almost no tasks - instead they are using common code in roles. So an update of a task has just to be done in one place, keeping code updates much cleaner and easier to overview.

You can find a more in-depth Project Presentation as well as a Q&A section in the [Wiki](https://github.com/innovationfleet/cca_for_splunk/wiki).

![alt text](https://www.orangecyberdefense.com/fileadmin/_processed_/d/8/csm_Splunk_vs_2_45d2f9bce5.png)

For a deep-dive in the technology behind CCA for Splunk please have a look at this documentation.
[Technical documentation](/documentation/TechnicalOverview.md).

### Where does CCA for come from and who supports it?

The framework concept utilized in CCA for Splunk goes back several years and has proven to be absolutely critical in managing complex Splunk infrastructures with 100+ servers in several environments. 450+ tasks has been developed across 10 carefully created Ansible roles. We continuously invest **hundreds of development hours for every release**, so that you can get the scalability that you should expect out of a automation framework.
Besides adding your servers to the ansible inventory file, there is less than 25 parameters that you have to set per environment - then off you go to much different Splunk journey going forward.

This is the free open-source version of this automation framework, a trickledown version from our premium option but with all features needed to administrate any size of Splunk environment.



## Commercial version of CCA for Splunk?
CCA for Splunk is designed to be a companion tool for Splunk administrators in any type of Enterprise. As any tool, it requires a lot of competence from the user to wield effectively. For Splunk Enterprise or Splunk Cloud customers who want to start their automation journey with CCA for Splunk with support and additional enterprise functionality, we offer a complete package of both technology and supporting services in the CCA for Splunk Premium portfolio.

Visit our [CCA for Splunk - Premium](https://www.orangecyberdefense.com/se/cca-for-splunk) page and read more about who backs this project and what else you can do with CCA for Splunk.


## Features
Open Source and Premium:
| Feature                                         | Open Source          | Premium          | Premium Extension |
| :-----------------------------------------------| :--------------------| :--------------- | :----------------- |
| Templates for Splunk validated Architectures    | :white_check_mark:   | :white_check_mark: | |
| Server naming convention for all Splunk roles    | :white_check_mark:   | :white_check_mark: | |
| Setup Wizard for environment creation            | :white_check_mark:   | :white_check_mark: | |
| Automation Readiness helper                      | :white_check_mark:   | :white_check_mark: | |
| Management of All in one Servers                 | :white_check_mark:   | :white_check_mark: | |
| Management of Data Collection Nodes              | :white_check_mark:   | :white_check_mark: | |
| Management of Deployment Servers                 | :white_check_mark:   | :white_check_mark: | |
| Management of Forwarders                         | :white_check_mark:   | :white_check_mark: | |
| Management of Hybrid Search Heads                | :white_check_mark:   | :white_check_mark: | |
| Management of Index Clusters                     | :white_check_mark:   | :white_check_mark: | |
| Management of License Managers                   | :white_check_mark:   | :white_check_mark: | |
| Management of Monitoring Consoles                | :white_check_mark:   | :white_check_mark: | |
| Management of Search Head Clusters               | :white_check_mark:   | :white_check_mark: | |
| Management of Standalone Indexers               | :white_check_mark:   | :white_check_mark: | |
| Management of Standalone Search Heads            | :white_check_mark:   | :white_check_mark: | |
| Standard Data Onboarding                         | :white_check_mark:   | :white_check_mark: | |
| App deployment to all Splunk Roles               | :white_check_mark:   | :white_check_mark: | |
| Rolling Splunk Enterprise Upgrade - Clusters     | :white_check_mark:   | :white_check_mark: | |
| Upgrade Splunk Enterprise - Standalone servers   | :white_check_mark:   | :white_check_mark: | |
| Configure Splunk to use self-signed Splunk certs | :white_check_mark:   | :white_check_mark: | |
| Deploy Manually created organization certs       | :white_check_mark:   | :white_check_mark: | |
| Linux server configuration                       | :white_check_mark:   | :white_check_mark: | |
| Splunkd service creation with non-privileged user support | :white_check_mark:   | :white_check_mark: | |
| Setup of CCA Manager                            | :white_check_mark:   | :white_check_mark: | |
| Docker image with CCA for Splunk                | :white_check_mark:   | :white_check_mark: | |
| Configure Splunk user profile                   | :white_check_mark:   | :white_check_mark: | |
| Number of supported environments                | :infinity:   | :infinity: | |
| Number of supported Index Clusters per environment | :one: | :nine: | |
| Number of supported Search Head clusters per environment | :two: | :nine: | |
| Framework Support from Orange Cyberdefense       | :heavy_minus_sign:  | :white_check_mark: | |
| Password and Secrets update in Setup Wizard      | :heavy_minus_sign:  | :white_check_mark: | |
| Management of Forwarder Groups                   | :heavy_minus_sign:  | :white_check_mark: | |
| Management of Deployment Server Groups            | :heavy_minus_sign:  | :white_check_mark: | |
| Advanced Data Onboarding                         | :heavy_minus_sign:  | :white_check_mark: | |
| Advanced App deployment to Cluster Managers      | :heavy_minus_sign:  | :white_check_mark: | |
| Advanced App deployment to Deployment Servers    | :heavy_minus_sign:  | :white_check_mark: | |
| Advanced App deployment to Search Head Clusters   | :heavy_minus_sign:  | :white_check_mark: | |
| Support for Orange Cyberdefense Extensions       | :heavy_minus_sign:  | :white_check_mark: | |
| Version control of Splunk Infrastructure changes | :heavy_minus_sign:  | :white_check_mark: | |
| Version control of Splunk Data Onboarding changes | :heavy_minus_sign:  | :white_check_mark: | |
| Framework upgrade support                        | :heavy_minus_sign:  | :white_check_mark: | |
| Framework Knowledge training                     | :heavy_minus_sign:  | :white_check_mark: | |
| Data onboarding Knowledge training                | :heavy_minus_sign:  | :white_check_mark: | |
| Access to submit issues                          | :heavy_minus_sign:  | :white_check_mark: | |
| Access to pre-released                           | :heavy_minus_sign:  | :white_check_mark: | |
| Access to development resources for custom demands | :heavy_minus_sign:  | :white_check_mark: | |
| OS Disk setup and volume groups                  | :heavy_minus_sign:  | :white_check_mark: | |
| Rolling OS upgrade with minimal disruption on Splunk ingest | :heavy_minus_sign: | :white_check_mark: | |
| Deployment of certificates retrieved by Certificate API service | :heavy_minus_sign: | :white_check_mark: | |
| Configuration of Splunk Enterprise Authentication | :heavy_minus_sign: | :white_check_mark: | |
| Cloud LCM for AWS | :heavy_minus_sign: | :heavy_minus_sign: | :white_check_mark: |
| Cloud LCM for Azure | :heavy_minus_sign: | :heavy_minus_sign: | :white_check_mark: |
| Splunk Cloud LCM | :heavy_minus_sign: | :heavy_minus_sign: | :white_check_mark: |
| Solutions for IT Serivce Intelligence | :heavy_minus_sign: | :heavy_minus_sign: | :white_check_mark: |
| Dev Ops LCM for Splunk Enterprise | :heavy_minus_sign: | :heavy_minus_sign: | :white_check_mark: |
| Dev Ops LCM for Splunk ITSI | :heavy_minus_sign: | :heavy_minus_sign: | :white_check_mark: |
| Dev Ops LCM for Splunk Cloud Platform | :heavy_minus_sign: | :heavy_minus_sign: | :white_check_mark: |
| Dev Ops LCM for Github | :heavy_minus_sign: | :heavy_minus_sign: | :white_check_mark: |



## How to get started
1: **Plan your architecture**

  - CCA for Splunk can deploy anything from standalone servers to multisite clusters, and up to 9 clusters in each environment, controlled by the same automation framework. A proper planning is key to define the type of architecture(s) that will be created, their environment, individual specifications and requirements.
  <br>

2: **Setup the CCA manager**

  - The CCA manager is the host that orchestrates and manages the automation and configuration deployment.
    There are currently two ways to deploy the manager.
      1. Use the docker image for cca_for_splunk
      2. Setup the manager on a regular host and pull CCA for Splunk.

For more in depth information check this guide: [Setup CCA Manager](/documentation/SetupCCAManager.md)
  <br>

3: **Setup your environment**<br>
  Watch the video to see the steps of setup manager before you continue.

[![cca_for_splunk Setup Wizard](https://asciinema.org/a/567633.svg)](https://asciinema.org/a/567633)
For more in depth information check this guide: [Setup CCA Manager - Environment](/documentation/SetupCCAManager.md#setup-the-environment)



4: **Update ansible inventory and variables**
For more in depth information check this guide: [Setup CCA Manager - Ansible configuration](/documentation/SetupCCAManager.md#update-ansible-inventory-files-and-variable-values)
<br>

5: **Validate your environment variables**

Before you start using CCA after an updating to a new release, run the playbook `validate_cca_infrastructure_parameters.yml` to verify that all files in your `cca_splunk_infrastructure` repo are up to date with the required versions in the CCA framework. The verification needs to run in check mode, see command below.

To run an infrastructure playbook:
```
cd ~/data/main/cca_splunk_infrastructure
./cca_ctrl -c
```
<br>

6: **Configure environment using CCA**
If you have servers that is not yet setup for Splunk Enterprise, start by running the `configure_linux_servers.yml` playbook that will prepare the server with users, services and settings to install Splunk Enterprise on it. See [README.md](/roles/cca.core.linux/README.md)
for cca.core.linux role.

When the server configuration is completed, run playbook for managing one of the architectures you want to setup.

If you are to install a multisite index and search head cluster. Start with configuring the index cluster using the playbook [manage_index_clusters.yml](/playbooks/manage_index_clusters.yml) before you run the playbook [manage_searchhead_cluster.yml](/playbooks/manage_searchhead_clusters.yml)
<br>

7: **Onboard data and apps**

Now when your Splunk infrastructure is running smooth, it's time to onboard data and apps. Follow the documentation at [cca.splunk.onboarding](/roles/cca.splunk.onboarding/README.md). When the apps and configuration are completed, run one of the deploy_* playbooks to deploy your apps to the destination server.

To run an onboarding playbook:
```
cd ~/data/main/cca_splunk_onboarding
./cca_ctrl -c
```

>[!NOTE]
> Don't forget that we offer the service to setup and support CCA for you! Please check out our premium feature. [CCA for Splunk - Premium](https://www.orangecyberdefense.com/se/cca-for-splunk)
