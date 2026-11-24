import sys

import pygame

from core.algorithms import bfs_connected, kruskal_mst
from game.level_generator import LEVELS, generate_level
from game.scoring import efficiency_percent, stars_for_efficiency
from ui import colors, renderer

SCREEN_SIZE = (900, 640)
HUD_RECT = pygame.Rect(20, 16, 860, 64)
MAP_RECT = pygame.Rect(20, 94, 860, 436)
BANNER_RECT = pygame.Rect(20, 542, 640, 38)
RESET_BUTTON = pygame.Rect(670, 542, 100, 38)
SUBMIT_BUTTON = pygame.Rect(780, 542, 100, 38)
CAPTION_POS = (22, 596)

REVEAL_MS = 300
REVEAL_HOLD_MS = 600
NOTICE_MS = 2000

HELP_TEXT = "Klik garis putus-putus untuk membangun jembatan. Hubungkan semua pulau tanpa melebihi anggaran."


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Isle Weaver")
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        self.fonts = renderer.make_fonts()
        self.mouse = (0, 0)
        self.start_level(0)

    def start_level(self, index):
        self.level = generate_level(index, MAP_RECT.width, MAP_RECT.height)
        self.state = "PLAYING"
        self.mst_order = []
        self.result = None
        self.notice = None
        self.hover = None

    @property
    def spent(self):
        return sum(e.weight for e in self.level.edges if e.selected)

    def connected(self):
        return bfs_connected([e for e in self.level.edges if e.selected], len(self.level.islands))

    def toggle(self, edge):
        if edge.selected:
            edge.selected = False
        elif self.spent + edge.weight > self.level.budget:
            self.notice = ("Anggaran tidak cukup untuk jembatan ini!", pygame.time.get_ticks() + NOTICE_MS)
        else:
            edge.selected = True

    def submit(self):
        if not self.connected():
            return
        self.mst_order = kruskal_mst(self.level.edges, len(self.level.islands))
        self.anim_start = pygame.time.get_ticks()
        self.hover = None
        self.state = "ANIMATING"

    def revealed(self, now):
        k = min(len(self.mst_order), (now - self.anim_start) // REVEAL_MS + 1)
        return self.mst_order[:k]

    def finish(self):
        optimal = sum(e.weight for e in self.mst_order)
        efficiency = efficiency_percent(self.spent, optimal)
        self.result = {
            "level": self.level.index,
            "spent": self.spent,
            "optimal": optimal,
            "efficiency": efficiency,
            "stars": stars_for_efficiency(efficiency),
        }
        self.state = "RESULT"

    def on_click(self, pos):
        if self.state != "PLAYING":
            return
        if SUBMIT_BUTTON.collidepoint(pos):
            self.submit()
        elif RESET_BUTTON.collidepoint(pos):
            self.start_level(self.level.index)
        elif MAP_RECT.collidepoint(pos):
            edge = renderer.edge_at(self.level.islands, self.level.edges, MAP_RECT.topleft, pos)
            if edge:
                self.toggle(edge)

    def on_key(self, key):
        if key == pygame.K_ESCAPE:
            self.quit()
        elif key == pygame.K_r:
            self.start_level(0 if self.state == "COMPLETE" else self.level.index)
        elif key == pygame.K_SPACE and self.state == "RESULT":
            if self.level.index + 1 < len(LEVELS):
                self.start_level(self.level.index + 1)
            else:
                self.state = "COMPLETE"

    def update(self):
        now = pygame.time.get_ticks()
        if self.state == "PLAYING":
            inside = MAP_RECT.collidepoint(self.mouse)
            self.hover = renderer.edge_at(self.level.islands, self.level.edges, MAP_RECT.topleft, self.mouse) if inside else None
        elif self.state == "ANIMATING":
            if now - self.anim_start >= len(self.mst_order) * REVEAL_MS + REVEAL_HOLD_MS:
                self.finish()

    def caption(self, now):
        if self.notice and now < self.notice[1]:
            return self.notice[0]
        if self.state == "ANIMATING":
            return "Kruskal mengurutkan jembatan dari yang termurah dan melewati yang membentuk siklus..."
        if self.state in ("RESULT", "COMPLETE"):
            return "Garis hijau adalah jaringan termurah (Minimum Spanning Tree)."
        return HELP_TEXT

    def draw(self):
        now = pygame.time.get_ticks()
        screen = self.screen
        fonts = self.fonts
        screen.fill(colors.BACKGROUND)
        renderer.draw_background(screen, MAP_RECT)

        if self.state == "ANIMATING":
            mst = set(self.revealed(now))
        elif self.state in ("RESULT", "COMPLETE"):
            mst = set(self.mst_order)
        else:
            mst = set()

        renderer.draw_edges(screen, self.level.islands, self.level.edges, fonts["small"], MAP_RECT.topleft, mst, self.hover)
        renderer.draw_islands(screen, self.level.islands, fonts["bold"], MAP_RECT.topleft)
        renderer.draw_hud(screen, fonts, HUD_RECT, self.level, self.spent)

        connected = self.connected()
        playing = self.state == "PLAYING"
        renderer.draw_banner(screen, fonts["small"], BANNER_RECT, connected)
        renderer.draw_button(screen, fonts["small"], RESET_BUTTON, "Ulangi", primary=False, enabled=playing)
        renderer.draw_button(screen, fonts["small"], SUBMIT_BUTTON, "Submit", enabled=playing and connected)
        renderer.draw_text(screen, fonts["small"], self.caption(now), CAPTION_POS, colors.MUTED)

        if self.state == "RESULT":
            renderer.draw_result(screen, fonts, self.result)
        elif self.state == "COMPLETE":
            renderer.draw_complete(screen, fonts)

        pygame.display.flip()

    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.MOUSEMOTION:
                    self.mouse = event.pos
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.on_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.on_key(event.key)
            self.update()
            self.draw()


if __name__ == "__main__":
    Game().run()
