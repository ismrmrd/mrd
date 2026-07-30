"use strict";
(() => {
  // media/viewer/state.ts
  var vscode = acquireVsCodeApi();
  var bootstrapElement = document.getElementById("mrd-payload");
  var bootstrap = JSON.parse(bootstrapElement && bootstrapElement.textContent || "{}");
  var payload = bootstrap.payload || {};
  var config = bootstrap.config || {};
  var persisted = vscode.getState() || {};
  var state = {
    selectedIndex: null,
    selectedTileKey: null,
    requestSequence: 0,
    pendingRequestId: null,
    pendingRequestIndex: null,
    pendingRequestCoords: [],
    activeViewport: null,
    selectedImageIndex: null,
    selectedTileThumb: null,
    selectedSliceDims: [],
    selectedSliceCoords: [],
    mosaicMode: "images",
    mosaicRevertMode: "images",
    mosaicPending: false,
    mosaicRequestId: null,
    viewportHeight: Number(persisted.viewportHeight) || 0
  };
  var MAX_IMAGE_CACHE_ENTRIES = Number(config.maxImageCacheEntries) || 32;
  var imageCache = /* @__PURE__ */ new Map();
  function cacheImage(key, image) {
    if (imageCache.has(key)) {
      imageCache.delete(key);
    } else if (imageCache.size >= MAX_IMAGE_CACHE_ENTRIES) {
      const oldestKey = imageCache.keys().next().value;
      imageCache.delete(oldestKey);
    }
    imageCache.set(key, image);
  }
  function isMaximized() {
    return document.body.classList.contains("mrd-maximized");
  }
  function persistState() {
    vscode.setState({ viewportHeight: state.viewportHeight, maximized: isMaximized() });
  }

  // media/viewer/dom.ts
  function valueOrUnknown(value) {
    return value === void 0 || value === null || value === "" ? "unknown" : String(value);
  }
  function formatList(value) {
    return Array.isArray(value) ? value.join("x") : "";
  }
  function stat(label, value) {
    const span = document.createElement("span");
    span.className = "stat";
    span.textContent = label + ": " + valueOrUnknown(value);
    return span;
  }
  function notice(text, kind) {
    const div = document.createElement("div");
    div.className = kind === "error" ? "notice error" : "notice";
    div.textContent = String(text);
    return div;
  }
  function section(title) {
    const root = document.createElement("section");
    root.className = "metadata-section";
    const heading = document.createElement("h3");
    heading.textContent = title;
    root.appendChild(heading);
    return root;
  }
  function addField(root, key, value) {
    const dt = document.createElement("dt");
    dt.textContent = key;
    const dd = document.createElement("dd");
    dd.textContent = valueOrUnknown(value);
    root.append(dt, dd);
  }

  // media/viewer/metadata.ts
  function metadata() {
    return payload.metadata || {};
  }
  function images() {
    return metadata().images || [];
  }
  function acquisitions() {
    return metadata().acquisitions || [];
  }
  function waveforms() {
    return metadata().waveforms || [];
  }
  function otherItems() {
    return metadata().other_items || [];
  }
  function definitionList(entries) {
    const list = document.createElement("dl");
    entries.forEach(function(entry) {
      addField(list, entry[0], entry[1]);
    });
    return list;
  }
  function table(headers, rows) {
    const tableRoot = document.createElement("table");
    tableRoot.className = "metadata-table";
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    headers.forEach(function(header) {
      const th = document.createElement("th");
      th.textContent = header;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    tableRoot.appendChild(thead);
    const tbody = document.createElement("tbody");
    rows.forEach(function(row) {
      const tr = document.createElement("tr");
      row.forEach(function(cell) {
        const td = document.createElement("td");
        td.textContent = valueOrUnknown(cell);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    tableRoot.appendChild(tbody);
    return tableRoot;
  }
  function distribution(values) {
    const counts = /* @__PURE__ */ new Map();
    values.forEach(function(value) {
      const key = valueOrUnknown(value);
      counts.set(key, (counts.get(key) || 0) + 1);
    });
    return Array.from(counts.entries()).sort(function(left, right) {
      return String(left[0]).localeCompare(String(right[0]), void 0, { numeric: true });
    });
  }
  function headValue(image, key) {
    return image && image.head ? image.head[key] : void 0;
  }
  function shapeKey(image) {
    return formatList(image && image.data_shape) || "unknown";
  }
  function uniqueCount(values) {
    return distribution(values).length;
  }
  function appendEmpty(root, text) {
    const empty = document.createElement("div");
    empty.className = "metadata-note";
    empty.textContent = text;
    root.appendChild(empty);
  }
  function redactPayload(key, value) {
    if (key === "png_base64" && typeof value === "string") {
      return "<base64 PNG " + value.length + " chars>";
    }
    return value;
  }
  function renderShell() {
    document.getElementById("title").textContent = payload.filename || "MRD file";
    document.getElementById("subtitle").textContent = payload.path || "";
    const stats = document.getElementById("stats");
    stats.textContent = "";
    stats.append(
      stat("class", payload.file_class),
      stat("mode", payload.display_mode),
      stat("images", payload.stream && payload.stream.image_count),
      stat("acq", payload.stream && payload.stream.acquisition_count),
      stat("thumbs", payload.mosaic && payload.mosaic.thumbnails && payload.mosaic.thumbnails.length)
    );
    const notices = document.getElementById("notices");
    notices.textContent = "";
    if (!payload.ok) {
      notices.appendChild(notice(payload.error || "The backend reported an error.", "error"));
    }
    (payload.warnings || []).forEach(function(warning) {
      notices.appendChild(notice(warning, "warning"));
    });
    if (payload.mosaic && payload.mosaic.truncated) {
      notices.appendChild(notice("Thumbnail payload is truncated by the configured maximum."));
    }
    if (payload.file_class_reliable === false) {
      notices.appendChild(notice("File classification is based on a partial stream read.", "warning"));
    }
    renderMetadata();
  }
  function renderMetadata() {
    renderSummaryMetadata();
    renderOrganizationMetadata();
    renderStreamMetadata();
    renderRawJsonMetadata();
    document.querySelectorAll(".tab").forEach(function(tab) {
      tab.addEventListener("click", function() {
        activateTab(tab.dataset.tab);
      });
    });
  }
  function activateTab(name) {
    document.querySelectorAll(".tab").forEach(function(tab) {
      tab.setAttribute("aria-selected", String(tab.dataset.tab === name));
    });
    document.querySelectorAll(".tab-panel").forEach(function(panel) {
      panel.setAttribute("aria-hidden", String(panel.id !== "metadata-" + name));
    });
  }
  function renderSummaryMetadata() {
    const root = document.getElementById("metadata-summary");
    root.textContent = "";
    const file = section("File");
    file.appendChild(definitionList([
      ["class", payload.file_class],
      ["classification reliable", payload.file_class_reliable],
      ["display mode", payload.display_mode],
      ["schema version", payload.schema_version],
      ["file size bytes", payload.file_size_bytes]
    ]));
    root.appendChild(file);
    const stream = payload.stream || {};
    const counts = section("Counts");
    counts.appendChild(definitionList([
      ["images", stream.image_count],
      ["acquisitions", stream.acquisition_count],
      ["waveforms", stream.waveform_count],
      ["other items", stream.other_count],
      ["returned thumbnails", payload.mosaic && payload.mosaic.thumbnails && payload.mosaic.thumbnails.length],
      ["thumbnail payload truncated", payload.mosaic && payload.mosaic.truncated]
    ]));
    root.appendChild(counts);
    const summary = payload.summary || {};
    const header = section("Header Summary");
    header.appendChild(definitionList([
      ["encoding count", summary.encoding_count],
      ["encoded matrix", formatList(summary.encoded_matrix)],
      ["recon matrix", formatList(summary.recon_matrix)],
      ["encoded FOV mm", formatList(summary.encoded_fov_mm)],
      ["recon FOV mm", formatList(summary.recon_fov_mm)]
    ]));
    root.appendChild(header);
    if ((payload.warnings || []).length) {
      const warnings = section("Warnings");
      const list = document.createElement("ul");
      payload.warnings.forEach(function(warning) {
        const item = document.createElement("li");
        item.textContent = String(warning);
        list.appendChild(item);
      });
      warnings.appendChild(list);
      root.appendChild(warnings);
    }
  }
  function renderOrganizationMetadata() {
    const root = document.getElementById("metadata-organization");
    root.textContent = "";
    const imageItems = images();
    if (!imageItems.length) {
      appendEmpty(root, "No image metadata is available for this file.");
      return;
    }
    const overview = section("Image Set");
    overview.appendChild(definitionList([
      ["images", imageItems.length],
      ["unique slices", uniqueCount(imageItems.map(function(image) {
        return headValue(image, "slice");
      }))],
      ["unique image types", uniqueCount(imageItems.map(function(image) {
        return headValue(image, "image_type");
      }))],
      ["unique series", uniqueCount(imageItems.map(function(image) {
        return headValue(image, "image_series_index");
      }))],
      ["unique shapes", uniqueCount(imageItems.map(shapeKey))],
      ["unique dtypes", uniqueCount(imageItems.map(function(image) {
        return image.dtype;
      }))]
    ]));
    root.appendChild(overview);
    const sliceRows = distribution(imageItems.map(function(image) {
      return headValue(image, "slice");
    }));
    const slices = section("Slice Distribution");
    slices.appendChild(table(["slice", "image count"], sliceRows));
    root.appendChild(slices);
    const typeRows = distribution(imageItems.map(function(image) {
      return headValue(image, "image_type");
    }));
    const types = section("Image Type Distribution");
    types.appendChild(table(["image type", "image count"], typeRows));
    root.appendChild(types);
    const shapeRows = distribution(imageItems.map(function(image) {
      return shapeKey(image) + " / " + valueOrUnknown(image.dtype);
    }));
    const shapes = section("Shape / Dtype Consistency");
    shapes.appendChild(table(["shape / dtype", "image count"], shapeRows));
    root.appendChild(shapes);
  }
  function renderStreamMetadata() {
    const root = document.getElementById("metadata-stream");
    root.textContent = "";
    const stream = payload.stream || {};
    const itemCounts = section("Stream Item Counts");
    const rows = Object.entries(stream.item_counts || {}).sort(function(left, right) {
      return left[0].localeCompare(right[0]);
    });
    if (rows.length) {
      itemCounts.appendChild(table(["item type", "count"], rows));
    } else {
      appendEmpty(itemCounts, "No stream item counts were returned.");
    }
    root.appendChild(itemCounts);
    const examples = section("Metadata Examples");
    examples.appendChild(definitionList([
      ["image metadata entries", images().length],
      ["acquisition examples", acquisitions().length],
      ["waveform entries", waveforms().length],
      ["other item entries", otherItems().length]
    ]));
    root.appendChild(examples);
    if (acquisitions().length) {
      const firstAcquisition = acquisitions()[0];
      const acquisition = section("First Acquisition Example");
      acquisition.appendChild(definitionList([
        ["stream index", firstAcquisition.stream_index],
        ["shape", formatList(firstAcquisition.data_shape)],
        ["dtype", firstAcquisition.dtype],
        ["flags", firstAcquisition.flags],
        ["scan counter", firstAcquisition.scan_counter]
      ]));
      root.appendChild(acquisition);
    }
  }
  function renderRawJsonMetadata() {
    document.getElementById("json").textContent = JSON.stringify({
      summary: payload.summary,
      stream: payload.stream,
      warnings: payload.warnings,
      metadata: payload.metadata,
      mosaic: payload.mosaic
    }, redactPayload, 2);
  }

  // media/viewer/slice.ts
  function clampIndex(value, size) {
    const numeric = Number.isInteger(value) ? value : Number(value) || 0;
    return Math.max(0, Math.min(numeric, size - 1));
  }
  function defaultSliceCoords(dims, sourcePlane) {
    const coords = [];
    (dims || []).forEach(function(dim) {
      const axis = Number(dim.axis);
      let value = 0;
      if (sourcePlane && typeof sourcePlane === "object" && dim.name in sourcePlane) {
        value = Number(sourcePlane[dim.name]) || 0;
      }
      coords[axis] = clampIndex(value, Number(dim.size) || 1);
    });
    return coords;
  }
  function cacheKey(imageIndex, coords) {
    return String(imageIndex) + "@" + (coords || []).join(",");
  }
  function buildSliceSlider(dim, currentValue, onCommit) {
    const size = Number(dim.size) || 1;
    const axis = Number(dim.axis);
    const label = dim.name || "axis " + axis;
    const current = clampIndex(currentValue, size);
    const row = document.createElement("div");
    row.className = "mrd-slice-row";
    const caption = document.createElement("span");
    caption.className = "mrd-slice-name";
    caption.textContent = label + " " + current + " / " + (size - 1);
    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = "0";
    slider.max = String(size - 1);
    slider.step = "1";
    slider.value = String(current);
    slider.setAttribute("aria-label", "Step " + label);
    slider.addEventListener("input", function() {
      caption.textContent = label + " " + slider.value + " / " + (size - 1);
    });
    slider.addEventListener("change", function() {
      onCommit(axis, Number(slider.value));
    });
    row.append(caption, slider);
    return row;
  }

  // media/viewer/viewport.ts
  function makeToolButton(label, title, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mrd-tool-button";
    button.textContent = label;
    button.title = title;
    button.addEventListener("click", onClick);
    return button;
  }
  function toggleMaximize() {
    document.body.classList.toggle("mrd-maximized");
    persistState();
    if (state.activeViewport) {
      if (state.activeViewport.syncControls) {
        state.activeViewport.syncControls();
      }
      requestAnimationFrame(state.activeViewport.refit);
    }
  }
  function createImageViewport(tile) {
    const container = document.createElement("div");
    container.className = "mrd-viewport";
    const frame = document.createElement("div");
    frame.className = "mrd-viewport-frame";
    const img = document.createElement("img");
    img.className = "mrd-viewport-image";
    img.src = "data:image/png;base64," + tile.png_base64;
    img.alt = "Selected MRD image item " + valueOrUnknown(tile.image_index);
    img.draggable = false;
    frame.appendChild(img);
    const MIN_SCALE = 0.05;
    const MAX_SCALE = 40;
    let scale = 1;
    let offsetX = 0;
    let offsetY = 0;
    let mode = "fit";
    const zoomLabel = document.createElement("span");
    zoomLabel.className = "mrd-zoom-label";
    function naturalSize() {
      return { w: img.naturalWidth || 1, h: img.naturalHeight || 1 };
    }
    function fitScale() {
      const n = naturalSize();
      const fw = frame.clientWidth || 1;
      const fh = frame.clientHeight || 1;
      return Math.min(fw / n.w, fh / n.h);
    }
    function apply() {
      img.style.transform = "translate(" + offsetX + "px, " + offsetY + "px) scale(" + scale + ")";
      zoomLabel.textContent = Math.round(scale * 100) + "%";
      frame.classList.toggle("is-pannable", scale > fitScale() + 1e-4);
    }
    function fit() {
      mode = "fit";
      scale = fitScale();
      const n = naturalSize();
      offsetX = (frame.clientWidth - n.w * scale) / 2;
      offsetY = (frame.clientHeight - n.h * scale) / 2;
      apply();
    }
    function setScaleAbout(newScale, cx, cy) {
      newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, newScale));
      const ix = (cx - offsetX) / scale;
      const iy = (cy - offsetY) / scale;
      scale = newScale;
      offsetX = cx - ix * scale;
      offsetY = cy - iy * scale;
      apply();
    }
    function zoomBy(factor, cx, cy) {
      mode = "free";
      setScaleAbout(scale * factor, cx, cy);
    }
    function actualSize() {
      mode = "free";
      setScaleAbout(1, frame.clientWidth / 2, frame.clientHeight / 2);
    }
    function refit() {
      if (mode === "fit") {
        fit();
      } else {
        apply();
      }
    }
    frame.addEventListener("wheel", function(event) {
      event.preventDefault();
      const rect = frame.getBoundingClientRect();
      const factor = event.deltaY < 0 ? 1.1 : 1 / 1.1;
      zoomBy(factor, event.clientX - rect.left, event.clientY - rect.top);
    }, { passive: false });
    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    frame.addEventListener("pointerdown", function(event) {
      dragging = true;
      lastX = event.clientX;
      lastY = event.clientY;
      frame.classList.add("is-panning");
      try {
        frame.setPointerCapture(event.pointerId);
      } catch (err) {
      }
    });
    frame.addEventListener("pointermove", function(event) {
      if (!dragging) {
        return;
      }
      offsetX += event.clientX - lastX;
      offsetY += event.clientY - lastY;
      lastX = event.clientX;
      lastY = event.clientY;
      mode = "free";
      apply();
    });
    function endDrag(event) {
      if (!dragging) {
        return;
      }
      dragging = false;
      frame.classList.remove("is-panning");
      try {
        frame.releasePointerCapture(event.pointerId);
      } catch (err) {
      }
    }
    frame.addEventListener("pointerup", endDrag);
    frame.addEventListener("pointercancel", endDrag);
    frame.addEventListener("dblclick", toggleMaximize);
    function zoomIn() {
      zoomBy(1.2, frame.clientWidth / 2, frame.clientHeight / 2);
    }
    function zoomOut() {
      zoomBy(1 / 1.2, frame.clientWidth / 2, frame.clientHeight / 2);
    }
    const maximizeButton = makeToolButton("\u2922", "Maximize", toggleMaximize);
    maximizeButton.classList.add("mrd-tool-maximize");
    function syncMaximizeButton() {
      maximizeButton.textContent = isMaximized() ? "\u2921" : "\u2922";
      maximizeButton.title = isMaximized() ? "Restore view (Esc)" : "Maximize";
      maximizeButton.setAttribute("aria-label", maximizeButton.title);
    }
    syncMaximizeButton();
    const toolbar = document.createElement("div");
    toolbar.className = "mrd-viewport-toolbar";
    toolbar.append(
      makeToolButton("\u2212", "Zoom out (-)", zoomOut),
      zoomLabel,
      makeToolButton("+", "Zoom in (+)", zoomIn),
      makeToolButton("Fit", "Fit image to window (0)", fit),
      makeToolButton("1:1", "Actual size", actualSize),
      maximizeButton
    );
    const resizer = document.createElement("div");
    resizer.className = "mrd-viewport-resizer";
    resizer.title = "Drag to resize the image area";
    resizer.setAttribute("aria-label", "Resize image area");
    let resizing = false;
    let resizeStartY = 0;
    let resizeStartHeight = 0;
    resizer.addEventListener("pointerdown", function(event) {
      resizing = true;
      resizeStartY = event.clientY;
      resizeStartHeight = frame.getBoundingClientRect().height;
      try {
        resizer.setPointerCapture(event.pointerId);
      } catch (err) {
      }
      event.preventDefault();
    });
    resizer.addEventListener("pointermove", function(event) {
      if (!resizing) {
        return;
      }
      state.viewportHeight = Math.max(140, resizeStartHeight + (event.clientY - resizeStartY));
      frame.style.height = state.viewportHeight + "px";
      refit();
    });
    function endResize(event) {
      if (!resizing) {
        return;
      }
      resizing = false;
      try {
        resizer.releasePointerCapture(event.pointerId);
      } catch (err) {
      }
      persistState();
    }
    resizer.addEventListener("pointerup", endResize);
    resizer.addEventListener("pointercancel", endResize);
    if (state.viewportHeight > 0) {
      frame.style.height = state.viewportHeight + "px";
    }
    img.addEventListener("load", refit);
    if (img.complete && img.naturalWidth) {
      requestAnimationFrame(fit);
    }
    state.activeViewport = { refit, zoomIn, zoomOut, fit, syncControls: syncMaximizeButton };
    container.append(toolbar, frame, resizer);
    return container;
  }

  // media/viewer/messaging.ts
  function nextRequestId() {
    return String(++state.requestSequence);
  }
  function postMessage(message) {
    vscode.postMessage(message);
  }
  function initMessaging() {
    window.addEventListener("message", function(event) {
      const message = event.data || {};
      if (message.type === "imageLoaded") {
        handleImageLoaded(message);
      } else if (message.type === "imageError" && message.requestId === state.pendingRequestId) {
        renderSelectedError(message.error || "Unable to load selected image.");
      } else if (message.type === "mosaicUpdated") {
        handleMosaicUpdated(message);
      } else if (message.type === "mosaicError" && message.requestId === state.mosaicRequestId) {
        handleMosaicError(message.error || "Unable to update the mosaic.");
      }
    });
  }

  // media/viewer/selectedTile.ts
  function selectTile(tile) {
    if (!tile) {
      state.selectedImageIndex = null;
      state.selectedTileThumb = null;
      state.selectedTileKey = null;
      state.selectedSliceDims = [];
      state.selectedSliceCoords = [];
      renderSelectedTile(null);
      return;
    }
    state.selectedImageIndex = Number(tile.image_index);
    state.selectedTileThumb = tile;
    state.selectedTileKey = tile.mosaicKey != null ? String(tile.mosaicKey) : null;
    state.selectedSliceDims = Array.isArray(tile.slice_dims) ? tile.slice_dims : [];
    state.selectedSliceCoords = defaultSliceCoords(state.selectedSliceDims, tile.source_plane);
    loadSelectedImage();
  }
  function loadSelectedImage() {
    const canLoad = Number.isInteger(state.selectedImageIndex) && state.selectedImageIndex >= 0 && state.selectedTileThumb && Boolean(state.selectedTileThumb.renderable);
    if (!canLoad) {
      renderSelectedTile(state.selectedTileThumb);
      return;
    }
    const key = cacheKey(state.selectedImageIndex, state.selectedSliceCoords);
    const cachedImage = imageCache.get(key);
    if (cachedImage) {
      renderSelectedTile(cachedImage, "Loaded from selection cache.");
      return;
    }
    renderSelectedTile(state.selectedTileThumb, "Loading full-resolution image...");
    const requestId = nextRequestId();
    state.pendingRequestId = requestId;
    state.pendingRequestIndex = state.selectedImageIndex;
    state.pendingRequestCoords = state.selectedSliceCoords.slice();
    postMessage({
      type: "loadImage",
      requestId,
      imageIndex: state.selectedImageIndex,
      sliceCoords: state.selectedSliceCoords.slice()
    });
  }
  function renderSelectedTile(tile, statusText) {
    state.selectedIndex = tile ? tile.image_index : null;
    document.querySelectorAll(".tile").forEach(function(node) {
      node.setAttribute("aria-selected", String(state.selectedTileKey !== null && node.dataset.tileKey === state.selectedTileKey));
    });
    const root = document.getElementById("detail");
    root.textContent = "";
    if (!tile) {
      state.activeViewport = null;
      const empty = document.createElement("div");
      empty.className = "empty";
      empty.textContent = "No tile selected.";
      root.appendChild(empty);
      return;
    }
    if (statusText) {
      root.appendChild(notice(statusText, "warning"));
    }
    if (tile.png_base64) {
      root.appendChild(createImageViewport(tile));
    } else {
      state.activeViewport = null;
      const frame = document.createElement("div");
      frame.className = "selected-image";
      frame.textContent = tile.render_error || "No image payload available.";
      root.appendChild(frame);
    }
    const sliceControls = buildSelectedSliceControls();
    if (sliceControls) {
      root.appendChild(sliceControls);
    }
    const fields = document.createElement("dl");
    const head = tile.head || {};
    addField(fields, "slice", head.slice);
    addField(fields, "phase", head.phase);
    addField(fields, "contrast", head.contrast);
    addField(fields, "repetition", head.repetition);
    addField(fields, "image type", head.image_type);
    addField(fields, "series", head.image_series_index);
    addField(fields, "field of view", formatList(head.field_of_view));
    addField(fields, "image index", tile.image_index);
    addField(fields, "stream index", tile.stream_index);
    addField(fields, "stream item type", tile.stream_item_type);
    addField(fields, "data shape", formatList(tile.data_shape));
    addField(fields, "rendered shape", formatList(tile.rendered_shape));
    addField(fields, "dtype", tile.dtype);
    addField(fields, "source plane", JSON.stringify(tile.source_plane));
    root.appendChild(fields);
  }
  function handleImageLoaded(message) {
    if (message.requestId !== state.pendingRequestId) {
      return;
    }
    const responsePayload = message.payload || {};
    if (!responsePayload.ok || !responsePayload.image) {
      renderSelectedError(responsePayload.error || "Unable to load selected image.");
      return;
    }
    const image = responsePayload.image;
    if (Number.isInteger(state.pendingRequestIndex)) {
      cacheImage(cacheKey(state.pendingRequestIndex, state.pendingRequestCoords), image);
    }
    renderSelectedTile(image);
  }
  function buildSelectedSliceControls() {
    if (!state.selectedSliceDims || !state.selectedSliceDims.length) {
      return null;
    }
    const wrap = document.createElement("div");
    wrap.className = "mrd-slice-controls";
    let rendered = false;
    state.selectedSliceDims.forEach(function(dim) {
      if ((Number(dim.size) || 1) <= 1) {
        return;
      }
      rendered = true;
      wrap.appendChild(buildSliceSlider(dim, state.selectedSliceCoords[Number(dim.axis)], function(axis, value) {
        state.selectedSliceCoords[axis] = value;
        loadSelectedImage();
      }));
    });
    return rendered ? wrap : null;
  }
  function renderSelectedError(error) {
    state.activeViewport = null;
    const root = document.getElementById("detail");
    root.textContent = "";
    root.appendChild(notice(error, "error"));
  }

  // media/viewer/mosaic.ts
  function renderMosaic() {
    const root = document.getElementById("mosaic");
    root.textContent = "";
    removeMosaicModeControls();
    const tiles = payload.mosaic && payload.mosaic.thumbnails || [];
    if (!tiles.length) {
      const empty = document.createElement("div");
      empty.className = "empty";
      empty.textContent = payload.display_mode === "metadata_only" ? "No renderable image thumbnails. Metadata is available in the payload summary." : "No mosaic thumbnails were returned.";
      root.appendChild(empty);
      renderSelectedTile(null);
      return;
    }
    tiles.forEach(function(tile, tileIndex) {
      tile.mosaicKey = tileIndex;
      const button = document.createElement("button");
      button.className = "tile";
      button.type = "button";
      button.dataset.imageIndex = String(tile.image_index);
      button.dataset.tileKey = String(tileIndex);
      button.setAttribute("aria-selected", "false");
      if (tile.png_base64) {
        const img = document.createElement("img");
        img.src = "data:image/png;base64," + tile.png_base64;
        img.alt = "MRD image item " + valueOrUnknown(tile.image_index);
        button.appendChild(img);
      } else {
        const placeholder = document.createElement("div");
        placeholder.className = "tile-placeholder";
        placeholder.textContent = tile.render_error || "Not renderable";
        button.appendChild(placeholder);
      }
      const title = document.createElement("div");
      title.className = "tile-name";
      title.textContent = tile.tile_title || "Image " + valueOrUnknown(tile.image_index);
      button.appendChild(title);
      const meta = document.createElement("div");
      meta.className = "tile-meta";
      meta.textContent = formatList(tile.data_shape) + " | stream " + valueOrUnknown(tile.stream_index);
      button.appendChild(meta);
      button.addEventListener("click", function() {
        selectTile(tile);
      });
      root.appendChild(button);
    });
    renderMosaicModeControls(tiles);
    selectTile(tiles[0]);
  }
  function currentTiles() {
    return payload.mosaic && payload.mosaic.thumbnails || [];
  }
  function removeMosaicModeControls() {
    const existing = document.getElementById("mosaic-mode");
    if (existing) {
      existing.remove();
    }
  }
  function mosaicCanExplode(tiles) {
    return tiles.some(function(tile) {
      const dims = tile && tile.slice_dims;
      if (!Array.isArray(dims) || !dims.length) {
        return false;
      }
      const z = dims[dims.length - 1];
      return Boolean(z) && (Number(z.size) || 1) > 1;
    });
  }
  function setMosaicNotice(text, kind) {
    const noticesEl = document.getElementById("notices");
    if (!noticesEl) {
      return;
    }
    const existing = document.getElementById("mosaic-status");
    if (existing) {
      existing.remove();
    }
    if (text) {
      const node = notice(text, kind);
      node.id = "mosaic-status";
      noticesEl.appendChild(node);
    }
  }
  function makeMosaicModeButton(mode, label, title) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mrd-segmented-button";
    button.textContent = label;
    button.title = title;
    if (state.mosaicMode === mode) {
      button.classList.add("is-active");
    }
    button.setAttribute("aria-pressed", state.mosaicMode === mode ? "true" : "false");
    button.disabled = state.mosaicPending;
    button.addEventListener("click", function() {
      setMosaicMode(mode);
    });
    return button;
  }
  function renderMosaicModeControls(tiles) {
    removeMosaicModeControls();
    if (!mosaicCanExplode(tiles)) {
      return;
    }
    const bar = document.createElement("div");
    bar.id = "mosaic-mode";
    bar.className = "mrd-mosaic-mode";
    const label = document.createElement("span");
    label.className = "mrd-mosaic-mode-label";
    label.textContent = "View";
    bar.appendChild(label);
    const group = document.createElement("div");
    group.className = "mrd-segmented";
    group.setAttribute("role", "group");
    group.append(
      makeMosaicModeButton("images", "Images", "One thumbnail per image"),
      makeMosaicModeButton("slices", "Slices", "One thumbnail per z slice")
    );
    bar.appendChild(group);
    const mosaicEl = document.getElementById("mosaic");
    mosaicEl.parentNode.insertBefore(bar, mosaicEl);
  }
  function setMosaicMode(mode) {
    if (state.mosaicPending || mode === state.mosaicMode) {
      return;
    }
    state.mosaicRevertMode = state.mosaicMode;
    state.mosaicMode = mode;
    state.mosaicPending = true;
    const requestId = nextRequestId();
    state.mosaicRequestId = requestId;
    renderMosaicModeControls(currentTiles());
    setMosaicNotice(mode === "slices" ? "Rendering individual slices..." : "Rebuilding image mosaic...", "warning");
    postMessage({
      type: "setMosaicMode",
      requestId,
      mode
    });
  }
  function handleMosaicUpdated(message) {
    if (message.requestId !== state.mosaicRequestId) {
      return;
    }
    state.mosaicPending = false;
    const responsePayload = message.payload || {};
    if (responsePayload.ok !== true || !responsePayload.mosaic) {
      handleMosaicError(responsePayload && responsePayload.error || "Unable to update the mosaic.");
      return;
    }
    payload.mosaic = responsePayload.mosaic;
    setMosaicNotice("", null);
    renderMosaic();
  }
  function handleMosaicError(error) {
    state.mosaicPending = false;
    state.mosaicMode = state.mosaicRevertMode;
    setMosaicNotice(String(error), "error");
    renderMosaicModeControls(currentTiles());
  }

  // media/viewer.ts
  initMessaging();
  window.addEventListener("resize", function() {
    if (state.activeViewport) {
      state.activeViewport.refit();
    }
  });
  document.addEventListener("keydown", function(event) {
    const target = event.target;
    if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) {
      return;
    }
    if (event.key === "Escape" && isMaximized()) {
      toggleMaximize();
      return;
    }
    if (!state.activeViewport) {
      return;
    }
    if (event.key === "+" || event.key === "=") {
      state.activeViewport.zoomIn();
      event.preventDefault();
    } else if (event.key === "-" || event.key === "_") {
      state.activeViewport.zoomOut();
      event.preventDefault();
    } else if (event.key === "0") {
      state.activeViewport.fit();
      event.preventDefault();
    }
  });
  if (persisted.maximized) {
    document.body.classList.add("mrd-maximized");
  }
  renderShell();
  renderMosaic();
})();
