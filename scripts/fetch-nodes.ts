/* 

     _____                  _           _ _           _         
    │  __ ╲                │ │         │ │ │         │ │        
    │ │  │ │ ___   ___   __│ │ __ _  __│ │ │     __ _│ │__  ___ 
    │ │  │ │╱ _ ╲ ╱ _ ╲ ╱ _` │╱ _` │╱ _` │ │    ╱ _` │ '_ ╲╱ __│
    │ │__│ │ (_) │ (_) │ (_│ │ (_│ │ (_│ │ │___│ (_│ │ │_) ╲__ ╲
    │_____╱ ╲___╱ ╲___╱ ╲__,_│╲__,_│╲__,_│______╲__,_│_.__╱│___╱

    https://github.com/doodad-labs/tor-node-tracker-action

*/

import fs from 'fs/promises';
import moment from 'moment';
import { isIP } from 'net';

// Base URL for fetching historical data from the GitHub repository
const REPO = "https://raw.githubusercontent.com/doodad-labs/tor-node-tracker/refs/heads/main/"
const TOR_RELAY_NODES_URL = "https://onionoo.torproject.org/details?type=relay&running=true&fields=or_addresses,flags";

// Main function to fetch and process Tor relay nodes
async function main() {

    // Get the current year, month, and day in UTC format
    const year = moment().utc().format('YYYY');
    const month = moment().utc().format('MM');
    const today = moment().utc().format('YYYY-MM-DD');

    // Create necessary directories for output
    await fs.mkdir('out/active', { recursive: true });
    await fs.mkdir('out/stats', { recursive: true });
    await fs.mkdir(`out/history/${year}/${month}/${today}`, { recursive: true });

    // Initialize pagination and retry variables
    let page: number = 0;
    const limit: number = 1000;
    let retries: number = 0;

    // Set to store detailed relay information
    let detailedRelays: Set<string> = new Set<string>();
    let morePages: boolean = true;

    // Loop to fetch relay nodes with pagination
    while (morePages) {
        const url = `${TOR_RELAY_NODES_URL}&offset=${(page) * limit}&limit=${limit}`;

        // Fetch the relay nodes from the declared API
        const request = await fetch(url).catch(() => null);
        console.log(`Fetching nodes from: ${url}`);

        // Check if the request was successful
        if (!request || !request.ok) {
            retries++;
            if (retries >= 3) {
                throw new Error(`Failed to fetch Tor relay nodes after ${retries} attempts`);
            }
            continue;
        }

        // Parse the JSON response
        const response = await request.json().catch(() => null);

        // Check if the response contains the expected data
        if (!response || !response.relays) {
            retries++
            if (retries >= 3) {
                throw new Error(`Failed to parse Tor relay nodes after ${retries} attempts`);
            }
            continue;
        }

        // If no relays are returned, we've reached the end of the pages
        if (response.relays.length === 0) {
            morePages = false;
            break;
        }

        // Process the relay data to extract addresses and flags
        const relays = response.relays.map((relay: any) => {
            const addresses = relay.or_addresses.map((addr: string) => {
                // Handle IPv6 addresses wrapped in [ ] with port
                if (addr.startsWith('[')) {
                    // Find the closing bracket and get everything inside
                    const endBracketIndex = addr.indexOf(']');
                    if (endBracketIndex !== -1) {
                        return addr.slice(1, endBracketIndex);
                    }
                    // If no closing bracket found, remove leading '[' and any port after ':'
                    return addr.slice(1).split(':')[0];
                }

                // Handle IPv4 addresses with port
                const parts = addr.split(':');
                if (parts.length === 2 && isIP(parts[0]) === 4) {
                    return parts[0];
                }

                // Handle IPv4 addresses without port
                if (isIP(addr) === 4) {
                    return addr;
                }

                // For any other format, return as-is or handle as needed
                return addr;
            });

            const flags = relay.flags || [];

            return {
                addresses,
                isExit: flags.includes('Exit'),
                isGuard: flags.includes('Guard')
            };

        }).flat()

        // Add the detailed relay information to the set
        detailedRelays = new Set<string>([
            ...detailedRelays, 
            ...relays
        ]);

        // Move to the next page and reset retries
        page++;
        retries = 0;
    }

    // Check if any relay data was retrieved
    if (detailedRelays.size === 0) {
        throw new Error("No relay data retrieved.");
    }

    // Extract unique addresses for relays, guards, and exits
    const relaysAddresses = new Set<string>(Array.from(detailedRelays).map((relay: any) => relay.addresses).flat());
    const guardsAddresses = new Set<string>(Array.from(detailedRelays).filter((relay: any) => relay.isGuard).map((relay: any) => relay.addresses).flat());
    const exitsAddresses = new Set<string>(Array.from(detailedRelays).filter((relay: any) => relay.isExit).map((relay: any) => relay.addresses).flat());

    // Log the total counts of relays, guards, and exits
    console.log(`Total Relays: ${relaysAddresses.size}`);
    console.log(`Total Guards: ${guardsAddresses.size}`);
    console.log(`Total Exits: ${exitsAddresses.size}`);

    // Process each type of node (relay, guard, exit) and save the data to files
    ['relay', 'guard', 'exit'].forEach(async (type) => {
        let addresses: Set<string>;

        if (type === 'relay') {
            addresses = relaysAddresses;
        } else if (type === 'guard') {
            addresses = guardsAddresses;
        } else {
            addresses = exitsAddresses;
        }

        // Filter and sort the addresses, ensuring only valid IPs are included
        const addrArray = Array.from(addresses).sort().filter((addr) => isIP(addr) !== 0);

        // Save the active nodes to JSON and TXT files
        await fs.writeFile(`out/active/${type}-nodes.json`, JSON.stringify(addrArray));
        await fs.writeFile(`out/active/${type}-nodes.txt`, addrArray.join('\n'));
        await fs.writeFile(`out/active/${type}-nodes.csv`, addrArray.join(','));

        // Attempt to fetch historical data for today's date and merge with current data
        const todaysNodes = `${REPO}history/${today}/${type}-nodes.json`;
        const historyResponse = await fetch(todaysNodes).catch(() => null);
        
        let newList: string[] = addrArray;

        // If historical data exists, merge it with the current data and save; otherwise, save only the current data
        if (historyResponse && historyResponse.ok) {
            const json = await historyResponse.json();
            newList = Array.from(new Set([
                ...json,
                ...addrArray
            ])).sort();
        }

        await fs.writeFile(`out/history/${year}/${month}/${today}/${type}-nodes.json`, JSON.stringify(newList));
        await fs.writeFile(`out/history/${year}/${month}/${today}/${type}-nodes.txt`, newList.join('\n'));
        await fs.writeFile(`out/history/${year}/${month}/${today}/${type}-nodes.csv`, newList.join(','));

        // Create an endpoint info object with the count of active nodes and save it to a stats file
        const endpointInfo = {
            "schemaVersion": 1,
            "label": `active ${type} nodes`,
            "message": `${addrArray.length.toLocaleString()}`,
            "color": "#56bda4"
        }

        // Save the endpoint info to a JSON file in the stats directory
        await fs.writeFile(`out/stats/${type}-nodes.json`, JSON.stringify(endpointInfo));
    })

}

// Execute the main function and handle any errors that occur
void main().catch((err) => {
    console.error("Error:", err);
    process.exit(1);
});
