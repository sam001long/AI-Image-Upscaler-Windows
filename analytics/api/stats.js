import { list } from "@vercel/blob";

function validMonth(value) {
  return /^\d{4}-\d{2}$/.test(value || "");
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");

  if (req.method !== "GET") {
    return res.status(405).json({ ok: false, error: "method_not_allowed" });
  }

  const key = String(req.query.key || "");
  if (!process.env.BIGIMG_STATS_KEY || key !== process.env.BIGIMG_STATS_KEY) {
    return res.status(401).json({ ok: false, error: "unauthorized" });
  }

  const requested = String(req.query.month || "");
  const month = validMonth(requested) ? requested : new Date().toISOString().slice(0, 7);
  const prefix = `events/${month}/`;

  const summary = {
    month,
    total_events: 0,
    app_start: 0,
    youtube_click: 0,
    platforms: {},
    versions: {},
    youtube_targets: {}
  };

  let cursor;
  try {
    do {
      const result = await list({
        prefix,
        cursor,
        limit: 1000,
        token: process.env.BLOB_READ_WRITE_TOKEN
      });

      for (const blob of result.blobs) {
        const parts = blob.pathname.split("/");
        // events/YYYY-MM/event/platform/version/target/file.json
        if (parts.length < 7) continue;
        const [, , event, platform, version, target] = parts;

        summary.total_events += 1;
        if (event === "app_start") summary.app_start += 1;
        if (event === "youtube_click") summary.youtube_click += 1;

        summary.platforms[platform] = (summary.platforms[platform] || 0) + 1;
        summary.versions[version] = (summary.versions[version] || 0) + 1;
        if (event === "youtube_click") {
          summary.youtube_targets[target] = (summary.youtube_targets[target] || 0) + 1;
        }
      }

      cursor = result.cursor;
    } while (cursor);

    summary.youtube_click_rate_percent =
      summary.app_start > 0
        ? Number(((summary.youtube_click / summary.app_start) * 100).toFixed(1))
        : 0;

    return res.status(200).json({ ok: true, ...summary });
  } catch (error) {
    console.error("stats read failed", error);
    return res.status(500).json({ ok: false, error: "stats_failed" });
  }
}
