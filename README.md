# Secure OpenStack Peer-to-Peer Object Storage System

## Overview

This project implements a **Secure Peer-to-Peer (P2P) Object Storage System** for OpenStack, enhancing the scalability, fault tolerance, and security of OpenStack's object storage component. By transitioning from a traditional client-server architecture to a decentralized P2P model, the project addresses key limitations in performance, security, and scalability. The P2P architecture employs the **Sechord** algorithm, which is designed to defend against routing attacks while maintaining efficient data distribution and retrieval across nodes.

## Authors

- Kyle Felip Mondina
- Madhuri Sharma
- Chen Zhang

This project was completed as part of COEN 241 - Cloud Computing at Santa Clara University under the guidance of Professor Ming-Hwa Wang.

## Table of Contents

- [Introduction](#introduction)
- [Objective](#objective)
- [Problem Description](#problem-description)
- [Our Solution](#our-solution)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Testing and Simulation](#testing-and-simulation)
- [Results](#results)
- [Future Work](#future-work)

## Introduction

In modern cloud systems, scalability, fault tolerance, and security are critical for efficient resource distribution and reliable data storage. OpenStack, a prominent cloud platform, offers object storage solutions, but its current architecture has vulnerabilities to routing attacks. This project reimagines OpenStack's object storage using a secure P2P architecture to enhance performance and provide resilience against malicious activities.

## Objective

The primary goal of this project is to design and implement a **Secure P2P Object Storage System** for OpenStack that:

- Improves scalability and fault tolerance through decentralized data storage and retrieval.
- Protects against **routing attacks** by employing robust security measures within a P2P architecture.
- Ensures efficient load distribution and high performance, even under malicious attacks.

## Problem Description

OpenStack’s existing object storage system, while functional, faces several challenges:
- Vulnerability to routing attacks that compromise data integrity and availability.
- Performance issues such as high latency and inconsistent scaling under heavy load.
- Complexity in deployment and management.
  
## Our Solution

We propose a secure P2P system using the **Sechord routing algorithm**, which improves upon traditional Chord-based systems by introducing security checks at each routing step. Key features of our solution include:
- **Hop Verification**: Mitigates the risk of routing attacks by verifying the validity of each routing hop.
- **Decentralized Object Storage**: Reduces the load on central servers, distributing the data across the network for better scalability.
- **Malicious Node Detection**: Identifies and isolates malicious nodes to maintain the integrity of the system.

## Architecture

The architecture is based on a **modified Chord** distributed hash table (DHT) structure with added security features to defend against common routing attacks. The key architectural components are:
1. **Sechord Algorithm**: Secure routing protocol for mitigating malicious attacks.
2. **P2P Object Storage**: Decentralized system where each node is responsible for storing, retrieving, and replicating data.

## Installation

To run this project, you'll need:

- **Python** (version 3.x)
- **OpenStack Swift** for object storage
- **NSL-KDD dataset** (for simulating network attacks)

Clone the repository and install necessary dependencies:

```bash
git clone https://github.com/your-repository/secure-openstack-p2p-storage.git
cd secure-openstack-p2p-storage
pip install -r requirements.txt
