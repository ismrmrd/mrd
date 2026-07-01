"""Static HTML harness for iterating on the MRD Viz mosaic UI.

This file is not referenced directly by the current VS Code extension code. It
is kept as a useful reference for the webview shape and as a standalone way to
exercise the CLI/backend contract while testing MRD files locally.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .main import DEFAULT_OPTIONS, PreviewOptions, extract_image, open_file


def write_mosaic_html(
    path: Path,
    output_path: Path,
    *,
    max_thumbnails: int = DEFAULT_OPTIONS.max_thumbnails,
    thumbnail_size: int = DEFAULT_OPTIONS.thumbnail_size,
    preload_full_images: int = DEFAULT_OPTIONS.preload_full_images,
) -> Path:
    """Write a standalone HTML mosaic harness for one MRD file."""

    path = Path(path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = open_file(path, PreviewOptions(max_thumbnails=max_thumbnails, thumbnail_size=thumbnail_size))
    full_images = _preload_full_images(path, payload, preload_full_images)

    output_path.write_text(_build_html(payload, full_images), encoding="utf-8")
    return output_path


def _preload_full_images(path: Path, payload: dict[str, Any], count: int) -> dict[str, Any]:
    if count <= 0 or not payload.get("ok"):
        return {}

    tiles = payload.get("mosaic", {}).get("thumbnails", [])
    full_images: dict[str, Any] = {}
    for tile in tiles[:count]:
        image_index = tile.get("image_index")
        if image_index is None:
            continue
        full_images[str(image_index)] = extract_image(path, int(image_index))
    return full_images


def _build_html(payload: dict[str, Any], full_images: dict[str, Any]) -> str:
    payload_json = json.dumps(payload, ensure_ascii=True).replace("<", "\\u003c")
    full_images_json = json.dumps(full_images, ensure_ascii=True).replace("<", "\\u003c")
    title = html.escape(str(payload.get("filename", "MRD Mosaic")))

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} - MRD Mosaic Harness</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #101114;
      --panel: #181a1f;
      --panel-2: #20232a;
      --text: #eef1f6;
      --muted: #a7afbd;
      --line: #343946;
      --accent: #66a7ff;
      --warn: #ffd479;
      --bad: #ff8c8c;
      --radius: 6px;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--text); }}
    header {{
      position: sticky;
      top: 0;
      z-index: 2;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 16px;
      align-items: center;
      padding: 12px 16px;
      background: #15171c;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{ margin: 0; font-size: 15px; font-weight: 650; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .stats {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; color: var(--muted); font-size: 12px; }}
    .stat {{ padding: 3px 8px; background: var(--panel-2); border: 1px solid var(--line); border-radius: 999px; }}
    main {{ display: grid; grid-template-columns: minmax(360px, 1fr) minmax(320px, 420px); gap: 16px; padding: 16px; }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); min-width: 0; }}
    .panel h2 {{ margin: 0; padding: 10px 12px; font-size: 12px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted); border-bottom: 1px solid var(--line); }}
    .mosaic {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(116px, 1fr)); gap: 10px; padding: 12px; }}
    .tile {{
      display: grid;
      gap: 6px;
      width: 100%;
      padding: 8px;
      color: inherit;
      background: #121318;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      cursor: pointer;
      text-align: left;
    }}
    .tile:hover, .tile:focus {{ border-color: var(--accent); outline: none; }}
    .tile[aria-selected="true"] {{ border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }}
    .tile img {{ width: 100%; aspect-ratio: 1; object-fit: contain; image-rendering: pixelated; background: #000; }}
    .tile-title {{ font-size: 12px; font-weight: 650; }}
    .tile-meta {{ color: var(--muted); font-size: 11px; overflow-wrap: anywhere; }}
    .empty {{ padding: 16px; color: var(--muted); }}
    .detail {{ display: grid; gap: 12px; padding: 12px; }}
    .selected-image {{ display: grid; place-items: center; min-height: 240px; background: #050608; border: 1px solid var(--line); border-radius: var(--radius); }}
    .selected-image img {{ max-width: 100%; max-height: 68vh; object-fit: contain; image-rendering: pixelated; }}
    .notice {{ padding: 8px 10px; color: var(--warn); background: #2a2412; border: 1px solid #5b4a1a; border-radius: var(--radius); font-size: 12px; }}
    dl {{ display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 4px 12px; margin: 0; font-size: 12px; }}
    dt {{ color: var(--muted); }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    pre {{ margin: 0; max-height: 36vh; overflow: auto; padding: 12px; color: #d7deea; background: #0b0c10; border-top: 1px solid var(--line); font-size: 11px; }}
    @media (max-width: 900px) {{ main {{ grid-template-columns: 1fr; }} header {{ grid-template-columns: 1fr; }} .stats {{ justify-content: flex-start; }} }}
  </style>
</head>
<body>
  <header>
    <h1 id="title"></h1>
    <div class="stats" id="stats"></div>
  </header>
  <main>
    <section class="panel">
      <h2>Mosaic</h2>
      <div class="mosaic" id="mosaic"></div>
    </section>
    <aside class="panel">
      <h2>Selected Tile</h2>
      <div class="detail" id="detail"></div>
      <h2>Payload Summary</h2>
      <pre id="metadata"></pre>
    </aside>
  </main>
  <script id="mrd-payload" type="application/json">{payload_json}</script>
  <script id="mrd-full-images" type="application/json">{full_images_json}</script>
  <script>
    const payload = JSON.parse(document.getElementById('mrd-payload').textContent);
    const embeddedFullImages = JSON.parse(document.getElementById('mrd-full-images').textContent);
    let selectedIndex = null;

    async function defaultTileLoader(imageIndex) {{
      const key = String(imageIndex);
      if (embeddedFullImages[key]) {{
        return embeddedFullImages[key];
      }}
      const tile = (payload.mosaic?.thumbnails || []).find(item => item.image_index === imageIndex);
      return {{
        ok: Boolean(tile),
        image: tile,
        warning: 'Full-resolution tile is not embedded in this static harness. Future VS Code webview code can replace window.MrdVizHarness.loadTile with a postMessage-backed loader.'
      }};
    }}

    window.MrdVizHarness = {{
      payload,
      embeddedFullImages,
      loadTile: defaultTileLoader,
      setTileLoader(loader) {{ this.loadTile = loader; }},
      showTile
    }};

    function stat(label, value) {{
      const span = document.createElement('span');
      span.className = 'stat';
      span.textContent = `${{label}}: ${{value}}`;
      return span;
    }}

    function renderShell() {{
      document.getElementById('title').textContent = payload.filename || 'MRD Mosaic';
      const stats = document.getElementById('stats');
      stats.append(
        stat('class', payload.file_class),
        stat('mode', payload.display_mode),
        stat('images', payload.stream?.image_count ?? 0),
        stat('thumbs', payload.mosaic?.thumbnails?.length ?? 0)
      );

      document.getElementById('metadata').textContent = JSON.stringify({{
        summary: payload.summary,
        stream: payload.stream,
        warnings: payload.warnings,
        metadataCounts: {{
          images: payload.metadata?.images?.length ?? 0,
          acquisitions: payload.metadata?.acquisitions?.length ?? 0,
          waveforms: payload.metadata?.waveforms?.length ?? 0,
          other_items: payload.metadata?.other_items?.length ?? 0
        }}
      }}, null, 2);
    }}

    function renderMosaic() {{
      const root = document.getElementById('mosaic');
      const tiles = payload.mosaic?.thumbnails || [];
      if (!tiles.length) {{
        const message = document.createElement('div');
        message.className = 'empty';
        message.textContent = payload.warnings?.join(' ') || 'No mosaic thumbnails available.';
        root.appendChild(message);
        return;
      }}

      tiles.forEach(tile => {{
        const button = document.createElement('button');
        button.className = 'tile';
        button.type = 'button';
        button.dataset.imageIndex = tile.image_index;
        button.setAttribute('aria-selected', 'false');

        if (tile.png_base64) {{
          const img = document.createElement('img');
          img.src = `data:image/png;base64,${{tile.png_base64}}`;
          img.alt = `MRD image item ${{tile.image_index}}`;
          button.appendChild(img);
        }}

        const title = document.createElement('div');
        title.className = 'tile-title';
        title.textContent = `Image ${{tile.image_index}}`;
        button.appendChild(title);

        const meta = document.createElement('div');
        meta.className = 'tile-meta';
        meta.textContent = `${{(tile.data_shape || []).join('x')}} | stream ${{tile.stream_index}}`;
        button.appendChild(meta);

        button.addEventListener('click', () => showTile(tile.image_index));
        root.appendChild(button);
      }});

      showTile(tiles[0].image_index);
    }}

    async function showTile(imageIndex) {{
      selectedIndex = imageIndex;
      document.querySelectorAll('.tile').forEach(tile => {{
        tile.setAttribute('aria-selected', String(Number(tile.dataset.imageIndex) === imageIndex));
      }});

      const detail = document.getElementById('detail');
      detail.textContent = '';

      const result = await window.MrdVizHarness.loadTile(imageIndex);
      const image = result.image;
      if (!result.ok || !image) {{
        detail.appendChild(notice(result.error || 'Unable to load selected tile.'));
        return;
      }}
      if (result.warning) {{
        detail.appendChild(notice(result.warning));
      }}

      const frame = document.createElement('div');
      frame.className = 'selected-image';
      if (image.png_base64) {{
        const img = document.createElement('img');
        img.src = `data:image/png;base64,${{image.png_base64}}`;
        img.alt = `Selected MRD image item ${{image.image_index}}`;
        frame.appendChild(img);
      }} else {{
        frame.textContent = image.render_error || 'No image payload available.';
      }}
      detail.appendChild(frame);

      const fields = document.createElement('dl');
      addField(fields, 'image_index', image.image_index);
      addField(fields, 'stream_index', image.stream_index);
      addField(fields, 'shape', (image.data_shape || []).join('x'));
      addField(fields, 'rendered', (image.rendered_shape || []).join('x'));
      addField(fields, 'dtype', image.dtype);
      addField(fields, 'source_plane', JSON.stringify(image.source_plane));
      detail.appendChild(fields);
    }}

    function addField(root, key, value) {{
      const dt = document.createElement('dt');
      dt.textContent = key;
      const dd = document.createElement('dd');
      dd.textContent = value ?? '';
      root.append(dt, dd);
    }}

    function notice(text) {{
      const div = document.createElement('div');
      div.className = 'notice';
      div.textContent = text;
      return div;
    }}

    renderShell();
    renderMosaic();
  </script>
</body>
</html>
"""