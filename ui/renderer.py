import math

import pygame

from core.geometry import segment_distance
from ui import colors

ISLAND_RADIUS = 18


def make_fonts():
    family = "segoeui,arial"
    return {
        "small": pygame.font.SysFont(family, 14),
        "bold": pygame.font.SysFont(family, 18, bold=True),
        "big": pygame.font.SysFont(family, 28, bold=True),
    }


def draw_background(surface, rect):
    top, bottom = colors.OCEAN_TOP, colors.OCEAN_BOTTOM
    for y in range(rect.height):
        t = y / max(1, rect.height - 1)
        shade = [round(a + (b - a) * t) for a, b in zip(top, bottom)]
        pygame.draw.line(surface, shade, (rect.left, rect.top + y), (rect.right - 1, rect.top + y))


def dashed_line(surface, color, p1, p2, width=2, dash=7, gap=6):
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
    if any(math.hypot(px - i.x, py - i.y) < ISLAND_RADIUS for i in islands):
        return None
    best, best_d = None, reach
    for e in edges:
        p, q = islands[e.a], islands[e.b]
        d = segment_distance(px, py, p.x, p.y, q.x, q.y)
        if d < best_d:
            best, best_d = e, d
    return best


def draw_edges(surface, islands, edges, font, origin, mst, hover):
    ox, oy = origin
    for e in edges:
        p, q = islands[e.a], islands[e.b]
        p1, p2 = (p.x + ox, p.y + oy), (q.x + ox, q.y + oy)
        if e in mst:
            pygame.draw.line(surface, colors.OPTIMAL, p1, p2, 6)
        elif e.selected:
            pygame.draw.line(surface, colors.SELECTED, p1, p2, 4)
        elif e is hover:
            pygame.draw.line(surface, colors.HOVER, p1, p2, 3)
        else:
            dashed_line(surface, colors.CANDIDATE, p1, p2)

        strong = e.selected or e in mst or e is hover
        label = font.render(str(e.weight), True, colors.INK if strong else colors.MUTED)
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        surface.blit(label, (mx - label.get_width() / 2, my - label.get_height() - 2))


def draw_islands(surface, islands, font, origin):
    ox, oy = origin
    for p in islands:
        center = (int(p.x + ox), int(p.y + oy))
        pygame.draw.circle(surface, colors.SAND, center, ISLAND_RADIUS)
        pygame.draw.circle(surface, colors.SAND_DARK, center, ISLAND_RADIUS, 3)
        label = font.render(str(p.id + 1), True, colors.SAND_TEXT)
        surface.blit(label, label.get_rect(center=center))


def draw_text(surface, font, text, pos, color=colors.INK):
    label = font.render(text, True, color)
    surface.blit(label, pos)
    return label.get_size()


def draw_hud(surface, fonts, rect, level, spent):
    pygame.draw.rect(surface, colors.PANEL, rect, border_radius=12)
    pygame.draw.rect(surface, colors.PANEL_EDGE, rect, 1, border_radius=12)
    x, y = rect.left + 18, rect.top + 10
    left = level.budget - spent
    fields = [
        ("LEVEL", f"{level.index + 1} - {level.name}", colors.INK, 220),
        ("ANGGARAN", str(level.budget), colors.INK, 130),
        ("TERPAKAI", str(spent), colors.INK, 130),
        ("SISA", str(left), colors.DANGER if left < 0 else colors.INK, 130),
    ]
    for name, value, tone, width in fields:
        draw_text(surface, fonts["small"], name, (x, y), colors.MUTED)
        draw_text(surface, fonts["bold"], value, (x, y + 18), tone)
        x += width


def draw_banner(surface, font, rect, connected):
    if connected:
        bg, tone, text = colors.OK_BG, colors.OPTIMAL, "Semua pulau sudah terhubung"
    else:
        bg, tone, text = colors.BAD_BG, colors.DANGER, "Belum semua pulau terhubung"
    pygame.draw.rect(surface, bg, rect, border_radius=10)
    pygame.draw.circle(surface, tone, (rect.left + 18, rect.centery), 5)
    label = font.render(text, True, tone)
    surface.blit(label, (rect.left + 32, rect.centery - label.get_height() // 2))


def draw_button(surface, font, rect, text, primary=True, enabled=True):
    if not enabled:
        bg, fg = colors.DISABLED, colors.DISABLED_TEXT
    elif primary:
        bg, fg = colors.SELECTED, (255, 255, 255)
    else:
        bg, fg = colors.BUTTON_ALT, colors.INK
    pygame.draw.rect(surface, bg, rect, border_radius=10)
    label = font.render(text, True, fg)
    surface.blit(label, label.get_rect(center=rect.center))


def draw_star(surface, center, radius, on):
    cx, cy = center
    points = []
    for i in range(10):
        r = radius if i % 2 == 0 else radius * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pygame.draw.polygon(surface, colors.STAR_ON if on else colors.STAR_OFF, points)


def dim(surface, alpha):
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((20, 30, 40, alpha))
    surface.blit(shade, (0, 0))


def draw_result(surface, fonts, result):
    dim(surface, 140)
    card = pygame.Rect(0, 0, 380, 290)
    card.center = surface.get_rect().center
    pygame.draw.rect(surface, colors.PANEL, card, border_radius=16)

    y = card.top + 22
    title = fonts["small"].render(f"HASIL LEVEL {result['level'] + 1}", True, colors.MUTED)
    surface.blit(title, title.get_rect(midtop=(card.centerx, y)))
    for i in range(3):
        draw_star(surface, (card.centerx + (i - 1) * 52, y + 58), 22, i < result["stars"])

    y += 104
    rows = [
        ("Biaya kamu", str(result["spent"])),
        ("Biaya optimal (Kruskal)", str(result["optimal"])),
        ("Efisiensi", f"{result['efficiency']}%"),
    ]
    for name, value in rows:
        draw_text(surface, fonts["small"], name, (card.left + 26, y), colors.MUTED)
        label = fonts["bold"].render(value, True, colors.INK)
        surface.blit(label, (card.right - 26 - label.get_width(), y - 2))
        y += 30

    hint = fonts["small"].render("SPASI untuk lanjut, R untuk ulangi level ini", True, colors.MUTED)
    surface.blit(hint, hint.get_rect(midtop=(card.centerx, y + 14)))


def draw_complete(surface, fonts):
    dim(surface, 180)
    cx, cy = surface.get_rect().center
    title = fonts["big"].render("Semua level selesai!", True, (255, 255, 255))
    surface.blit(title, title.get_rect(center=(cx, cy - 20)))
    sub = fonts["small"].render("Tekan R untuk main dari Level 1 lagi, atau ESC untuk keluar.", True, (225, 230, 235))
    surface.blit(sub, sub.get_rect(center=(cx, cy + 18)))
