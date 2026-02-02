import fs from 'fs/promises';
import moment from 'moment';
import { isIP } from 'net';

const REPO = "https://raw.githubusercontent.com/doodad-labs/tor-nodes/refs/heads/main/"
const TOR_RELAY_NODES_URL = "https://onionoo.torproject.org/details?type=relay&running=true&fields=or_addresses,flags";

async function main() {

    const year = moment().utc().format('YYYY');
    const month = moment().utc().format('MM');
    const today = moment().utc().format('YYYY-MM-DD');
    await fs.mkdir('out', { recursive: true });
    await fs.mkdir('out/active', { recursive: true });
    await fs.mkdir('out/stats', { recursive: true });
    await fs.mkdir('out/history', { recursive: true });
    await fs.mkdir(`out/history/${year}`, { recursive: true });
    await fs.mkdir(`out/history/${year}/${month}`, { recursive: true });
    await fs.mkdir(`out/history/${year}/${month}/${today}`, { recursive: true });

    let page: number = 0;
    const limit: number = 1000;
    let retries: number = 0;

    let detailedRelays: Set<string> = new Set<string>();
    let morePages: boolean = true;

    while (morePages) {
        const url = `${TOR_RELAY_NODES_URL}&offset=${(page) * limit}&limit=${limit}`;
        
        const request = await fetch(url).catch(() => null);
        console.log(`Fetching nodes from: ${url}`);

        if (!request || !request.ok) {
            retries++;
            if (retries >= 3) {
                throw new Error(`Failed to fetch Tor relay nodes after ${retries} attempts`);
            }
            continue;
        }

        const response = await request.json().catch(() => null);

        if (!response || !response.relays) {
            retries++
            if (retries >= 3) {
                throw new Error(`Failed to parse Tor relay nodes after ${retries} attempts`);
            }
            continue;
        }

        if (response.relays.length === 0) {
            morePages = false;
            break;
        }

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

        detailedRelays = new Set<string>([...detailedRelays, ...relays]);

        page++;
        retries = 0;
    }

    if (detailedRelays.size === 0) {
        throw new Error("No relay data retrieved.");
    }

    const relaysAddresses = new Set<string>(Array.from(detailedRelays).map((relay: any) => relay.addresses).flat());
    const guardsAddresses = new Set<string>(Array.from(detailedRelays).filter((relay: any) => relay.isGuard).map((relay: any) => relay.addresses).flat());
    const exitsAddresses = new Set<string>(Array.from(detailedRelays).filter((relay: any) => relay.isExit).map((relay: any) => relay.addresses).flat());

    console.log(`Total Relays: ${relaysAddresses.size}`);
    console.log(`Total Guards: ${guardsAddresses.size}`);
    console.log(`Total Exits: ${exitsAddresses.size}`);


    ['relay', 'guard', 'exit'].forEach(async (type) => {
        let addresses: Set<string>;

        if (type === 'relay') {
            addresses = relaysAddresses;
        } else if (type === 'guard') {
            addresses = guardsAddresses;
        } else {
            addresses = exitsAddresses;
        }

        const addrArray = Array.from(addresses).sort().filter((addr) => isIP(addr) !== 0);

        await fs.writeFile(`out/active/${type}-nodes.json`, JSON.stringify(addrArray));
        await fs.writeFile(`out/active/${type}-nodes.txt`, addrArray.join('\n'));

        const todaysNodes = `${REPO}history/${today}/${type}-nodes.json`;
        const historyResponse = await fetch(todaysNodes).catch(() => null);
        if (historyResponse && historyResponse.ok) {
            const json = await historyResponse.json();
            const newList = Array.from(new Set([
                ...json,
                ...addrArray
            ])).sort();
            await fs.writeFile(`out/history/${year}/${month}/${today}/${type}-nodes.json`, JSON.stringify(newList));
            await fs.writeFile(`out/history/${year}/${month}/${today}/${type}-nodes.txt`, newList.join('\n'));
        } else {
            await fs.writeFile(`out/history/${year}/${month}/${today}/${type}-nodes.json`, JSON.stringify(addrArray));
            await fs.writeFile(`out/history/${year}/${month}/${today}/${type}-nodes.txt`, addrArray.join('\n'));
        }

        const endpointInfo = { 
            "schemaVersion": 1, 
            "label": `active ${type} nodes`, 
            "message": `${addrArray.length}`, 
            "color": "#56bda4" 
        }

        await fs.writeFile(`out/stats/${type}-nodes.json`, JSON.stringify(endpointInfo));
    })

}

main().catch((err) => {
    console.error("Error:", err);
    process.exit(1);
});
