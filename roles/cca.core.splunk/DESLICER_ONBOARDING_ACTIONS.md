# Deslicer Automation Platform – Onboarding / Deployment Actions

This document describes the **action** steps from `roles/cca.core.splunk/tasks` that the Deslicer Automation Platform (rust Worker Node) must perform after file/ini updates to deploy onboarding changes: Splunk restart, status checks, bundle push, deploy server reload, and related steps.

**No state files.** The platform is aware of all changes before they happen and can calculate all required actions from the set of changed paths and host roles. Actions are determined purely by **what changed** and **which hosts** are affected.

For each step: **when/why** it runs (change-based), **commands and arguments** to execute, **variables** used, and **expected result** (return codes and stdout/stderr strings to check, as used by the Ansible tasks).

---

## 1. Calculating actions from changes

Before applying updates, compute which actions to run from the **changed paths** and **host inventory** (see `filter_plugins/splunk_config_changes.py` for the same logic).

**Path → action mapping (per host / role):**

| Changed path pattern | Action(s) to run | Where |
|---------------------|------------------|--------|
| `etc/` but **not** `deployment-apps`, `shcluster`, `master-apps`, `manager-apps` | **Splunkd restart** (or rolling restart for cluster/SHC) | Affected host(s); see below for cluster vs standalone |
| `deployment-apps` | **Deployment server reload** (or restart if too many serverclasses) | Deployment server host(s) |
| `shcluster` | **Apply SHC bundle** | Search head deployer for that SHC |
| `master-apps` or `manager-apps` | **Apply cluster bundle** (+ optionally **rolling restart cluster-peers** if validate says restart required) | Cluster manager for that cluster |

**Restart variant by host type:**

- **Standalone / non-cluster, non-SHC:** Run **restart Splunkd** (§5) on that host.
- **Cluster peer (indexer):** Run **rolling restart cluster-peers** (§11) on the **cluster manager** for that cluster (one action per cluster that had core/config changes on its peers).
- **SHC member:** Run **rolling restart shcluster-members** (§13) on the SHC members of that deployer (or **restart Splunkd** if `force_splunkd_restart` is set).

**Deployment server:** If deployment-apps changed on a deployment server host, run **reload deploy-server** (§8). If the number of serverclasses to reload exceeds `cca_max_reload_serverclass_items` (default 50), use **restart Splunkd** (§5) instead of reload.

Use the computed action set to drive the apply plan; no pending files are read or written.

---

## 2. Splunk status check

**When:** Before any action that needs a running Splunk (login, reload, bundle push, restart verification). Also after restart to confirm splunkd is up.

**Why:** Ensures Splunk is running and accepts CLI commands.

**Command:**

```bash
timeout {{ cca_splunk_command_timeout | default('60') }} {{ splunk_path }}/bin/splunk status [--accept-license --answer-yes --no-prompt]
```

**Variables:**

- `splunk_path` — default `"/opt/splunk"`
- `cca_splunk_command_timeout` — default `60`
- Optional: `--accept-license --answer-yes --no-prompt` for non-interactive

**Retries:** `cca_splunkd_status_retries` (default `10`), delay `10` s.

**Expected result (check):**
- **Return code:** `0` (success).
- **Stdout:** must match regex `splunkd is running` (confirms daemon is up). Retry until both rc and stdout pass.

**Skip:** When `skip_splunk_status_check` is true.

---

## 3. Splunk CLI login

**When:** Before any CLI operation that requires an authenticated session (reload deploy-server, apply cluster-bundle, apply shcluster-bundle, preflight, rolling-restart, transfer captain, maintenance-mode).

**Why:** Splunk CLI uses a stored session for privileged operations.

**Command:**

```bash
timeout {{ cca_splunk_command_timeout | default('60') }} {{ splunk_path }}/bin/splunk login \
  --accept-license --answer-yes --no-prompt -auth '{{ splunk_cli_user }}:{{ splunk_cli_user_password }}'
```

**Variables:**

- `splunk_path`, `cca_splunk_command_timeout`
- `splunk_cli_user`, `splunk_cli_user_password` — credentials (handle securely, never log)

**Retries:** `cca_splunk_login_retries` (default `15`), delay `10` s.

**Expected result (check):**
- **Return code:** `0` (success). Task uses `until: splunk_login_result.rc == 0`; assert then requires `splunk_login_result.rc | int == 0`.
- **Stderr/stdout:** On failure, assert uses stderr and stdout in the fail message; treat non-zero rc as failure.

---

## 4. Splunk CLI logout

**When:** After a block of CLI operations that used login (e.g. after reload deploy-server, apply bundle, preflight, maintenance-mode).

**Why:** Cleans up CLI session.

**Command:**

```bash
timeout {{ cca_splunk_command_timeout | default('60') }} {{ splunk_path }}/bin/splunk logout
```

**Variables:** `splunk_path`, `cca_splunk_command_timeout`.
**Retries:** `cca_splunk_logout_retries` (default `60`), delay `10` s.

**Expected result (check):**
- **Return code:** `0` (success). Task uses `until: splunk_logout_result.rc == 0`. Final task fails when `splunk_logout_result.rc > 0` (debug + failed_when).

---

## 5. Restart Splunkd

**When (calculated from changes):**

- Any change under `etc/` that is **not** `deployment-apps`, `shcluster`, `master-apps`, or `manager-apps` on a **standalone** host (non-cluster, non-SHC), or
- `splunk.secret` was replaced (restart immediately after that change), or
- Deployment-apps changed on a deployment server and the platform chose full restart instead of reload (e.g. serverclass count > `cca_max_reload_serverclass_items`), or
- `force_splunkd_restart` is set for an SHC member (use restart instead of rolling restart).

**Why:** Core config or app changes require a process restart on that host.

**Command:**

```bash
{{ restart_command }}
```

With default vars:

```bash
{{ splunk_path }}/bin/splunk restart --accept-license --answer-yes --no-prompt
```

Optional wrapper for timeout:

```bash
timeout {{ cca_splunk_command_timeout | default('120') }} {{ restart_command }}
```

**Variables:**

- `splunk_path` — default `"/opt/splunk"`
- `restart_command` — default `"{{ splunk_path }}/bin/splunk restart --accept-license --answer-yes --no-prompt"`
- `cca_splunk_command_timeout` — default `120` for restart
- `cca_splunkd_restart_retries` — default `5`, delay `10` s

**After restart:** Wait until status check passes (see §2):

```bash
timeout {{ cca_splunk_command_timeout | default('60') }} {{ splunk_path }}/bin/splunk status --accept-license --answer-yes --no-prompt
```

with `cca_splunkd_restart_status_retries` (default `60`), delay `10` s.

**Expected result (check):**
- **Restart command:** Return code `0` (success). Treat as failure if stdout or stderr contains `Root permission is required` (polkit/privilege issue). Treat as non-fatal retry if stderr contains `web interface does not seem to be available` (recovery path waits then retries status).
- **Status after restart:** Return code `0` and stdout matches `splunkd is running` (same as §2).

---

## 6. Start Splunk (systemd)

**When:** First-time run or when Splunk must be started (e.g. after stop for updates, or when ensuring service is up).

**Why:** Start and enable Splunk service.

**Command (systemd):**

```bash
systemctl start {{ systemd_enterprise_name }}
systemctl enable {{ systemd_enterprise_name }}
```

**Variables:**

- `systemd_enterprise_name` — default `"Splunkd.service"`

---

## 7. Stop Splunk (systemd)

**When:** During orchestrated updates (e.g. rolling restart, OS/package updates) before applying changes or before restart.

**Commands:**

```bash
systemctl stop {{ systemd_enterprise_name }}
systemctl disable {{ systemd_enterprise_name }}
```

**Variables:** `systemd_enterprise_name` — default `"Splunkd.service"`.

---

## 8. Reload Deployment Server

**When (calculated from changes):** Paths under `deployment-apps` changed on a **deployment server** host, and the platform did **not** choose full restart (e.g. number of serverclasses ≤ `cca_max_reload_serverclass_items`).

**Why:** Notify deployment server clients of new/updated apps.

**Standard mode (reload all):**

```bash
timeout {{ reload_deploy_server_timeout | default(900) + 60 }} {{ splunk_path }}/bin/splunk reload deploy-server \
  -timeout {{ reload_deploy_server_timeout | default(900) }}
```

**Serverclass mode (reload specific serverclasses):**
Run once per serverclass (up to `cca_max_reload_serverclass_items` default `50`):

```bash
timeout {{ reload_deploy_server_timeout | default(900) + 60 }} {{ splunk_path }}/bin/splunk reload deploy-server \
  -timeout {{ reload_deploy_server_timeout | default(900) }} -class {{ serverclass_name }}
```

**Variables:**

- `splunk_path`
- `reload_deploy_server_timeout` — default `900`
- `skip_ds_reload_handler` — if true, skip reload
- `use_serverclass_mode` — if true, use `-class` with list `serverclass` (filter to first `cca_max_reload_serverclass_items`)

**Prerequisite:** Login (§3) on the deployment server host.

**Expected result (check):** Return code `0` for successful reload. (Tasks do not assert on specific stdout; treat rc 0 as success.)

---

## 9. Apply Search Head Cluster bundle (bundle push)

**When (calculated from changes):** Paths under `shcluster` changed; run on the **search head deployer** for each affected SHC.

**Why:** Push updated apps/config from deployer to SHC members.

**Command (run on deployer, one target member per SHC):**

```bash
timeout {{ cca_splunk_apply_shcluster_bundle_timeout | default(600) }} {{ splunk_path }}/bin/splunk apply shcluster-bundle \
  -target https://{{ shcluster_member_host }}:8089 \
  --answer-yes {{ custom_opts_apply_shcluster_bundle | default('') }}
```

`shcluster_member_host` is typically the first member of the SHC (e.g. `groups['searchhead_members_shcluster_c1'][0]` for cluster c1).

**Variables:**

- `splunk_path`
- `cca_splunk_apply_shcluster_bundle_timeout` — default `600`
- `custom_opts_apply_shcluster_bundle` — optional extra CLI args
- `cca_splunk_apply_shcluster_bundle_retries` — default `3`, delay `cca_splunk_apply_shcluster_bundle_delay` (default `60`)

**Prerequisite:** Login (§3) on deployer.

**Scope:** Run only on the deployer host(s) for the SHC that had shcluster content changes (inventory: e.g. `searchhead_deployer_shcluster_c1` … `searchhead_deployer_shcluster_c9`).

**Expected result (check):** Return code `0` (success). Tasks use `until: apply.rc == 0` with retries/delay; retry until rc is 0.

---

## 10. Apply Indexer Cluster bundle (bundle push)

**When (calculated from changes):** Paths under `master-apps` or `manager-apps` changed; run on the **cluster manager** for that cluster.

**Why:** Push updated bundle to indexer cluster.

**Pre-step – Validate and check restart (recommended):**

```bash
{{ splunk_path }}/bin/splunk validate cluster-bundle --check-restart
```

Then wait until cluster bundle status shows validation done and, for older Splunk, `last_validated_bundle` timestamp updated:

```bash
{{ splunk_path }}/bin/splunk show cluster-bundle-status --check-restart
# and/or
{{ splunk_path }}/bin/splunk show cluster-bundle-status
```

Loop until `cluster_status=None` (and no [Critical] validation errors if you enforce that).

**Apply command:**

```bash
{{ splunk_path }}/bin/splunk apply cluster-bundle --answer-yes
```

**Variables:**

- `splunk_path`
- `cca_splunk_cluster_bundle_status_retries` — default `40`, delay `15` s for status wait
- `cluster_bundle_status_command_retries` — default `30`, delay `60` s for restart status

**Prerequisite:** Login (§3) on cluster manager.

**After:** If validate indicated restart required, run cluster peer rolling restart (§11), then preflight (§12).

**Expected result (check):**
- **validate cluster-bundle --check-restart:** rc 0; optional: stdout contains `Created new bundle with checksum` (for version-specific wait logic).
- **show cluster-bundle-status (validation):** stdout contains `None` in the cluster_status line (e.g. `cluster_status=None`); retry until that appears. For timestamp wait (older Splunk): `last_check_restart_bundle_epoch.stdout | int > current_epoch`.
- **show cluster-bundle-status (before apply):** stdout matches regex `cluster_status=None`; fail if stdout contains `bundle_validation_errors` and `[Critical]` (unless `accept_bundle_validation_errors`). `Not Critical` in stdout is stored for display.
- **Restart required:** If stdout matches regex `last_check_restart_result=restart required`, create rolling-restart flow and later remove rolling_restart_pending (no state file in new solution; just run §11).
- **apply cluster-bundle:** rc 0 (no explicit until in task; treat as success on rc 0).

---

## 11. Cluster peer rolling restart (indexer cluster)

**When (calculated from changes):** Core/config changes affect **cluster peers** in a cluster, or after apply cluster-bundle (§10) when validate reported restart required. Run on the **cluster manager**.

**Why:** Apply bundle or config that requires indexers to restart in a rolling fashion.

**Command (on cluster manager):**

```bash
{{ splunk_path }}/bin/splunk rolling-restart cluster-peers -searchable {{ searchable_rolling_restart | default('false') }} --answer-yes
```

**Variables:**

- `splunk_path`
- `searchable_rolling_restart` — default `'false'`
- `wait_time_cluster_peers_report` — default `3` (minutes to wait after before preflight)

**Prerequisite:** Login (§3) on cluster manager.

**After:** Wait `wait_time_cluster_peers_report` minutes, then run preflight (§12).

**Expected result (check):** Return code `0` (success). (Tasks do not assert on stdout for this command; rc 0 is sufficient.)

---

## 12. Preflight status check (cluster manager)

**When:** After applying cluster bundle (§10) or after cluster peer rolling restart (§11), to ensure cluster is healthy.

**Why:** Confirm preflight check is successful before considering cluster operations complete.

**Commands:**

```bash
# 1) Kvstore ready (if applicable)
timeout {{ cca_splunk_command_timeout | default('60') }} {{ splunk_path }}/bin/splunk show kvstore-status
# Expect: 'status : ready' in stdout

# 2) Pre-flight check
timeout {{ cca_splunk_command_timeout | default('60') }} {{ splunk_path }}/bin/splunk show cluster-status --verbose | grep Pre-flight
# Expect: 'Pre-flight check successful.*YES'
```

**Variables:**

- `splunk_path`, `cca_splunk_command_timeout`
- `preflight_command_retries` — e.g. `30` (after apply cluster-bundle) or `cluster_peer_rolling_restart_preflight_retries` (default `180`) after rolling restart
- `cca_splunk_kvstore_status_retries` — default `6`, delay `10` s
- `skip_preflight_check` — if true, skip

**Prerequisite:** Login (§3) on cluster manager.

**Expected result (check):**
- **show kvstore-status:** stdout contains `status : ready` (string match). Retry until true; `cca_splunk_kvstore_status_retries`, delay 10 s.
- **show cluster-status --verbose | grep Pre-flight:** stdout matches regex `Pre-flight check successful.*YES`. Retry until true; `preflight_command_retries` (e.g. 30 or 180), delay 60 s (or 30 s when retries &lt; 90). Fallback path on cluster manager uses `-auth` and same regex.

---

## 13. Search Head Cluster rolling restart (SHC members)

**When (calculated from changes):** Core/config changes under `etc/` (excluding deployment-apps, shcluster, master-apps/manager-apps) affect **SHC members**, and `force_splunkd_restart` is **not** set. Run on each **SHC member** that is in the set of changed hosts (or on all members of the affected SHC, depending on policy).

**Why:** Restart SHC members in a rolling way so one member stays up.

**Command (on each SHC member):**

```bash
{{ shcluster_members_rolling_restart_command }}
```

With default:

```bash
{{ splunk_path }}/bin/splunk rolling-restart shcluster-members
```

**Variables:**

- `splunk_path`
- `shcluster_members_rolling_restart_command` — default `'{{ splunk_path }}/bin/splunk rolling-restart shcluster-members'`

**Prerequisite:** Login (§3) on the SHC member.

**Expected result (check):** Return code `0` or `22` (acceptable). Tasks use `failed_when: splunk_rolling_restart_result.rc != 22 and splunk_rolling_restart_result.rc != 0` — so rc 0 (success) or rc 22 (e.g. nothing to do / already in progress) is acceptable; any other rc is failure.

---

## 14. KVStore status (for preflight / cluster)

**When:** Before preflight or maintenance-mode on cluster manager.

**Command:**

```bash
timeout {{ cca_splunk_command_timeout | default('60') }} {{ splunk_path }}/bin/splunk show kvstore-status
```

**Variables:** `splunk_path`, `cca_splunk_command_timeout`, `cca_splunk_kvstore_status_retries` (default `6`), delay `10` s.

**Expected result (check):** Return code `0`; stdout must contain `status : ready` (string). Retry until both are true.

---

## 15. Maintenance mode (indexer cluster) – enable / disable

**When:** During orchestrated indexer peer stop/start (e.g. rolling OS update). Enable before stopping a peer, disable after it is back up.

**Enable (on cluster manager):**

```bash
timeout {{ cca_splunk_command_timeout | default('30') }} {{ splunk_path }}/bin/splunk enable maintenance-mode --answer-yes --no-prompt
```

**Disable (on cluster manager):**

```bash
timeout {{ cca_splunk_command_timeout | default('30') }} {{ splunk_path }}/bin/splunk disable maintenance-mode --answer-yes --no-prompt
```

**Variables:** `splunk_path`, `cca_splunk_command_timeout`.
**Prerequisite:** Login (§3) on cluster manager; kvstore and preflight checks may be required before enabling.

**Expected result (check):** Return code `0` for enable and disable. Tasks use `until: splunk_logout_result.rc == 0` after logout; enable/disable commands themselves are not retried in the same way — treat rc 0 as success.

---

## 16. Transfer SHC captain (search head cluster)

**When:** During SHC rolling restart or rebalancing; current captain transfers captaincy to another member before restart.

**Command (on current captain):**

```bash
timeout {{ cca_splunk_command_timeout | default('360') }} {{ splunk_path }}/bin/splunk transfer shcluster-captain \
  -mgmt_uri https://{{ new_captain_host }}:{{ splunk_enterprise_mgmt_port }}
```

**Variables:**

- `splunk_path`
- `splunk_enterprise_mgmt_port` — default `8089`
- `new_captain_host` — target member hostname (from inventory, e.g. adjacent member)
- `cca_splunkd_cli_transfer_retries` — default `10`, delay `10` s

**Prerequisite:** Login (§3). Often preceded by `show shcluster-status` to get current captain and pick adjacent member.

**Expected result (check):** Return code `0` (success). Task uses `until: splunk_transfer_result.rc == 0` with `cca_splunkd_cli_transfer_retries` (default 10), delay 10 s.

---

## 17. Splunk offline (graceful stop for indexer peer)

**When:** Before stopping an indexer peer for updates (e.g. OS/kernel or Splunk service restart).

**Command:**

```bash
timeout 900 {{ splunk_path }}/bin/splunk offline
```

**Variables:** `splunk_path`. Fallback if offline fails: `splunk stop` with `cca_splunk_stop_timeout` (default `600`), `cca_splunkd_cli_stop_retries` (default `10`).

**Expected result (check):** Tasks use `failed_when: false` for the offline command (non-fatal). Fallback `splunk stop`: retry until `splunk_stop_result.rc == 0`. Treat offline rc 0 as success; non-zero can trigger fallback stop.

---

## 18. Splunk stop (CLI)

**When:** When a graceful stop is needed (e.g. after offline, or force restart).

**Command:**

```bash
timeout {{ cca_splunk_stop_timeout | default('600') }} {{ splunk_path }}/bin/splunk stop
```

**Variables:** `splunk_path`, `cca_splunk_stop_timeout`, `cca_splunkd_cli_stop_retries`.

**Expected result (check):** Return code `0` (success). Task uses `until: splunk_stop_result.rc == 0` in the fallback path; for direct stop, treat rc 0 as success.

---

## 19. Variable reference (defaults)

| Variable | Default / usage |
|----------|------------------|
| `splunk_path` | `"/opt/splunk"` |
| `start_command` | `"{{ splunk_path }}/bin/splunk start --accept-license --answer-yes --no-prompt"` |
| `restart_command` | `"{{ splunk_path }}/bin/splunk restart --accept-license --answer-yes --no-prompt"` |
| `stop_command` | `"{{ splunk_path }}/bin/splunk stop"` |
| `systemd_enterprise_name` | `"Splunkd.service"` |
| `shcluster_members_rolling_restart_command` | `'{{ splunk_path }}/bin/splunk rolling-restart shcluster-members'` |
| `splunk_enterprise_mgmt_port` | `8089` |
| `cca_splunk_command_timeout` | `60` (120 for restart/start in some paths) |
| `cca_splunkd_restart_retries` | `5` |
| `cca_splunkd_restart_status_retries` | `60` |
| `cca_splunkd_status_retries` | `10` |
| `cca_splunk_login_retries` | `15` |
| `cca_splunk_logout_retries` | `60` |
| `reload_deploy_server_timeout` | `900` |
| `cca_max_reload_serverclass_items` | `50` |
| `cca_splunk_apply_shcluster_bundle_timeout` | `600` |
| `cca_splunk_apply_shcluster_bundle_retries` | `3` |
| `cca_splunk_apply_shcluster_bundle_delay` | `60` |
| `searchable_rolling_restart` | `'false'` |
| `wait_time_cluster_peers_report` | `3` |
| `cluster_peer_rolling_restart_preflight_retries` | `90` |
| `preflight_command_retries` | (e.g. `30` or `180`) |
| `cca_splunk_kvstore_status_retries` | `6` |
| `cca_splunk_stop_timeout` | `600` |
| `cca_splunkd_cli_stop_retries` | `10` |
| `cca_splunkd_cli_transfer_retries` | `10` |

Credentials (must be provided securely, never logged):

- `splunk_cli_user`
- `splunk_cli_user_password`

Inventory groups (for which host runs which action):

- `deployment_servers`, `cluster_managers`, `searchhead_deployers`, `searchhead_members`, `cluster_peers`
- `searchhead_deployer_shcluster_c1` … `searchhead_deployer_shcluster_c9`
- `searchhead_members_shcluster_c1` … `searchhead_members_shcluster_c9`
- `cluster_manager_cluster_c1` … `cluster_manager_cluster_c9`
- `cluster_peers_cluster_c1` … `cluster_peers_cluster_c9`

---

## 20. Suggested apply-plan order (change-driven)

1. **Compute actions** from the set of changed paths and host inventory (§1). No state files; all actions are derived from changes.
2. **Deployment servers:** For each deployment server with `deployment-apps` changes: if reload is chosen (serverclass count within limit), login → reload deploy-server (§8) → logout. If restart is chosen, restart (§5) and wait for status (§2).
3. **Cluster managers:** For each cluster with `master-apps`/`manager-apps` changes: login → validate/apply cluster-bundle (§10). If validate indicates restart required: rolling-restart cluster-peers (§11) → wait → preflight (§12) → logout.
4. **Search head deployers:** For each deployer with `shcluster` changes: login → apply shcluster-bundle (§9) → logout.
5. **SHC members:** For each SHC with core/config changes (and not force restart): login → rolling-restart shcluster-members (§13).
6. **Standalone / non-cluster:** For each standalone host with core/config changes (or `splunk.secret` replaced): restart (§5) → wait for status (§2).
7. **Any host:** Run status check (§2) where needed to confirm splunkd is running after restarts.

This gives the Deslicer Automation Platform a change-driven map of **when** and **why** each step runs, **what** to execute, and **which variables** to use, with no state files.

---

# Part B: Setup and operational actions (non-onboarding)

The following actions are used for **setup**, **initialization**, **start/stop**, **accept license**, **SHC bootstrap**, **cluster/SHC upgrade init**, **search peer setup**, and **KVStore migration/upgrade**. They are not driven by config-change detection; the platform runs them when performing initial setup, ensuring Splunk is running, or executing a known procedure (e.g. bootstrap SHC, add search peer). No state files are used; the platform decides when to run each action from context (e.g. “first run”, “initializing SHC”, “adding search peer”).

---

## B1. Start Splunk (CLI, accept license)

**When:** First-time run, after install, or when ensuring Splunk is running (e.g. before config apply on a host that was stopped). Used for both standalone and cluster/SHC members.

**Why:** Start the Splunk daemon and accept the license non-interactively.

**Command:**

```bash
timeout {{ cca_splunk_command_timeout | default('240') }} {{ start_command }}
```

With default vars:

```bash
timeout {{ cca_splunk_command_timeout | default('240') }} {{ splunk_path }}/bin/splunk start --accept-license --answer-yes --no-prompt
```

**Variables:**

- `splunk_path` — default `"/opt/splunk"`
- `start_command` — default `"{{ splunk_path }}/bin/splunk start --accept-license --answer-yes --no-prompt"`
- `cca_splunk_command_timeout` — default `240` for first-time start
- `cca_splunkd_start_retries` — default `5`, delay `10` s

**Success:** Exit code 0, or stdout contains `The splunk daemon (splunkd) is already running`. First-time run may show `This appears to be your first time running this version of Splunk.`

**Where:** Run on the target host (non–search-head members first, then search head members, or as determined by your apply plan).

**Expected result (check):**
- **Return code:** `0` (success), or treat as success if stdout contains `The splunk daemon (splunkd) is already running`. Tasks use `until: splunk_status_result.rc == 0 or ('The splunk daemon (splunkd) is already running' in splunk_status_result.stdout)`.
- **Fail when:** rc != 0 and stdout does **not** contain `The splunk daemon (splunkd) is already running`.
- **First-time run:** stdout may contain `This appears to be your first time running this version of Splunk.` (used for changed_when only).

---

## B2. Stop Splunk (CLI)

**When:** Before upgrade, before systemd disable, or when gracefully shutting down Splunk (e.g. for OS update or migration recovery).

**Why:** Stop the Splunk daemon cleanly.

**Command:**

```bash
{{ stop_command }}
```

With default:

```bash
{{ splunk_path }}/bin/splunk stop
```

Optional timeout (e.g. for upgrades):

```bash
timeout {{ cca_splunk_stop_timeout | default('600') }} {{ splunk_path }}/bin/splunk stop
```

**Variables:** `splunk_path`, `stop_command`, `cca_splunk_stop_timeout`, `cca_splunkd_cli_stop_retries`.

**Expected result (check):** Return code `0` (success). systemd stop may use `failed_when: false` in some paths; for CLI stop, treat rc 0 as success.

---

## B3. Splunk status (with accept license)

**When:** After start or restart to verify splunkd is running, or before any CLI operation that requires a running instance. Use when you need non-interactive acceptance of the license (e.g. first run).

**Why:** Confirm Splunk is up and, if needed, accept the license without prompts.

**Command:**

```bash
timeout {{ cca_splunk_command_timeout | default('60') }} {{ splunk_path }}/bin/splunk status --accept-license --answer-yes --no-prompt
```

**Variables:** `splunk_path`, `cca_splunk_command_timeout`, `cca_splunkd_status_retries` (default `10` or `30` in install path).

**Expected result (check):** Return code `0`; stdout must match regex `splunkd is running`. Same as §2.

---

## B4. Get Splunk version

**When:** After install or when determining the running Splunk version (e.g. for upgrade logic or version-specific behavior).

**Why:** Read the installed/running Splunk Enterprise version.

**Command:**

```bash
timeout {{ cca_splunk_command_timeout | default('60') }} {{ splunk_path }}/bin/splunk version --accept-license --answer-yes --no-prompt
```

Parse version from output (e.g. `grep -E "Splunk [0-9\.]+" | awk '{ print $2 }'` or `awk '{ print $2 }'` depending on format).

**Variables:** `splunk_path`, `cca_splunk_command_timeout`, `cca_splunkd_cli_version_retries` (default `10`).

**Expected result (check):** Return code `0`; stdout (or parsed output) contains the version string. Tasks use `until: splunk_enterprise_version_result.rc == 0`. For version from running instance, stdout is trimmed and used as `current_splunk_enterprise_version`.

---

## B5. Bootstrap Search Head Cluster captain (SHC init)

**When:** The platform is initializing a **search head cluster** for the first time (one captain per SHC, e.g. per `searchhead_members_shcluster_c1` … `c9`). Run once per SHC, on one member (typically the first in the group).

**Why:** Form the SHC by bootstrapping the captain with the list of all SHC member management URLs.

**Command (run on one SHC member per cluster, e.g. first in group):**

```bash
{{ splunk_path }}/bin/splunk bootstrap shcluster-captain -servers_list 'https://host1:{{ splunk_enterprise_mgmt_port }},https://host2:{{ splunk_enterprise_mgmt_port }},...'
```

The comma-separated list must include all members of that SHC (e.g. from `groups['searchhead_members_shcluster_cN']`).

**Variables:**

- `splunk_path`
- `splunk_enterprise_mgmt_port` — default `8089`
- `cca_splunk_bootstrap_shcluster_captain_retries` — default `10`, delay `30` s

**Retries:** Until exit code 0 or stderr contains `node seems to have already joined another cluster` (idempotent).

**Expected result (check):**
- **Success:** Return code `0`. Tasks use `changed_when: bootstrap_shc_result.rc == 0`.
- **Acceptable (idempotent):** stderr contains `node seems to have already joined another cluster` — treat as success (no retry). Task uses `until: bootstrap_shc_result.rc == 0 or "node seems to have already joined another cluster" in bootstrap_shc_result.stderr`.
- **Failure:** rc != 0 and stderr does **not** contain `node seems to have already joined another cluster`. Task uses `failed_when: bootstrap_shc_result.rc != 0 and "node seems to have already joined another cluster" not in bootstrap_shc_result.stderr`.

**Prerequisite:** Login (§3) on the host where the command runs. All SHC members must be running and reachable.

**After:** Wait until SHC is initialized and service ready (see B6, B7).

---

## B6. Wait for SHC initialized (show shcluster-status)

**When:** After bootstrap SHC captain (B5), to ensure the cluster has reached initialized state.

**Why:** Block until the SHC reports initialized and, optionally, service ready.

**Command:**

```bash
timeout {{ splunk_timeout_shcluster_status | default(120) }} {{ splunk_path }}/bin/splunk show shcluster-status
```

**Success criteria (retry until):**

- `initialized_flag : 1` in stdout
- Then (optional) `service_ready_flag : 1` in stdout

**Variables:**

- `splunk_path`
- `splunk_timeout_shcluster_status` — default `120`
- `shc_sync_retry_num` — default `30`
- `retry_delay` — default `30` s

**Expected result (check):** Poll until stdout contains `initialized_flag : 1`; then (optional) poll until stdout contains `service_ready_flag : 1`. Tasks use `until: "'initialized_flag : 1' in shcluster_status_result.stdout | default('')"` and `until: "'service_ready_flag : 1' in shcluster_status_result.stdout | default('')"` with `failed_when: false`.

---

## B7. Wait for SHC service ready and rolling restart complete

**When:** After SHC is initialized, or when waiting for an in-progress SHC rolling restart to finish (e.g. before running further steps on SHC members).

**Why:** Ensure the SHC is ready to serve and no rolling restart is in progress.

**Commands (run in order or as needed):**

```bash
timeout {{ splunk_timeout_shcluster_status | default(120) }} {{ splunk_path }}/bin/splunk show shcluster-status
```

- Until `service_ready_flag : 1` in stdout.
- Until `rolling_restart_flag : 0` in stdout.

**Variables:** Same as B6. Optionally run `show kvstore-status` until `status : ready` before or after (see §14).

**Expected result (check):** Same as B6 for `service_ready_flag : 1`. For rolling restart: poll until stdout contains `rolling_restart_flag : 0`. Tasks use `until: "'rolling_restart_flag : 0' in shcluster_status_result.stdout | default('')"` with `failed_when: false`. KVStore: stdout contains `status : ready`.

---

## B8. Show SHC status (verbose) – version and info

**When:** When you need SHC member versions, captain label, or detailed status (e.g. for upgrade or health checks).

**Why:** Get running Splunk versions, kvstore engine, or full SHC status.

**Commands:**

```bash
# Versions
timeout {{ cca_splunk_command_timeout | default('60') }} {{ splunk_path }}/bin/splunk show shcluster-status --verbose | grep 'splunk_version :'

# Kvstore engine
timeout {{ cca_splunk_command_timeout | default('60') }} {{ splunk_path }}/bin/splunk show kvstore-status | grep 'storageEngine :'

# Full status
timeout {{ splunk_timeout_shcluster_status | default(120) }} {{ splunk_path }}/bin/splunk show shcluster-status
```

**Variables:** `splunk_path`, `cca_splunk_command_timeout`, `splunk_timeout_shcluster_status`, `cca_splunkd_cli_shcluster_version_retries`, `cca_splunkd_cli_kvstore_engine_retries`.

**Expected result (check):** Return code `0` for version/kvstore commands. Tasks use `until: shcluster_splunk_version.rc == 0`, `until: kvstore_engine.rc == 0`, `until: verbose_shcluster_status.rc == 0`. For health checks, stdout is parsed for `dynamic_captain : 1`, `initialized_flag : 1`, `rolling_restart_flag : 0`, `rolling_upgrade_flag : 0`, `service_ready_flag : 1`, `stable_captain : 1`, `manual_detention : off`, `status : ready`.

---

## B9. Add search server (search peer)

**When:** The platform is configuring a **monitoring console** (or similar) and needs to add other Splunk servers as search peers.

**Why:** Register a search peer so the current host can dispatch search to it.

**Command (run on the host that will have the search peer; delegate_to that host):**

```bash
timeout {{ cca_splunk_command_timeout | default('60') }} {{ splunk_path }}/bin/splunk add search-server {{ host }}:{{ splunk_enterprise_mgmt_port }} -remoteUsername {{ splunk_cli_user }} -remotePassword {{ splunk_cli_user_password }} -auth '{{ splunk_cli_user }}:{{ splunk_cli_user_password }}'
```

**Variables:**

- `splunk_path`, `splunk_enterprise_mgmt_port` (default `8089`)
- `splunk_cli_user`, `splunk_cli_user_password` (credentials; handle securely)
- `host` — hostname (or FQDN) of the server to add as search peer
- `cca_splunk_command_timeout`

**Expected result (check):** Return code `0` (success). Return code `24` is acceptable (e.g. search server already added). Tasks use `failed_when: command_result.rc != 0 and command_result.rc != 24` and `changed_when: command_result.rc == 0`.

**Prerequisite:** Login (§3) on the host where the command runs.

---

## B10. KVStore migration readiness (SHC, dry run)

**When:** Before starting a KVStore migration on an SHC (e.g. to WiredTiger). Run when the platform is preparing an SHC KVStore migration.

**Why:** Verify that the SHC is ready for migration without performing it.

**Command:**

```bash
{{ splunk_path }}/bin/splunk start-shcluster-migration kvstore -storageEngine wiredTiger -isDryRun true
```

**Expected result (check):** Stdout must equal exactly `Dry run for SHC KV Store migration for search head cluster passed`. Task asserts on that string; fail otherwise.

**Prerequisite:** Login (§3) on an SHC member (run_once). Variables: `splunk_path`.

---

## B11. KVStore migration (SHC)

**When:** When the platform is performing a KVStore migration on an SHC (e.g. to WiredTiger). Run after readiness (B10) passes.

**Why:** Start the SHC KVStore migration.

**Command:**

```bash
{{ splunk_path }}/bin/splunk start-shcluster-migration kvstore -storageEngine wiredTiger
```

**Success:** stdout equals `SHC KV Store migration has been successfully triggered`. Then poll until migration completes:

```bash
{{ splunk_path }}/bin/splunk show shcluster-kvmigration-status
```

Until stdout contains `migrationStatus: kvstore_migration_completed`. Variables: `kvstore_migration_retry` (default `60`), `retry_delay` (default `30`). Prerequisite: Login (§3).

**Expected result (check):**
- **start-shcluster-migration:** stdout must equal `SHC KV Store migration has been successfully triggered`. Task asserts on that string.
- **show shcluster-kvmigration-status:** poll until stdout contains `migrationStatus: kvstore_migration_completed`. Task uses `until: "'migrationStatus: kvstore_migration_completed' in kvstore_migration_status.stdout"`.

---

## B12. KVStore engine upgrade readiness (SHC, dry run)

**When:** Before starting a KVStore engine version upgrade on an SHC.

**Why:** Verify that the SHC is ready for the upgrade without performing it.

**Command:**

```bash
{{ splunk_path }}/bin/splunk start-shcluster-upgrade kvstore -version {{ cca_splunk_kvstore_engine_version }} -isDryRun true
```

**Expected result (check):** Stdout must equal exactly `Dry run for SHC KV Store upgrade for search head cluster passed`. Task asserts on that string.

**Variables:** `splunk_path`, `cca_splunk_kvstore_engine_version` (e.g. `4.2` from template). Prerequisite: Login (§3).

---

## B13. KVStore engine upgrade (SHC)

**When:** When the platform is performing a KVStore engine version upgrade on an SHC. Run after readiness (B12) passes.

**Why:** Start the SHC KVStore engine upgrade.

**Command:**

```bash
{{ splunk_path }}/bin/splunk start-shcluster-upgrade kvstore -version {{ cca_splunk_kvstore_engine_version }}
```

**Success:** stdout equals `SHC KV Store upgrade has been successfully triggered`. Then poll until all members report the new version, e.g.:

```bash
timeout {{ cca_splunk_kvstore_upgrade_timeout | default('360') }} {{ splunk_path }}/bin/splunk show kvstore-status --verbose | grep serverVersion | sort -u | grep -v '{{ cca_splunk_kvstore_engine_version }}' | wc -l
```

Until output is `0`. Variables: `cca_splunk_kvstore_engine_version`, `cca_splunk_kvstore_upgrade_timeout`, `kvstore_upgrade_retry` (default `60`), `retry_delay` (default `30`). Prerequisite: Login (§3).

**Expected result (check):**
- **start-shcluster-upgrade:** stdout must equal `SHC KV Store upgrade has been successfully triggered`. Task asserts on that string.
- **show kvstore-status --verbose:** poll until no serverVersion line shows a version other than `cca_splunk_kvstore_engine_version` (e.g. count of such lines is 0). Task uses `until: kvstore_upgrade_status.stdout == '0'`.

---

## B14. Upgrade-init cluster-peers (indexer cluster)

**When:** When the platform is starting a **rolling upgrade** of indexer cluster peers (e.g. before upgrading or restarting peers one by one).

**Why:** Initialize the rolling upgrade process on the cluster manager.

**Command (on cluster manager):**

```bash
{{ splunk_path }}/bin/splunk upgrade-init cluster-peers
```

**Variables:** `splunk_path`. Prerequisite: Login (§3) on cluster manager.

**Expected result (check):** Return code `0` (success). If stderr contains `Rolling upgrade/restart is already in progress`, treat as success (idempotent). Task uses `failed_when: upgrade_init_cluster_peers.rc != 0 and not upgrade_init_cluster_peers.stderr | regex_search('Rolling upgrade/restart is already in progress')`.

---

## B15. Upgrade-init shcluster-members (SHC)

**When:** When the platform is starting a **rolling upgrade** of SHC members.

**Why:** Initialize the rolling upgrade process for the SHC.

**Command (on one SHC member, run_once):**

```bash
{{ splunk_path }}/bin/splunk upgrade-init shcluster-members
```

**Variables:** `splunk_path`. Prerequisite: Login (§3). Typically run when `enterprise_upgrade` is true.

**Expected result (check):** Return code `0` (success). No explicit stdout check in task.

---

## B16. Start Splunk via systemd (ensure started)

**When:** When the platform ensures Splunk is started and enabled at boot (e.g. after install or after manual stop).

**Why:** Start and enable the Splunk systemd service.

**Commands:**

```bash
systemctl start {{ systemd_enterprise_name }}
systemctl enable {{ systemd_enterprise_name }}
```

**Variables:** `systemd_enterprise_name` — default `"Splunkd.service"`. May require root/become. Used when `stat_ansible_managed` and `ensure_splunkd_started` (default true) indicate the host is managed and should have Splunk running.

**Expected result (check):** systemd start/enable: success (Ansible uses `until: splunk_systemd_result is succeeded` in update path). No specific rc for raw systemctl; treat success as normal.

---

## B17. Stop / disable Splunk via systemd

**When:** When the platform is stopping Splunk for an update or maintenance and ensuring it does not start at boot.

**Commands:**

```bash
systemctl stop {{ systemd_enterprise_name }}
systemctl disable {{ systemd_enterprise_name }}
```

**Variables:** `systemd_enterprise_name` — default `"Splunkd.service"`. May require root/become.

**Expected result (check):** systemd stop/disable often use `failed_when: false` (best-effort). Treat success when the service is stopped/disabled.

---

## B18. Check if SHC member is joined (show shcluster-status)

**When:** When the platform needs to know whether the current node has joined an SHC (e.g. to decide whether to add the member or run bootstrap).

**Why:** Detect “Search Head Clustering is not enabled on this node” or equivalent.

**Command:**

```bash
timeout {{ splunk_timeout_shcluster_status | default(120) }} {{ splunk_path }}/bin/splunk show shcluster-status
```

**Variables:** `splunk_path`, `splunk_timeout_shcluster_status`.

**Expected result (check):** If stdout matches regex `.*Search Head Clustering is not enabled on this node.*`, the member is **not** yet in the cluster (task sets `add_shcluster_member: true`). Otherwise the node has joined. No specific rc assertion; use stdout to decide next action.

---

## B19. Recovery from migration state (stop then start)

**When:** When a previous run left Splunk in a migration state (e.g. version output stderr contains “Migration information”).

**Why:** Clear the migration state by stopping and then starting Splunk.

**Commands:**

```bash
{{ splunk_path }}/bin/splunk stop
# then
{{ start_command }}
```

**Variables:** `splunk_path`, `start_command`. Use when version check stderr indicates migration state.

**Expected result (check):** Stop: rc 0. Start: rc 0 (or stdout contains `The splunk daemon (splunkd) is already running`). Tasks run when `splunk_enterprise_version_result.stderr | default('') | regex_search('Migration information')`.

---

## B20. Additional variables for Part B

| Variable | Default / usage |
|----------|------------------|
| `splunk_timeout_shcluster_status` | `120` |
| `shc_sync_retry_num` | `30` |
| `retry_delay` | `30` |
| `cca_splunk_bootstrap_shcluster_captain_retries` | `10` |
| `cca_splunk_kvstore_engine_version` | e.g. `4.2` |
| `cca_splunk_kvstore_upgrade_timeout` | `360` |
| `kvstore_migration_retry` | `60` |
| `kvstore_upgrade_retry` | `60` |
| `cca_wait_for_connection_timeout` | `600` |
| `ensure_splunkd_started` | `true` |

Use the same credentials and inventory groups as in Part A where relevant (login, bootstrap target groups, cluster manager, etc.).
