# Session Handoff

## Scope

This repo is building a Ludus lab for a HashiCorp Nomad cluster:

- 3 Nomad servers
- 1 Nomad client
- Debian 12 on all nodes
- TLS, ACLs, and gossip encryption enabled
- optional demo job via `nomad_deploy_demo_job`

The user wants:

- a working Ludus lab definition
- local Ansible roles in this repo that they can commit
- `Architecture.md`
- `decisions.md`
- production-oriented security defaults

## Repo State

Files created:

- `range-config.nomad-cluster.yml`
- `Architecture.md`
- `decisions.md`
- `README.md`
- `scripts/render_nomad_lab.py`
- `scripts/apply_ludus_nomad_lab.py`
- `ansible/roles/ludus_nomad_common/...`
- `ansible/roles/ludus_nomad_server/...`
- `ansible/roles/ludus_nomad_client/...`

Important role names in the Ludus config:

- `ludus_nomad_common`
- `ludus_nomad_server`
- `ludus_nomad_client`

## Ludus Connectivity

The user tunneled the Ludus server locally:

- `ssh -L 8081:127.0.0.1:8081 -L 8080:127.0.0.1:8080 root@10.42.0.10`

Relevant endpoints discovered by direct API probing:

- `https://127.0.0.1:8081/user`
- `https://127.0.0.1:8081/user/apikey`
- `https://127.0.0.1:8080/`
- `https://127.0.0.1:8080/range`
- `https://127.0.0.1:8080/range/config`
- `https://127.0.0.1:8080/range/logs`
- `https://127.0.0.1:8080/range/deploy`
- `https://127.0.0.1:8080/ansible`
- `https://127.0.0.1:8080/ansible/role/fromtar`
- `https://127.0.0.1:8080/templates`

Observed behavior:

- `:8081` is user-only. `/range/*` returns a server error telling you to use `:8080`.
- `GET /range/config` returns JSON with the YAML in `result`.
- `PUT /range/config` requires `multipart/form-data` with form field `file`.
- `POST /range/deploy` starts a deployment.
- `PUT /ansible/role/fromtar` requires `multipart/form-data` with form field `file`.
- Uploading local roles works best when the multipart filename is the desired role name.
- `force=true` is accepted on `/ansible/role/fromtar?force=true` and should be used for updates.

## Secrets

Do not commit API keys into the repo.

The session used a working Codex user API key, but it is intentionally not written here. Ask the user for the current key if needed, or use the Ludus tunnel plus a valid key they provide.

## Range Config Notes

`range-config.nomad-cluster.yml` was accepted by Ludus after adding the full required `defaults:` block. Ludus 1.11.2 rejects partial `defaults`.

The config currently:

- uses VLAN `50`
- uses IPs `.11`, `.12`, `.13`, `.21`
- blocks `10.42.0.0/16`
- sets `nomad_deploy_demo_job: false` by default

## Role Upload Notes

Successful pattern used:

1. package a role directory as a `.tar.gz`
2. upload with `PUT /ansible/role/fromtar?force=true`
3. use multipart filename equal to the target role name, e.g. `ludus_nomad_server`

The raw `/ansible` listing is not a reliable guide for config validation unless uploads are named correctly.

## Debugging History

### Fixed already

1. Common role was restarting `nomad` too early.
   - Cause: the common role notified `restart nomad` before the server/client roles placed final config and certs.
   - Fix: removed that notify from `ansible/roles/ludus_nomad_common/tasks/main.yml`.

2. Server/client roles could not see common-role defaults.
   - Cause: Ludus executes roles in separate role contexts; defaults from `ludus_nomad_common` were not available in `ludus_nomad_server`.
   - Fix: added `defaults/main.yml` to both server and client roles.

3. Server/client roles could not find the `restart nomad` handler.
   - Cause: handler scoping is per role in this execution path.
   - Fix: added local `handlers/main.yml` to both server and client roles.

4. `nomad.hcl` was likely unreadable by the `nomad` service user.
   - Cause: config was written `root:root 0640`.
   - Fix: changed group on `nomad.hcl` to `{{ nomad_group }}` in both server and client roles.

5. The packaged Nomad version rejected some ACL config keys.
   - Cause: `nomad 1.9.6` on Debian rejected `default_policy` and `enable_token_persistence` in the server `acl` stanza.
   - Fix: removed those keys from `ansible/roles/ludus_nomad_server/templates/server.hcl.j2`.

6. The server role health check was testing the wrong conditions.
   - Cause: the original probe used `https://127.0.0.1:4646/v1/status/leader`, which fails before quorum even when the agent is healthy, and later `/v1/agent/self` returned `403` before ACL bootstrap.
   - Fix: changed the readiness gate to a simple listener check on `127.0.0.1:4646` in `ansible/roles/ludus_nomad_server/tasks/main.yml`.

7. Role handlers were obscuring startup diagnostics.
   - Cause: handler-driven restarts failed before the role could emit useful service logs.
   - Fix: replaced the server/client restart flow with explicit `systemd` restart tasks in role tasks, and added inline `systemctl` / `journalctl` capture on server restart or probe failure.

8. The Ludus role uploader was not forcing updates.
   - Cause: `scripts/apply_ludus_nomad_lab.py` uploaded to `/ansible/role/fromtar` without `?force=true`.
   - Fix: changed uploads to `/ansible/role/fromtar?force=true`.

9. The systemd hardening override may have been stricter than needed while debugging startup.
   - Cause: `CapabilityBoundingSet` / `AmbientCapabilities` were present in the override.
   - Fix: removed those lines from `ansible/roles/ludus_nomad_common/tasks/main.yml` for now.

### Current live state before this handoff

The latest confirmed deployment is:

- started at `2026-04-17T19:51:59.969625831-04:00`
- ended in `SUCCESS`

The latest confirmed log position is:

- `ludus_nomad_client` on `codex-nomad-client1`
- task: `Restart Nomad client service with the rendered configuration`
- after that, the remaining range-management plays completed and Ludus reported `rangeState: SUCCESS`

The most important state transition since the previous handoff is:

- `srv1`, `srv2`, and `srv3` now all restart Nomad successfully
- each server role reaches `Wait for the Nomad server listener to bind locally`
- that listener check passes on all three servers
- the bootstrap/quorum path was patched and the lab now deploys end-to-end

The original failure point is no longer the problem:

- Nomad is now starting and binding `:4646`
- cluster formation, ACL bootstrap, and client configuration all completed in the latest successful run

Useful confirmed diagnostics from recent runs:

- `nomad 1.9.6` emitted:
  - `acl unexpected keys default_policy, enable_token_persistence`
- later, once Nomad was healthy but not yet clustered:
  - `GET /v1/status/leader` returned `500 No cluster leader`
  - `GET /v1/agent/self` returned `403 Forbidden`
- journal output on `srv1` also showed:
  - `error looking up Nomad servers in Consul`
  - this comes from server join behavior and does not mean Ludus is trying to deploy Consul
  - current templates still use the `server_join` block with `retry_join`
- a later failed run confirmed:
  - `nomad server members` returned `403 (Permission denied)` before ACL bootstrap
  - this was resolved by removing the pre-bootstrap `server members` gate and retrying `nomad acl bootstrap -json` only on the host in `nomad_bootstrap`

## Most Likely Remaining Root Causes

If the current run still fails, inspect these first:

1. Server join behavior is not forming a cluster across `srv1`, `srv2`, and `srv3`.
   - Review:
     - `ansible/roles/ludus_nomad_server/templates/server.hcl.j2`
   - Current symptom:
     - servers bind locally but `srv1` reports `No cluster leader`
     - logs show `agent.joiner: retry join completed: initial_servers=1`
   - Most likely next patch area:
     - simplify or replace the `server_join` block
     - consider explicit `retry_join` / `start_join` syntax appropriate for `1.9.6`
     - verify expected port usage for peer join addresses

2. The bootstrap quorum wait command may be too strict or may be running before the other servers fully settle.
   - File:
     - `ansible/roles/ludus_nomad_server/tasks/main.yml`
   - Current condition:
     - this was a real failure mode in an earlier run
   - Most likely next patch area:
     - re-check bootstrap-node selection first if this regresses
     - the intended control point is the `nomad_bootstrap` group, not `groups["nomad_servers"][0]`

3. Nomad package behavior may differ from current upstream docs because the lab is pinned to `1.9.6-1`.
   - Current pinned version:
     - `1.9.6-1`
   - If join semantics or config behavior keep fighting the lab, consider testing a newer package version that is actually available in the target repo.

4. The lingering `error looking up Nomad servers in Consul` log line may indicate that the current join config is falling into an unexpected discovery path.
   - Treat this as a strong clue against the current `server_join` configuration, not as evidence that Consul should be added.

## Fastest Next Steps

1. Re-check `https://127.0.0.1:8080/range` and `https://127.0.0.1:8080/range/logs`.
2. If the deployment failed again, inspect the tail of logs for:
   - `Wait for cluster quorum from the bootstrap server`
   - any `nomad server members` output or retries
   - any join-related messages from `systemctl status nomad` / `journalctl -u nomad`
3. If the run is stuck in quorum formation, patch in this order:
   - simplify `server_join` behavior in `server.hcl.j2`
   - if needed, add more direct diagnostics around `nomad acl bootstrap -json` or server membership
   - only after that, reconsider Nomad version changes
5. Re-upload changed roles with:
   - `PUT /ansible/role/fromtar?force=true`
6. Re-run:
   - `POST /range/deploy`

## Useful Local Commands

Render config with demo job enabled:

```powershell
$env:NOMAD_DEPLOY_HELLO_WORLD='1'
uv run -- python scripts/render_nomad_lab.py
```

Upload roles/config and deploy:

```powershell
$env:LUDUS_API_KEY='<current-key>'
uv run -- python scripts/apply_ludus_nomad_lab.py --deploy --status
```

## External References Used

- Ludus range configuration docs: https://docs.ludus.cloud/docs/configuration
- Ludus roles docs: https://docs.ludus.cloud/docs/roles/
- Ludus ansible-role developer docs: https://docs.ludus.cloud/docs/developers/ansible-roles/
