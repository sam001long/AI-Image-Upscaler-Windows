import { put } from "@vercel/blob";
import crypto from "node:crypto";

const ALLOWED_EVENTS = new Set(["app_start", "youtube_click"]);

function clean(value, fallback = "unknown", max = 48) {
  const text = String(value || fallback).trim().toLowerCase();
  return text.replace(/[^a-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, max) || fallback;
}

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Cache-Control", "no-store");

  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") {
    return res.status(405).json({ ok: false, error: "method_not_allowed" });
  }

  const body = typeof req.body === "object" && req.body ? req.body : {};
  const event = String(body.event || "").trim();
  if (!ALLOWED_EVENTS.has(event)) {
    return res.status(400).json({ ok: false, error: "invalid_event" });
  }

  const platform = clean(body.platform, "unknown", 24);
  const version = clean(body.version, "unknown", 40);
  const target = event === "youtube_click" ? clean(body.target, "unknown", 24) : "na";
  const now = new Date();
  const month = now.toISOString().slice(0, 7);
  const stamp = now.toISOString().replace(/[:.]/g, "-");
  const id = crypto.randomBytes(6).toString("hex");
  const pathname = `events/${month}/${event}/${platform}/${version}/${target}/${stamp}-${id}.json`;

  try {
    await put(
      pathname,
      JSON.stringify({ event, platform, version, target, at: now.toISOString() }),
      {
        access: "private",
        contentType: "application/json",
        token: process.env.BLOB_READ_WRITE_TOKEN
      }
    );
    return res.status(200).json({ ok: true });
  } catch (error) {
    console.error("blob analytics write failed", error);
    return res.status(200).json({ ok: false, error: "track_failed" });
  }
}
