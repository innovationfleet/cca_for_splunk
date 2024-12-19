# Callback Module for Logging Ansible Events to Splunk

This repository contains a callback module for logging Ansible playbook events to Splunk. The callback module captures detailed event data during the execution of playbooks and sends this data to Splunk for analysis and monitoring.

## Features

- Logs Ansible playbook events to Splunk HTTP Event Collector (HEC).
- Handles special Ansible Python objects and datetime objects for JSON serialization.
- Configurable logging level and log file path with a rotating file handler.
- Extracts and formats event messages for easier readability.
- Supports capturing both global and local event context.
- Uses environment variables for configuration.

## Requirements

- Ansible
- Python 3.x
- Required Python packages: `requests`, `aiohttp`, `dateutil`

## Dependencies
This Callback is dependent on the selectable splunk apps: 
- cca_insights_app: For dashboard and macro definition
- cca_insights_hec: HEC Input setup
- cca_insights_hec_indexes: for callback index definition. 

## Environment Variables

The following environment variables are used for configuring the callback module:

- `CALLBACK_HEC_URL`: The Splunk HTTP Event Collector (HEC) endpoint URL. Use the `/services/collector/raw` endpoint
- `CALLBACK_HEC_TOKEN`: The Splunk HEC token.
- `CALLBACK_VERBOSITY`: Defaults to 1, will only log failed, changed and stats events to splunk, value above 1 will send all event to callback url
- `CALLBACK_LOG_PATH`: The path to the internal callback log file (default is `/opt/cca_manager/output/logs/cca_splunk_callback.log`).
- `CALLBACK_SSL_VERIFY`: Determines whether to use verified SSL requests or not. (default is `True`).
## Usage

1. Set up the required environment variables:

   ```sh
   export CALLBACK_HEC_URL="https://splunk-server:8088/services/collector/raw"
   export CALLBACK_HEC_TOKEN="your_splunk_hec_token"
   export CALLBACK_LOG_PATH="/path/to/log/file.log"
   ```

2. Run your Ansible playbook as usual. The callback module will log events to Splunk.

## Code Overview

### `AnsibleJSONEncoderLocal` Class

This class extends `json.JSONEncoder` to handle special Ansible Python objects, including vault objects and datetime objects.

### `CallbackModule` Class

This class extends `CallbackBase` and implements various callback methods to capture and log Ansible events.

#### Key Methods

- `send_to_splunk(data)`: Sends the captured event data to Splunk.
- `extract_msg_data(data)`: Extracts relevant message data from the event.
- `capture_event_data(event, **event_data)`: Context manager for capturing event data.
- Various `v2_` prefixed methods to handle specific Ansible events like `v2_playbook_on_start`, `v2_runner_on_ok`, etc.

### `EventContext` Class

This class manages the global and local context for events, ensuring thread-safety and providing utility methods for adding, removing, and retrieving context data.

## Logging Configuration

The callback module uses the `logging` library to log event data. The log level and log file path are configurable via environment variables. A rotating file handler is set up to manage log files, with a default maximum size of 10 MB and one backup file.

## Example

```sh
# Example of setting environment variables and running an Ansible playbook
export CALLBACK_HEC_URL="https://splunk-server:8088/services/collector/raw"
export CALLBACK_HEC_TOKEN="your_splunk_hec_token"
export CALLBACK_LOG_LEVEL="DEBUG"
export CALLBACK_LOG_PATH="/path/to/log/file.log"
export ANSIBLE_CALLBACK_PLUGINS="/opt/cca_manager/main/cca_for_splunk-premium/callback_plugins"
export ANSIBLE_CALLBACKS_ENABLED="ansible.posix.profile_tasks"

```

### Changing Verbosity
If you would like to send all output events from playbooks to Splunk, you need to change the verbosity accordingly
```sh
# Example of setting callback verbosity to send all data to Splunk. anything above 1 will send all events. please make sure that the value is an number.
export CALLBACK_VERBOSITY="2"
```

# Now run your Ansible playbook using


Using CCA control `./cca_control`
Default ansible:  `ansible-playbook your_playbook.yml`

# Dependent selectable Apps Configuration to view insights in Splunk SH

## cca_insights_app
- **Purpose**: Dashboard app to view CCA ansible playbook insights
- **Target Group**:
  - searchhead_deployer_shcluster_c1
  - searchhead_deployer_shcluster_c2
  - standalone_searchhead

## cca_insights_hec
- **Purpose**: TA for parsing CCA callback HEC events
- **Target Group**:
  - cluster_manager_cluster_c1
