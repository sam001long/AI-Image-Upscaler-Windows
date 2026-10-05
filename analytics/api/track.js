import { track } from "@vercel/analytics/server";

const ALLOWED_EVENTS = new Set(["app_start", "youtube_click"]);

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    return res.status(204).end();
  }
  if (req.method !== "POST") {
    return res.status(405).json({ ok: false, error: "method_not_allowed" });
  }

  const body = typeof req.body === "object" && req.body ? req.body : {};
  const event = String(body.event || "").trim();
  if (!ALLOWED_EVENTS.has(event)) {
    return res.status(400).json({ ok: false, error: "invalid_event" });
  }

  const platform = String(body.platform || "unknown").slice(0, 32);
  const version = String(body.version || "unknown").slice(0, 64);
  const app = String(body.app || "BigIMG").slice(0, 32);

  try {
    await track(event, { app, platform, version });
    return res.status(200).json({ ok: true });
  } catch (error) {
    console.error("track failed", error);
    return res.status(200).json({ ok: false, error: "track_failed" });
  }
}
