"""Generate PWA icons with stdlib only (no Pillow). Brand green rounded square + white E."""
import struct, zlib, pathlib

BRAND = (14, 124, 91)
WHITE = (255, 255, 255)
OUT = pathlib.Path(__file__).resolve().parents[1] / "web" / "public" / "icons"


def _chunk(typ: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + typ + data + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


def png(w: int, h: int, px: bytes) -> bytes:
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + px[y * w * 4:(y + 1) * w * 4] for y in range(h))
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(raw, 9)) + _chunk(b"IEND", b""))


def icon(size: int, pad: int = 0) -> bytes:
    r = int(size * 0.22)
    buf = bytearray(size * size * 4)
    s = size - 2 * pad
    for y in range(size):
        for x in range(size):
            inside = pad <= x < pad + s and pad <= y < pad + s
            if inside:
                lx, ly = x - pad, y - pad
                # rounded corners
                ok = True
                ex = min(lx, s - 1 - lx)
                ey = min(ly, s - 1 - ly)
                if ex < r and ey < r:
                    ccx, ccy = (r if lx < s // 2 else s - 1 - r), (r if ly < s // 2 else s - 1 - r)
                    if (lx - ccx) ** 2 + (ly - ccy) ** 2 > r * r:
                        ok = False
                col = BRAND if ok else None
            else:
                col = None
            if col is None:
                buf[(y * size + x) * 4:(y * size + x) * 4 + 4] = b"\x00\x00\x00\x00"
                continue
            # white "E": left bar + top/mid/bottom bars (relative coords)
            u = s / 100.0
            lx, ly = x - pad, y - pad
            e = (28 * u <= lx <= 38 * u and 24 * u <= ly <= 76 * u) or \
                (28 * u <= lx <= 72 * u and 24 * u <= ly <= 34 * u) or \
                (28 * u <= lx <= 64 * u and 45 * u <= ly <= 55 * u) or \
                (28 * u <= lx <= 72 * u and 66 * u <= ly <= 76 * u)
            c = WHITE if e else BRAND
            buf[(y * size + x) * 4:(y * size + x) * 4 + 4] = bytes((c[0], c[1], c[2], 255))
    return png(size, size, bytes(buf))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "icon-192.png").write_bytes(icon(192))
    (OUT / "icon-512.png").write_bytes(icon(512))
    (OUT / "maskable-512.png").write_bytes(icon(512, pad=52))
    print("icons written to", OUT)


if __name__ == "__main__":
    main()
