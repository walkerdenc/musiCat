import * as dgram from "dgram";

/**
 * Sends a Wake-on-LAN magic packet to wake a sleeping Mac on the local network.
 *
 * @param mac  Target MAC address, e.g. "AA:BB:CC:DD:EE:FF" or "AA-BB-CC-DD-EE-FF"
 * @param opts Optional broadcast address (default 255.255.255.255) and port (default 9)
 */
export function wakeMac(
  mac: string,
  opts: { broadcastAddress?: string; port?: number } = {}
): Promise<void> {
  const { broadcastAddress = "255.255.255.255", port = 9 } = opts;

  const macBytes = parseMac(mac);
  const packet = buildMagicPacket(macBytes);

  return new Promise((resolve, reject) => {
    const socket = dgram.createSocket("udp4");

    socket.once("error", (err) => {
      socket.close();
      reject(err);
    });

    socket.bind(() => {
      socket.setBroadcast(true);
      socket.send(packet, 0, packet.length, port, broadcastAddress, (err) => {
        socket.close();
        if (err) reject(err);
        else {
          console.log(`[WakeOnLan] Magic packet sent to ${mac}`);
          resolve();
        }
      });
    });
  });
}

function parseMac(mac: string): Buffer {
  const hex = mac.replace(/[:\-]/g, "");
  if (hex.length !== 12 || !/^[0-9a-fA-F]{12}$/.test(hex)) {
    throw new Error(`Invalid MAC address: ${mac}`);
  }
  const bytes = Buffer.alloc(6);
  for (let i = 0; i < 6; i++) {
    bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  return bytes;
}

function buildMagicPacket(macBytes: Buffer): Buffer {
  // 6 bytes of 0xFF followed by 16 repetitions of the MAC address = 102 bytes total
  const packet = Buffer.alloc(102);
  packet.fill(0xff, 0, 6);
  for (let i = 0; i < 16; i++) {
    macBytes.copy(packet, 6 + i * 6);
  }
  return packet;
}
