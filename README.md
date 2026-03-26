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