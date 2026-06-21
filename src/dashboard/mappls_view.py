"""Mappls (MapmyIndia) map via official JS SDK."""

from __future__ import annotations

import html
import json
from pathlib import Path


def build_mappls_html(
    api_key: str,
    markers: list[dict],
    circles: list[dict],
    center: tuple[float, float] = (12.9716, 77.5946),
    zoom: int = 11,
    height: int | str = 560,
) -> str:
    safe_key = html.escape(api_key, quote=True)
    markers = markers[:150]
    circles = circles[:30]
    markers_json = json.dumps(markers)
    circles_json = json.dumps(circles)
    lat, lon = center
    height_css = f"{height}px" if isinstance(height, int) else height

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="referrer" content="origin" />
  <title>EventOps · Mappls</title>
  <style>
    html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }}
    #map {{ width: 100%; height: {height_css}; min-height: {height_css}; }}
    .attribution {{
      position: absolute; bottom: 0; left: 0; right: 0; z-index: 1000;
      font: 11px sans-serif; padding: 4px 8px; color: #444;
      background: rgba(255,255,255,0.9);
    }}
    .err {{ padding: 16px; color: #b71c1c; font-family: sans-serif; }}
  </style>
  <script>
    var eventMarkers = {markers_json};
    var riskCircles = {circles_json};
    var mapCenter = {{ lat: {lat}, lng: {lon} }};
    var mapZoom = {zoom};

    function showError(msg) {{
      document.getElementById("map").innerHTML =
        '<div class="err"><b>Mappls failed to load</b><br>' + msg + '</div>';
    }}

    function drawOverlays(map) {{
      riskCircles.forEach(function(c) {{
        try {{
          new mappls.Circle({{
            map: map,
            center: {{ lat: c.lat, lng: c.lng }},
            radius: c.radius || 800,
            strokeColor: c.color || "#d32f2f",
            strokeOpacity: 0.85,
            strokeWeight: 2,
            fillColor: c.color || "#d32f2f",
            fillOpacity: 0.22,
            popupHtml: c.popup || ""
          }});
        }} catch (e) {{ console.warn("circle", e); }}
      }});
      eventMarkers.forEach(function(m) {{
        try {{
          new mappls.Marker({{
            map: map,
            position: {{ lat: m.lat, lng: m.lng }},
            popupHtml: m.popup || ""
          }});
        }} catch (e) {{ console.warn("marker", e); }}
      }});
    }}

    function initMap() {{
      try {{
        if (typeof mappls === "undefined" || !mappls.Map) {{
          showError("SDK not loaded. Check MAPMYINDIA_API_KEY in .env");
          return;
        }}
        var map = new mappls.Map("map", {{ center: mapCenter, zoom: mapZoom }});
        drawOverlays(map);
      }} catch (e) {{
        showError(e.message || String(e));
      }}
    }}
    window.initMap = initMap;
  </script>
  <script src="https://apis.mappls.com/advancedmaps/api/{safe_key}/map_sdk?v=3.0&layer=vector&callback=initMap" async defer></script>
</head>
<body>
  <div id="map"></div>
  <div class="attribution">© Mappls (MapmyIndia) · ASTraM overlays · EventOps</div>
</body>
</html>"""


def save_mappls_page(html_content: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_content, encoding="utf-8")
    return path
