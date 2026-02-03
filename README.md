# Tor Network Node Tracker

[![Relay Nodes](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fdoodad-labs%2Ftor-nodes%2Frefs%2Fheads%2Fmain%2Fstats%2Frelay-nodes.json&style=flat-square&cache=1)](https://github.com/doodad-labs/tor-nodes/blob/main/active/relay-nodes.txt)
[![Guard Nodes](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fdoodad-labs%2Ftor-nodes%2Frefs%2Fheads%2Fmain%2Fstats%2Fguard-nodes.json&style=flat-square&cache=1)](https://github.com/doodad-labs/tor-nodes/blob/main/active/guard-nodes.txt)
[![Exit Nodes](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fdoodad-labs%2Ftor-nodes%2Frefs%2Fheads%2Fmain%2Fstats%2Fexit-nodes.json&style=flat-square&cache=1)](https://github.com/doodad-labs/tor-nodes/blob/main/active/exit-nodes.txt)

An automated hourly archive of active Tor network nodes with comprehensive historical tracking. This repository provides structured datasets of relay, exit, and guard nodes for research, monitoring, and analysis purposes.

This system continuously monitors and archives Tor network infrastructure by collecting data directly from the Tor network every hour. The data is categorized into three distinct node types and preserved with complete historical records for longitudinal analysis.

## Node Categories

- **Relay Nodes**: All active relays operating within the Tor network, forming the core infrastructure for traffic routing.
- **Exit Nodes**: Specialized relays configured to allow traffic to exit the Tor network and reach the public internet.
- **Guard Nodes**: Entry points to the Tor network, selected as the first hop in circuit creation due to their stability and performance.

## Repository Structure

```
├── active/                     # Current node lists (hourly updates)
│   ├── relay-nodes.json        # All active relays (JSON)
│   ├── relay-nodes.txt         # All active relays (Plain text)
│   ├── exit-nodes.json         # Exit-capable relays (JSON)
│   ├── exit-nodes.txt          # Exit-capable relays (Plain text)
│   ├── guard-nodes.json        # Guard-capable relays (JSON)
│   └── guard-nodes.txt         # Guard-capable relays (Plain text)
│
└── history/                    # Historical archives
     └── YYYY/
         └── MM/
             └── YYYY-MM-DD/            # Daily snapshots
                 ├── relay-nodes.json   # All active relays (JSON)
                 ├── relay-nodes.txt    # All active relays (Plain text)
                 ├── exit-nodes.json    # Exit-capable relays (JSON)
                 ├── exit-nodes.txt     # Exit-capable relays (Plain text)
                 ├── guard-nodes.json   # Guard-capable relays (JSON)
                 └── guard-nodes.txt    # Guard-capable relays (Plain text)
```

## Data Specifications

- **Update Frequency:** Hourly synchronization  
- **Data Source:** Direct Tor network queries  
- **Formats Available:**
  - **JSON** – Structured data for programmatic access and analysis
  - **Plain Text** – Human-readable format for quick reference and simple parsing
- **Retention:** Complete historical records with daily organization

## Ethical Consideration

**Bridge nodes will never be tracked or published.** We recognize that publishing bridge node information would directly harm users in censored regions who rely on these resources for safe access to the Tor network. This repository is intentionally limited to publicly discoverable relay infrastructure only.

## Usage

The data is suitable for:
- Network research and analysis
- Security monitoring and threat intelligence
- Academic studies of decentralized networks
- Infrastructure monitoring and visualization projects

## Automation

All data collection, processing, and archiving is fully automated through scheduled workflows, ensuring consistent updates without manual intervention.

## Outage History

Sometimes monitoring systems go offline or break this is a log of all them instances.

- `02/02/2026 @ 6:21 PM - 02/02/2026 @ 11:09 PM` [github actions outages](https://www.githubstatus.com/incidents/xwn6hjps36ty) 
