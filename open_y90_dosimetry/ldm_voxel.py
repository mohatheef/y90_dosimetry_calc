"""
Local Deposition Model (LDM) Voxel-Based Dosimetry & Dose-Volume Histogram (DVH) Engine.
Implements standardized voxel dosimetry algorithms with known injected activity normalization.
Normalizes functional imaging (PET or SPECT) to known administered activity and calculates 3D absorbed dose.
"""

from dataclasses import dataclass
from typing import Optional, Union
import math
from .constants import (
    DOSE_CONSTANT_GY_KG_PER_GBQ,
    DOSE_CONSTANT_GY_G_PER_GBQ,
    DEFAULT_LIVER_DENSITY_G_PER_CC,
    DEFAULT_TUMOR_DENSITY_G_PER_CC
)


@dataclass
class DVHPoint:
    dose_gy: float
    volume_pct: float
    volume_cc: float


@dataclass
class RegionDosimetryStats:
    region_name: str
    volume_cc: float
    mean_dose_gy: float
    min_dose_gy: float
    max_dose_gy: float
    d50_gy: float
    d70_gy: float
    d90_gy: float
    v30_pct: float   # % volume receiving >= 30 Gy
    v50_pct: float   # % volume receiving >= 50 Gy
    v100_pct: float  # % volume receiving >= 100 Gy
    v120_pct: float  # % volume receiving >= 120 Gy
    dvh_curve: list[DVHPoint]


@dataclass
class LDMDosimetryResult:
    injected_activity_gbq: float
    residual_waste_pct: float
    net_injected_activity_gbq: float
    calibration_factor_gbq_per_count: float
    total_absorbed_energy_joules: float
    regions: dict[str, RegionDosimetryStats]
    notes: list[str]


def compute_dvh(
    dose_values: list[float],
    voxel_volume_cc: float,
    bins: int = 100,
    max_dose_limit: Optional[float] = None
) -> tuple[list[DVHPoint], dict[str, float]]:
    """
    Compute cumulative Dose-Volume Histogram (DVH) from a list of voxel dose values.
    """
    if not dose_values:
        return [], {}

    total_voxels = len(dose_values)
    total_volume_cc = total_voxels * voxel_volume_cc
    sorted_doses = sorted(dose_values)

    min_dose = sorted_doses[0]
    max_dose = sorted_doses[-1]
    mean_dose = sum(sorted_doses) / total_voxels

    # Percentiles
    def get_percentile(p: float) -> float:
        idx = int(round((1.0 - p / 100.0) * (total_voxels - 1)))
        return sorted_doses[max(0, min(total_voxels - 1, idx))]

    d50 = get_percentile(50.0)
    d70 = get_percentile(70.0)
    d90 = get_percentile(90.0)

    # V-metrics: % receiving >= threshold
    def get_v_metric(thresh_gy: float) -> float:
        cnt = sum(1 for d in dose_values if d >= thresh_gy)
        return (cnt / total_voxels) * 100.0

    v30 = get_v_metric(30.0)
    v50 = get_v_metric(50.0)
    v100 = get_v_metric(100.0)
    v120 = get_v_metric(120.0)

    # Discretize for curve
    upper = max_dose_limit if max_dose_limit else max(max_dose * 1.05, 10.0)
    step = upper / max(bins, 1)

    dvh_curve = []
    for i in range(bins + 1):
        dose_thresh = i * step
        # Count voxels >= dose_thresh
        # Using binary search since sorted_doses is sorted
        import bisect
        idx = bisect.bisect_left(sorted_doses, dose_thresh)
        count_ge = total_voxels - idx
        pct_ge = (count_ge / total_voxels) * 100.0
        vol_ge = count_ge * voxel_volume_cc
        dvh_curve.append(DVHPoint(
            dose_gy=round(dose_thresh, 1),
            volume_pct=round(pct_ge, 2),
            volume_cc=round(vol_ge, 2)
        ))

    summary = {
        "volume_cc": round(total_volume_cc, 1),
        "mean_dose_gy": round(mean_dose, 2),
        "min_dose_gy": round(min_dose, 2),
        "max_dose_gy": round(max_dose, 2),
        "d50_gy": round(d50, 2),
        "d70_gy": round(d70, 2),
        "d90_gy": round(d90, 2),
        "v30_pct": round(v30, 2),
        "v50_pct": round(v50, 2),
        "v100_pct": round(v100, 2),
        "v120_pct": round(v120, 2)
    }
    return dvh_curve, summary


def calculate_voxel_ldm_dosimetry(
    voxel_counts: dict[str, list[float]],
    voxel_size_mm: tuple[float, float, float],
    injected_activity_gbq: float,
    residual_waste_pct: float = 0.0,
    lung_shunt_pct: float = 0.0,
    calibration_region_keys: Optional[list[str]] = None,
    tissue_density_g_per_cc: float = DEFAULT_LIVER_DENSITY_G_PER_CC
) -> LDMDosimetryResult:
    """
    Calculate Local Deposition Model (LDM) 3D absorbed dose for defined regions.

    Arguments:
      voxel_counts: Dict mapping region name (e.g., 'Tumor', 'Normal Liver') to list of voxel intensities/counts.
      voxel_size_mm: (dx, dy, dz) voxel spacing in mm.
      injected_activity_gbq: Administered activity in GBq.
      residual_waste_pct: Measured residual activity left in vial/tubing.
      lung_shunt_pct: Known lung shunt fraction.
      calibration_region_keys: Regions over which total counts equal liver activity. Defaults to all regions.
    """
    notes = []
    if injected_activity_gbq <= 0:
        raise ValueError("Injected activity must be positive.")
    if residual_waste_pct < 0 or residual_waste_pct >= 100.0:
        raise ValueError("Residual waste percentage must be in [0, 100).")

    # Voxel volume in cc: (dx * dy * dz) mm^3 / 1000 = cc (cm^3)
    dx, dy, dz = voxel_size_mm
    voxel_volume_cc = (dx * dy * dz) / 1000.0
    voxel_mass_g = voxel_volume_cc * tissue_density_g_per_cc

    # Net activity administered
    net_injected_gbq = injected_activity_gbq * (1.0 - (residual_waste_pct / 100.0))
    # Activity deposited in liver (minus lung shunt)
    liver_deposited_gbq = net_injected_gbq * (1.0 - (lung_shunt_pct / 100.0))

    if not calibration_region_keys:
        calibration_region_keys = list(voxel_counts.keys())

    total_calib_counts = 0.0
    for key in calibration_region_keys:
        total_calib_counts += sum(voxel_counts.get(key, []))

    if total_calib_counts <= 0:
        raise ValueError("Total counts in calibration regions must be greater than zero.")

    # Calibration factor: GBq per count
    calib_factor = liver_deposited_gbq / total_calib_counts

    # Dose conversion factor per voxel:
    # Dose [Gy] = (Activity_voxel [GBq] * 49670 Gy*g/GBq) / Voxel_mass [g]
    # Dose [Gy] = Count_voxel * calib_factor * 49670 / voxel_mass_g
    dose_multiplier = (calib_factor * DOSE_CONSTANT_GY_G_PER_GBQ) / voxel_mass_g

    regions_stats = {}
    for region_name, counts in voxel_counts.items():
        if not counts:
            continue
        doses = [max(0.0, c * dose_multiplier) for c in counts]
        curve, summary = compute_dvh(doses, voxel_volume_cc)
        regions_stats[region_name] = RegionDosimetryStats(
            region_name=region_name,
            volume_cc=summary["volume_cc"],
            mean_dose_gy=summary["mean_dose_gy"],
            min_dose_gy=summary["min_dose_gy"],
            max_dose_gy=summary["max_dose_gy"],
            d50_gy=summary["d50_gy"],
            d70_gy=summary["d70_gy"],
            d90_gy=summary["d90_gy"],
            v30_pct=summary["v30_pct"],
            v50_pct=summary["v50_pct"],
            v100_pct=summary["v100_pct"],
            v120_pct=summary["v120_pct"],
            dvh_curve=curve
        )

    # Total absorbed energy (J = Gy * kg)
    total_energy_j = liver_deposited_gbq * DOSE_CONSTANT_GY_KG_PER_GBQ

    return LDMDosimetryResult(
        injected_activity_gbq=round(injected_activity_gbq, 3),
        residual_waste_pct=round(residual_waste_pct, 1),
        net_injected_activity_gbq=round(net_injected_gbq, 3),
        calibration_factor_gbq_per_count=calib_factor,
        total_absorbed_energy_joules=round(total_energy_j, 1),
        regions=regions_stats,
        notes=notes
    )


def generate_synthetic_phantom(
    matrix_size: int = 64,
    tumor_radius_voxels: float = 12.0,
    liver_radius_voxels: float = 26.0,
    tumor_to_normal_count_ratio: float = 3.5,
    noise_std: float = 0.15
) -> dict[str, list[float]]:
    """
    Generate synthetic 3D phantom voxel arrays for demonstration and testing.
    Creates a spherical tumor embedded in a larger liver volume with realistic uptake.
    """
    import random
    center = matrix_size / 2.0
    tumor_center = (center + 4, center + 4, center)

    tumor_counts = []
    normal_counts = []

    for z in range(matrix_size):
        for y in range(matrix_size):
            for x in range(matrix_size):
                # Distance to liver center
                dist_liver = math.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
                # Distance to tumor center
                dist_tumor = math.sqrt((x - tumor_center[0])**2 + (y - tumor_center[1])**2 + (z - tumor_center[2])**2)

                if dist_tumor <= tumor_radius_voxels:
                    val = tumor_to_normal_count_ratio * (1.0 + random.gauss(0, noise_std))
                    tumor_counts.append(max(0.1, val))
                elif dist_liver <= liver_radius_voxels:
                    val = 1.0 * (1.0 + random.gauss(0, noise_std))
                    normal_counts.append(max(0.05, val))

    return {
        "Tumor": tumor_counts,
        "Normal Liver": normal_counts
    }
