# Apps

Customer apps that have environment specific information in them are
stored in `ONBOARDING_REPO/splunk/etc/apps/selectable/`. Here
the `name:` and `source_app:` values are usually the same.

Versioned apps, typically splunkbase apps, are stored with version
information in `ONBOARDING_REPO/splunk/etc/apps/versioned`.

For versioned apps the prefix `appFile-` and suffix `vX.Y.Z` shall be
removed when specifying the app name variable.

Always use the full name of app in the `source_app:` variable.

## Optional parameters:

```
target: 'INVENTORY_HOSTNAME'
```

When a target option is added to a app, the app will be deployed only when a matching host `INVENTORY_HOSTNAME` is found in the play. Only a single target can be specified. To address multiple hosts, repeat the app configuration with unique targets.

```
rsync_opts:
   - "--include=DIR1/FILENAME1"
   - "--exclude=DIR1/*"
   - "--exclude=DIR2/*"
   - "--exclude=FILENAME2"
```

Standard rsync arguments applies, `rsync_opts` defined here are merged with default `rsync_opts` from `group_vars/all/onboarding`

```
dest_dir: 'manager-apps|master-apps|shcluster/apps|deployment-apps'
```

Apps will be installed in SPLUNK_HOME/etc/apps by default. If needed override by specifying dest_dir variable and set it to either of `manager-apps|master-apps|shcluster/apps|deployment-apps`


## Example app configuration
```
selected_apps:
  - name: 'splunk_httpinput'
    source_app: 'innovationfleet-splunk_httpinput'
    state: 'present'
    rsync_opts:
      - "--exclude=default"

versioned_apps:
  - name: 'splunk_app_db_connect'
    source_app: 'appFile-splunk_app_db_connect_v370'
    state: 'present'
    target: 'PREFIX-spl-fwd-101'
    rsync_opts:
      - "--include=local/db_connection_types.conf"
      - "--include=local/dbx_settings.conf"
      - "--exclude=local/*"
      - "--exclude=secret/*"
      - "--exclude=certs/identity.dat"
      - "--exclude=keystore"
      - "--exclude=customized.java.path"
```

# Deployment Server Apps

For deployment servers, all apps located in `deployment-apps/ENVIRONMENT_NAME/ will be included in the deployment towards the deployment sever. Additional selected deployment-apps can be specified.
```
selected_deployment_apps:
  - name: 'innovationfleet_lab_outputs_conf'
    source_app: 'innovationfleet_lab_outputs_conf'
    state: 'present'
```

# Cluster Manager Apps

For cluster manager apps, all apps located in `manager-apps/ENVIRONMENT_NAME/cluster_ID` will be included in the deployment towards the cluster manager. Additional selected manager-apps can be specified.
```
selected_manager_apps:
  - name: 'innovationfleet_props_conf'
    source_app: 'innovationfleet_props_conf'
    state: 'present'
```

# Search Head Cluster Apps

For shcluster apps, all apps located in `shcluster/ENVIRONMENT_NAME/shcluster_ID/apps` will be included in the deployment towards the search head deployer. Additional selected shcluster apps can be specified.

```
selected_shcluster_apps:
  - name: 'innovationfleet-sh_landing_page'
    source_app: 'innovationfleet-sh_landing_page'
    state: 'present'
```