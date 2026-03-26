import { spawn, ChildProcess } from "child_process";
import { platform } from "os";

/**
 * WakeMac prevents the Mac from sleeping while music is playing.
 *
 * Uses macOS's built-in `caffeinate` utility:
 *   -i  prevent idle sleep
 *   -d  prevent display sleep
 *   -s  prevent system sleep (when on AC power)
 */
export class WakeMac {
  private process: ChildProcess | null = null;
  private active = false;

  /** Start preventing sleep. No-op on non-macOS platforms. */
  start(): void {
    if (platform() !== "darwin") return;
    if (this.active) return;

    this.process = spawn("caffeinate", ["-i", "-d", "-s"], {
      stdio: "ignore",
      detached: false,
    });

    this.process.on("error", (err) => {
      console.error("[WakeMac] Failed to start caffeinate:", err.message);
      this.active = false;
      this.process = null;
    });

    this.process.on("exit", () => {
      this.active = false;
      this.process = null;
    });

    this.active = true;
    console.log("[WakeMac] Sleep prevention started.");
  }

  /** Stop preventing sleep. */
  stop(): void {
    if (!this.active || !this.process) return;

    this.process.kill("SIGTERM");
    this.process = null;
    this.active = false;
    console.log("[WakeMac] Sleep prevention stopped.");
  }

  /** Returns true if currently preventing sleep. */
  isActive(): boolean {
    return this.active;
  }
}
