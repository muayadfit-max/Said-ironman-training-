import pkg from 'pg';
const { Pool } = pkg;

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

async function ensureTable(client) {
  await client.query(`
    CREATE TABLE IF NOT EXISTS nutrition_logs (
      day_key     TEXT PRIMARY KEY,
      user_id     TEXT NOT NULL DEFAULT 'muayad',
      data        JSONB NOT NULL,
      updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `);
  await client.query(`
    CREATE INDEX IF NOT EXISTS nutrition_logs_user_idx ON nutrition_logs (user_id)
  `);
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin',  '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(204).end();

  const client = await pool.connect();
  try {
    await ensureTable(client);

    // ── GET  /api/nutrition  → return all logs as { dk: data, … }
    if (req.method === 'GET') {
      const result = await client.query(
        `SELECT day_key, data FROM nutrition_logs WHERE user_id = 'muayad' ORDER BY day_key DESC`
      );
      const logs = {};
      result.rows.forEach(row => { logs[row.day_key] = row.data; });
      return res.status(200).json(logs);
    }

    // ── POST /api/nutrition  body: { dk, data }  → upsert one log
    if (req.method === 'POST') {
      const { dk, data } = req.body;
      if (!dk || !data) return res.status(400).json({ error: 'Missing dk or data' });
      await client.query(
        `INSERT INTO nutrition_logs (day_key, data)
         VALUES ($1, $2)
         ON CONFLICT (day_key)
         DO UPDATE SET data = $2, updated_at = NOW()`,
        [dk, JSON.stringify(data)]
      );
      return res.status(200).json({ ok: true });
    }

    // ── DELETE /api/nutrition  → wipe all nutrition logs
    if (req.method === 'DELETE') {
      await client.query(`DELETE FROM nutrition_logs WHERE user_id = 'muayad'`);
      return res.status(200).json({ ok: true });
    }

    return res.status(405).json({ error: 'Method not allowed' });

  } catch (err) {
    console.error('[nutrition]', err);
    return res.status(500).json({ error: 'Database error', detail: err.message });
  } finally {
    client.release();
  }
}
