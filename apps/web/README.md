# Web Application

This strict TypeScript, React, and Next.js application provides the English Rhymes report. It accepts
pasted lyrics or local UTF-8 `.txt`/`.md` files up to 256 KiB, supports both pronunciation profiles
and all six primary tags, handles pronunciation review, and renders score, confidence, families,
schemes, pair filters, metrics, findings, versions, and limitations.

```bash
npm install
npm run dev
```

Run these checks before shipping UI changes:

```bash
npm test
npm run typecheck
npm run build
```

The client uses `http://127.0.0.1:8000` by default. Set `NEXT_PUBLIC_API_URL` to use another API
origin. The source-reference field records provenance only; the client does not scrape Genius or any
other lyrics source.
