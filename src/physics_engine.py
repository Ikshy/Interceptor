import numpy as np


class PhysicsBody:
    

    def __init__(self, x: float, y: float, vx: float = 0.0, vy: float = 0.0):
        self.position = np.array([x, y], dtype=float)
        self.velocity = np.array([vx, vy], dtype=float)
        self.heading = 0.0          # radians, 0 = right, CCW positive
        self.trail: list[np.ndarray] = []
        self.max_trail = 60         # number of trail points to keep

    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        """Integrate position forward by dt seconds."""
        self.position += self.velocity * dt
        if np.linalg.norm(self.velocity) > 1e-6:
            self.heading = np.arctan2(self.velocity[1], self.velocity[0])
        self.trail.append(self.position.copy())
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)

    # ------------------------------------------------------------------
    def speed(self) -> float:
        return float(np.linalg.norm(self.velocity))

    # ------------------------------------------------------------------
    def set_velocity_from_heading(self, speed: float, angle_rad: float) -> None:
        self.velocity = np.array([
            speed * np.cos(angle_rad),
            speed * np.sin(angle_rad),
        ], dtype=float)

    # ------------------------------------------------------------------
    def distance_to(self, other: "PhysicsBody") -> float:
        return float(np.linalg.norm(self.position - other.position))

    # ------------------------------------------------------------------
    def wrap(self, width: float, height: float) -> None:
     
        self.position[0] %= width
        self.position[1] %= height