import { list } from "@vercel/blob";

const add = (o, k) => { k = String(k || "unknown"); o[k] = (o[k] || 0) + 1; };

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "GET") return res.status(405).json({ ok:false, error:"method_not_allowed" });
  if (!process.env.BIGIMG_STATS_KEY || String(req.query.key || "") !== process.env.BIGIMG_STATS_KEY) {
    return res.status(401).json({ ok:false, error:"unauthorized" });
  }

  const month = /^\d{4}-\d{2}$/.test(String(req.query.month || ""))
    ? String(req.query.month)
    : new Intl.DateTimeFormat("en-CA", { timeZone:"Asia/Taipei", year:"numeric", month:"2-digit" }).format(new Date());

  const s = {
    ok:true, month, timezone:"Asia/Taipei",
    total_events:0, app_start:0, youtube_click:0,
    average_youtube_clicks_per_start:0,
    platforms:{}, versions:{}, youtube_targets:{},
    by_day:{}, by_hour:{},
    hardware:{ architectures:{}, ram_gb:{}, cpu_cores:{}, gpu:{}, vram_gb:{} }
  };

  let cursor;
  do {
    const r = await list({ prefix:`events-v2/${month}/`, cursor, limit:1000, token:process.env.BLOB_READ_WRITE_TOKEN });
    for (const b of r.blobs) {
      const p = b.pathname.split("/");
      if (p.length < 14) continue;
      const [, , day, hour, event, platform, version, arch, ram, cores, vram, gpu, target] = p;
      s.total_events++;
      if (event === "app_start") s.app_start++;
      if (event === "youtube_click") s.youtube_click++;
      add(s.platforms, platform); add(s.versions, version);
      add(s.by_day, day); add(s.by_hour, hour);
      add(s.hardware.architectures, arch);
      add(s.hardware.ram_gb, ram.replace("ram-",""));
      add(s.hardware.cpu_cores, cores.replace("cores-",""));
      add(s.hardware.vram_gb, vram.replace("vram-",""));
      add(s.hardware.gpu, gpu);
      if (event === "youtube_click") add(s.youtube_targets, target);
    }
    cursor = r.cursor;
  } while (cursor);

  cursor = undefined;
  do {
    const r = await list({ prefix:`events/${month}/`, cursor, limit:1000, token:process.env.BLOB_READ_WRITE_TOKEN });
    for (const b of r.blobs) {
      const p = b.pathname.split("/");
      if (p.length < 7) continue;
      const [, , event, platform, version, target] = p;
      s.total_events++;
      if (event === "app_start") s.app_start++;
      if (event === "youtube_click") s.youtube_click++;
      add(s.platforms, platform); add(s.versions, version);
      if (event === "youtube_click") add(s.youtube_targets, target);
    }
    cursor = r.cursor;
  } while (cursor);

  s.average_youtube_clicks_per_start = s.app_start ? Number((s.youtube_click / s.app_start).toFixed(2)) : 0;
  return res.status(200).json(s);
}
