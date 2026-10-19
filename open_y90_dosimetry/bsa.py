"""
BSA (Body Surface Area) Model for Y-90 SIR-Spheres Activity Planning.
Implements standardized formulas from clinical consensus guidelines and the SIR-Spheres product monograph.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from .constants import (
    DOSE_CONSTANT_GY_KG_PER_GBQ,
    DEFAULT_LUNG_MASS_KG,
    LSF_TIER_NORMAL_MAX,
    LSF_TIER_MODERATE_MAX,
    LSF_TIER_HIGH_MAX,
    MAX_LUNG_DOSE_SINGLE_SESSION_GY
)


class LSFStatus(str, Enum):
    NORMAL = "Normal (< 10%) - No Activity Reduction"
    MODERATE = "Moderate (10% - 15%) - 20% Activity Reduction"
    HIGH = "High (15% - 20%) - 40% Activity Reduction"
    CONTRAINDICATED = "Contraindicated (> 20%) - High Risk of Radiation Pneumonitis"


@dataclass
class BSAResult:
    bsa_m2: float
    tumor_involvement_pct: float
    unscaled_activity_gbq: float
    target_scaling_fraction: float
    calculated_activity_gbq: float
    lsf_reduction_pct: float
    lsf_status: LSFStatus
    prescribed_activity_gbq: float
    prescribed_activity_mbq: float
    estimated_lung_dose_gy: float
    lung_dose_safe: bool
    notes: list[str]


def calculate_bsa_dubois(height_m: float, weight_kg: float) -> float:
    """
    Du Bois & Du Bois formula:
    BSA [m^2] = 0.20247 * (Height [m] ^ 0.725) * (Weight [kg] ^ 0.425)
    """
    if height_m <= 0 or weight_kg <= 0:
        raise ValueError("Height and weight must be positive.")
    return 0.20247 * (height_m ** 0.725) * (weight_kg ** 0.425)


def calculate_bsa_mosteller(height_cm: float, weight_kg: float) -> float:
    """
    Mosteller formula:
    BSA [m^2] = sqrt((Height [cm] * Weight [kg]) / 3600)
    """
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("Height and weight must be positive.")
    import math
    return math.sqrt((height_cm * weight_kg) / 3600.0)


def evaluate_lsf_tier(lung_shunt_pct: float) -> tuple[float, LSFStatus]:
    """
    Determines activity reduction tier based on lung shunt percentage:
    < 10%: 0% reduction
    10% - 15%: 20% reduction
    15% - 20%: 40% reduction
    > 20%: Contraindicated
    """
    if lung_shunt_pct < LSF_TIER_NORMAL_MAX:
        return 0.0, LSFStatus.NORMAL
    elif lung_shunt_pct < LSF_TIER_MODERATE_MAX:
        return 20.0, LSFStatus.MODERATE
    elif lung_shunt_pct <= LSF_TIER_HIGH_MAX:
        return 40.0, LSFStatus.HIGH
    else:
        return 100.0, LSFStatus.CONTRAINDICATED


def plan_bsa_activity(
    height_m: float,
    weight_kg: float,
    tumor_volume_cc: float,
    target_volume_cc: float,
    total_liver_volume_cc: Optional[float] = None,
    lung_shunt_pct: float = 0.0,
    lung_mass_kg: float = DEFAULT_LUNG_MASS_KG,
    formula: str = "dubois"
) -> BSAResult:
    """
    Calculate planned Y-90 activity using the SIR-Spheres BSA empirical model.

    Equations (Standard Clinical Formulation):
      BSA = 0.20247 * (Height ^ 0.725) * (Weight ^ 0.425)
      Tumor Involvement [%] = (Volume_tumor / Volume_target) * 100
      Calculated Activity [GBq] = [BSA - 0.2 + (Volume_tumor / Volume_target)] * (Volume_target / Volume_liver)
      Prescribed Activity [GBq] = Calculated Activity * (1 - LSF_Reduction_Pct / 100)
    """
    notes = []
    if height_m < 1.0 or height_m > 2.2:
        notes.append(f"Warning: Patient height ({height_m:.2f} m) is outside typical range [1.0, 2.2 m].")
    if weight_kg < 30.0 or weight_kg > 200.0:
        notes.append(f"Warning: Patient weight ({weight_kg:.1f} kg) is outside typical range [30, 200 kg].")

    if target_volume_cc <= 0:
        raise ValueError("Target volume must be greater than 0.")
    if tumor_volume_cc < 0:
        raise ValueError("Tumor volume cannot be negative.")
    if tumor_volume_cc > target_volume_cc:
        notes.append("Warning: Tumor volume exceeds target volume; capped tumor volume to target volume.")
        tumor_volume_cc = target_volume_cc

    if total_liver_volume_cc is None or total_liver_volume_cc <= 0:
        total_liver_volume_cc = target_volume_cc

    # Calculate BSA
    if formula.lower() == "mosteller":
        bsa = calculate_bsa_mosteller(height_m * 100.0, weight_kg)
    else:
        bsa = calculate_bsa_dubois(height_m, weight_kg)

    # Tumor involvement
    tumor_involvement = (tumor_volume_cc / target_volume_cc) * 100.0

    # Unscaled activity: [BSA - 0.2 + (V_tumor / V_target)]
    unscaled_activity = bsa - 0.2 + (tumor_volume_cc / target_volume_cc)
    if unscaled_activity < 0:
        unscaled_activity = 0.0
        notes.append("Warning: Calculated unscaled activity is negative; clamped to 0 GBq.")

    # Target scaling fraction: (V_target / V_liver)
    scaling_fraction = target_volume_cc / total_liver_volume_cc
    if scaling_fraction > 1.0:
        scaling_fraction = 1.0

    calculated_activity = unscaled_activity * scaling_fraction

    # LSF Evaluation
    reduction_pct, lsf_status = evaluate_lsf_tier(lung_shunt_pct)
    if lsf_status == LSFStatus.CONTRAINDICATED:
        notes.append("CRITICAL: Lung shunt fraction > 20%. Administration is contraindicated per product monograph.")

    prescribed_activity = calculated_activity * (1.0 - (reduction_pct / 100.0))
    prescribed_mbq = prescribed_activity * 1000.0

    # Estimated Lung Dose
    # Dose = Activity * (LSF / 100) * 49.67 / Mass_lung
    estimated_lung_dose = (prescribed_activity * (lung_shunt_pct / 100.0) * DOSE_CONSTANT_GY_KG_PER_GBQ) / lung_mass_kg
    lung_dose_safe = estimated_lung_dose <= MAX_LUNG_DOSE_SINGLE_SESSION_GY
    if not lung_dose_safe:
        notes.append(f"ALERT: Estimated lung dose ({estimated_lung_dose:.1f} Gy) exceeds 30 Gy single-session limit!")

    return BSAResult(
        bsa_m2=round(bsa, 3),
        tumor_involvement_pct=round(tumor_involvement, 2),
        unscaled_activity_gbq=round(unscaled_activity, 3),
        target_scaling_fraction=round(scaling_fraction, 3),
        calculated_activity_gbq=round(calculated_activity, 3),
        lsf_reduction_pct=reduction_pct,
        lsf_status=lsf_status,
        prescribed_activity_gbq=round(prescribed_activity, 3),
        prescribed_activity_mbq=round(prescribed_mbq, 1),
        estimated_lung_dose_gy=round(estimated_lung_dose, 2),
        lung_dose_safe=lung_dose_safe,
        notes=notes
    )
