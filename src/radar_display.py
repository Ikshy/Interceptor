import pygame
import numpy as np
import math
from typing import Optional



RADAR_BG       = (0,  10,  0)
GRID_COLOR     = (0,  60,  0)
GRID_BRIGHT    = (0,  90,  0)
SWEEP_COLOR    = (0, 255, 80)
SWEEP_TRAIL    = (0, 180, 40)
TARGET_COLOR   = (255, 60, 60)
INTERCEPT_COLOR= (255, 200,  0)
PREDICT_COLOR  = (255, 220,  0)
HIT_COLOR      = (255, 255, 255)
SCAN_LINE_CLR  = (0,  25,  0)

PHOSPHOR_GREEN = (0, 255, 70)
DIM_GREEN      = (0, 100, 30)


class RadarDisplay:
   

    SWEEP_SPEED = math.radians(90)   # degrees per second (full 360 in 4 s)
    BLIP_RADIUS = 6
    GLOW_LAYERS = 5

    # ------------------------------------------------------------------
    def __init__(
        self,
        surface: pygame.Surface,
        radar_rect: pygame.Rect,
        world_size: tuple[float, float],
    ):
        self.surface    = surface
        self.rect       = radar_rect
        self.world_w, self.world_h = world_size
        self.sweep_angle: float = 0.0
        self._sweep_surface = pygame.Surface(
            (radar_rect.width, radar_rect.height), pygame.SRCALPHA
        )
        self._base_surface  = pygame.Surface(
            (radar_rect.width, radar_rect.height)
        )
        self._build_base()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        self.sweep_angle = (self.sweep_angle + self.SWEEP_SPEED * dt) % (2 * math.pi)

    # ------------------------------------------------------------------
    def draw(
        self,
        interceptor_pos: np.ndarray,
        interceptor_trail: list[np.ndarray],
        target_pos: np.ndarray,
        target_trail: list[np.ndarray],
        predict_pos: Optional[np.ndarray],
        intercept_hit: bool,
    ) -> None:
        # 1. base grid
        self.surface.blit(self._base_surface, self.rect.topleft)

        # 2. sweep cone
        self._draw_sweep()

        # 3. trails
        self._draw_trail(interceptor_trail, PHOSPHOR_GREEN, alpha_max=160)
        self._draw_trail(target_trail, TARGET_COLOR, alpha_max=120)

        # 4. predicted intercept marker
        if predict_pos is not None:
            self._draw_predict_marker(predict_pos)

        # 5. trajectory line (interceptor → predict)
        if predict_pos is not None:
            ip = self._w2r(interceptor_pos)
            pp = self._w2r(predict_pos)
            pygame.draw.line(self.surface, (*PREDICT_COLOR[:3], 80),
                             ip, pp, 1)

        # 6. blips
        color = HIT_COLOR if intercept_hit else INTERCEPT_COLOR
        self._draw_blip(interceptor_pos, color, self.BLIP_RADIUS)
        self._draw_blip(target_pos, TARGET_COLOR, self.BLIP_RADIUS)

        # 7. scanline overlay
        self._draw_scanlines()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_base(self) -> None:
        """Pre-render static radar background onto _base_surface."""
        s = self._base_surface
        s.fill(RADAR_BG)

        cx = self.rect.width  // 2
        cy = self.rect.height // 2
        max_r = min(cx, cy)

        # concentric range rings
        for i in range(1, 6):
            r = int(max_r * i / 5)
            bright = GRID_BRIGHT if i % 2 == 0 else GRID_COLOR
            pygame.draw.circle(s, bright, (cx, cy), r, 1)

        # crosshairs
        pygame.draw.line(s, GRID_BRIGHT, (cx, 0), (cx, self.rect.height), 1)
        pygame.draw.line(s, GRID_BRIGHT, (0, cy), (self.rect.width, cy), 1)

        # cardinal tick marks
        for deg in range(0, 360, 10):
            rad = math.radians(deg)
            outer = max_r
            inner = max_r - (8 if deg % 30 == 0 else 4)
            x1 = int(cx + outer * math.cos(rad))
            y1 = int(cy + outer * math.sin(rad))
            x2 = int(cx + inner * math.cos(rad))
            y2 = int(cy + inner * math.sin(rad))
            pygame.draw.line(s, GRID_BRIGHT, (x1, y1), (x2, y2), 1)

        # outer border circle
        pygame.draw.circle(s, GRID_BRIGHT, (cx, cy), max_r, 2)

        # corner vignette (simple)
        vignette = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        for r in range(max_r, max_r + 30):
            alpha = min(255, (r - max_r) * 20)
            pygame.draw.circle(vignette, (0, 0, 0, alpha), (cx, cy), r, 2)
        s.blit(vignette, (0, 0))

    # ------------------------------------------------------------------
    def _draw_sweep(self) -> None:
        cx = self.rect.x + self.rect.width  // 2
        cy = self.rect.y + self.rect.height // 2
        max_r = min(self.rect.width, self.rect.height) // 2

        # sweep cone (fan of lines fading behind the leading edge)
        FAN_DEGREES = 35
        steps = 40
        for i in range(steps):
            frac  = i / steps
            angle = self.sweep_angle - math.radians(FAN_DEGREES * frac)
            alpha = int(200 * (1 - frac) * frac * 4)  # bell shape
            color = (0, int(220 * (1 - frac) + 40), int(60 * (1 - frac)))
            end_x = cx + int(max_r * math.cos(angle))
            end_y = cy + int(max_r * math.sin(angle))
            pygame.draw.line(self.surface, color, (cx, cy), (end_x, end_y), 2)

        # bright leading edge
        ex = cx + int(max_r * math.cos(self.sweep_angle))
        ey = cy + int(max_r * math.sin(self.sweep_angle))
        pygame.draw.line(self.surface, SWEEP_COLOR, (cx, cy), (ex, ey), 2)

    # ------------------------------------------------------------------
    def _draw_blip(
        self,
        world_pos: np.ndarray,
        color: tuple,
        radius: int,
    ) -> None:
        sx, sy = self._w2r(world_pos)
        # glow layers
        for g in range(self.GLOW_LAYERS, 0, -1):
            glow_r  = radius + g * 3
            alpha   = int(80 / g)
            glow_s  = pygame.Surface((glow_r*2+2, glow_r*2+2), pygame.SRCALPHA)
            gc      = (*color[:3], alpha)
            pygame.draw.circle(glow_s, gc, (glow_r+1, glow_r+1), glow_r)
            self.surface.blit(glow_s, (sx - glow_r - 1, sy - glow_r - 1))
        # solid core
        pygame.draw.circle(self.surface, color, (sx, sy), radius)
        pygame.draw.circle(self.surface, (255, 255, 255), (sx, sy), max(1, radius//3))

    # ------------------------------------------------------------------
    def _draw_trail(
        self,
        trail: list[np.ndarray],
        color: tuple,
        alpha_max: int = 180,
    ) -> None:
        if len(trail) < 2:
            return
        n = len(trail)
        for i in range(1, n):
            alpha = int(alpha_max * i / n)
            c     = (*color[:3], alpha)
            p1    = self._w2r(trail[i-1])
            p2    = self._w2r(trail[i])
            line_s = pygame.Surface(
                (abs(p2[0]-p1[0])+3, abs(p2[1]-p1[1])+3), pygame.SRCALPHA
            )
            pygame.draw.line(self.surface, c, p1, p2, 1)

    # ------------------------------------------------------------------
    def _draw_predict_marker(self, world_pos: np.ndarray) -> None:
        sx, sy = self._w2r(world_pos)
        r = 12
        # animated pulsing cross
        pygame.draw.line(self.surface, PREDICT_COLOR, (sx-r, sy), (sx+r, sy), 1)
        pygame.draw.line(self.surface, PREDICT_COLOR, (sx, sy-r), (sx, sy+r), 1)
        pygame.draw.circle(self.surface, (*PREDICT_COLOR, 100), (sx, sy), r, 1)
        # diamond corners
        d = 5
        for dx, dy in [(r, 0), (-r, 0), (0, r), (0, -r)]:
            pygame.draw.circle(self.surface, PREDICT_COLOR, (sx+dx, sy+dy), 2)

    # ------------------------------------------------------------------
    def _draw_scanlines(self) -> None:
        """Overlay subtle horizontal scanlines for CRT feel."""
        for y in range(self.rect.top, self.rect.bottom, 4):
            pygame.draw.line(
                self.surface, SCAN_LINE_CLR,
                (self.rect.left, y), (self.rect.right, y), 1
            )

    # ------------------------------------------------------------------
    def _w2r(self, world_pos: np.ndarray) -> tuple[int, int]:
        """Map world coordinates to radar surface screen coordinates."""
        rx = int(self.rect.x + (world_pos[0] / self.world_w) * self.rect.width)
        ry = int(self.rect.y + (world_pos[1] / self.world_h) * self.rect.height)
        return rx, ry