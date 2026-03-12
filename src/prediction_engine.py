import numpy as np
from typing import Optional


class PredictionEngine:
    
    MAX_ITER   = 40
    TOL        = 0.5   # px convergence tolerance

    # ------------------------------------------------------------------
    def predict(
        self,
        interceptor_pos: np.ndarray,
        interceptor_speed: float,
        target_pos: np.ndarray,
        target_vel: np.ndarray,
    ) -> tuple[Optional[np.ndarray], float]:
        
        if interceptor_speed < 1e-3:
            return None, -1.0

        # initial guess: time for straight-line closure
        d0 = np.linalg.norm(target_pos - interceptor_pos)
        t  = d0 / interceptor_speed

        for _ in range(self.MAX_ITER):
            future_pos  = target_pos + target_vel * t
            required_d  = np.linalg.norm(future_pos - interceptor_pos)
            t_new       = required_d / interceptor_speed
            if abs(t_new - t) < self.TOL / interceptor_speed:
                return future_pos, t_new
            t = t_new

        # fallback: best estimate after max iterations
        future_pos = target_pos + target_vel * t
        return future_pos, t

    # ------------------------------------------------------------------
    def eta_string(self, eta: float) -> str:
        if eta < 0:
            return "N/A"
        if eta > 9999:
            return ">9999s"
        return f"{eta:.1f}s"