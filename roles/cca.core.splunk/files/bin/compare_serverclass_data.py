import json
import sys
import os

def compare_serverclass_data(local_file, remote_file):
    with open(local_file) as f_local, open(remote_file) as f_remote:
        local_data = json.load(f_local)
        remote_data = json.load(f_remote)

    deleted = {k: v for k, v in remote_data.items() if k not in local_data}
    added = {k: v for k, v in local_data.items() if k not in remote_data}
    modified = set()

    # Identify modified sections
    for key in local_data:
        if key in remote_data:
            if local_data[key] != remote_data[key]:
                main_key = key.split(':')[1]
                modified.add(main_key)

    # Ensure deleted items are not incorrectly marked as modified
    for key in deleted:

        # Skip global stanza in Splunk
        if key == 'global':
            continue
        main_key = key.split(':')[1]
        if main_key in modified:
            modified.remove(main_key)

    # Filter out deleted and added items if their main serverClass is modified
    filtered_deleted = {
        k: v for k, v in deleted.items()
        if ':' in k and k.split(':')[1] not in modified
    }

    filtered_added = {
        k: v for k, v in added.items()
        if ':' in k and k.split(':')[1] not in modified
    }

    result = {
        "Added": filtered_added,
        "Deleted": filtered_deleted,
        "Modified": list(modified)
    }

    print(json.dumps(result, indent=4))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_serverclass_data.py <local_file> <remote_file>")
        sys.exit(1)

    local_file = sys.argv[1]
    remote_file = sys.argv[2]

    if not os.path.exists(local_file) or not os.path.exists(remote_file):
        print("One or both of the files do not exist.")
        sys.exit(1)

    compare_serverclass_data(local_file, remote_file)
