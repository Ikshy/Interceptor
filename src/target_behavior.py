
import numpy as np
import random
from physics_engine import PhysicsBody


class TargetDrone:
    

    BASE_SPEED       = 130.0   # px / s  (simulation units)
    EVASION_INTERVAL = (2.5, 6.0)   # seconds between maneuver decisions
    EVASION_TURN     = np.radians(45)   # max turn per maneuver
    TURN_RATE        = np.radians(120)  # rad/s during turn

    # ------------------------------------------------------------------
    def __init__(self, x: float, y: float, heading_deg: float = 30.0):
        angle = np.radians(heading_deg)
        self.body = PhysicsBody(
            x, y,
            self.BASE_SPEED * np.cos(angle),
            self.BASE_SPEED * np.sin(angle),
        )
        self._current_heading: float = angle
        self._target_heading:  float = angle
        self._time_to_maneuver: float = random.uniform(*self.EVASION_INTERVAL)
        self._evading: bool = False
        self.status: str = "STRAIGHT"

    # ------------------------------------------------------------------
    def update(self, dt: float, world_w: float, world_h: float) -> None:
        self._time_to_maneuver -= dt

        # --- decide next maneuver ---
        if self._time_to_maneuver <= 0:
            turn = random.uniform(-self.EVASION_TURN, self.EVASION_TURN)
            self._target_heading = self._current_heading + turn
            self._time_to_maneuver = random.uniform(*self.EVASION_INTERVAL)
            self._evading = True
            self.status = "EVASIVE"

        # --- smooth heading interpolation ---
        diff = self._target_heading - self._current_heading
        # normalise to [-pi, pi]
        diff = (diff + np.pi) % (2 * np.pi) - np.pi
        max_turn = self.TURN_RATE * dt
        if abs(diff) < max_turn:
            self._current_heading = self._target_heading
            if self._evading:
                self._evading = False
                self.status = "STRAIGHT"
        else:
            self._current_heading += np.sign(diff) * max_turn

        self.body.set_velocity_from_heading(self.BASE_SPEED, self._current_heading)
        self.body.update(dt)
        self.body.wrap(world_w, world_h)

    # ------------------------------------------------------------------
    @property
    def position(self) -> np.ndarray:
        return self.body.position

    @property
    def velocity(self) -> np.ndarray:
        return self.body.velocity