
import json
import logging
import requests
import os
import sys
import socket
import getpass
import uuid
import aiohttp
import multiprocessing
import threading
from datetime import datetime, timezone
from dateutil import tz
from collections import defaultdict
from logging.handlers import RotatingFileHandler
from contextlib import contextmanager
from copy import copy


# Ansible
from ansible.plugins.callback import CallbackBase


class AnsibleJSONEncoderLocal(json.JSONEncoder):
    '''
    The class AnsibleJSONEncoder exists in Ansible core for this function
    this performs a mostly identical function via duck typing
    '''

    def default(self, o):
        '''
        Returns JSON-valid representation for special Ansible python objects
        which including vault objects and datetime objects
        '''
        if getattr(o, 'yaml_tag', None) == '!vault':
            encrypted_form = o._ciphertext
            if isinstance(encrypted_form, bytes):
                encrypted_form = encrypted_form.decode('utf-8')
            return {'__ansible_vault': encrypted_form}
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        return super().default(o)


CENSORED = "the output has been hidden due to the fact that 'no_log: true' was specified for this result"  # noqa

def current_time():
    return datetime.now(timezone.utc)


def datetime_handler(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S.%f")
    raise TypeError("Unknown type")

def convert_datetimes_in_dict(d):
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.strftime("%Y-%m-%d %H:%M:%S.%f")
        elif isinstance(v, dict):
            convert_datetimes_in_dict(v)
        elif isinstance(v, list):
            d[k] = [convert_datetimes_in_dict(item) if isinstance(item, dict) else item for item in v]
    return d


class CallbackModule(CallbackBase):
    '''
    Callback module for logging ansible/ansible-playbook events to Splunk.
    '''

    CALLBACK_NAME = 'cca_splunk'
    CALLBACK_VERSION = "1.0.0"

    # These events should never have an associated play.
    EVENTS_WITHOUT_PLAY = [
        'playbook_on_start',
        'playbook_on_stats',
    ]

    # These events should never have an associated task.
    EVENTS_WITHOUT_TASK = EVENTS_WITHOUT_PLAY + [
        'playbook_on_setup',
        'playbook_on_notify',
        'playbook_on_import_for_host',
        'playbook_on_not_import_for_host',
        'playbook_on_no_hosts_matched',
        'playbook_on_no_hosts_remaining',
    ]

    splunk_url = os.environ.get("CCA_SPLUNK_HEC_URL")
    splunk_token = os.environ.get("CCA_SPLUNK_HEC_TOKEN")
    max_retries = 1

    def __init__(self):
        super().__init__()

        # Inputs
        # Define the failed and changed event sets for easier readability
        self.failed_events = {'runner_on_failed', 'runner_on_async_failed', 'runner_item_on_failed', 'playbook_on_stats'}
        self.changed_events = {'runner_on_ok', 'runner_item_on_ok', 'playbook_on_stats'}
        self.splunk_url = os.environ.get("CCA_SPLUNK_HEC_URL")
        self.splunk_token = os.environ.get("CCA_SPLUNK_HEC_TOKEN")
        self.session = str(uuid.uuid4())
        self.host = socket.gethostname()
        self.ip_address = socket.gethostbyname(socket.gethostname())
        self.user = getpass.getuser()
        self._host_start = {}
        self.task_uuids = set()
        self.duplicate_task_counts = defaultdict(lambda: 1)
        self.play_uuids = set()
        self.duplicate_play_counts = defaultdict(lambda: 1)
        self.local_timezone = tz.tzlocal()
        self.playbook_start_time = datetime.now(self.local_timezone)
        # Logging configuration
        self.logger = logging.getLogger('cca_splunk_callback')
        self.log_level = os.environ.get("CCA_SPLUNK_CALLBACK_LOG_LEVEL", "INFO").upper()
        log_level = logging.getLevelName(self.log_level)
        self.logger.setLevel(log_level) # Adjust the logging level as needed

        # Path to the log file
        log_file_path = os.environ.get(
            "CCA_SPLUNK_CALLBACK_LOG_PATH", "/opt/cca_manager/output/logs/cca_splunk_callback.log")
        # Set up a rotating file handler
        max_log_size = 10 * 1024 * 1024  # 10 MB
        backup_count = 1  # Keep only one backup file
        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=max_log_size, backupCount=backup_count)
        file_handler.setLevel(log_level)  # Change level to DEBUG to actually get some logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        # Initialize Event Context
        self.event_context = EventContext(logger=self.logger)
        # Define Constructor within CallbackModule
        self.start_datetimes = {}
        self.ansible_check_mode = ""
        self.event_count = 0  # Initialize the event count

        # Specify the CEST timezone
        local_timezone_aware_datetime = datetime.now().astimezone()
        self.timezone = local_timezone_aware_datetime.tzinfo
        literal_timestamp = datetime.now().astimezone()
        self.timestamp = round(literal_timestamp.timestamp(), 6)
        self.rounded_datetime = datetime.fromtimestamp(self.timestamp).astimezone(literal_timestamp.tzinfo).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )



    def send_to_splunk(self, data):
        """
        Sends data to Splunk HTTP Event Collector (HEC).

        :param data: The data to be sent to Splunk.
        :param splunk_url: The Splunk HEC endpoint URL.
        :param splunk_token: The Splunk HEC token.
        :return: Response from Splunk or an error message.
        """


        headers = {
                'Authorization': f'Splunk {self.splunk_token}',
                'Content-Type': 'application/json',
            }
        
        # Increment the event count each time an event is sent to Splunk
        
        # Convert datetime fields to ISO format
        data = convert_datetimes_in_dict(data)

        try:
            json_data = json.dumps(data, cls=AnsibleJSONEncoderLocal)
            response = requests.post(self.splunk_url, data=json_data, headers=headers, timeout=10)

            # Check if the response status code indicates success
            if response.status_code == 200:
                self.event_count += 1
                self.logger.debug("Event sent to Splunk successfully")
                return False

            else:
                self.logger.debug(f"Failed to send event to Splunk: {response.status_code} - {response.text}")
                return f"Failed to send event to Splunk: {response.status_code} - {response.text}"

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Exception while sending to Splunk: {e}")
            return f"Exception while sending to Splunk: {e}"
        
    def process_host_stats(self, host, summary):
        """
        Sends host stats to Splunk.

        :param host: The name of the host.
        :param summary: The summary stats for the host.
        """
        try:
            event_data = {
                "duration": (datetime.now(self.local_timezone) - self.playbook_start_time).total_seconds(),
                "_time": datetime.now(self.local_timezone).timestamp(),
                "host": host,
                "changed": summary['changed'],
                "failed": summary['failures'],
                "ok": summary['ok'],
                "skipped": summary['skipped'],
                "unreachable": summary['unreachable'],
                "rescued": summary['rescued'],
            }

            with self.capture_event_data(event="playbook_on_host_stats", **event_data):
                pass
        except Exception as e:
            self.logger.error(f"Error in send_host_stats_to_splunk: {str(e)}")


    def extract_msg_data(self, data):
        """
        Extract stdout, msg, or stderr from result._result if available,
        otherwise return event and result._host.

        Args:
        data: The event data dictionary.

        Returns:
        str: The extracted data or a combination of event and host.
        """
        self.logger.debug("Starting extract_msg_data")

        # Function to convert dictionary to string
        def parse_to_string(item):
            if isinstance(item, dict):
                return json.dumps(item)
            return str(item)

        event = data.get('type', '')
        name = data.get('name', '')
        self.logger.debug(f"Event type: {event}")

        try:
            if 'res' in data:
                res = data['res']
                self.logger.debug(f"Processing res: {res}")
                host_name = data.get('host', 'unknown')  # Access host as string directly
                if 'stderr' in res:
                    return f"{event} - {host_name} - error {parse_to_string(res['stderr'])}"
                elif 'stdout' in res:
                    return f"{event} - {host_name} - stdout {parse_to_string(res['stdout'])}"
                elif 'msg' in res:
                    if event == "ok" and "changed" in res:
                        changed = parse_to_string(res['changed'])
                        return f"{event} - {host_name} - changed {changed} msg {parse_to_string(res['msg'])}"
                    else:
                        return f"{event} - {host_name} - msg {parse_to_string(res['msg'])}"
                elif "skip_reason" in res:
                    reason = res.get('skip_reason', "skipped")
                    return f"{event} - {host_name} - skip_reason {parse_to_string(reason)}"
                elif 'item' in res:
                    item = res.get('item', "")
                    return f"{event} - {host_name} - items {parse_to_string(item)}"
            else:
                self.logger.debug("No 'res' field in data")

            host_name = data.get('host', None)  # Access host as string directly
            task = data.get('task', '')
            if name:
                return f"{event} - {parse_to_string(name)}"
            elif 'task' in data:
                if host_name:
                    return f"{event} - {host_name} - {parse_to_string(task)}"
                else:
                    return f"{event} - {parse_to_string(task)}"
            elif event == 'stats':
                return f"{event} - summary"


            return f"{event} - {host_name}"
        except Exception as e:
            self.logger.error(f"Error in extract_msg_data: {e}")
            return f"{event} - error extracting message"

    @contextmanager
    def capture_event_data(self, event, **event_data):
        if self.log_level == "INFO":
            # Check if the event should be processed based on INFO log level criteria
            res = event_data.get('res')
            should_process_event_data = (
                event in ('runner_on_failed', 'runner_on_async_failed', 'runner_item_on_failed', 'playbook_on_stats','playbook_on_host_stats', 'playbook_on_start') or
                (event in ('runner_on_ok', 'runner_item_on_ok') and res is not None and res.get('changed', False))
            )
        else:
            # Process all events if log level is not INFO
            should_process_event_data = True


        if not should_process_event_data:
            self.logger.info(f"Skipping event: {event} as only including failed events")
            yield
            return

        self.logger.debug(f"capturing event data: {event_data} for context {event}")
        global_ctx = self.event_context.get_global()
        self.logger.debug(f"Global context {global_ctx}")
        event_data.setdefault('uuid', str(uuid.uuid4()))
        if event not in self.EVENTS_WITHOUT_TASK:
            task = event_data.pop('task', None)
        else:
            task = None

        #set global fields
        event_data['session'] = self.session
        event_data['user'] = self.user


        if event_data.get('type', None):
            event_data['custom_msg'] = self.extract_msg_data(event_data)

        if event_data.get('res'):
            if event_data['res'].get('_ansible_no_log', False):
                event_data['res'] = {'censored': CENSORED}
            if event_data['res'].get('results', []):
                event_data['res']['results'] = copy(event_data['res']['results'])
            for i, item in enumerate(event_data['res'].get('results', [])):
                if isinstance(item, dict) and item.get('_ansible_no_log', False):
                    event_data['res']['results'][i] = {'censored': CENSORED}

        self.logger.debug(f"processed event data: {event_data} for context {event}")


        with event_context.display_lock:
            try:
                self.event_context.add_local(event=event, **event_data)
                if task:
                    self.set_task(task, local=True)
                event_data_obj = self.event_context.dump_begin(sys.stdout)
                self.logger.debug(f"capture: data to send: {event_data_obj}")
                response = self.send_to_splunk(event_data_obj)
                if response:
                    self._display.display(f"{response} for {event}")
                if event=="playbook_on_stats":
                    self._display.display(f"{self.event_count} events sent to splunk for session {self.session}")
                yield
            finally:
                if task:
                    self.clear_task(local=True)
                self.event_context.remove_local(event=None, **event_data)

    def v2_playbook_on_start(self, playbook):
        self.set_playbook(playbook)
        event_data = dict(uuid=self.playbook_uuid)

        event_data['type'] = "start"
        with self.capture_event_data(event="playbook_on_start", **event_data):
            pass


    def v2_playbook_on_play_start(self, play):
        play_uuid = str(play._uuid)
        if play_uuid in self.play_uuids:
            self.duplicate_play_counts[play_uuid] += 1
            play_uuid = '_'.join([play_uuid, str(self.duplicate_play_counts[play_uuid])])
        self.play_uuids.add(play_uuid)
        play._uuid = play_uuid

        self.set_play(play)
        if hasattr(play, 'hosts'):
            if isinstance(play.hosts, list):
                pattern = ','.join(play.hosts)
            else:
                pattern = play.hosts
        else:
            pattern = ''
        name = play.get_name().strip() or pattern

        event_data = dict(name=name, pattern=pattern, uuid=str(play._uuid))
        event_data['type'] = "start play"
        with self.capture_event_data(event="playbook_on_play_start", **event_data):
            pass

    def v2_playbook_on_task_start(self, task, is_conditional):
        task_uuid = str(task._uuid)
        if task_uuid in self.task_uuids:
            self.duplicate_task_counts[task_uuid] += 1
            task_uuid = '_'.join([task_uuid, str(self.duplicate_task_counts[task_uuid])])
        self.task_uuids.add(task_uuid)
        self.set_task(task)
        event_data = dict(task=task, name=task.get_name(), is_conditional=is_conditional, uuid=task_uuid)
        event_data['type'] = "start task"
        with self.capture_event_data(event="playbook_on_task_start", **event_data):
            pass
        self.start_datetimes[task._uuid] = datetime.now(self.timezone)

    def v2_playbook_on_handler_task_start(self, task):
        self.start_datetimes[task._uuid] = datetime.now(self.timezone)
        self.set_task(task)
        event_data = dict(
            task=task,
            name=task.get_name(),
            uuid=str(task._uuid),
            is_conditional=True,
            type="start handler"
        )
        with self.capture_event_data(event="playbook_on_handler_task_start", **event_data):
            pass

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host_start, end_time, duration = self._get_result_timing_data(result)
        event_data = dict(
            host=result._host.get_name(),
            remote_addr=result._host.address,
            res=result._result,
            task=result._task,
            start=host_start,
            end=end_time,
            duration=duration,
            ignore_errors=ignore_errors,
            event_loop=self._get_event_loop(result._task),
            type="failed"
        )

        with self.capture_event_data(event="runner_on_failed", **event_data):
            pass

    def v2_runner_on_ok(self, result, **kwargs):
        if result._task.action in ('setup', 'gather_facts'):
            result._result.get('ansible_facts', {}).pop('ansible_env', None)

        host_start, end_time, duration = self._get_result_timing_data(result)

        event_data = dict(
            host=result._host.get_name(),
            remote_addr=result._host.address,
            task=result._task,
            res=result._result,
            start=host_start,
            end=end_time,
            duration=duration,
            event_loop=self._get_event_loop(result._task),
            type="ok",
        )
        with self.capture_event_data(event="runner_on_ok", **event_data):
            pass

    def v2_runner_on_skipped(self, result, **kwargs):
        self.logger.debug("received skipped event")
        host_start, end_time, duration = self._get_result_timing_data(result)
        event_data = dict(
            host=result._host.get_name(),
            remote_addr=result._host.address,
            task=result._task,
            start=host_start,
            end=end_time,
            duration=duration,
            event_loop=self._get_event_loop(result._task),
            type="skipped",
        )
        with self.capture_event_data('runner_on_skipped', **event_data):
            super().v2_runner_on_skipped(result)

    def v2_runner_on_unreachable(self, result, **kwargs):
        host_start, end_time, duration = self._get_result_timing_data(result)
        event_data = dict(
            host=result._host.get_name(),
            remote_addr=result._host.address,
            task=result._task,
            start=host_start,
            end=end_time,
            duration=duration,
            res=result._result,
            type="unreachable",
        )
        with self.capture_event_data(event="runner_on_unreachable", **event_data):
            pass

    def v2_playbook_on_no_hosts_matched(self):
        event_data = dict(type="no hosts matched")
        with self.capture_event_data(event="runner_on_no_hosts_matched", **event_data):
            pass

    def v2_playbook_on_no_hosts_remaining(self):
        event_data = dict(type="no hosts remaining")
        with self.capture_event_data(event="runner_on_no_hosts_remaining", **event_data):
            pass
    def v2_runner_item_on_ok(self, result):
        host_start, end_time, duration = self._get_result_timing_data(result)

        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            res=result._result,
            start=host_start,
            end=end_time,
            duration=duration,
            type="ok"
        )
        with self.capture_event_data(event="runner_item_on_ok", **event_data):
            pass

    def v2_runner_item_on_failed(self, result):
        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            res=result._result,
            type="failed",
        )
        with self.capture_event_data(event="runner_item_on_failed", **event_data):
            pass

    def v2_runner_item_on_skipped(self, result):
        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            res=result._result,
            type="skipped",
        )
        with self.capture_event_data(event="runner_item_on_skipped", **event_data):
            pass

    def v2_runner_retry(self, result):

        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            res=result._result,
            type="retry",
        )
        with self.capture_event_data(event="playbook_on_task_start", **event_data):
            pass

    def v2_runner_on_start(self, host, task):

        event_data = dict(
            host=host.get_name(),
            task=task,
            type="start",
        )
        self._host_start[host.get_name()] = current_time()
        with self.capture_event_data(event="runner_on_start", **event_data):
            super()

    def v2_playbook_on_notify(self, handler, host):
        # NOTE: Not used by Ansible < 2.5.
        event_data = {
            'host': host.get_name(),
            'handler': handler.get_name(),
            'type': 'playbook on notify',
        }
        with self.capture_event_data(event="runner_on_start", **event_data):
            pass


    def v2_playbook_on_stats(self, stats, **kwargs):
        try:
            self.logger.debug("Received playbook_on_stats event")
            self.clear_play()

            total_stats = {
                'total_ok': 0,
                'total_changed': 0,
                'total_unreachable': 0,
                'total_failures': 0,
                'total_skipped': 0,
                'total_processed': 0,
                'total_rescued': 0,
            }
            event_data = {
                'skipped': {},
                'ok': {},
                'changed': {},
                'unreachable': {},
                'failures': {},
                'ignored': {},
                'rescued': {},
                'processed': stats.processed,
                "artifact_data": stats.custom.get('_run', {}) if hasattr(stats, 'custom') else {},
                "type": "stats",
            }
            processed_hosts = 0
            hosts = sorted(stats.processed.keys())
            for host in hosts:
                summary = stats.summarize(host)
                processed_hosts += 1
                event_data['ok'][host] = summary['ok']
                event_data['changed'][host] = summary['changed']
                event_data['unreachable'][host] = summary['unreachable']
                event_data['failures'][host] = summary['failures']
                event_data['skipped'][host] = summary['skipped']
                event_data['rescued'][host] = summary['rescued']

                total_stats['total_ok'] += summary['ok']
                total_stats['total_changed'] += summary['changed']
                total_stats['total_unreachable'] += summary['unreachable']
                total_stats['total_failures'] += summary['failures']
                total_stats['total_skipped'] += summary['skipped']
                total_stats['total_rescued'] += summary['rescued']
                
                # Send stats for each host to Splunk
                self.process_host_stats(host, summary)
                

            event_data['ok']['total'] = total_stats['total_ok']
            event_data['changed']['total'] = total_stats['total_changed']
            event_data['unreachable']['total'] = total_stats['total_unreachable']
            event_data['failures']['total'] = total_stats['total_failures']
            event_data['skipped']['total'] = total_stats['total_skipped']
            event_data['rescued']['total'] = total_stats['total_rescued']
            event_data['processed_hosts'] = processed_hosts
            duration = (current_time() - self.playbook_start_time).total_seconds()
            event_data['duration'] = duration
            event_data['start_time'] = self.playbook_start_time.timestamp()
            event_data['end_time'] = datetime.now(self.local_timezone).timestamp()

            with self.capture_event_data('playbook_on_stats', **event_data):
                super().v2_playbook_on_stats(stats)

        except Exception as e:
            self.logger.error(f"Error in v2_playbook_on_stats: {str(e)}")

    def _get_result_timing_data(self, result):
        host_start = self._host_start.get(result._host.get_name())
        if host_start:
            end_time = current_time()
            return host_start, end_time, (end_time - host_start).total_seconds()
        return None, None, None

    def set_playbook(self, playbook):
        self.playbook_uuid = str(uuid.uuid4())
        self.playbook_start_time = datetime.now(self.local_timezone)
        file_name = getattr(playbook, '_file_name', '???')
        # Extract the base name (file name with extension) from the full path
        base_name = os.path.basename(file_name)
        # Remove the file extension to get the playbook name
        playbook_name = os.path.splitext(base_name)[0]
        command =  ' '.join(sys.argv)
            # Check if sys.argv[3] exists and process it
            
        # Set default env values
        environment = "unknown"
        repo_type = "main"
        
        # Check if sys.argv[3] exists and process it
        if len(sys.argv) > 3:
            environment = sys.argv[3]
            if '/' in environment:
                try:
                    repo_type_candidate = environment.split('/')[-3]
                    environment_candidate = environment.split('/')[-1]
                    # Ensure the values are not None
                    if repo_type_candidate:
                        repo_type = repo_type_candidate
                    if environment_candidate:
                        environment = environment_candidate
                except IndexError:
                    pass  # Fallback to default values if there is an IndexError
                
        # Add global context
        self.event_context.add_global(
            playbook=file_name,
            playbook_name=playbook_name,
            playbook_uuid=self.playbook_uuid,
            command=command,
            environment=environment,
            repo_type=repo_type
        )

        self.clear_play()

    def set_play(self, play):
        if hasattr(play, 'hosts'):
            if isinstance(play.hosts, list):
                pattern = ','.join(play.hosts)
            else:
                pattern = play.hosts
        else:
            pattern = ''
        name = play.get_name().strip() or pattern
        self.event_context.add_global(play=name, play_uuid=str(play._uuid), play_pattern=pattern)
        self.clear_task()

    def clear_play(self):
        self.event_context.remove_global(play=None, play_uuid=None, play_pattern=None)
        self.clear_task()

    def set_task(self, task, local=False):
        self.clear_task(local)
        task_ctx = dict(
            task=(task.name or task.action),
            task_uuid=str(task._uuid),
            task_action=task.action,
            task_args='',
        )
        try:
            task_ctx['task_path'] = task.get_path()
        except AttributeError:
            pass

        if task.no_log:
            task_ctx['task_args'] = "the output has been hidden due to the fact that 'no_log: true' was specified for this result"
        else:
            task_args = ', '.join(('%s=%s' % a for a in task.args.items()))
            task_ctx['task_args'] = task_args
        if getattr(task, '_role', None):
            task_role = task._role._role_name
        else:
            task_role = getattr(task, 'role_name', '')
        if task_role:
            task_ctx['role'] = task_role
        if local:
            self.event_context.add_local(**task_ctx)
        else:
            self.event_context.add_global(**task_ctx)

    def clear_task(self, local=False):
        task_ctx = dict(task=None, task_path=None, task_uuid=None, task_action=None, task_args=None, role=None)
        if local:
            self.event_context.remove_local(**task_ctx)
        else:
            self.event_context.remove_global(**task_ctx)

    @staticmethod
    def _get_event_loop(task):
        if hasattr(task, 'loop_with'):
            return task.loop_with
        elif hasattr(task, 'loop'):
            return task.loop
        return None

    def _runtime(self, result):
        current_time = datetime.now(self.timezone)
        return (
            current_time -
            self.start_datetimes[result._task._uuid]
        ).total_seconds()

    def _checkmode(self, result):
        check_mode = result._task_fields.get('check_mode', False)
        return check_mode

    def _ansible_python_version(self, result):
        _ansible_python_version = result._ansible_result['ansible_facts'].get(
            'ansible_python_version', False)
        return _ansible_python_version

    def _ansible_roles(self, result):
        ansible_roles = result._task_fields['args'].get('tasks_from')
        return ansible_roles

class EventContext(object):
    '''
    Store global and local (per thread/process) data associated with callback
    events and other display output methods.
    '''

    def __init__(self, logger=None):
        self.display_lock = multiprocessing.RLock()
        self._global_ctx = {}
        self._local = threading.local()
        self.splunk_url = os.environ.get("CCA_SPLUNK_HEC_URL")
        self.splunk_token = os.environ.get("CCA_SPLUNK_HEC_TOKEN")
        self.logger = logger or logging.getLogger(__name__)

    def add_local(self, **kwargs):
        self.logger.debug(f"adding local kwargs {kwargs}")
        tls = vars(self._local)
        ctx = tls.setdefault('_ctx', {})
        ctx.update(kwargs)

    def remove_local(self, **kwargs):
        for key in kwargs.keys():
            self._local._ctx.pop(key, None)

    @contextmanager
    async def set_local(self, **kwargs):
        try:
            # context = dict(verbose=True, vebosity=4, **kwargs)
            await self.add_local(**kwargs)
            yield
        finally:
            await self.remove_local(**kwargs)

    def get_local(self):
        return getattr(getattr(self, '_local', None), '_ctx', {})

    def add_global(self, **kwargs):
        self.logger.debug(f"adding global kwargs {kwargs}")
        if not hasattr(self, '_global_ctx'):
            self._global_ctx = {}
        self._global_ctx.update(kwargs)

    def remove_global(self, **kwargs):
        self.logger.debug(f"remove global kwargs {kwargs}")
        if hasattr(self, '_global_ctx'):
            for key in kwargs.keys():
                self._global_ctx.pop(key, None)

    @contextmanager
    def set_global(self, **kwargs):
        try:
            self.add_global(**kwargs)
            yield
        finally:
            self.remove_global(**kwargs)

    def get_global(self):
        return getattr(self, '_global_ctx', {})

    def get(self):
        ctx = {}
        ctx.update(self.get_global())
        ctx.update(self.get_local())
        self.logger.debug(f"get ctx {ctx}")
        return ctx

    def get_begin_dict(self):
        event_data = self.get()
        event = event_data.pop('event', None)
        if not event:
            event = 'verbose'
            for key in ('debug', 'verbose', 'deprecated', 'warning', 'system_warning', 'error'):
                if event_data.get(key, False):
                    event = key
                    break
        event_dict = dict(event=event)
        event_dict['pid'] = event_data.pop('pid', os.getpid())
        event_dict['uuid'] = event_data.pop('uuid', str(uuid.uuid4()))
        event_dict['_time'] = event_data.get('created', current_time().isoformat())
        event_dict['session'] = event_data.pop('session', '')
        event_dict['user'] = event_data.pop('user', '')
        event_dict['stdout'] = event_data.pop('custom_msg', '')
        event_dict['playbook'] = event_data.pop('playbook', '')
        event_dict['playbook_name'] = event_data.pop('playbook_name', '')
        global_ctx = self.get_global()
        if 'environment' in global_ctx:
            event_dict['environment'] = global_ctx['environment']
        if 'repo_type' in global_ctx:
            event_dict['repo_type'] = global_ctx['repo_type']

        event_data.pop('repo_type', None)
        event_data.pop('environment', None)

        if not event_data.get('parent_uuid', None):
            for key in ('task_uuid', 'play_uuid', 'playbook_uuid'):
                parent_uuid = event_data.get(key, None)
                if parent_uuid and parent_uuid != event_data.get('uuid', None):
                    event_dict['parent_uuid'] = parent_uuid
                    break
        else:
            event_dict['parent_uuid'] = event_data.get('parent_uuid', None)
        if "verbosity" in event_data.keys():
            event_dict["verbosity"] = event_data.pop("verbosity")
        event_dict['event_data'] = event_data
        return event_dict

    def get_end_dict(self):
        return {}

    def dump(self, fileobj, data, max_width=78, flush=False):
        pass

    def dump_begin(self, fileobj):
        begin_dict = self.get_begin_dict()
        return begin_dict

    def dump_end(self, fileobj):
        self.dump(fileobj, self.get_end_dict(), flush=True)

event_context = EventContext()