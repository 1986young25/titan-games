#!/usr/bin/env python3
"""
Titan Games Security LLC - Acoustic Wave Extraction & 2D Scan Bridge
Calculates Room Mode Standing Waves (Axial, Tangential, Oblique) and 
converts 3D Volumetric Wavefields into 2D Scanning Slices.
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

# Constant: Speed of Sound in Air at 20°C (m/s)
SPEED_OF_SOUND = 343.0

@dataclass
class RoomDimensions:
    length: float  # X axis (meters)
    width: float   # Y axis (meters)
    height: float  # Z axis (meters)

class TitanAcousticEngine:
    def __init__(self, room: RoomDimensions, sample_rate: int = 48000):
        self.room = room
        self.sample_rate = sample_rate

    def calculate_room_modes(self, max_order: int = 4) -> List[Dict[str, Any]]:
        """
        Calculate standing wave resonant room modes using Rayleigh's equation:
        f = (c / 2) * sqrt((nx/Lx)^2 + (ny/Ly)^2 + (nz/Lz)^2)
        """
        modes = []
        c_half = SPEED_OF_SOUND / 2.0

        for nx in range(max_order + 1):
            for ny in range(max_order + 1):
                for nz in range(max_order + 1):
                    if nx == 0 and ny == 0 and nz == 0:
                        continue
                    
                    term_x = (nx / self.room.length) ** 2
                    term_y = (ny / self.room.width) ** 2
                    term_z = (nz / self.room.height) ** 2

                    freq = c_half * math.sqrt(term_x + term_y + term_z)
                    
                    # Classify mode type
                    non_zero = sum(1 for n in (nx, ny, nz) if n > 0)
                    mode_type = "Axial" if non_zero == 1 else ("Tangential" if non_zero == 2 else "Oblique")

                    modes.append({
                        "frequency_hz": round(freq, 2),
                        "indices": (nx, ny, nz),
                        "type": mode_type,
                        "wavelength_m": round(SPEED_OF_SOUND / freq, 3)
                    })

        modes.sort(key=lambda m: m["frequency_hz"])
        return modes

    def compute_2d_scan_slice(
        self,
        grid_res: Tuple[int, int] = (64, 64),
        scan_z_position: float = 1.2, # Height in meters (ear level)
        active_mode: Tuple[int, int, int] = (1, 0, 0),
        time_t: float = 0.0
    ) -> np.ndarray:
        """
        Extracts a 2D spatial acoustic slice at a given Z plane:
        P(x, y, z, t) = A * cos(kx * x) * cos(ky * y) * cos(kz * z) * cos(omega * t)
        """
        nx, ny, nz = active_mode
        kx = (nx * math.pi) / self.room.length
        ky = (ny * math.pi) / self.room.width
        kz = (nz * math.pi) / self.room.height

        freq = (SPEED_OF_SOUND / 2.0) * math.sqrt(
            (nx / self.room.length)**2 + (ny / self.room.width)**2 + (nz / self.room.height)**2
        )
        omega = 2.0 * math.pi * freq

        x = np.linspace(0, self.room.length, grid_res[0])
        y = np.linspace(0, self.room.width, grid_res[1])
        X, Y = np.meshgrid(x, y)

        # 2D Acoustic Pressure Matrix
        pressure_2d = (
            np.cos(kx * X) *
            np.cos(ky * Y) *
            math.cos(kz * scan_z_position) *
            math.cos(omega * time_t)
        )
        return pressure_2d

if __name__ == "__main__":
    # Example room mapping: 5.2m length, 3.8m width, 2.4m height (Laminate Floor Reference)
    room = RoomDimensions(length=5.2, width=3.8, height=2.4)
    engine = TitanAcousticEngine(room)

    print("--- TITAN GAMES SECURITY LLC: ACOUSTIC ROOM MODES ---")
    modes = engine.calculate_room_modes(max_order=2)
    for m in modes[:8]:
        print(f"Mode {m['indices']} | Type: {m['type']:<10} | Freq: {m['frequency_hz']:>6.2f} Hz | Wavelength: {m['wavelength_m']}m")

    # Generate sample 2D scan slice
    slice_2d = engine.compute_2d_scan_slice(grid_res=(8, 8), scan_z_position=1.0, active_mode=(2, 0, 0))
    print("\n--- 2D SCANNING SLICE MATRIX (ANTINODE PEAKS) ---")
    print(np.round(slice_2d, 2))