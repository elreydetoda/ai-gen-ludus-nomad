# Architecture

## Topology

The lab creates four Debian 12 virtual machines in a single Ludus VLAN:

- `{{ range_id }}-nomad-srv1` at `10.5.50.11`
- `{{ range_id }}-nomad-srv2` at `10.5.50.12`
- `{{ range_id }}-nomad-srv3` at `10.5.50.13`
- `{{ range_id }}-nomad-client1` at `10.5.50.21`

All four nodes live in VLAN `50`, which keeps the initial cluster simple while still letting you explore Nomad server and client behavior separately.

## Cluster Model

This deployment uses three Nomad servers, one dedicated Nomad client, integrated Raft for Nomad state storage, and Docker as the workload driver on the client.

This is the smallest topology that still demonstrates quorum, leader election, Raft replication, ACL bootstrap, and real workload scheduling.

## Security Model

The cluster is configured with the main control-plane protections you would expect in a production-oriented Nomad deployment:

- TLS enabled for HTTP and RPC
- mutual TLS between agents
- hostname verification enabled for servers
- ACLs enabled with default deny
- token persistence enabled
- Serf gossip encryption enabled
- package installation from signed repositories
- Nomad service hardening via a systemd override

The role also generates a CLI certificate and installs a shell profile so local administration commands on the VMs use TLS consistently.

## PKI Design

The deployment generates a small private CA during Ansible execution and signs:

- one shared server certificate used by all Nomad servers
- one shared client certificate used by Nomad clients
- one shared CLI certificate for operator commands

This is intentionally simple for a learning lab. It keeps the PKI understandable while still enforcing TLS and mutual authentication. In a larger production system, you would normally issue node-specific certificates from an external CA workflow.

## ACL Flow

After the three servers form quorum, the bootstrap server waits for healthy server membership, runs `nomad acl bootstrap`, and stores the bootstrap token in `/etc/nomad.d/bootstrap.token`.

## Optional Demo Workload

If `nomad_deploy_demo_job` is set to `true`, the bootstrap server submits a simple job that runs `hashicorp/http-echo` on the client through the Docker driver.

## Operational Walkthrough

After deployment, useful commands on a server include:

```bash
source /etc/profile.d/nomad.sh
export NOMAD_TOKEN="$(cat /etc/nomad.d/bootstrap.token)"
nomad server members
nomad node status
nomad job status
nomad status
```
