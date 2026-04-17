# Decisions

## Base OS

Decision: Use `debian-12-x64-server-template` for all four machines.

Reasoning:

- it is already available in your Ludus environment
- it keeps package behavior consistent across servers and client
- Debian 12 is stable enough for a reproducible lab

## Nomad Storage Backend

Decision: Use Nomad integrated Raft instead of adding Consul.

Reasoning:

- it keeps the lab focused on Nomad itself
- three servers are enough to demonstrate quorum and replication
- it avoids adding a second distributed system before you are comfortable with the first

## Separate Client Node

Decision: Run workloads on a dedicated client instead of on the servers.

Reasoning:

- it cleanly separates control plane from workload plane
- it reduces accidental resource contention on the servers
- it more closely reflects a production operating model

## Security Defaults

Decision: Enable TLS, ACLs, and gossip encryption from the start.

Reasoning:

- it avoids building a habit of starting with an insecure cluster and adding security later
- it gives you hands-on exposure to the parts of Nomad operators actually manage
- it better matches the production-oriented requirement for this lab

## Demo Job Toggle

Decision: Keep the demo job disabled by default and enable it through an environment-variable-driven render step.

Mechanism:

- `NOMAD_DEPLOY_HELLO_WORLD=1` before running `scripts/render_nomad_lab.py`
