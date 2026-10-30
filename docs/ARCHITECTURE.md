# Architecture: Offline Ofrenda Keeper

Offline Ofrenda Keeper is a local-first web application designed to preserve family memories for Dia de los Muertos without sending personal data to external servers.

## End-to-End Workflow

```
[Browser UI]                  [FastAPI on localhost]                [Local models]
1. About them       --------> POST /api/ofrendas       --------> data/ofrendas/<id>/ofrenda.json
2. Offerings (foods, songs, objects)
3. Photo            --------> POST /api/ofrendas/<id>/photo ---> photo.jpg|png|webp
4. Memories:
   type text        --------> PATCH /api/ofrendas/<id>
   record voice     --------> POST /api/ofrendas/<id>/audio ---> faster-whisper -> transcript
5. Generate         --------> POST /api/ofrendas/<id>/generate-> Ollama -> remembrance
6. Preview          <-------- GET /api/ofrendas/<id>/page       (Jinja2 -> one HTML file)
7. Save             Download HTML | Print/Save as PDF (browser print CSS)
```

## Privacy & Security Boundaries
- **No external network requests:** App strictly connects to `127.0.0.1` / `localhost` for Ollama.
- **Offline audio transcription:** faster-whisper runs on CPU with int8 quantization.
- **Self-contained output:** Generated HTML inlines all styles, SVG icons, and embeds photos as base64 data URIs. No CDN links, web fonts, or remote assets.
- **Data isolation:** All user data is stored strictly in `./data` (gitignored). Story text is never logged.
