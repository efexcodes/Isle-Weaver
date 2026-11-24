import random
import sys

import pygame

from core.algorithms import connected_groups, kruskal_mst
from game.level_generator import LEVELS, generate_level
from game.scoring import efficiency_percent, stars_for_efficiency
from ui import layout
from ui.renderer import Renderer, edge_at

VERSION = "1.1"

STORM_INTERVAL = 4000
STORM_CHANCE = 0.3
STORM_RATE = 1.6
NOTICE_MS = 2400
POPUP_MS = 900
REVEAL_MS = 280
REVEAL_HOLD_MS = 700

HELP_CALM = "Klik garis putus-putus untuk membangun jembatan, klik jembatan untuk membongkarnya."
HELP_STORM = "Jembatan berawan sedang kena badai, harganya naik 60%. Tunggu reda atau cari jalur lain."


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Isle Weaver")
        self.screen = pygame.display.set_mode(layout.SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        self.view = Renderer()
        self.state = "MENU"
        self.level = None
        self.mouse = (0, 0)
        self.hover = None
        self.hand_cursor = False

    def start_level(self, index):
        self.level = generate_level(index, layout.MAP_RECT.width, layout.MAP_RECT.height)
        self.view.load_islands(self.level.islands)
        self.mst_order = []
        self.result = None
        self.popups = []
        self.notice = None
        self.hover = None
        self.state = "PLAYING"
        self.next_storm = pygame.time.get_ticks() + STORM_INTERVAL
        if self.level.storms:
            self.roll_storms()

    @property
    def spent(self):
        return sum(e.locked_cost for e in self.level.edges if e.selected)

    @property
    def groups(self):
        return connected_groups([e for e in self.level.edges if e.selected], len(self.level.islands))

    def say(self, text):
        self.notice = (text, pygame.time.get_ticks() + NOTICE_MS)

    def popup(self, edge, text, kind):
        ox, oy = layout.MAP_RECT.topleft
        p, q = self.level.islands[edge.a], self.level.islands[edge.b]
        self.popups.append({
            "x": ox + (p.x + q.x) / 2,
            "y": oy + (p.y + q.y) / 2 - 14,
            "text": text,
            "kind": kind,
            "born": pygame.time.get_ticks(),
        })

    def toggle(self, edge):
        if edge.selected:
            self.popup(edge, f"+{edge.locked_cost}", "refund")
            edge.selected = False
            edge.locked_cost = 0
            return
        cost = edge.current_cost(STORM_RATE)
        if self.spent + cost > self.level.budget:
            self.say(f"Anggaran tidak cukup. Jembatan ini butuh {cost}, sisa {self.level.budget - self.spent}.")
            return
        edge.selected = True
        edge.locked_cost = cost
        self.popup(edge, f"-{cost}", "spend")

    def roll_storms(self):
        for e in self.level.edges:
            if not e.selected:
                e.storm = random.random() < STORM_CHANCE

    def submit(self):
        if self.groups > 1:
            self.say("Masih ada pulau yang belum terhubung.")
            return
        self.mst_order = kruskal_mst(self.level.edges, len(self.level.islands))
        self.anim_start = pygame.time.get_ticks()
        self.hover = None
        self.notice = None
        self.state = "ANIMATING"

    def revealed(self, now):
        k = min(len(self.mst_order), (now - self.anim_start) // REVEAL_MS + 1)
        return self.mst_order[:k]

    def finish(self):
        optimal = sum(e.weight for e in self.mst_order)
        spent = self.spent
        efficiency = efficiency_percent(spent, optimal)
        self.result = {
            "level": self.level.index,
            "name": self.level.name,
            "spent": spent,
            "optimal": optimal,
            "efficiency": efficiency,
            "stars": stars_for_efficiency(efficiency),
        }
        self.state = "RESULT"

    def next_level(self):
        if self.level.index + 1 < len(LEVELS):
            self.start_level(self.level.index + 1)
        else:
            self.state = "COMPLETE"

    def on_click(self, pos):
        if self.state == "MENU":
            if layout.START_BUTTON.collidepoint(pos):
                self.start_level(0)
        elif self.state == "PLAYING":
            if layout.SUBMIT_BUTTON.collidepoint(pos):
                self.submit()
            elif layout.RESET_BUTTON.collidepoint(pos):
                self.start_level(self.level.index)
            elif layout.MAP_RECT.collidepoint(pos):
                edge = edge_at(self.level.islands, self.level.edges, layout.MAP_RECT.topleft, pos)
                if edge:
                    self.toggle(edge)
        elif self.state == "RESULT":
            if layout.CARD_LEFT_BUTTON.collidepoint(pos):
                self.start_level(self.level.index)
            elif layout.CARD_RIGHT_BUTTON.collidepoint(pos):
                self.next_level()
        elif self.state == "COMPLETE":
            if layout.SMALL_WIDE_BUTTON.collidepoint(pos):
                self.state = "MENU"

    def on_key(self, key):
        confirm = key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
        if self.state == "MENU":
            if key == pygame.K_ESCAPE:
                self.quit()
            elif confirm:
                self.start_level(0)
            return

        if key == pygame.K_ESCAPE:
            self.state = "MENU"
        elif self.state == "PLAYING":
            if key == pygame.K_r:
                self.start_level(self.level.index)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.submit()
        elif self.state == "RESULT":
            if key == pygame.K_r:
                self.start_level(self.level.index)
            elif confirm:
                self.next_level()
        elif self.state == "COMPLETE":
            if confirm:
                self.state = "MENU"

    def update(self, dt):
        now = pygame.time.get_ticks()
        if self.state == "PLAYING":
            if self.level.storms and now >= self.next_storm:
                self.next_storm = now + STORM_INTERVAL
                self.roll_storms()
            if layout.MAP_RECT.collidepoint(self.mouse):
                self.hover = edge_at(self.level.islands, self.level.edges, layout.MAP_RECT.topleft, self.mouse)
            else:
                self.hover = None
        elif self.state == "ANIMATING":
            if now - self.anim_start >= len(self.mst_order) * REVEAL_MS + REVEAL_HOLD_MS:
                self.finish()

        if self.level:
            self.popups = [p for p in self.popups if now - p["born"] < POPUP_MS]
        self.update_cursor()

    def update_cursor(self):
        if self.state == "MENU":
            hand = layout.START_BUTTON.collidepoint(self.mouse)
        elif self.state == "PLAYING":
            buttons = (layout.SUBMIT_BUTTON, layout.RESET_BUTTON)
            hand = self.hover is not None or any(b.collidepoint(self.mouse) for b in buttons)
        else:
            hand = False
        if hand != self.hand_cursor:
            self.hand_cursor = hand
            try:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if hand else pygame.SYSTEM_CURSOR_ARROW)
            except pygame.error:
                pass

    def caption(self, now):
        if self.notice and now < self.notice[1]:
            return self.notice[0]
        if self.state == "ANIMATING":
            return "Kruskal mengurutkan jembatan dari yang termurah dan melewati yang membentuk siklus..."
        if self.state in ("RESULT", "COMPLETE"):
            return "Garis hijau adalah Minimum Spanning Tree hasil algoritma Kruskal."
        return HELP_STORM if self.level.storms else HELP_CALM

    def draw(self):
        now = pygame.time.get_ticks()
        t = now / 1000
        screen = self.screen

        if self.state == "MENU":
            self.view.draw_menu(screen, t, self.mouse, VERSION)
            pygame.display.flip()
            return

        playing = self.state == "PLAYING"
        mst = None
        if self.state == "ANIMATING":
            mst = set(self.revealed(now))
        elif self.state in ("RESULT", "COMPLETE"):
            mst = set(self.mst_order)

        view = self.view
        view.clear(screen)
        view.draw_map(screen, self.level, t, hover=self.hover, mst=mst, storm_rate=STORM_RATE)
        view.draw_hud(screen, self.level, self.spent)

        groups = self.groups
        if self.state == "ANIMATING":
            view.draw_status(screen, "Kruskal sedang menyusun jaringan termurah...", True)
        elif groups <= 1:
            view.draw_status(screen, "Semua pulau sudah terhubung", True)
        else:
            view.draw_status(screen, f"Masih ada {groups} kelompok pulau yang terpisah", False)

        view.draw_button(screen, layout.RESET_BUTTON, "Ulangi", self.mouse, enabled=playing)
        view.draw_button(screen, layout.SUBMIT_BUTTON, "Selesai", self.mouse, primary=True, enabled=playing and groups <= 1)
        view.draw_caption(screen, self.caption(now))
        view.draw_popups(screen, self.popups, now)

        if self.state == "RESULT":
            view.draw_result(screen, self.result, self.mouse, self.level.index == len(LEVELS) - 1)
        elif self.state == "COMPLETE":
            view.draw_complete(screen, self.mouse)

        pygame.display.flip()

    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            dt = self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.MOUSEMOTION:
                    self.mouse = event.pos
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.mouse = event.pos
                    self.on_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.on_key(event.key)
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    Game().run()
