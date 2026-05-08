import pkg from 'pg';
const { Pool } = pkg;

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

async function ensureTable(client) {
  await client.query(`
    CREATE TABLE IF NOT EXISTS session_logs (
      sid         TEXT PRIMARY KEY,
      user_id     TEXT NOT NULL DEFAULT 'muayad',
      data        JSONB NOT NULL,
      updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `);
  await client.query(`
    CREATE INDEX IF NOT EXISTS session_logs_user_idx ON session_logs (user_id)
  `);
}

export default async function handler(req, res) {
  // CORS headers so the browser can call this from the same Vercel domain
  res.setHeader('Access-Control-Allow-Origin',  '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(204).end();

  const client = await pool.connect();
  try {
    await ensureTable(client);

    // ── GET  /api/sessions  → return all logs as { sid: data, … }
    if (req.method === 'GET') {
      const result = await client.query(
        `SELECT sid, data FROM session_logs WHERE user_id = 'muayad' ORDER BY updated_at DESC`
      );
      const logs = {};
      result.rows.forEach(row => { logs[row.sid] = row.data; });
      return res.status(200).json(logs);
    }

    // ── POST /api/sessions  body: { sid, data }  → upsert one log
    if (req.method === 'POST') {
      const { sid, data } = req.body;
      if (!sid || !data) return res.status(400).json({ error: 'Missing sid or data' });
      await client.query(
        `INSERT INTO session_logs (sid, data)
         VALUES ($1, $2)
         ON CONFLICT (sid)
         DO UPDATE SET data = $2, updated_at = NOW()`,
        [sid, JSON.stringify(data)]
      );
      return res.status(200).json({ ok: true });
    }

    // ── DELETE /api/sessions  body: { sid? }  → delete one or all
    if (req.method === 'DELETE') {
      const { sid } = req.body || {};
      if (sid) {
        await client.query(`DELETE FROM session_logs WHERE sid = $1`, [sid]);
      } else {
        await client.query(`DELETE FROM session_logs WHERE user_id = 'muayad'`);
      }
      return res.status(200).json({ ok: true });
    }

    return res.status(405).json({ error: 'Method not allowed' });

  } catch (err) {
    console.error('[sessions]', err);
    return res.status(500).json({ error: 'Database error', detail: err.message });
  } finally {
    client.release();
  }
}
