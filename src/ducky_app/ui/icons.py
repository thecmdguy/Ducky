"""
Flat SVG tool icons — 40×40, rendered once and cached.
Each icon uses a colored rounded-rect background with a white symbol,
matching the style used by network tool sites like mxtoolbox.com.
"""

from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

_CACHE: dict[str, QIcon] = {}

_SVGS: dict[str, str] = {

'ping': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#3b82f6"/>
<circle cx="20" cy="27" r="3.5" fill="white"/>
<path d="M13 21a9 9 0 0 1 14 0" stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round"/>
<path d="M8 15a16 16 0 0 1 24 0" stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round"/>
</svg>''',

'traceroute': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#0ea5e9"/>
<circle cx="9" cy="20" r="3.5" fill="white"/>
<circle cx="20" cy="11" r="3.5" fill="white"/>
<circle cx="31" cy="20" r="3.5" fill="white"/>
<circle cx="20" cy="29" r="3.5" fill="white"/>
<line x1="12" y1="20" x2="17" y2="13" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="23" y1="13" x2="28" y2="20" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="28" y1="23" x2="23" y2="26" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="17" y1="26" x2="12" y2="23" stroke="white" stroke-width="2" stroke-linecap="round"/>
</svg>''',

'dns': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#2563eb"/>
<circle cx="20" cy="20" r="12" fill="none" stroke="white" stroke-width="2"/>
<path d="M20 8 Q15 14 15 20 Q15 26 20 32 Q25 26 25 20 Q25 14 20 8Z" fill="none" stroke="white" stroke-width="1.5"/>
<line x1="8" y1="20" x2="32" y2="20" stroke="white" stroke-width="1.5"/>
<line x1="10" y1="14.5" x2="30" y2="14.5" stroke="white" stroke-width="1.5"/>
<line x1="10" y1="25.5" x2="30" y2="25.5" stroke="white" stroke-width="1.5"/>
</svg>''',

'mx': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#f59e0b"/>
<rect x="7" y="12" width="26" height="18" rx="2.5" fill="none" stroke="white" stroke-width="2"/>
<polyline points="7,12 20,23 33,12" stroke="white" stroke-width="2" fill="none" stroke-linejoin="round"/>
</svg>''',

'whois': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#6366f1"/>
<circle cx="20" cy="20" r="12" fill="none" stroke="white" stroke-width="2"/>
<line x1="20" y1="19" x2="20" y2="28" stroke="white" stroke-width="3" stroke-linecap="round"/>
<circle cx="20" cy="13.5" r="2" fill="white"/>
</svg>''',

'port': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#10b981"/>
<rect x="7" y="9" width="26" height="8" rx="2" fill="none" stroke="white" stroke-width="2"/>
<rect x="7" y="21" width="26" height="8" rx="2" fill="none" stroke="white" stroke-width="2"/>
<circle cx="28" cy="13" r="2" fill="white"/>
<circle cx="28" cy="25" r="2" fill="white"/>
<line x1="16" y1="17" x2="16" y2="21" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="24" y1="17" x2="24" y2="21" stroke="white" stroke-width="2" stroke-linecap="round"/>
</svg>''',

'ipinfo': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#14b8a6"/>
<path d="M20 8 a9 9 0 1 1 0 18 a9 9 0 0 1 0-18z" fill="none" stroke="white" stroke-width="2"/>
<circle cx="20" cy="17" r="3.5" fill="white"/>
<path d="M14 27 Q17 31 20 33 Q23 31 26 27" stroke="white" stroke-width="2" fill="none" stroke-linecap="round"/>
</svg>''',

'asn': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#64748b"/>
<path d="M30 26 h2 a6 6 0 0 0 0-12 c-0.5 0-0.9 0.1-1.3 0.2 A9.5 9.5 0 1 0 12 22 v4 h18z" fill="none" stroke="white" stroke-width="2" stroke-linejoin="round"/>
</svg>''',

'subnet': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#3b82f6"/>
<rect x="8" y="8" width="10" height="10" rx="2" fill="white"/>
<rect x="22" y="8" width="10" height="10" rx="2" fill="white"/>
<rect x="8" y="22" width="10" height="10" rx="2" fill="white"/>
<rect x="22" y="22" width="10" height="10" rx="2" fill="white"/>
</svg>''',

'topology': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#8b5cf6"/>
<circle cx="20" cy="11" r="4" fill="white"/>
<circle cx="10" cy="29" r="4" fill="white"/>
<circle cx="30" cy="29" r="4" fill="white"/>
<line x1="20" y1="15" x2="12" y2="25" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
<line x1="20" y1="15" x2="28" y2="25" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
<line x1="14" y1="29" x2="26" y2="29" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
</svg>''',

'devices': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#7c3aed"/>
<rect x="5" y="10" width="30" height="18" rx="2.5" fill="none" stroke="white" stroke-width="2"/>
<line x1="5" y1="22" x2="35" y2="22" stroke="white" stroke-width="1.5"/>
<line x1="20" y1="28" x2="20" y2="33" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="13" y1="33" x2="27" y2="33" stroke="white" stroke-width="2" stroke-linecap="round"/>
</svg>''',

'http': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#6d28d9"/>
<polyline points="15,13 7,20 15,27" stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<polyline points="25,13 33,20 25,27" stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<line x1="23" y1="11" x2="17" y2="29" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
</svg>''',

'ssl': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#059669"/>
<rect x="11" y="20" width="18" height="14" rx="3" fill="none" stroke="white" stroke-width="2"/>
<path d="M14 20 v-4.5 a6 6 0 0 1 12 0 v4.5" fill="none" stroke="white" stroke-width="2" stroke-linecap="round"/>
<circle cx="20" cy="27" r="2.5" fill="white"/>
</svg>''',

'smtp': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#d97706"/>
<path d="M8 20 L28 9 L22 20 L28 31 Z" fill="white"/>
<line x1="22" y1="20" x2="9" y2="20" stroke="white" stroke-width="2" stroke-linecap="round"/>
</svg>''',

'blacklist': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#dc2626"/>
<path d="M20 7 L32 13 V22 C32 28.5 27 33.5 20 35 C13 33.5 8 28.5 8 22 V13 Z" fill="none" stroke="white" stroke-width="2" stroke-linejoin="round"/>
<line x1="15" y1="16" x2="25" y2="26" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
<line x1="25" y1="16" x2="15" y2="26" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
</svg>''',

'cve': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#b91c1c"/>
<circle cx="20" cy="22" r="9" fill="none" stroke="white" stroke-width="2"/>
<path d="M16 14 a4 4 0 0 1 8 0" fill="none" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="20" y1="12" x2="20" y2="9" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="8" y1="22" x2="11" y2="22" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="29" y1="22" x2="32" y2="22" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="20" y1="31" x2="20" y2="34" stroke="white" stroke-width="2" stroke-linecap="round"/>
</svg>''',

'password': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#ef4444"/>
<circle cx="15" cy="18" r="7" fill="none" stroke="white" stroke-width="2.5"/>
<line x1="20" y1="23" x2="33" y2="36" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
<line x1="27" y1="30" x2="31" y2="26" stroke="white" stroke-width="2" stroke-linecap="round"/>
</svg>''',

'hash': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#dc2626"/>
<line x1="14" y1="9"  x2="12" y2="31" stroke="white" stroke-width="3" stroke-linecap="round"/>
<line x1="26" y1="9"  x2="24" y2="31" stroke="white" stroke-width="3" stroke-linecap="round"/>
<line x1="9"  y1="17" x2="31" y2="17" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
<line x1="9"  y1="25" x2="31" y2="25" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
</svg>''',

'monitor': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#1d4ed8"/>
<rect x="10" y="16" width="5" height="14" rx="1.5" fill="white" opacity="0.55"/>
<rect x="18" y="11" width="5" height="19" rx="1.5" fill="white"/>
<rect x="26" y="19" width="5" height="11" rx="1.5" fill="white" opacity="0.55"/>
<line x1="9" y1="31" x2="31" y2="31" stroke="white" stroke-width="2" stroke-linecap="round"/>
</svg>''',

'wol': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#ea580c"/>
<path d="M24 7 L14 22 L20 22 L16 33 L26 18 L20 18 Z" fill="white"/>
</svg>''',

'macvendor': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#0891b2"/>
<rect x="12" y="12" width="16" height="16" rx="2.5" fill="none" stroke="white" stroke-width="2"/>
<line x1="17" y1="8"  x2="17" y2="12" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="23" y1="8"  x2="23" y2="12" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="17" y1="28" x2="17" y2="32" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="23" y1="28" x2="23" y2="32" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="8"  y1="17" x2="12" y2="17" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="8"  y1="23" x2="12" y2="23" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="28" y1="17" x2="32" y2="17" stroke="white" stroke-width="2" stroke-linecap="round"/>
<line x1="28" y1="23" x2="32" y2="23" stroke="white" stroke-width="2" stroke-linecap="round"/>
</svg>''',

'propagation': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#15803d"/>
<circle cx="20" cy="20" r="12" fill="none" stroke="white" stroke-width="2"/>
<path d="M20 8 Q16 14 16 20 Q16 26 20 32 Q24 26 24 20 Q24 14 20 8Z" fill="none" stroke="white" stroke-width="1.5"/>
<line x1="8" y1="20" x2="32" y2="20" stroke="white" stroke-width="1.5"/>
<polyline points="14,19 18,25 28,13" stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>''',

'arptable': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#4338ca"/>
<rect x="6" y="9"  width="28" height="7" rx="1.5" fill="white" opacity="0.9"/>
<rect x="6" y="19" width="28" height="5" rx="1"   fill="none" stroke="white" stroke-width="1.5"/>
<rect x="6" y="27" width="28" height="5" rx="1"   fill="none" stroke="white" stroke-width="1.5"/>
<line x1="16" y1="9" x2="16" y2="32" stroke="white" stroke-width="1.5" opacity="0.4"/>
</svg>''',

}


def get_tool_icon(name: str, size: int = 40) -> QIcon:
    """Return a cached QIcon for the named tool."""
    key = f"{name}@{size}"
    if key not in _CACHE:
        svg = _SVGS.get(name, _SVGS['whois'])
        data = QByteArray(svg.strip().encode())
        renderer = QSvgRenderer(data)
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        renderer.render(painter)
        painter.end()
        _CACHE[key] = QIcon(pix)
    return _CACHE[key]
