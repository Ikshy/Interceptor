import pygame
import math
import time
from typing import Optional


# ── palette ────────────────────────────────────────────────────────────────────
HUD_BG         = (0, 8, 0)
HUD_BORDER     = (0, 160, 50)
HUD_DIM        = (0,  80, 25)
HUD_GREEN      = (0, 230, 80)
HUD_BRIGHT     = (0, 255, 100)
HUD_AMBER      = (255, 180, 0)
HUD_RED        = (255, 50,  50)
HUD_WHITE      = (200, 240, 200)
TITLE_COLOR    = (0, 255, 110)


class UIOverlay:
    

    def __init__(self, surface: pygame.Surface, window_size: tuple[int, int]):
        self.surface     = surface
        self.win_w, self.win_h = window_size
        self._boot_time  = time.time()
        self._blink      = True
        self._blink_t    = 0.0

        # fonts — monospace for that radar-room feel
        pygame.font.init()
        self._font_title = pygame.font.SysFont("Courier New", 22, bold=True)
        self._font_large = pygame.font.SysFont("Courier New", 18, bold=True)
        self._font_med   = pygame.font.SysFont("Courier New", 14)
        self._font_small = pygame.font.SysFont("Courier New", 11)

    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        self._blink_t += dt
        self._blink = (self._blink_t % 1.0) < 0.5

    # ------------------------------------------------------------------
    def draw(
        self,
        distance: float,
        interceptor_speed: float,
        target_speed: float,
        eta: float,
        sim_status: str,
        intercept_count: int,
        elapsed: float,
        intercept_hit: bool,
        interceptor_pos: tuple[float, float],
        target_pos: tuple[float, float],
        target_behavior: str,
    ) -> None:
        self._draw_background()
        self._draw_title_bar(elapsed, sim_status)
        self._draw_left_panel(
            distance, interceptor_speed, target_speed,
            eta, interceptor_pos, target_pos
        )
        self._draw_right_panel(intercept_count, sim_status, target_behavior, intercept_hit)
        self._draw_bottom_bar(sim_status, intercept_hit)
        self._draw_decorative_corners()

    # ------------------------------------------------------------------
    # Private drawing helpers
    # ------------------------------------------------------------------

    def _draw_background(self) -> None:
        self.surface.fill((2, 6, 2))

    # ------------------------------------------------------------------
    def _draw_title_bar(self, elapsed: float, status: str) -> None:
        bar_h = 50
        pygame.draw.rect(self.surface, HUD_BG, (0, 0, self.win_w, bar_h))
        pygame.draw.line(self.surface, HUD_BORDER, (0, bar_h-1), (self.win_w, bar_h-1), 2)

        # title
        title = "◈  INTERCEPTOR  /  RADAR CONTROL  ◈"
        t = self._font_title.render(title, True, TITLE_COLOR)
        self.surface.blit(t, (self.win_w//2 - t.get_width()//2, 12))

        # elapsed clock
        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        clock_str = f"T+{mins:02d}:{secs:02d}"
        ct = self._font_large.render(clock_str, True, HUD_GREEN)
        self.surface.blit(ct, (self.win_w - ct.get_width() - 20, 14))

        # blinking live indicator
        if self._blink:
            live = self._font_med.render("● LIVE", True, HUD_RED)
            self.surface.blit(live, (18, 17))

    # ------------------------------------------------------------------
    def _draw_left_panel(
        self,
        distance: float,
        int_speed: float,
        tgt_speed: float,
        eta: float,
        int_pos: tuple,
        tgt_pos: tuple,
    ) -> None:
        x0, y0 = 10, 60
        panel_w = 200
        panel_h = self.win_h - 110

        pygame.draw.rect(self.surface, HUD_BG,    (x0, y0, panel_w, panel_h))
        pygame.draw.rect(self.surface, HUD_BORDER,(x0, y0, panel_w, panel_h), 1)

        y = y0 + 10
        lh = 22

        def row(label: str, value: str, color=HUD_GREEN):
            nonlocal y
            lbl = self._font_small.render(label, True, HUD_DIM)
            val = self._font_large.render(value,  True, color)
            self.surface.blit(lbl, (x0+8, y))
            self.surface.blit(val, (x0+8, y+12))
            y += lh + 8

        def divider():
            nonlocal y
            pygame.draw.line(self.surface, HUD_DIM,
                             (x0+8, y), (x0+panel_w-8, y), 1)
            y += 8

        hdr = self._font_med.render("[ TELEMETRY ]", True, HUD_BRIGHT)
        self.surface.blit(hdr, (x0 + panel_w//2 - hdr.get_width()//2, y))
        y += lh + 4
        divider()

        row("DISTANCE", f"{distance:>7.1f} u")
        divider()

        row("INTERCEPTOR SPD", f"{int_speed:>6.1f} u/s", HUD_BRIGHT)
        row("TARGET SPD",      f"{tgt_speed:>6.1f} u/s", HUD_AMBER)
        divider()

        if eta > 0:
            eta_color = HUD_RED if eta < 3 else HUD_GREEN
            row("ETA TO INTERCEPT", f"{eta:>6.1f} s", eta_color)
        else:
            row("ETA TO INTERCEPT", "    N/A", HUD_DIM)
        divider()

        row("INT POSITION",
            f"({int_pos[0]:>5.0f},{int_pos[1]:>5.0f})", HUD_GREEN)
        row("TGT POSITION",
            f"({tgt_pos[0]:>5.0f},{tgt_pos[1]:>5.0f})", HUD_AMBER)

    # ------------------------------------------------------------------
    def _draw_right_panel(
        self,
        intercept_count: int,
        sim_status: str,
        target_behavior: str,
        intercept_hit: bool,
    ) -> None:
        panel_w = 200
        x0 = self.win_w - panel_w - 10
        y0 = 60
        panel_h = self.win_h - 110

        pygame.draw.rect(self.surface, HUD_BG,    (x0, y0, panel_w, panel_h))
        pygame.draw.rect(self.surface, HUD_BORDER,(x0, y0, panel_w, panel_h), 1)

        y = y0 + 10
        lh = 22
        cx = x0 + panel_w // 2

        hdr = self._font_med.render("[ MISSION STATUS ]", True, HUD_BRIGHT)
        self.surface.blit(hdr, (cx - hdr.get_width()//2, y))
        y += lh + 4
        pygame.draw.line(self.surface, HUD_DIM, (x0+8, y), (x0+panel_w-8, y), 1)
        y += 8

        # intercept count big
        ic_lbl = self._font_small.render("INTERCEPTS", True, HUD_DIM)
        self.surface.blit(ic_lbl, (cx - ic_lbl.get_width()//2, y))
        y += 14
        big_font = pygame.font.SysFont("Courier New", 40, bold=True)
        ic_val = big_font.render(str(intercept_count), True, HUD_BRIGHT)
        self.surface.blit(ic_val, (cx - ic_val.get_width()//2, y))
        y += 50

        pygame.draw.line(self.surface, HUD_DIM, (x0+8, y), (x0+panel_w-8, y), 1)
        y += 10

        # pursit status
        status_map = {
            "SEARCHING": HUD_AMBER,
            "PURSUIT":   HUD_GREEN,
            "CLOSING":   HUD_BRIGHT,
            "INTERCEPT": HUD_RED,
        }
        sc = status_map.get(sim_status, HUD_GREEN)
        sl = self._font_small.render("INT STATUS", True, HUD_DIM)
        self.surface.blit(sl, (cx - sl.get_width()//2, y));  y += 14
        sv = self._font_large.render(sim_status, True, sc)
        self.surface.blit(sv, (cx - sv.get_width()//2, y));  y += lh + 8

        pygame.draw.line(self.surface, HUD_DIM, (x0+8, y), (x0+panel_w-8, y), 1)
        y += 10

        tl = self._font_small.render("TGT BEHAVIOR", True, HUD_DIM)
        self.surface.blit(tl, (cx - tl.get_width()//2, y));  y += 14
        tb_color = HUD_RED if target_behavior == "EVASIVE" else HUD_AMBER
        tv = self._font_large.render(target_behavior, True, tb_color)
        self.surface.blit(tv, (cx - tv.get_width()//2, y));  y += lh + 8

        pygame.draw.line(self.surface, HUD_DIM, (x0+8, y), (x0+panel_w-8, y), 1)
        y += 10

        # intercept flash
        if intercept_hit and self._blink:
            flash = self._font_large.render("★ TARGET HIT ★", True, HUD_RED)
            self.surface.blit(flash, (cx - flash.get_width()//2, y))

    # ------------------------------------------------------------------
    def _draw_bottom_bar(self, sim_status: str, intercept_hit: bool) -> None:
        bar_h = 40
        y0    = self.win_h - bar_h
        pygame.draw.rect(self.surface, HUD_BG, (0, y0, self.win_w, bar_h))
        pygame.draw.line(self.surface, HUD_BORDER, (0, y0), (self.win_w, y0), 2)

        controls = "  [R] RESET    [SPACE] PAUSE    [ESC] QUIT  "
        ct = self._font_small.render(controls, True, HUD_DIM)
        self.surface.blit(ct, (self.win_w//2 - ct.get_width()//2, y0 + 13))

    # ------------------------------------------------------------------
    def _draw_decorative_corners(self) -> None:
        """L-shaped corner brackets for HUD chrome."""
        corners = [
            (0,           0,          1,  1),
            (self.win_w,  0,         -1,  1),
            (0,           self.win_h,  1, -1),
            (self.win_w,  self.win_h, -1, -1),
        ]
        sz = 20
        for (cx, cy, dx, dy) in corners:
            pygame.draw.line(self.surface, HUD_BRIGHT,
                             (cx, cy), (cx + dx*sz, cy), 2)
            pygame.draw.line(self.surface, HUD_BRIGHT,
                             (cx, cy), (cx, cy + dy*sz), 2)