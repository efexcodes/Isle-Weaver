import math
import random

import pygame

from core.algorithms import kruskal_mst
from core.geometry import segment_distance
from core.graph import Bridge, Island
from ui import colors, layout

FONT_FAMILY = "segoeui,trebuchetms,arial"
TITLE_FAMILY = "georgia,timesnewroman"
ISLAND_TOUCH = 20

MENU_DECOR = [
    [(60, 64), (186, 40), (120, 178)],
    [(790, 48), (906, 104), (850, 214)],
    [(64, 616), (204, 636)],
    [(756, 632), (900, 600)],
]


def _font(size, bold=False, family=FONT_FAMILY):
    return pygame.font.SysFont(family, size, bold=bold)


def _blob(seed, radius, samples=40):
    rng = random.Random(seed)
    k = rng.randint(6, 8)
    radii = [radius * rng.uniform(0.8, 1.2) for _ in range(k)]
    turn = rng.uniform(0, math.tau)
    points = []
    for i in range(samples):
        a = math.tau * i / samples
        f = a / math.tau * k
        j = int(f) % k
        t = (1 - math.cos((f - int(f)) * math.pi)) / 2
        r = radii[j] * (1 - t) + radii[(j + 1) % k] * t
        points.append((math.cos(a + turn) * r, math.sin(a + turn) * r))
    return points


def _placed(points, cx, cy, scale=1.0, dy=0.0):
    return [(cx + x * scale, cy + y * scale + dy) for x, y in points]


def _star_points(cx, cy, outer, inner):
    points = []
    for i in range(10):
        r = outer if i % 2 == 0 else inner
        a = -math.pi / 2 + i * math.pi / 5
        points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return points


def _outlined(font, text, fg, edge):
    base = font.render(text, True, fg)
    rim = font.render(text, True, edge)
    out = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)
    for dx in range(3):
        for dy in range(3):
            if dx != 1 or dy != 1:
                out.blit(rim, (dx, dy))
    out.blit(base, (1, 1))
    return out


def dashed_line(surface, color, p1, p2, width=2, dash=8, gap=6):
    x1, y1 = p1
    x2, y2 = p2
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        pygame.draw.line(surface, color, (x1 + ux * pos, y1 + uy * pos), (x1 + ux * end, y1 + uy * end), width)
        pos = end + gap


def edge_at(islands, edges, origin, point, reach=10):
    ox, oy = origin
    px, py = point[0] - ox, point[1] - oy
    if any(math.hypot(px - i.x, py - i.y) < ISLAND_TOUCH for i in islands):
        return None
    best, best_d = None, reach
    for e in edges:
        p, q = islands[e.a], islands[e.b]
        d = segment_distance(px, py, p.x, p.y, q.x, q.y)
        if d < best_d:
            best, best_d = e, d
    return best


class Renderer:
    def __init__(self):
        self.small = _font(13)
        self.label = _font(11, bold=True)
        self.body = _font(15)
        self.button = _font(15, bold=True)
        self.bold = _font(17, bold=True)
        self.big = _font(26, bold=True)
        self.pill = _font(12, bold=True)
        self.number = _font(14, bold=True)
        self.title = pygame.font.SysFont(TITLE_FAMILY, 66, bold=True)

        self.fx = pygame.Surface(layout.SCREEN_SIZE, pygame.SRCALPHA)
        self.shade = pygame.Surface(layout.SCREEN_SIZE, pygame.SRCALPHA)
        self.shade.fill((24, 36, 44, 120))

        self.map_sea = self._sea(layout.MAP_RECT.size, 14)
        self.menu_sea = self._sea(layout.SCREEN_SIZE, 0)
        rng = random.Random(11)
        self.map_waves = self._waves(rng, layout.MAP_RECT, 28)
        self.menu_waves = self._waves(rng, pygame.Rect((0, 0), layout.SCREEN_SIZE), 42)
        self.island_art = []
        self.decor = self._build_decor()

    def _sea(self, size, radius):
        w, h = size
        sea = pygame.Surface(size, pygame.SRCALPHA)
        for y in range(h):
            t = y / max(1, h - 1)
            shade = [round(a + (b - a) * t) for a, b in zip(colors.SEA_TOP, colors.SEA_BOTTOM)]
            pygame.draw.line(sea, shade, (0, y), (w, y))

        grid = pygame.Surface(size, pygame.SRCALPHA)
        for x in range(0, w, 48):
            pygame.draw.line(grid, (255, 255, 255, 20), (x, 0), (x, h))
        for y in range(0, h, 48):
            pygame.draw.line(grid, (255, 255, 255, 20), (0, y), (w, y))
        sea.blit(grid, (0, 0))
        self._compass(sea, (w - 62, h - 62), 32)

        if radius:
            mask = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
            sea.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return sea

    def _compass(self, surface, center, r):
        c = r + 16
        layer = pygame.Surface((c * 2, c * 2), pygame.SRCALPHA)
        points = []
        for i in range(8):
            a = -math.pi / 2 + i * math.pi / 4
            rr = r if i % 2 == 0 else r * 0.26
            points.append((c + rr * math.cos(a), c + rr * math.sin(a)))
        pygame.draw.circle(layer, (255, 255, 255, 55), (c, c), int(r * 0.62), 1)
        pygame.draw.polygon(layer, (255, 255, 255, 70), points)
        pygame.draw.polygon(layer, (255, 255, 255, 120), points, 1)
        north = self.label.render("U", True, (255, 255, 255))
        north.set_alpha(150)
        layer.blit(north, north.get_rect(center=(c, c - r - 8)))
        surface.blit(layer, (center[0] - c, center[1] - c))

    def _waves(self, rng, rect, amount):
        return [
            (
                rng.uniform(rect.left + 20, rect.right - 40),
                rng.uniform(rect.top + 20, rect.bottom - 20),
                rng.uniform(0, math.tau),
                rng.randint(8, 13),
            )
            for _ in range(amount)
        ]

    def _draw_waves(self, surface, waves, t):
        for x, y, phase, s in waves:
            x += math.sin(t * 0.7 + phase) * 6
            y += math.cos(t * 0.45 + phase) * 2
            for k in range(2):
                pygame.draw.arc(surface, colors.WAVE, (x + k * s, y, s, s * 0.8), 0.35, math.pi - 0.35, 2)

    def _island_art(self, seed, text=None):
        radius = random.Random(seed).uniform(19, 23)
        shape = _blob(seed, radius)
        grass = _blob(seed + 1, radius * 0.62)
        size = int(radius * 4)
        c = size / 2

        halo = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(halo, colors.SHALLOW + (110,), _placed(shape, c, c, 1.55))
        pygame.draw.polygon(halo, colors.SHALLOW + (210,), _placed(shape, c, c, 1.22))

        body = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(body, colors.SAND_EDGE, _placed(shape, c, c, 1.0, 3))
        pygame.draw.polygon(body, colors.SAND, _placed(shape, c, c))
        pygame.draw.polygon(body, colors.GRASS_DARK, _placed(grass, c, c, 1.0, 1))
        pygame.draw.polygon(body, colors.GRASS, _placed(grass, c, c, 1.0, -1))
        if text:
            tag = _outlined(self.number, text, (255, 255, 255), colors.LABEL_EDGE)
            body.blit(tag, tag.get_rect(center=(c, c - 1)))
        return halo, body

    def _art_for(self, islands, origin, labelled):
        ox, oy = origin
        art = []
        for isl in islands:
            seed = int(isl.x) * 7919 + int(isl.y) * 104729
            halo, body = self._island_art(seed, str(isl.id + 1) if labelled else None)
            pos = (ox + isl.x - halo.get_width() / 2, oy + isl.y - halo.get_height() / 2)
            art.append((halo, body, pos))
        return art

    def load_islands(self, islands):
        self.island_art = self._art_for(islands, layout.MAP_RECT.topleft, True)

    def _build_decor(self):
        groups = []
        for spots in MENU_DECOR:
            islands = [Island(i, x, y) for i, (x, y) in enumerate(spots)]
            n = len(islands)
            edges = [
                Bridge(a, b, round(math.hypot(islands[a].x - islands[b].x, islands[a].y - islands[b].y)))
                for a in range(n)
                for b in range(a + 1, n)
            ]
            groups.append((islands, kruskal_mst(edges, n), self._art_for(islands, (0, 0), False)))
        return groups

    def _bridge(self, surface, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        length = math.hypot(x2 - x1, y2 - y1)
        if length == 0:
            return
        ux, uy = (x2 - x1) / length, (y2 - y1) / length
        nx, ny = -uy, ux
        pygame.draw.line(surface, colors.WOOD_DARK, p1, p2, 11)
        pygame.draw.line(surface, colors.WOOD, p1, p2, 7)
        s = 10.0
        while s < length - 10:
            cx, cy = x1 + ux * s, y1 + uy * s
            pygame.draw.line(surface, colors.WOOD_DARK, (cx - nx * 5, cy - ny * 5), (cx + nx * 5, cy + ny * 5), 2)
            s += 8

    def _pill(self, surface, text, center, fg, bg, edge):
        tag = self.pill.render(text, True, fg)
        box = tag.get_rect(center=center).inflate(10, 2)
        pygame.draw.rect(surface, bg, box, border_radius=box.height // 2)
        pygame.draw.rect(surface, edge, box, 1, border_radius=box.height // 2)
        surface.blit(tag, tag.get_rect(center=box.center))
        return box

    def _cloud(self, surface, x, y):
        for dx, dy, r in ((-6, 1, 5), (0, -3, 6), (7, 1, 4)):
            pygame.draw.circle(surface, colors.CLOUD, (x + dx, y + dy), r)
        pygame.draw.lines(surface, colors.BOLT, False, [(x + 1, y + 5), (x - 2, y + 9), (x + 2, y + 9), (x - 1, y + 14)], 2)

    def _panel(self, surface, rect, radius=12):
        pygame.draw.rect(surface, colors.PAPER, rect, border_radius=radius)
        pygame.draw.rect(surface, colors.PAPER_EDGE, rect, 1, border_radius=radius)

    def _card(self, surface, rect):
        pygame.draw.rect(surface, colors.TITLE_SHADOW, rect.move(0, 6), border_radius=18)
        pygame.draw.rect(surface, colors.PAPER, rect, border_radius=18)
        pygame.draw.rect(surface, colors.PAPER_EDGE, rect, 1, border_radius=18)

    def _text(self, surface, font, text, color, pos):
        img = font.render(text, True, color)
        surface.blit(img, pos)
        return img.get_rect(topleft=pos)

    def _centered(self, surface, font, text, color, cx, top):
        img = font.render(text, True, color)
        surface.blit(img, img.get_rect(midtop=(cx, top)))

    def _star(self, surface, center, r, on):
        points = _star_points(center[0], center[1], r, r * 0.46)
        if on:
            pygame.draw.polygon(surface, colors.STAR_SHADE, [(x, y + 3) for x, y in points])
        pygame.draw.polygon(surface, colors.STAR_ON if on else colors.STAR_OFF, points)
        pygame.draw.polygon(surface, colors.STAR_EDGE if on else colors.STAR_OFF_EDGE, points, 2)

    def clear(self, surface):
        surface.fill(colors.BACKGROUND)

    def draw_map(self, surface, level, t, hover=None, mst=None, storm_rate=1.6):
        rect = layout.MAP_RECT
        surface.blit(self.map_sea, rect.topleft)
        surface.set_clip(rect)
        self._draw_waves(surface, self.map_waves, t)
        for halo, _, pos in self.island_art:
            surface.blit(halo, pos)

        ox, oy = rect.topleft
        pts = [(ox + i.x, oy + i.y) for i in level.islands]
        reveal = mst is not None
        mst = mst or set()

        self.fx.fill((0, 0, 0, 0))
        for e in level.edges:
            p1, p2 = pts[e.a], pts[e.b]
            if e in mst:
                pygame.draw.line(self.fx, colors.OPTIMAL + (170,), p1, p2, 24)
            elif not reveal and e is hover:
                pygame.draw.line(self.fx, colors.HOVER + (170,), p1, p2, 12)
        surface.blit(self.fx, (0, 0))

        for e in level.edges:
            if e.selected:
                continue
            p1, p2 = pts[e.a], pts[e.b]
            if e in mst:
                pygame.draw.line(surface, colors.OPTIMAL, p1, p2, 4)
            elif reveal:
                dashed_line(surface, colors.ROPE_FADED, p1, p2)
            else:
                dashed_line(surface, colors.STORM if e.storm else colors.ROPE, p1, p2)

        for e in level.edges:
            if e.selected:
                self._bridge(surface, pts[e.a], pts[e.b])

        for _, body, pos in self.island_art:
            surface.blit(body, pos)

        for e in level.edges:
            p1, p2 = pts[e.a], pts[e.b]
            mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            if e.selected:
                self._pill(surface, str(e.locked_cost), mid, colors.PAPER, colors.WOOD_DARK, colors.WOOD_DARK)
            elif e in mst:
                self._pill(surface, str(e.weight), mid, (255, 255, 255), colors.OPTIMAL, colors.OPTIMAL)
            elif reveal:
                continue
            elif e.storm:
                box = self._pill(surface, str(e.current_cost(storm_rate)), mid, (255, 255, 255), colors.STORM, colors.STORM_EDGE)
                self._cloud(surface, box.right + 9, box.top - 2)
            elif e is hover:
                self._pill(surface, str(e.weight), mid, colors.INK, colors.HOVER_PILL, colors.WOOD)
            else:
                self._pill(surface, str(e.weight), mid, colors.MUTED, colors.PAPER, colors.PAPER_EDGE)

        surface.set_clip(None)
        pygame.draw.rect(surface, colors.CARD_SHADOW, rect, 2, border_radius=14)

    def draw_hud(self, surface, level, spent):
        r = layout.HUD_RECT
        self._panel(surface, r)
        top = r.top + 10

        x = r.left + 18
        self._text(surface, self.label, f"LEVEL {level.index + 1}", colors.MUTED, (x, top))
        self._text(surface, self.bold, level.name, colors.INK, (x, top + 16))

        x = r.left + 240
        self._text(surface, self.label, "ANGGARAN", colors.MUTED, (x, top))
        info = self.body.render(f"{spent} / {level.budget}", True, colors.INK)
        surface.blit(info, (x + 300 - info.get_width(), top - 4))
        bar = pygame.Rect(x, top + 24, 300, 10)
        pygame.draw.rect(surface, colors.BAR_BG, bar, border_radius=5)
        ratio = min(1.0, spent / level.budget) if level.budget else 0
        if ratio > 0:
            fill = pygame.Rect(bar.left, bar.top, max(10, int(bar.width * ratio)), bar.height)
            pygame.draw.rect(surface, colors.DANGER if ratio > 0.9 else colors.WOOD, fill, border_radius=5)

        x = r.left + 580
        self._text(surface, self.label, "SISA", colors.MUTED, (x, top))
        self._text(surface, self.bold, str(level.budget - spent), colors.INK, (x, top + 16))

        x = r.left + 680
        self._text(surface, self.label, "CUACA", colors.MUTED, (x, top))
        weather, tone = ("Badai", colors.STORM) if level.storms else ("Cerah", colors.INK)
        self._text(surface, self.bold, weather, tone, (x, top + 16))

    def draw_status(self, surface, text, good):
        r = layout.STATUS_RECT
        self._panel(surface, r)
        pygame.draw.circle(surface, colors.OPTIMAL if good else colors.DANGER, (r.left + 20, r.centery), 6)
        img = self.body.render(text, True, colors.INK)
        surface.blit(img, (r.left + 36, r.centery - img.get_height() // 2))

    def draw_button(self, surface, rect, text, mouse, primary=False, enabled=True):
        hot = enabled and rect.collidepoint(mouse)
        if not enabled:
            bg, fg, edge = colors.DISABLED, colors.DISABLED_TEXT, colors.DISABLED
        elif primary:
            bg = colors.TEAL_HOT if hot else colors.TEAL
            fg, edge = colors.PAPER, bg
        else:
            bg = colors.PAPER_HOT if hot else colors.PAPER
            fg, edge = colors.INK, colors.PAPER_EDGE
        box = rect.move(0, -1) if hot else rect
        if enabled:
            pygame.draw.rect(surface, colors.SHADOW, rect.move(0, 3), border_radius=10)
        pygame.draw.rect(surface, bg, box, border_radius=10)
        pygame.draw.rect(surface, edge, box, 1, border_radius=10)
        img = self.button.render(text, True, fg)
        surface.blit(img, img.get_rect(center=box.center))

    def draw_caption(self, surface, text):
        self._text(surface, self.small, text, colors.MUTED, layout.CAPTION_POS)

    def draw_popups(self, surface, popups, now):
        for p in popups:
            age = (now - p["born"]) / 900
            if age >= 1:
                continue
            tone = colors.DANGER if p["kind"] == "spend" else colors.OPTIMAL
            img = _outlined(self.bold, p["text"], tone, colors.PAPER)
            img.set_alpha(int(255 * (1 - age)))
            surface.blit(img, img.get_rect(center=(p["x"], p["y"] - 34 * age)))

    def draw_result(self, surface, result, mouse, last_level):
        surface.blit(self.shade, (0, 0))
        card = layout.CARD_RECT
        self._card(surface, card)
        cx, top = card.centerx, card.top + 24

        self._centered(surface, self.label, f"LEVEL {result['level'] + 1} SELESAI", colors.MUTED, cx, top)
        self._centered(surface, self.big, result["name"], colors.INK, cx, top + 14)
        for i in range(3):
            self._star(surface, (cx + (i - 1) * 60, top + 88), 28 if i == 1 else 23, i < result["stars"])

        if result["efficiency"] >= 100:
            verdict = "Sempurna, sama persis dengan hasil Kruskal."
        elif result["stars"] == 3:
            verdict = "Hampir optimal. Mantap."
        elif result["stars"] == 2:
            verdict = "Lumayan, tapi masih ada susunan yang lebih hemat."
        else:
            verdict = "Semua terhubung, tapi biayanya boros."
        self._centered(surface, self.body, verdict, colors.MUTED, cx, top + 124)

        rows = [
            ("Biaya kamu", str(result["spent"])),
            ("Biaya optimal (Kruskal)", str(result["optimal"])),
            ("Efisiensi", f"{result['efficiency']}%"),
        ]
        y = top + 166
        for i, (name, value) in enumerate(rows):
            if i:
                pygame.draw.line(surface, colors.BAR_BG, (card.left + 34, y - 6), (card.right - 34, y - 6))
            self._text(surface, self.body, name, colors.MUTED, (card.left + 36, y))
            img = self.bold.render(value, True, colors.INK)
            surface.blit(img, (card.right - 36 - img.get_width(), y - 2))
            y += 32

        self.draw_button(surface, layout.CARD_LEFT_BUTTON, "Ulangi  (R)", mouse)
        self.draw_button(surface, layout.CARD_RIGHT_BUTTON, "Selesai" if last_level else "Lanjut  (Spasi)", mouse, primary=True)

    def draw_complete(self, surface, mouse):
        surface.blit(self.shade, (0, 0))
        card = layout.SMALL_CARD_RECT
        self._card(surface, card)
        cx, top = card.centerx, card.top + 26
        self._centered(surface, self.label, "SEMUA LEVEL SELESAI", colors.OPTIMAL, cx, top)
        self._centered(surface, self.big, "Semua pulau sudah terhubung", colors.INK, cx, top + 18)
        self._centered(surface, self.body, "Kamu sudah menyelesaikan kelima level.", colors.MUTED, cx, top + 74)
        self._centered(surface, self.body, "Main lagi untuk mengejar efisiensi 100%.", colors.MUTED, cx, top + 98)
        self.draw_button(surface, layout.SMALL_WIDE_BUTTON, "Kembali ke menu", mouse, primary=True)

    def draw_menu(self, surface, t, mouse, version):
        surface.blit(self.menu_sea, (0, 0))
        self._draw_waves(surface, self.menu_waves, t)
        for islands, mst, art in self.decor:
            for halo, _, pos in art:
                surface.blit(halo, pos)
            for e in mst:
                self._bridge(surface, (islands[e.a].x, islands[e.a].y), (islands[e.b].x, islands[e.b].y))
            for _, body, pos in art:
                surface.blit(body, pos)

        shadow = self.title.render("Isle Weaver", True, colors.TITLE_SHADOW)
        title = self.title.render("Isle Weaver", True, colors.PAPER)
        spot = title.get_rect(center=(layout.SCREEN_SIZE[0] // 2, 150))
        surface.blit(shadow, spot.move(3, 4))
        surface.blit(title, spot)
        self._centered(surface, self.body, "Hubungkan semua pulau dengan jembatan, sehemat mungkin.", colors.PAPER, spot.centerx, spot.bottom + 4)

        self.draw_button(surface, layout.START_BUTTON, "Main", mouse, primary=True)

        foot = self.small.render("Enter untuk mulai   ·   ESC untuk keluar", True, colors.PAPER)
        surface.blit(foot, foot.get_rect(center=(layout.SCREEN_SIZE[0] // 2, 598)))
        tag = self.small.render(f"v{version}", True, colors.PAPER)
        surface.blit(tag, tag.get_rect(bottomright=(layout.SCREEN_SIZE[0] - 12, layout.SCREEN_SIZE[1] - 8)))

