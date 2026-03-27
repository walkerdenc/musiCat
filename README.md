# musiCat

A music player for Mac.

## Wake Mac

The **Wake Mac** feature prevents macOS from sleeping while music is playing. It uses the built-in `caffeinate` utility to suppress idle sleep, display sleep, and system sleep (on AC power).

### Usage

```typescript
import { WakeMac } from "./src/wakeMac";

const wakeMac = new WakeMac();

// Call when playback starts
wakeMac.start();

// Call when playback stops or is paused
wakeMac.stop();

// Check current state
console.log(wakeMac.isActive()); // true / false
```

### How it works

`WakeMac` spawns a `caffeinate -i -d -s` child process when music starts playing and terminates it when playback stops. It is a no-op on non-macOS platforms.

## Wake My Mac (Wake-on-LAN)

The **Wake My Mac** feature sends a Wake-on-LAN magic packet over UDP to wake a sleeping Mac on your local network.

> **Prerequisite:** Enable "Wake for network access" in System Settings → Energy on the target Mac.

### Usage

```typescript
import { wakeMac } from "./src/wakeOnLan";

// Wake the Mac with the given MAC address
await wakeMac("AA:BB:CC:DD:EE:FF");

// Optionally specify a subnet broadcast address and port
await wakeMac("AA:BB:CC:DD:EE:FF", {
  broadcastAddress: "192.168.1.255",
  port: 9,
});
```

### How it works

`wakeMac` builds a 102-byte magic packet (6×`0xFF` + 16 repetitions of the target MAC address) and broadcasts it via UDP. The sleeping Mac's network adapter recognises the packet and powers the machine on.