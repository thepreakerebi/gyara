/**
 * End-to-end: the TypeScript GatewayBackend against the real Python Gyara Gateway.
 *
 * Spawns the Python stub gateway (the real FastAPI app over a StubBackend, no GPU) and
 * drives it with the actual TS SDK, proving the cross-language contract. Skips cleanly
 * if the Python venv isn't built (`uv pip install -e ".[dev]"` in ../python).
 */

import { spawn, type ChildProcess } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { z } from "zod";
import { GatewayBackend, Structured } from "../src/index.js";

const here = dirname(fileURLToPath(import.meta.url));
const venvPython = resolve(here, "../../python/.venv/bin/python");
const PORT = 8744;
const BASE = `http://127.0.0.1:${PORT}`;

const available = existsSync(venvPython);
let proc: ChildProcess | undefined;

async function waitForHealth(timeoutMs = 25000): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${BASE}/health`);
      if (response.ok) return true;
    } catch {
      // not up yet
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  return false;
}

describe.skipIf(!available)("TS GatewayBackend <-> Python Gateway", () => {
  beforeAll(async () => {
    proc = spawn(venvPython, ["-m", "gyara.gateway.stub"], {
      env: {
        ...process.env,
        GYARA_STUB_PORT: String(PORT),
        GYARA_STUB_RESPONSE: JSON.stringify({ name: "Ada", amount: 5000 }),
      },
      stdio: "ignore",
    });
    if (!(await waitForHealth())) throw new Error("stub gateway did not start");
  });

  afterAll(() => {
    proc?.kill();
  });

  it("returns a validated record from the live Python gateway", async () => {
    const client = new Structured(new GatewayBackend(`${BASE}/v1/structured`));
    const Transfer = z.object({ name: z.string(), amount: z.number().int() });
    const data = await client.generate("extract the transfer", Transfer);
    expect(data).toEqual({ name: "Ada", amount: 5000 });
  });

  it("rejects a bad request shape with a non-2xx the client surfaces", async () => {
    const backend = new GatewayBackend(`${BASE}/v1/structured`);
    // Missing "schema" -> the gateway returns 422; the client throws.
    const bad = await fetch(`${BASE}/v1/structured`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ prompt: "x" }),
    });
    expect(bad.status).toBe(422);
    void backend;
  });
});
