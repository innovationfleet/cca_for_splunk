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

## Environment Variables

The following environment variables are used for configuring the callback module:

- `CCA_SPLUNK_HEC_URL`: The Splunk HTTP Event Collector (HEC) endpoint URL. Use the `/services/collector/event` endpoint
- `CCA_SPLUNK_HEC_TOKEN`: The Splunk HEC token.
- `CCA_SPLUNK_CALLBACK_ONLY_FAILED_EVENTS`: Set to `true` to log only failed events (default is `false`).
- `CCA_SPLUNK_CALLBACK_LOG_PATH`: The path to the internal callback log file (default is `/opt/cca_manager/output/logs/cca_splunk_callback.log`).

## Usage

1. Set up the required environment variables:

    ```sh
    export CCA_SPLUNK_HEC_URL="https://splunk-server:8088/services/collector/event"
    export CCA_SPLUNK_HEC_TOKEN="your_splunk_hec_token"
    export CCA_SPLUNK_CALLBACK_LOG_PATH="/path/to/log/file.log"
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

```python
# Example of setting environment variables and running an Ansible playbook
import os

os.environ['CCA_SPLUNK_HEC_URL'] = "https://splunk-server:8088/services/collector/event"
os.environ['CCA_SPLUNK_HEC_TOKEN'] = "your_splunk_hec_token"
os.environ['CCA_SPLUNK_CALLBACK_LOG_LEVEL'] = "DEBUG"
os.environ['CCA_SPLUNK_CALLBACK_LOG_PATH'] = "/path/to/log/file.log"

```
# Now run your Ansible playbook using
Using CCA control `./cca_control`
Default ansible:  `ansible-playbook your_playbook.yml`
