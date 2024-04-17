import requests
import json
import uuid
import socket
import getpass
import os
import time
import aiohttp
import asyncio
import threading
import logging, json
from logging.handlers import RotatingFileHandler

from datetime import datetime, timezone, timedelta
from os.path import basename

from ansible.plugins.callback import CallbackBase

from requests.exceptions import RequestException

from tenacity import retry, stop_after_attempt, retry_if_exception_type

#Define Collector Source to include Self URLs and Auth Token

class SplunkHTTPCollectorSource(object):
    def __init__(self):

        self.ansible_check_mode = False
        self.ansible_playbook = ""
        self.ansible_version = ""
        self.session = str(uuid.uuid4())
        self.host = socket.gethostname()
        self.ip_address = socket.gethostbyname(socket.gethostname())
        self.user = getpass.getuser()

        local_timezone_aware_datetime = datetime.now().astimezone()
        # Extract the tzinfo from this object to use for other datetime operations
        self.timezone = local_timezone_aware_datetime.tzinfo
        #self.logger.debug(self.timezone)

        # Flag to track whether send_stored_logs_elsewhere has been called
        self.sent_stored_logs = False

    def send_event(self, url, authtoken, state, result, runtime):
        if result._task_fields['args'].get('_ansible_check_mode') is True:
            self.ansible_check_mode = True

        if result._task_fields['args'].get('_ansible_version'):
            self.ansible_version = \
                result._task_fields['args'].get('_ansible_version')

        if result._task._role:
            ansible_role = str(result._task._role)
        else:
            ansible_role = None

        #Define data dictionary and involve key parameters.

        data = {}
        data['uuid'] = result._task._uuid
        data['session'] = self.session
        data['ansible_version'] = self.ansible_version
        data['ansible_check_mode'] = self.ansible_check_mode
        data['ansible_host'] = result._host.name
        data['ansible_playbook'] = self.ansible_playbook
        data['ansible_role'] = self.ansible_role
        data['ansible_task'] = result._task_fields
        data['ansible_result'] = result._result
        data['host'] = self.host
        data['ip_address'] = self.ip_address
        data['user'] = self.user
        data['runtime'] = self._runtime(result)
        data['timestamp'] = datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S.%f')
        data['state'] = self.playbook_state

class CallbackModule(CallbackBase):
    CALLBACK_NAME = 'cca_splunk'

    splunk_url = os.environ.get("CCA_SPLUNK_HEC_URL")
    splunk_token = os.environ.get("CCA_SPLUNK_HEC_TOKEN")
    updated_log_file_path = '/opt/cca_manager/updated_rescued.json'

    max_retries = 1

    def __init__(self):
        super().__init__()
        super(CallbackModule, self).__init__()

        # Logging configuration
        self.logger = logging.getLogger('cca_splunk_callback')
        self.logger.setLevel(logging.DEBUG)  # Adjust the logging level as needed

        # Path to the log file
        log_file_path = os.environ.get("CCA_SPLUNK_CALLBACK_LOG_PATH", "/opt/cca_manager/output/logs/cca_splunk_callback.log")

        # Set up a rotating file handler
        max_log_size = 10 * 1024 * 1024  # 10 MB
        backup_count = 1  # Keep only one backup file

        file_handler = RotatingFileHandler(log_file_path, maxBytes=max_log_size, backupCount=backup_count)
        # Change level to DEBUG to actually get some logs
        file_handler.setLevel(logging.DEBUG)

        # Include %(funcName)s in the formatter to display the function name
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)


        # Initialize playbook_state as "SUCCESS" by default
        self.playbook_state = "SUCCESS"

        # Initialize the SplunkHTTPCollectorSource object
        self.splunk = SplunkHTTPCollectorSource()

        # Define Constructor within CallbackModule
        self.start_datetimes = {}

        self.ansible_check_mode = ""

        # Specify the CEST timezone
        local_timezone_aware_datetime = datetime.now().astimezone()
        # Extract the tzinfo from this object to use for other datetime operations
        self.timezone = local_timezone_aware_datetime.tzinfo
        #self.logger.debug(self.timezone)

        literal_timestamp = datetime.now().astimezone()
        self.timestamp = round(literal_timestamp.timestamp(), 6)
        #self.logger.debug(self.timestamp)

        # Convert the rounded timestamp back to a datetime object
        self.rounded_datetime = datetime.fromtimestamp(self.timestamp).astimezone(literal_timestamp.tzinfo).strftime(
                        "%Y-%m-%d %H:%M:%S.%f"
                        )
        #self.logger.debug(self.rounded_datetime)
        # Get the current time in the CEST timezone

        # Initialize stored_events as an empty list
        self.stored_events = []


    def v2_playbook_on_start(self, playbook):
        self.splunk.ansible_playbook = basename(playbook._file_name)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.start_datetimes[task._uuid] = datetime.now(self.timezone)

    def v2_playbook_on_handler_task_start(self, task):
        self.start_datetimes[task._uuid] = datetime.now(self.timezone)

    @retry(stop=stop_after_attempt(1), retry=retry_if_exception_type(RequestException))
    async def send_to_splunk(self, task_result):

        start_time = time.time()  # Record start time

        headers = {
            'Authorization': f'Splunk {self.splunk_token}',
            'Content-Type': 'application/json',
        }

        response = None
        # Add A timeout of 10 seconds to prevent the session post to be hanging around.
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:

            for retry_count in range(self.max_retries):

                try:
                    self.logger.debug(f"Sending event to splunk url: {self.splunk_url}")
                    async with session.post(self.splunk_url, headers=headers, json=task_result) as response:
                    #response = requests.post(splunk_url, headers=headers, data=json.dumps(task_result), verify=True)
                        #self.logger.debug("response", response)

                        self.logger.debug(f"Response status: {response.status}")


                        # if status is not None:
                        #     # Check if the response body is not empty
                        #     # if response.content_length:
                        #     #     # Decode the response body as JSON
                        #     #     response = await response.json()
                        #     #     #self.logger.debug("response_data", response_data)
                        # self.logger.debug("status is not none...")
                        if response.status == 200:
                            end_time = time.time()  # Record end time
                            elapsed_time = end_time - start_time
                            self.logger.debug(f'Successfully sent logs to Splunk. Response: {response.status}. Time taken for send_to_splunk: {elapsed_time} seconds')
                            self._display.display(f'Successfully sent logs to Splunk. Response: {response.status}. Time taken for send_to_splunk: {elapsed_time} seconds')
                            break
                        else:
                            self.logger.debug(f'Error sending logs to Splunk (retry {retry_count + 1}). Response: {response.status}')
                            self._display.display(f'Error sending logs to Splunk (retry {retry_count + 1}). Response: {response.status}', color='red')
                            self._display.display(f'Sending logs to Splunk events storing on manager apps: Response: {response.status}', color='yellow')
                            self._store_logs_elsewhere(task_result)
                            break

                        # else:
                        #     # Handle the case when response is None
                        #     #self.logger.debug("Response is None.")
                        #     self._store_logs_elsewhere(task_result)

                except RequestException as e:
                    if retry_count < self.max_retries - 1:
                        self._display.display(f'Error sending logs to Splunk (retry {retry_count + 1}): {str(e)}', color='red')
                        self._display.display(f'Sending logs to Splunk events storing on manager apps: {str(e)}', color='yellow')
                        self._store_logs_elsewhere(task_result)
                    else:
                        #self.logger.debug(f'Max retries exceeded. Could not send logs to Splunk.')
                        self._store_logs_elsewhere(task_result)

    async def process_events(self, individual_results):

        #self.logger.debug("individual_results with process events", individual_results)
        await self.send_to_splunk(individual_results)

    def run_async_in_thread(self, coroutine_func, *args, **kwargs):
        """
        Runs the coroutine function with provided arguments in a separate thread to avoid blocking
        the main thread and conflicts with the existing event loop.
        """
        def thread_target(loop):
            self.logger.debug(f'Starting new event loop in thread for coroutine {coroutine_func.__name__}.')
            asyncio.set_event_loop(loop)
            loop.run_forever()
            self.logger.debug(f'Event loop in thread stopped for coroutine {coroutine_func.__name__}.')

        def stop_loop(loop):
            self.logger.debug(f'Stopping event loop in thread for coroutine {coroutine_func.__name__}.')
            loop.call_soon_threadsafe(loop.stop)

        new_loop = asyncio.new_event_loop()
        t = threading.Thread(target=thread_target, args=(new_loop,))
        t.start()
        self.logger.debug(f'New thread and event loop started for coroutine {coroutine_func.__name__}.')

        # Schedule the coroutine function to be run in the new loop with provided arguments
        coroutine = coroutine_func(*args, **kwargs)
        future = asyncio.run_coroutine_threadsafe(coroutine, new_loop)

        # Schedule the stop_loop function once the coroutine completes
        future.add_done_callback(lambda x: stop_loop(new_loop))

    def v2_runner_on_failed(self, result, **kwargs):
        self.run_async_in_thread(self.async_v2_runner_on_failed, result, **kwargs)

    def v2_runner_on_ok(self, result, **kwargs):
        self.run_async_in_thread(self.async_v2_runner_on_ok,result, **kwargs)

    def v2_runner_on_skipped(self, result, **kwargs):
        self.run_async_in_thread(self.async_v2_runner_on_skipped,result, **kwargs)

    def v2_runner_on_unreachable(self, result, **kwargs):
        self.run_async_in_thread(self.async_v2_runner_on_unreachable,result, **kwargs)

    async def async_v2_runner_on_ok(self, result, **kwargs):

        individual_results = []
        #current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.logger.debug("In async_runner_on_ok")

        if "results" in result._result and result._result["results"]:
            ansible_results = result._result.get("results", [])

            for individual_result in ansible_results:

                # Create a new dictionary for each individual result
                individual_task_result = {
                    "event": {
                        "ansible_timestamp": datetime.now(self.timezone).strftime(
                        "%Y-%m-%d %H:%M:%S.%f"
                        ),
                        "ansible_playbook": self.splunk.ansible_playbook,
                        "task_name": result._task.get_name(),
                        "uuid": result._task._uuid,
                        "session": self.splunk.session,
                        "ansible_tasks": result._task_fields,
                        "ansible_version": result._task_fields["args"].get("_ansible_version"),
                        "ansible_result": individual_result,
                        "ansible_role": self._ansible_roles(result),
                        "ansible_check_mode": self._checkmode(result),
                        "ansible_host": result._host.name,
                        "changed": result._result.get("changed", False),
                        "ip_address": self.splunk.ip_address,
                        "user": self.splunk.user,
                        "runtime": self._runtime(result),
                        "state": "SUCCESS",
                    },
                    "time": datetime.now(self.timezone).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                    ),
                }

                individual_results.append(individual_task_result)

                self.stored_events.extend(individual_results)

                self.modify_json_file(self.updated_log_file_path)

        else:
                # Create a new dictionary for each individual result
                task_result = {
                    "event": {
                       "ansible_timestamp": datetime.now(self.timezone).strftime(
                        "%Y-%m-%d %H:%M:%S.%f"
                        ),
                       "ansible_playbook": self.splunk.ansible_playbook,
                       "task_name": result._task.get_name(),
                        "uuid": result._task._uuid,
                        "session": self.splunk.session,
                        "ansible_tasks": result._task_fields,
                        "ansible_version": result._task_fields["args"].get("_ansible_version"),
                        "ansible_result": result._result,
                        "ansible_role": self._ansible_roles(result),
                        "ansible_check_mode": self._checkmode(result),
                        "ansible_host": result._host.name,
                        "changed": result._result.get("changed", False),
                        "ip_address": self.splunk.ip_address,
                        "user": self.splunk.user,
                        "runtime": self._runtime(result),
                        "state": "SUCCESS",
                    },
                    "time": datetime.now(self.timezone).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                    ),
                }
                individual_results.append(task_result)
                #self.logger.debug("results", individual_results)

                self.stored_events.extend(individual_results)
                self.modify_json_file(self.updated_log_file_path)

                for event in individual_results:

                    if event and event is not None:
                # Create a task to process events asynchronously
                        await self.process_events(event)
                        self.logger.debug("event within ok")
                    else:
                        await self.process_events(event)
                        self.logger.debug("event within ok with none results")


                # Check the flag before calling send_stored_logs_elsewhere
                if not self.splunk.sent_stored_logs:
                    await self.send_stored_logs_elsewhere(event)
                # Set the flag to True to indicate that the function has been called
                    self.splunk.sent_stored_logs = True

    async def async_v2_runner_on_skipped(self, result, **kwargs):

        individual_results = []

        ansible_results = result._result.get("results", [])
        self.logger.debug(f"results: {len(ansible_results)}")

        for individual_result in ansible_results:

            # Create a new dictionary for each individual result
            individual_task_result = {
                "event": {
                    "ansible_timestamp": datetime.now(self.timezone).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                    ),
                    "ansible_playbook": self.splunk.ansible_playbook,
                    "task_name": result._task.get_name(),
                    "uuid": result._task._uuid,
                    "session": self.splunk.session,
                    "ansible_tasks": result._task_fields,
                    "ansible_version": result._task_fields["args"].get("_ansible_version"),
                    "ansible_result": individual_result,
                    "ansible_role": self._ansible_roles(result),
                    "ansible_check_mode": self._checkmode(result),
                    "ansible_host": result._host.name,
                    "changed": result._result.get("changed", False),
                    "ip_address": self.splunk.ip_address,
                    "user": self.splunk.user,
                    "runtime": self._runtime(result),
                    "state": "SKIPPED",
                },
                "time": datetime.now(self.timezone).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                    ),
            }

            individual_results.append(individual_task_result)

            self.stored_events.extend(individual_results)
            self.modify_json_file(self.updated_log_file_path)

            for event in individual_results:

                if event and event is not None:
            # Create a task to process events asynchronously
                    await self.process_events(event)
                    #self.logger.debug("results", event)
                    self.logger.debug("event within skipped")

                else:
                        await self.process_events(event)
                        self.logger.debug("event within ok with none results")

            # Check the flag before calling send_stored_logs_elsewhere
            if not self.splunk.sent_stored_logs:
                await self.send_stored_logs_elsewhere(event)
            # Set the flag to True to indicate that the function has been called
                self.splunk.sent_stored_logs = True

    async def async_v2_runner_on_failed(self, result, **kwargs):

        # Process task success event and extract information
        task_result = {
            "event": {
                "ansible_playbook": self.splunk.ansible_playbook,
                "task_name": result._task.get_name(),
                "uuid": result._task._uuid,
                "session": self.splunk.session,
                "ansible_tasks": result._task_fields,
                "ansible_version": result._task_fields['args'].get('_ansible_version'),
                "ansible_result": result._result,
                "ansible_role": self._ansible_roles(result),
                "ansible_check_mode": self._checkmode(result),
                "ansible_host": result._host.name,
                "changed": result._result.get('changed', False),
                "ip_address": self.splunk.ip_address,
                "user": self.splunk.user,
                "ansible_timestamp": datetime.now(self.timezone).strftime(
                "%Y-%m-%d %H:%M:%S.%f"
                ),
                "runtime": self._runtime(result),
                "state": "FAILED",
            },
            "time": datetime.now(self.timezone).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                    ),
        }

        self.stored_events.extend(task_result)
        self.modify_json_file(self.updated_log_file_path)

            #if event and event is not None:

        await self.process_events(task_result)
        self.logger.debug("event within failed")
        # Check the flag before calling send_stored_logs_elsewhere
        if not self.splunk.sent_stored_logs:
            await self.send_stored_logs_elsewhere(task_result)
        # Set the flag to True to indicate that the function has been called
            self.splunk.sent_stored_logs = True

    async def async_v2_runner_on_unreachable(self, result, **kwargs):

        # Process task success event and extract information
        task_result = {
            "event": {
                "ansible_playbook": self.splunk.ansible_playbook,
                "task_name": result._task.get_name(),
                "uuid": result._task._uuid,
                "session": self.splunk.session,
                "ansible_tasks": result._task_fields,
                "ansible_version": result._task_fields['args'].get('_ansible_version'),
                "ansible_result": result._result,
                "ansible_role": self._ansible_roles(result),
                "ansible_check_mode": self._checkmode(result),
                "ansible_host": result._host.name,
                "changed": result._result.get('changed', False),
                "ip_address": self.splunk.ip_address,
                "user": self.splunk.user,
            #Handles seconds in timestamp
                "ansible_timestamp": datetime.now(self.timezone).strftime(
                "%Y-%m-%d %H:%M:%S.%f"
                ),
                "runtime": self._runtime(result),
                "state": "UNREACHABLE",
            },
            "time": datetime.now(self.timezone).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                    ),
        }

        self.stored_events.extend(task_result)
        self.modify_json_file(self.updated_log_file_path)

        for event in task_result:

            if event and event is not None:

                await self.process_events(event)
        # Check the flag before calling send_stored_logs_elsewhere
        if not self.splunk.sent_stored_logs:
            await self.send_stored_logs_elsewhere(event)
            # Set the flag to True to indicate that the function has been called
            self.splunk.sent_stored_logs = True

    def _runtime(self, result):
         # Get the current time as an offset-aware datetime
        current_time = datetime.now(self.timezone)
        return (
            current_time -
            self.start_datetimes[result._task._uuid]
        ).total_seconds()

    def _checkmode(self, result):
        check_mode = result._task_fields.get('check_mode', False)
        #self.logger.debug('Inside a _checkmode function:', check_mode)
        return check_mode

    def _ansible_python_version(self, result):
        _ansible_python_version = result._ansible_result['ansible_facts'].get('ansible_python_version', False)
        #self.logger.debug('Python Verson:', _ansible_python_version)
        return _ansible_python_version

    def _ansible_roles(self, result):
        ansible_roles = result._task_fields['args'].get('tasks_from')
        #self.logger.debug('Ansible roles:', ansible_roles)
        return ansible_roles

    def _store_logs_elsewhere(self):

        #Make sure file_path is defined as env_variable in .profile_local -> 'SPLUNK_HEC_RESCUE_FILEPATH'
        log_file_path = os.environ.get("SPLUNK_HEC_RESCUE_FILEPATH")
        updated_log_file_path = '/opt/cca_manager/updated_rescued.json'

        with open(log_file_path, "a") as log_file:
            json_array = [log["event"] for log in self.stored_events]
            log_file.write(json.dumps(json_array, indent=4) + "\n")
            #self.logger.debug("Logs stored as JSON array:", json_array)
            #self.logger.debug("Others stored log:", log_json)

    def modify_json_file(self, updated_log_file_path):
        try:
            # Open the input file in read mode
            with open(updated_log_file_path, 'r') as input_file:
                content = input_file.read()

            # Replace ']\n[' with ','
            content = content.replace(']\n[', ',')

            # Open the output file in write mode and write the modified content
            with open(updated_log_file_path, 'w') as output_file:
                output_file.write(content)

            #self.logger.debug(f'Modified content of {updated_log_file_path}')
        except Exception as e:
            self.logger.debug(f'Error modifying JSON file: {str(e)}')


    def send_stored_logs_elsewhere(self, result, logs):

        #log_file_path = os.environ.get("SPLUNK_HEC_RESCUE_FILEPATH")
        updated_log_file_path = '/opt/cca_manager/updated_rescued.json'

        try:
            with open(updated_log_file_path, 'r') as file:
            # Load JSON events from the file
                events = json.load(file)
                #self.logger.debug("Events from rescued file", events)

            headers = {
                'Authorization': f'Splunk {self.splunk_token}',
            }


            response = requests.post(self.splunk_url, json={"event": events}, headers=headers, verify=True)
            if response.status == 200:
                self.logger.debug(f"Event sent to Splunk from rescued json file successfully: {response.json()}")
            else:
                self.logger.debug(f"Failed to send event to Splunk. Status code: {response.status}")
        except Exception as e:
            self.logger.debug(f"Error sending events to Splunk: {str(e)}")
