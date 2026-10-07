"""
Gymnasium Wildfire Suppression Environment
State space: H3 spatial grid cells with FRP intensity, wind vectors, structures nearby.
Action space: [unit_id, target_cell_idx, action_type] (0=water_drop, 1=cut_fireline, 2=evacuate)
Reward function:
  reward = - 1.0 * new_burned_hectares
           - 100.0 * structures_threatened
           - 0.15 * flight_fuel_cost
           + 80.0 * containment_established
"""

from typing import Dict, Any, Tuple, Optional
import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces

class WildfireSuppressionEnv(gym.Env):
    metadata = {"render_modes": ["ansi"]}

    def __init__(self, grid_size: int = 16):
        super().__init__()
        self.grid_size = grid_size
        self.max_steps = 24  # 24-hour tactical intervention horizon

        # Observation space:
        # Per cell: [frp_normalized, fuel_density, slope, structure_proximity, containment_status]
        # Shape: (grid_size, grid_size, 5)
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(self.grid_size, self.grid_size, 5), dtype=np.float32
        )

        # Action space: Discrete action tuple
        # 0: Unit ID (0: Air Tanker 1, 1: Air Tanker 2, 2: Bulldozer Crew Alpha, 3: Bulldozer Crew Bravo, 4: Evac Unit)
        # 1: Target cell index (0 to grid_size*grid_size - 1)
        # 2: Action type (0: water_drop, 1: cut_fireline, 2: evacuate)
        self.action_space = spaces.MultiDiscrete([5, self.grid_size * self.grid_size, 3])

        self.current_step = 0
        self.state = np.zeros((self.grid_size, self.grid_size, 5), dtype=np.float32)
        self.containment_established = 0.0
        self.cumulative_reward = 0.0
        self.structures_saved = 0
        self.hectares_saved = 0.0

    def reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        self.current_step = 0
        self.containment_established = 0.0
        self.cumulative_reward = 0.0
        self.structures_saved = 0
        self.hectares_saved = 0.0

        # Initialize environment grid with a realistic ignition core and settlements
        self.state = np.zeros((self.grid_size, self.grid_size, 5), dtype=np.float32)

        # Channel 1: Fuel density (vegetation)
        self.state[:, :, 1] = 0.70 + np.random.uniform(-0.15, 0.15, (self.grid_size, self.grid_size))

        # Channel 2: Slope (mountain ridge along diagonal)
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                self.state[r, c, 2] = min(1.0, abs(r - c) / float(self.grid_size))

        # Channel 3: Settlement structures (Valley Sector B at bottom-right)
        self.state[self.grid_size-4:self.grid_size, self.grid_size-4:self.grid_size, 3] = 1.0

        # Channel 0: Fire ignition at center (FRP)
        c_x, c_y = self.grid_size // 3, self.grid_size // 3
        self.state[c_x:c_x+2, c_y:c_y+2, 0] = 0.85

        info = {
            "initial_fire_cells": int(np.sum(self.state[:, :, 0] > 0.2)),
            "settlement_risk": True
        }
        return self.state.copy(), info

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        unit_id, target_idx, action_type = action[0], action[1], action[2]
        self.current_step += 1

        target_r = target_idx // self.grid_size
        target_c = target_idx % self.grid_size

        # Action execution effects
        # 0: Water drop (air tanker)
        # 1: Cut fireline (bulldozer)
        # 2: Evacuate corridor
        flight_fuel_cost = 0.0
        new_containment = 0.0
        structures_threatened = 0.0
        new_burned_hectares = 0.0

        if action_type == 0:
            # Air tanker water drop directly dampens FRP
            radius = 2
            r_min, r_max = max(0, target_r - radius), min(self.grid_size, target_r + radius + 1)
            c_min, c_max = max(0, target_c - radius), min(self.grid_size, target_c + radius + 1)
            active_fire_hit = np.sum(self.state[r_min:r_max, c_min:c_max, 0] > 0.1)
            self.state[r_min:r_max, c_min:c_max, 0] *= 0.15
            flight_fuel_cost = 45.0  # fuel gal / cost
            new_containment = 25.0 if active_fire_hit > 0 else 5.0
            self.hectares_saved += float(active_fire_hit) * 120.0

        elif action_type == 1:
            # Cut fireline: sets fuel to 0 and containment flag to 1.0
            self.state[target_r, target_c, 1] = 0.0  # strip fuel
            self.state[target_r, target_c, 4] = 1.0  # firebreak established
            flight_fuel_cost = 10.0  # diesel cost
            new_containment = 35.0
            self.hectares_saved += 40.0

        elif action_type == 2:
            # Evacuate: protects settlements
            is_near_settlement = self.state[target_r, target_c, 3] > 0.5
            if is_near_settlement:
                self.structures_saved += 12
                new_containment = 20.0

        # Simulate natural fire propagation step (wind pushing towards bottom-right)
        fire_mask = (self.state[:, :, 0] > 0.25)
        spread_r, spread_c = np.where(fire_mask)
        for r, c in zip(spread_r, spread_c):
            # Try to push to neighbors (downwind)
            for dr, dc in [(1, 0), (0, 1), (1, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                    # Firebreak blocks propagation
                    if self.state[nr, nc, 4] > 0.5:
                        continue
                    fuel = self.state[nr, nc, 1]
                    slope = self.state[nr, nc, 2]
                    # Spread probability driven by fuel & slope
                    if np.random.rand() < (0.35 * fuel + 0.25 * slope):
                        self.state[nr, nc, 0] = min(1.0, self.state[nr, nc, 0] + 0.35)
                        new_burned_hectares += 8.5

        # Check if fire has encroached on settlements
        settlement_encroachment = np.sum((self.state[:, :, 0] > 0.2) & (self.state[:, :, 3] > 0.5))
        structures_threatened = float(settlement_encroachment) * 5.0

        # Core Reward Formula matching the user architecture:
        # reward = - 1.0 * new_burned_hectares - 100.0 * structures_threatened - 0.15 * flight_fuel_cost + 80.0 * containment_established
        reward = (
            - 1.0 * new_burned_hectares
            - 100.0 * structures_threatened
            - 0.15 * flight_fuel_cost
            + 80.0 * (new_containment / 100.0)
        )
        self.cumulative_reward += reward

        terminated = bool(self.current_step >= self.max_steps or np.sum(self.state[:, :, 0] > 0.2) == 0)
        truncated = False
        info = {
            "step": self.current_step,
            "reward": round(reward, 2),
            "cumulative_reward": round(self.cumulative_reward, 2),
            "new_burned_hectares": round(new_burned_hectares, 1),
            "structures_threatened": int(structures_threatened),
            "structures_saved": self.structures_saved,
            "hectares_saved": round(self.hectares_saved, 1),
            "containment_pct": min(100.0, round(self.current_step * 4.2 + (self.hectares_saved / 50.0), 1))
        }

        return self.state.copy(), reward, terminated, truncated, info
