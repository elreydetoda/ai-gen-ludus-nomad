# Ludus Nomad Lab

This repository contains a Ludus range definition and local Ansible roles for a 3-server, 1-client HashiCorp Nomad lab.

Files of interest:

- `range-config.nomad-cluster.yml` - Ludus range definition
- `ansible/roles/ludus_nomad_common` - shared installation and PKI logic
- `ansible/roles/ludus_nomad_server` - Nomad server configuration and ACL bootstrap
- `ansible/roles/ludus_nomad_client` - Nomad client configuration
- `scripts/render_nomad_lab.py` - renders the range config and toggles the demo job from env vars
- `Architecture.md` - architecture walkthrough
- `decisions.md` - implementation and security decisions

The lab defaults to Debian 12, one VLAN for the cluster (`10.5.50.0/24`), three Nomad servers with integrated Raft, one Nomad client with Docker enabled, and TLS, ACLs, and gossip encryption enabled.

Set `NOMAD_DEPLOY_HELLO_WORLD=1` before rendering if you want the role to submit a simple Docker-backed demo job after the cluster comes up.

**Other setup notes:**
- Utilized the local skill in this repo + an ssh local port-forward (`ssh -L 8081:127.0.0.1:8081 -L 8080:127.0.0.1:8080 root@<ludus_server>`) to the ludus server allow it to keep iterating quicker over localhost API requests
- Generated a dedicated non-admin token for codex with this
   ```
    export LUDUS_API_KEY='<admin_token>'
   ludus user add --name "Codex" --userid codex --url https://127.0.0.1:8081
   # continued to monitor from admin user:
   ludus range status --user codex
   ```