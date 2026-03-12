import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pygame
import numpy as np
import time

from physics_engine         import PhysicsBody
from target_behavior        import TargetDrone
from interceptor_navigation import InterceptorDrone
from prediction_engine      import PredictionEngine
from radar_display          import RadarDisplay
from ui_overlay             import UIOverlay


# ── window / world constants ───────────────────────────────────────────────────
WIN_W, WIN_H   = 960, 780
RADAR_MARGIN_X = 220          # left & right panel width
RADAR_TOP      = 55
RADAR_BOT      = 45
WORLD_W        = float(WIN_W - 2 * RADAR_MARGIN_X)
WORLD_H        = float(WIN_H - RADAR_TOP - RADAR_BOT)

RADAR_RECT = pygame.Rect(
    RADAR_MARGIN_X,
    RADAR_TOP,
    WIN_W - 2 * RADAR_MARGIN_X,
    WIN_H - RADAR_TOP - RADAR_BOT,
)

TARGET_FPS     = 60
INTERCEPT_DIST = 18.0          # px — counts as hit


# ── helpers ───────────────────────────────────────────────────────────────────

def spawn_target() -> TargetDrone:
    import random
    x = random.uniform(WORLD_W * 0.1, WORLD_W * 0.9)
    y = random.uniform(WORLD_H * 0.1, WORLD_H * 0.9)
    hdg = random.uniform(0, 360)
    return TargetDrone(x, y, hdg)


def spawn_interceptor() -> InterceptorDrone:
    return InterceptorDrone(WORLD_W / 2, WORLD_H / 2)


# ── main simulation loop ───────────────────────────────────────────────────────

def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("INTERCEPTOR — Radar Control")
    clock  = pygame.time.Clock()

    target      = spawn_target()
    interceptor = spawn_interceptor()
    predictor   = PredictionEngine()
    radar       = RadarDisplay(screen, RADAR_RECT, (WORLD_W, WORLD_H))
    hud         = UIOverlay(screen, (WIN_W, WIN_H))

    paused          = False
    intercept_count = 0
    sim_start       = time.time()
    intercept_hit   = False
    hit_timer       = 0.0

    while True:
        dt = clock.tick(TARGET_FPS) / 1000.0
        dt = min(dt, 0.05)   # cap to avoid spiral on slow machines

        # ── events ──────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_r:
                    target      = spawn_target()
                    interceptor = spawn_interceptor()
                    intercept_count = 0
                    sim_start   = time.time()
                    intercept_hit = False
                    hit_timer   = 0.0

        if paused:
            # still render, just freeze physics
            _render(screen, radar, hud, target, interceptor,
                    predictor, intercept_count, sim_start,
                    intercept_hit, dt, eta=0.0)
            continue

        # ── physics & AI ────────────────────────────────────────────────
        target.update(dt, WORLD_W, WORLD_H)

        predict_pos, eta = predictor.predict(
            interceptor.position,
            interceptor.body.speed(),
            target.position,
            target.velocity,
        )

        interceptor.update(dt, target.position, predict_pos,
                           WORLD_W, WORLD_H)

        # ── intercept detection ─────────────────────────────────────────
        dist = interceptor.body.distance_to(target.body)
        if dist < INTERCEPT_DIST:
            intercept_count += 1
            intercept_hit    = True
            hit_timer        = 1.2   # seconds to display flash
            # respawn target far from interceptor
            import random
            angle = random.uniform(0, 2 * np.pi)
            r     = min(WORLD_W, WORLD_H) * 0.35
            nx    = (interceptor.position[0] + r * np.cos(angle)) % WORLD_W
            ny    = (interceptor.position[1] + r * np.sin(angle)) % WORLD_H
            target = TargetDrone(nx, ny, random.uniform(0, 360))

        if hit_timer > 0:
            hit_timer -= dt
        else:
            intercept_hit = False

        # ── render ──────────────────────────────────────────────────────
        _render(screen, radar, hud, target, interceptor,
                predictor, intercept_count, sim_start,
                intercept_hit, dt, eta)

        pygame.display.flip()


def _render(
    screen, radar, hud, target, interceptor,
    predictor, intercept_count, sim_start,
    intercept_hit, dt, eta
):
    radar.update(dt)
    hud.update(dt)

    # prediction for display
    predict_pos, eta_val = predictor.predict(
        interceptor.position,
        interceptor.body.speed(),
        target.position,
        target.velocity,
    )
    if eta > 0:
        eta_val = eta

    dist = interceptor.body.distance_to(target.body)

    hud.draw(
        distance         = dist,
        interceptor_speed= interceptor.body.speed(),
        target_speed     = target.body.speed(),
        eta              = eta_val,
        sim_status       = interceptor.status,
        intercept_count  = intercept_count,
        elapsed          = time.time() - sim_start,
        intercept_hit    = intercept_hit,
        interceptor_pos  = tuple(interceptor.position),
        target_pos       = tuple(target.position),
        target_behavior  = target.status,
    )

    radar.draw(
        interceptor_pos  = interceptor.position,
        interceptor_trail= interceptor.body.trail,
        target_pos       = target.position,
        target_trail     = target.body.trail,
        predict_pos      = predict_pos,
        intercept_hit    = intercept_hit,
    )


if __name__ == "__main__":
    main()