# interceptor_navigation.py
# Pure-pursuit / proportional navigation algorithm for the interceptor drone.

import numpy as np
from physics_engine import PhysicsBody


class InterceptorDrone:
    """
    Interceptor drone using Proportional Navigation (PN) guidance law.
    Steers toward a predicted intercept point.
    """

    MAX_SPEED    = 210.0          # px / s — faster than target
    TURN_RATE    = np.radians(180) # rad / s
    NAV_CONSTANT = 4.0            # PN gain (N')

    # ------------------------------------------------------------------
    def __init__(self, x: float, y: float):
        self.body = PhysicsBody(x, y, 0.0, -self.MAX_SPEED * 0.5)
        self._heading: float = -np.pi / 2  # initially pointing up
        self.status: str = "SEARCHING"
        self._prev_los_angle: float | None = None   # line-of-sight angle

    # ------------------------------------------------------------------
    def update(
        self,
        dt: float,
        target_pos: np.ndarray,
        intercept_pos: np.ndarray,
        world_w: float,
        world_h: float,
    ) -> None:
       
        aim = intercept_pos if intercept_pos is not None else target_pos

        # --- compute LOS angle ---
        delta = aim - self.body.position
        dist  = np.linalg.norm(delta)

        if dist < 1e-3:
            self.status = "INTERCEPT"
            return

        los_angle = np.arctan2(delta[1], delta[0])

        # --- Proportional Navigation ---
        if self._prev_los_angle is not None:
            los_rate = (los_angle - self._prev_los_angle + np.pi) % (2 * np.pi) - np.pi
            los_rate /= dt if dt > 1e-6 else 1e-6
            # commanded heading rate
            heading_rate = self.NAV_CONSTANT * los_rate
        else:
            heading_rate = 0.0

        self._prev_los_angle = los_angle

        # --- apply turn-rate limit ---
        max_turn = self.TURN_RATE * dt
        delta_h  = heading_rate * dt
        delta_h  = np.clip(delta_h, -max_turn, max_turn)

        # Blend PN with direct bearing for stability
        bearing_error = (los_angle - self._heading + np.pi) % (2 * np.pi) - np.pi
        direct_turn   = np.clip(bearing_error, -max_turn, max_turn)
        self._heading += 0.6 * direct_turn + 0.4 * delta_h

        self.body.set_velocity_from_heading(self.MAX_SPEED, self._heading)
        self.body.update(dt)
        self.body.wrap(world_w, world_h)

        # --- status ---
        if dist < 30:
            self.status = "INTERCEPT"
        elif dist < 200:
            self.status = "CLOSING"
        else:
            self.status = "PURSUIT"

    # ------------------------------------------------------------------
    @property
    def position(self) -> np.ndarray:
        return self.body.position

    @property
    def velocity(self) -> np.ndarray:
        return self.body.velocity