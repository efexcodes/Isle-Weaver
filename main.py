import random
import sys

import pygame

from core.algorithms import connected_groups, kruskal_steps, suggest_bridge
from game.level_generator import LEVELS, generate_level
from game.progress import is_unlocked, load_progress, save_progress
from game.scoring import efficiency_percent, stars_for_efficiency
from ui import layout
from ui.renderer import Renderer, edge_at

VERSION = "1.2"

STORM_INTERVAL = 4000
STORM_CHANCE = 0.3
STORM_RATE = 1.6
HINTS_PER_LEVEL = 3
HINT_GLOW_MS = 2600
NOTICE_MS = 2400
POPUP_MS = 900
STEP_MS_MAX = 320
STEP_MS_MIN = 110
REVEAL_BUDGET_MS = 6000
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
        self.progress = load_progress()
        self.state = "MENU"
        self.level = None
        self.mouse = (0, 0)
        self.hover = None
        self.hand_cursor = False

    def start_level(self, index):
        self.level = generate_level(index, layout.MAP_RECT.width, layout.MAP_RECT.height)
        self.view.load_islands(self.level.islands)
        self.time_left = self.level.time_limit
        self.hints_left = HINTS_PER_LEVEL
        self.hints_used = 0
        self.hint = None
        self.hint_until = 0
        self.steps = []
        self.mst = set()
        self.result = None
        self.popups = []
        self.notice = None
        self.show_card = True
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
        if edge is self.hint:
            self.hint = None

    def roll_storms(self):
        for e in self.level.edges:
            if not e.selected:
                e.storm = random.random() < STORM_CHANCE

    def use_hint(self):
        if self.hints_left == 0:
            self.say("Jatah saran untuk level ini sudah habis.")
            return
        edge = suggest_bridge(self.level.edges, len(self.level.islands), lambda e: e.current_cost(STORM_RATE))
        if edge is None:
            self.say("Semua pulau sudah terhubung, tinggal tekan Selesai.")
            return
        self.hints_left -= 1
        self.hints_used += 1
        self.hint = edge
        self.hint_until = pygame.time.get_ticks() + HINT_GLOW_MS
        self.say(f"Coba jembatan {edge.a + 1}-{edge.b + 1}: termurah yang menyambung dua kelompok berbeda.")

    def submit(self):
        if self.groups > 1:
            self.say("Masih ada pulau yang belum terhubung.")
            return
        self.steps = kruskal_steps(self.level.edges, len(self.level.islands))
        self.step_ms = max(STEP_MS_MIN, min(STEP_MS_MAX, REVEAL_BUDGET_MS // max(1, len(self.steps))))
        self.anim_start = pygame.time.get_ticks()
        self.hint = None
        self.hover = None
        self.notice = None
        self.state = "ANIMATING"

    def step_cursor(self, now):
        return min(len(self.steps), (now - self.anim_start) // self.step_ms)

    def skip_animation(self):
        self.anim_start = pygame.time.get_ticks() - len(self.steps) * self.step_ms - REVEAL_HOLD_MS

    def finish(self):
        self.mst = {e for e, joined in self.steps if joined}
        optimal = sum(e.weight for e in self.mst)
        spent = self.spent
        efficiency = efficiency_percent(spent, optimal)
        stars = stars_for_efficiency(efficiency)
        chosen = [e for e in self.level.edges if e.selected]
        self.result = {
            "level": self.level.index,
            "name": self.level.name,
            "spent": spent,
            "optimal": optimal,
            "efficiency": efficiency,
            "stars": stars,
            "matched": sum(1 for e in chosen if e in self.mst),
            "needed": len(self.level.islands) - 1,
            "hints": self.hints_used,
        }
        if stars > self.progress.get(self.level.index, 0):
            self.progress[self.level.index] = stars
            save_progress(self.progress)
        self.show_card = True
        self.state = "RESULT"

    def next_level(self):
        if self.level.index + 1 < len(LEVELS):
            self.start_level(self.level.index + 1)
        else:
            self.state = "COMPLETE"

    def menu_info(self):
        return [
            {
                "name": cfg["name"],
                "islands": cfg["islands"],
                "storms": cfg["storms"],
                "time_limit": cfg["time_limit"],
                "stars": self.progress.get(i, 0),
                "unlocked": is_unlocked(self.progress, i),
            }
            for i, cfg in enumerate(LEVELS)
        ]

    def latest_unlocked(self):
        return max(i for i in range(len(LEVELS)) if is_unlocked(self.progress, i))

    def on_click(self, pos):
        if self.state == "MENU":
            for i, rect in enumerate(layout.menu_cards(len(LEVELS))):
                if rect.collidepoint(pos) and is_unlocked(self.progress, i):
                    self.start_level(i)
            return

        if self.state == "PLAYING":
            if layout.SUBMIT_BUTTON.collidepoint(pos):
                self.submit()
            elif layout.RESET_BUTTON.collidepoint(pos):
                self.start_level(self.level.index)
            elif layout.HINT_BUTTON.collidepoint(pos):
                self.use_hint()
            elif layout.MAP_RECT.collidepoint(pos):
                edge = edge_at(self.level.islands, self.level.edges, layout.MAP_RECT.topleft, pos)
                if edge:
                    self.toggle(edge)
        elif self.state == "ANIMATING":
            self.skip_animation()
        elif self.state == "RESULT":
            if not self.show_card:
                self.show_card = True
            elif layout.CARD_LEFT_BUTTON.collidepoint(pos):
                self.start_level(self.level.index)
            elif layout.CARD_RIGHT_BUTTON.collidepoint(pos):
                self.next_level()
        elif self.state == "TIME_UP":
            if layout.SMALL_LEFT_BUTTON.collidepoint(pos):
                self.start_level(self.level.index)
            elif layout.SMALL_RIGHT_BUTTON.collidepoint(pos):
                self.state = "MENU"
        elif self.state == "COMPLETE":
            if layout.SMALL_WIDE_BUTTON.collidepoint(pos):
                self.state = "MENU"

    def on_key(self, key):
        confirm = key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
        if self.state == "MENU":
            if key == pygame.K_ESCAPE:
                self.quit()
            elif confirm:
                self.start_level(self.latest_unlocked())
            elif pygame.K_1 <= key < pygame.K_1 + len(LEVELS):
                index = key - pygame.K_1
                if is_unlocked(self.progress, index):
                    self.start_level(index)
            return

        if key == pygame.K_ESCAPE:
            self.state = "MENU"
        elif self.state == "PLAYING":
            if key == pygame.K_r:
                self.start_level(self.level.index)
            elif key == pygame.K_h:
                self.use_hint()
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.submit()
        elif self.state == "ANIMATING":
            if confirm:
                self.skip_animation()
        elif self.state == "RESULT":
            if key == pygame.K_v:
                self.show_card = not self.show_card
            elif key == pygame.K_r:
                self.start_level(self.level.index)
            elif confirm:
                self.next_level()
        elif self.state == "TIME_UP":
            if key == pygame.K_r or confirm:
                self.start_level(self.level.index)
        elif self.state == "COMPLETE":
            if confirm:
                self.state = "MENU"

    def update(self, dt):
        now = pygame.time.get_ticks()
        if self.state == "PLAYING":
            if self.level.storms and now >= self.next_storm:
                self.next_storm = now + STORM_INTERVAL
                self.roll_storms()
            if self.time_left is not None:
                self.time_left -= dt / 1000
                if self.time_left <= 0:
                    self.time_left = 0
                    self.state = "TIME_UP"
            if self.hint and now > self.hint_until:
                self.hint = None
            if layout.MAP_RECT.collidepoint(self.mouse):
                self.hover = edge_at(self.level.islands, self.level.edges, layout.MAP_RECT.topleft, self.mouse)
            else:
                self.hover = None
        elif self.state == "ANIMATING":
            if now - self.anim_start >= len(self.steps) * self.step_ms + REVEAL_HOLD_MS:
                self.finish()

        if self.level:
            self.popups = [p for p in self.popups if now - p["born"] < POPUP_MS]
        self.update_cursor()

    def update_cursor(self):
        if self.state == "MENU":
            cards = layout.menu_cards(len(LEVELS))
            hand = any(r.collidepoint(self.mouse) and is_unlocked(self.progress, i) for i, r in enumerate(cards))
        elif self.state == "PLAYING":
            buttons = (layout.SUBMIT_BUTTON, layout.RESET_BUTTON, layout.HINT_BUTTON)
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
            k = self.step_cursor(now)
            if k >= len(self.steps):
                return f"Kruskal selesai. Biaya minimum jaringan ini {sum(e.weight for e, ok in self.steps if ok)}."
            e, ok = self.steps[k]
            verdict = "diambil" if ok else "dilewati karena akan membentuk siklus"
            return f"Langkah {k + 1}/{len(self.steps)}: jembatan {e.a + 1}-{e.b + 1} (biaya {e.weight}) {verdict}.   Spasi untuk lewati."
        if self.state == "RESULT":
            if not self.show_card:
                return "Hijau = jaringan optimal. Jembatan bersinar merah tidak termasuk solusi Kruskal. Tekan V untuk kembali."
            return "Garis hijau adalah Minimum Spanning Tree hasil algoritma Kruskal."
        return HELP_STORM if self.level.storms else HELP_CALM

    def draw(self):
        now = pygame.time.get_ticks()
        t = now / 1000
        screen = self.screen

        if self.state == "MENU":
            self.view.draw_menu(screen, t, self.menu_info(), self.mouse, VERSION)
            pygame.display.flip()
            return

        playing = self.state == "PLAYING"
        mst, current, compare = None, None, False
        if self.state == "ANIMATING":
            k = self.step_cursor(now)
            mst = {e for e, ok in self.steps[:k] if ok}
            current = self.steps[k] if k < len(self.steps) else None
        elif self.state in ("RESULT", "COMPLETE"):
            mst, compare = self.mst, True

        view = self.view
        view.clear(screen)
        view.draw_map(screen, self.level, t, hover=self.hover, hint=self.hint, mst=mst, current=current, compare=compare, storm_rate=STORM_RATE)
        view.draw_hud(screen, self.level, self.spent, self.time_left, t)

        groups = self.groups
        if self.state == "ANIMATING":
            view.draw_status(screen, "Kruskal sedang menyusun jaringan termurah...", True)
        elif groups <= 1:
            view.draw_status(screen, "Semua pulau sudah terhubung", True)
        else:
            view.draw_status(screen, f"Masih ada {groups} kelompok pulau yang terpisah", False)

        view.draw_button(screen, layout.HINT_BUTTON, f"Saran ({self.hints_left})", self.mouse, enabled=playing and self.hints_left > 0)
        view.draw_button(screen, layout.RESET_BUTTON, "Ulangi", self.mouse, enabled=playing)
        view.draw_button(screen, layout.SUBMIT_BUTTON, "Selesai", self.mouse, primary=True, enabled=playing and groups <= 1)
        view.draw_caption(screen, self.caption(now))
        view.draw_popups(screen, self.popups, now)

        if self.state == "RESULT" and self.show_card:
            view.draw_result(screen, self.result, self.mouse, self.level.index == len(LEVELS) - 1)
        elif self.state == "TIME_UP":
            view.draw_time_up(screen, self.mouse)
        elif self.state == "COMPLETE":
            view.draw_complete(screen, sum(self.progress.values()), 3 * len(LEVELS), self.mouse)

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
