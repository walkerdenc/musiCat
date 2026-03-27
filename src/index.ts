import { WakeMac } from "./wakeMac";

const wakeMac = new WakeMac();

// Example: integrate with music playback lifecycle
function onPlaybackStarted(): void {
  wakeMac.start();
}

function onPlaybackStopped(): void {
  wakeMac.stop();
}

// Ensure sleep prevention is released on process exit
process.on("exit", () => wakeMac.stop());
process.on("SIGINT", () => {
  wakeMac.stop();
  process.exit(0);
});
process.on("SIGTERM", () => {
  wakeMac.stop();
  process.exit(0);
});

export { WakeMac, onPlaybackStarted, onPlaybackStopped };
export { wakeMac } from "./wakeOnLan";
