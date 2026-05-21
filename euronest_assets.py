"""Vector asset generator for the Euronest pitch deck.

Renders a consistent line-icon set and a stylised France map to PNG via
cairosvg, so the deck can embed crisp graphics. Icons are cached in
assets/ keyed by name + colour.
"""

import os
import cairosvg

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSET_DIR, exist_ok=True)

# Line-icon set. 24x24 viewBox, stroke-based. {C} is replaced by the
# requested colour where a solid fill is needed.
ICONS = {
    "shield_check":
        '<path d="M12 2.5l7.5 3.2v5.3c0 4.8-3.2 8.6-7.5 10.5'
        '-4.3-1.9-7.5-5.7-7.5-10.5V5.7z"/>'
        '<path d="M8.4 11.6l2.6 2.6 4.6-5.2"/>',
    "wallet":
        '<path d="M3 7.8A1.8 1.8 0 0 1 4.8 6H19a2 2 0 0 1 2 2v9'
        'a2 2 0 0 1-2 2H4.8A1.8 1.8 0 0 1 3 17.2z"/>'
        '<path d="M3 7.8V6.2A2 2 0 0 1 5 4.2h10.5"/>'
        '<circle cx="16.6" cy="12.6" r="1.5" fill="{C}" stroke="none"/>',
    "headset":
        '<path d="M4 13v-1.6a8 8 0 0 1 16 0V13"/>'
        '<path d="M4 13.4A2 2 0 0 1 6 11.4h1.2v6H6a2 2 0 0 1-2-2z"/>'
        '<path d="M20 13.4a2 2 0 0 0-2-2h-1.2v6H18a2 2 0 0 0 2-2z"/>'
        '<path d="M20 16v.8a3.2 3.2 0 0 1-3.2 3.2H14"/>',
    "alert":
        '<path d="M12 3.6l9 15.4H3z"/>'
        '<path d="M12 9.6v4.6"/>'
        '<circle cx="12" cy="17" r="0.4" fill="{C}" stroke="none"/>',
    "doc":
        '<path d="M6.5 3h7l4.5 4.5V21H6.5z"/>'
        '<path d="M13.5 3v4.5H18"/>'
        '<path d="M9 12.5h6"/><path d="M9 15.5h6"/><path d="M9 9.5h2.5"/>',
    "euro":
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M15.6 8.9a4 4 0 1 0 0 6.2"/>'
        '<path d="M7.6 11h6"/><path d="M7.6 13.2h5"/>',
    "calendar":
        '<rect x="4" y="5.5" width="16" height="15" rx="1.8"/>'
        '<path d="M4 10h16"/><path d="M9 3.5v4"/><path d="M15 3.5v4"/>',
    "trend":
        '<path d="M4 15.6l5-5 3.5 3 6.5-7.1"/>'
        '<path d="M14.6 6.5H19V11"/>',
    "building":
        '<path d="M5 21V6.5l8-3.5V21"/>'
        '<path d="M13 10.5h6V21"/>'
        '<path d="M8 8.6h2.2"/><path d="M8 12h2.2"/><path d="M8 15.4h2.2"/>'
        '<path d="M3.5 21h17"/>',
    "scatter":
        '<rect x="3.5" y="3.5" width="6.2" height="6.2" rx="1.2"/>'
        '<rect x="14" y="5" width="6.2" height="6.2" rx="1.2"/>'
        '<rect x="4.6" y="14" width="6.2" height="6.2" rx="1.2"/>'
        '<rect x="14.3" y="14.6" width="5.8" height="5.8" rx="1.2"/>',
    "search":
        '<circle cx="11" cy="11" r="6.6"/>'
        '<path d="M20.5 20.5l-4.9-4.9"/>',
    "cursor":
        '<path d="M6.5 5.3l3.7 14.4 3-6.2 6.5-2.6z"/>',
    "key":
        '<circle cx="8" cy="12" r="4.3"/>'
        '<path d="M11.9 11.4H21"/>'
        '<path d="M18.3 11.4v3.1"/><path d="M21 11.4v2.5"/>',
    "home":
        '<path d="M3.4 11.6L12 4l8.6 7.6"/>'
        '<path d="M5.7 9.8v10.4h12.6V9.8"/>'
        '<path d="M9.9 20.2v-5.6h4.2v5.6"/>',
    "refresh":
        '<path d="M4.6 12a7.4 7.4 0 0 1 12.6-5.2l2.2 2.2"/>'
        '<path d="M19.6 4.2v5h-5"/>'
        '<path d="M19.4 12a7.4 7.4 0 0 1-12.6 5.2l-2.2-2.2"/>'
        '<path d="M4.4 19.8v-5h5"/>',
    "wifi":
        '<path d="M4.6 11.4a11 11 0 0 1 14.8 0"/>'
        '<path d="M7.6 14.7a6.7 6.7 0 0 1 8.8 0"/>'
        '<path d="M10.4 17.9a2.5 2.5 0 0 1 3.2 0"/>'
        '<circle cx="12" cy="20.4" r="0.5" fill="{C}" stroke="none"/>',
    "dumbbell":
        '<path d="M3.5 9.3v5.4"/><path d="M6.5 6.8v10.4"/>'
        '<path d="M6.5 12h11"/>'
        '<path d="M17.5 6.8v10.4"/><path d="M20.5 9.3v5.4"/>',
    "bank":
        '<path d="M3.4 9.6L12 4l8.6 5.6"/>'
        '<path d="M5 9.6h14"/>'
        '<path d="M6.6 9.6v8"/><path d="M10.2 9.6v8"/>'
        '<path d="M13.8 9.6v8"/><path d="M17.4 9.6v8"/>'
        '<path d="M4 20.4h16"/>',
    "wrench":
        '<path d="M15.4 7.2a4.4 4.4 0 0 1-5.6 5.6l-5 5L6 19l5-5'
        'a4.4 4.4 0 0 0 5.6-5.6l-2.6 2.6-2.2-.4-.4-2.2z"/>',
    "clock":
        '<circle cx="12" cy="12" r="8.6"/>'
        '<path d="M12 6.8v5.5l3.5 2"/>',
    "moon":
        '<path d="M20.2 13.6A8.6 8.6 0 0 1 10.4 3.8'
        ' 8.6 8.6 0 1 0 20.2 13.6z"/>',
    "users":
        '<circle cx="9" cy="8.4" r="3.5"/>'
        '<path d="M3 19.6c0-3.7 2.9-5.8 6-5.8s6 2.1 6 5.8"/>'
        '<path d="M16 5.2a3.5 3.5 0 0 1 0 6.7"/>'
        '<path d="M17.5 14.1c2.7.5 4 2.4 4 5.5"/>',
    "person":
        '<circle cx="12" cy="8" r="3.7"/>'
        '<path d="M4.8 20.2c0-4 3.2-6.2 7.2-6.2s7.2 2.2 7.2 6.2"/>',
    "target":
        '<circle cx="12" cy="12" r="8.6"/>'
        '<circle cx="12" cy="12" r="4.9"/>'
        '<circle cx="12" cy="12" r="1.4" fill="{C}" stroke="none"/>',
    "pin":
        '<path d="M12 21.5c4.6-4.7 7-8 7-11.2A7 7 0 0 0 5 10.3'
        'c0 3.2 2.4 6.5 7 11.2z"/>'
        '<circle cx="12" cy="10.2" r="2.7"/>',
    "rocket":
        '<path d="M12 3.4c3 2.3 4.8 5.3 4.8 8.9L15 16.2H9l-1.8-3.9'
        'c0-3.6 1.8-6.6 4.8-8.9z"/>'
        '<circle cx="12" cy="10" r="1.9"/>'
        '<path d="M9 16.2l-2.2 4.2 3.7-1.7"/>'
        '<path d="M15 16.2l2.2 4.2-3.7-1.7"/>',
    "flag":
        '<path d="M6 21V3.6"/>'
        '<path d="M6 4.4h11.5l-2.3 3.4 2.3 3.4H6"/>',
    "lock":
        '<rect x="4.8" y="10.8" width="14.4" height="9.8" rx="2.2"/>'
        '<path d="M8 10.8V8a4 4 0 0 1 8 0v2.8"/>'
        '<circle cx="12" cy="15.4" r="1.5" fill="{C}" stroke="none"/>',
    "leaf":
        '<path d="M5 19c0-8.6 6.6-14 15-14 0 8.6-6.6 14-15 14z"/>'
        '<path d="M5.4 18.6c3.6-3.9 7.2-6.5 11.2-8.4"/>',
    "chat":
        '<path d="M4.6 5.5h14.8v10.2h-9.2L5.6 20z"/>'
        '<path d="M8.6 9.1h7.2"/><path d="M8.6 12.1h4.6"/>',
    "fire":
        '<path d="M12 3.2c.5 3 2.4 4.3 3.8 6.1 1 1.3 1.7 2.8 1.7 4.4'
        'a5.5 5.5 0 0 1-11 0c0-1.6.6-2.9 1.6-3.9.3 1.3 1 2.1 2.1 2.5'
        '-1.2-2.7-.3-6.3 1.8-9.1z"/>',
    "camera":
        '<rect x="3.5" y="6.8" width="17" height="12.7" rx="2.4"/>'
        '<circle cx="12" cy="13" r="3.9"/>'
        '<path d="M8.4 6.8l1.5-2.4h4.2l1.5 2.4"/>',
    "check":
        '<circle cx="12" cy="12" r="8.7"/>'
        '<path d="M8.2 12.2l2.6 2.6 5-5.5"/>',
    "star":
        '<path d="M12 3.4l2.7 5.4 6 .9-4.3 4.2 1 6L12 17.1l-5.4 2.8'
        ' 1-6L3.3 9.7l6-.9z"/>',
    "globe":
        '<circle cx="12" cy="12" r="8.6"/>'
        '<path d="M3.4 12h17.2"/>'
        '<path d="M12 3.4c2.6 2.6 3.9 5.6 3.9 8.6s-1.3 6-3.9 8.6'
        'c-2.6-2.6-3.9-5.6-3.9-8.6s1.3-6 3.9-8.6z"/>',
    "compass":
        '<circle cx="12" cy="12" r="8.6"/>'
        '<path d="M15.5 8.5l-2 5.5-5 2 2-5.5z"/>',
    "handshake":
        '<path d="M3.5 12.5l4-4 3 1 3.5-1 6.5 4"/>'
        '<path d="M3.5 12.5v3.5l3.5 3 2.5-2 2 1.5 2-1.5 4-2.5"/>'
        '<path d="M10.5 9.5l2.5 2.5"/>',
    "plus":
        '<path d="M12 5v14"/><path d="M5 12h14"/>',
}

_ICON_TPL = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'fill="none" stroke="{C}" stroke-width="{W}" '
    'stroke-linecap="round" stroke-linejoin="round">{BODY}</svg>'
)

_cache = set()


def icon(name, color="#102A54", size=220, weight=1.65):
    """Render an icon to assets/ and return the PNG path."""
    key = f"{name}_{color.lstrip('#')}_{size}_{weight}"
    path = os.path.join(ASSET_DIR, key + ".png")
    if key in _cache or os.path.exists(path):
        _cache.add(key)
        return path
    body = ICONS[name].replace("{C}", color)
    svg = _ICON_TPL.format(C=color, W=weight, BODY=body)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=path,
                     output_width=size, output_height=size)
    _cache.add(key)
    return path


# ---------------------------------------------------------------------
# Stylised France map
# ---------------------------------------------------------------------
# Outline in a 0..200 x 0..215 box, clockwise from the north.
FRANCE_OUTLINE = [
    (98, 15), (110, 22), (130, 31), (151, 43), (165, 59), (168, 78),
    (162, 94), (172, 110), (170, 126), (160, 140), (165, 151),
    (138, 156), (116, 161), (98, 172), (72, 164), (50, 155),
    (44, 136), (52, 112), (44, 95), (34, 88), (12, 80), (26, 68),
    (54, 66), (62, 55), (74, 45), (86, 31),
]

FRANCE_VIEW = (200, 215)

# City anchor points in the same coordinate space.
FRANCE_CITIES = {
    "Paris": (95, 52),
    "Lille": (100, 26),
    "Lyon": (132, 104),
    "Toulouse": (82, 142),
    "Marseille": (140, 150),
}


def france_map(fill="#E7EDF6", outline="#102A54", width=900):
    """Render the France silhouette (no pins) to a transparent PNG."""
    path = os.path.join(ASSET_DIR, "france.png")
    pts = " ".join(f"{x},{y}" for x, y in FRANCE_OUTLINE)
    vw, vh = FRANCE_VIEW
    height = int(width * vh / vw)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {vw} {vh}">'
        f'<polygon points="{pts}" fill="{fill}" stroke="{outline}" '
        f'stroke-width="1.8" stroke-linejoin="round"/>'
        f'</svg>'
    )
    cairosvg.svg2png(bytestring=svg.encode(), write_to=path,
                     output_width=width, output_height=height)
    return path, (vw, vh)


if __name__ == "__main__":
    for nm in ICONS:
        icon(nm)
    france_map()
    print(f"Rendered {len(ICONS)} icons + France map into {ASSET_DIR}")
