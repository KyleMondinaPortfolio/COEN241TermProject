# COEN 241 Term Project

## Overview

Our project is an implementation of a Chord P2P based version of OpenStack with security mechanisms against routing attacks using the Sechord hop verification protocol, as outlined in the paper "Secure routing in peer-to-peer distributed hash tables" from the Proceedings of the 2009 ACM symposium on Applied Computing.

## Usage

### Demo Assumptions
The demo of this implementation is built on the assumption that you are in SCU’s ECC and the machines you use have SSH permissions for access.

### Setup

1. **Configure `globals.py`:**
   - Set the necessary port (`PORT`).
   - Define the hash function space (`M`).
   - Specify the directory you wish to use (`USER`).

2. **Initialize the First Node:**
   ```bash
   python3 starting_node.py {self.ip}
   ```

3. **Add a New Node:**
   ```bash
   python3 new_node.py {self.ip} {bootstrap_ip}
   ```
### Stabilization

In a proper Chord implementation, the stabilize protocol runs automatically in the background. For this demo, we manually run stabilize on nodes to speed up network stabilization.

- **Manually Run Stabilize:**
   ```bash
    stabilize
    ```

- **Check Node’s Predecessor and Successor:**

   ```bash
    info
    ```
- Run stabilize on all nodes until info shows a circular dependency on all nodes.


### Node Failure
When a node is dropped, its successor and predecessor need to run:

```bash
reconcile
```
Then, the stabilize protocol needs to be run on the whole network to re-establish a ring.

### File Operations
