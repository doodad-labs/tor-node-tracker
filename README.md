# Tor Network Node Tracker

Automated hourly archive of active Tor network nodes (relay/exit/guard) with current and historical data.

This repository provides automated tracking and archiving of Tor network nodes. The system collects data hourly, categorizing nodes into three groups: relay nodes (all active relays), exit nodes (relays that permit exiting traffic), and guard nodes (relays designated as entry guards).

## Data Collection

Data is sourced directly from the Tor network and updated every hour. Each update captures the current state of active nodes across all three categories. Historical data is preserved for reference and analysis.

## Repository Structure

- [`active/`](/active) - Contains the most recent node lists, updated hourly. Files include JSON and plain text formats for each node category.
- `history/YYYY-MM-DD/` - Historical archives organized by date, preserving daily snapshots of node activity.

## Update Schedule

Updates occur automatically every hour. The system maintains both current active node lists and historical archives without manual intervention.

## Data Formats

Two formats are provided for each node category and timestamp:
- JSON format for programmatic access and structured data processing
- Plain text format for human readability and simple parsing

## Usage

This data can be used for network analysis, security research, Tor network monitoring, or as a reference dataset for academic studies. The historical archives enable tracking of node availability and network changes over time.

## Categories

Three node categories are tracked:
- Relay nodes: All active relays in the Tor network
- Exit nodes: Relays configured to allow traffic to exit the Tor network
- Guard nodes: Relays suitable for use as entry points to the Tor network (Entry nodes)
