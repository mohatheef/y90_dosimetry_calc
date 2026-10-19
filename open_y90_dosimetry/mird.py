"""
MIRD (Medical Internal Radiation Dose) Single-Compartment Model for Y-90 Microsphere Dosimetry.
Implements standardized formulas from clinical consensus guidelines and the TheraSphere package insert.
"""

from dataclasses import dataclass
from typing import Optional
from .constants import (
    DOSE_CONSTANT_MIRD_APPROX,
    DOSE_CONSTANT_GY_KG_PER_GBQ,
    DEFAULT_LIVER_DENSITY_G_PER_CC,
    DEFAULT_LUNG_MASS_KG,
    MAX_LUNG_DOSE_SINGLE_SESSION_GY
)


@dataclass
class MIRDResult:
    target_volume_cc: float
    target_mass_kg: float
    desired_dose_gy: float
    lung_shunt_pct: float
    calculated_activity_gbq: float
    calculated_activity_mbq: float
    anticipated_waste_pct: float
    vial_activity_gbq: float
    vial_activity_mbq: float
    estimated_lung_dose_gy: float
    lung_dose_safe: bool
    dose_constant_used: float
    notes: list[str]


def plan_mird_activity(
    desired_dose_gy: float,
    target_volume_cc: Optional[float] = None,
    target_mass_kg: Optional[float] = None,
    lung_shunt_pct: float = 0.0,
    residual_waste_pct: float = 0.0,
    tissue_density_g_per_cc: float = DEFAULT_LIVER_DENSITY_G_PER_CC,
    lung_mass_kg: float = DEFAULT_LUNG_MASS_KG,
    exact_constant: bool = False
) -> MIRDResult:
    """
    Calculate planned Y-90 activity using the MIRD Single-Compartment Model.

    Formulas (Standard MIRD / Boston Scientific TheraSphere):
      Mass_target = Volume_target * Density / 1000
      Calculated Activity [GBq] = (Dose_target * Mass_target) / [Constant * (1 - LSF)]
      Lung Dose [Gy] = Activity * LSF * Constant / Mass_lung
      Vial Activity [GBq] = Calculated Activity / (1 - Waste%)
    """
    notes = []
    dose_constant = DOSE_CONSTANT_GY_KG_PER_GBQ if exact_constant else DOSE_CONSTANT_MIRD_APPROX

    if desired_dose_gy <= 0:
        raise ValueError("Desired dose must be positive.")

    # Determine mass
    if target_mass_kg is None:
        if target_volume_cc is None or target_volume_cc <= 0:
            raise ValueError("Either target_volume_cc or target_mass_kg must be provided.")
        target_mass_kg = (target_volume_cc * tissue_density_g_per_cc) / 1000.0
    else:
        if target_mass_kg <= 0:
            raise ValueError("Target mass must be positive.")
        if target_volume_cc is None:
            target_volume_cc = (target_mass_kg * 1000.0) / tissue_density_g_per_cc

    lsf_fraction = lung_shunt_pct / 100.0
    if lsf_fraction >= 1.0:
        raise ValueError("Lung shunt fraction cannot be 100% or greater.")

    # Injected activity to achieve desired target dose
    calculated_activity = (desired_dose_gy * target_mass_kg) / (dose_constant * (1.0 - lsf_fraction))

    # Waste compensation
    if residual_waste_pct < 0 or residual_waste_pct >= 100.0:
        raise ValueError("Residual waste percentage must be in [0, 100).")
    vial_activity = calculated_activity / (1.0 - (residual_waste_pct / 100.0)) if residual_waste_pct > 0 else calculated_activity

    # Lung absorbed dose
    lung_dose = (calculated_activity * lsf_fraction * dose_constant) / lung_mass_kg
    lung_safe = lung_dose <= MAX_LUNG_DOSE_SINGLE_SESSION_GY
    if not lung_safe:
        notes.append(f"ALERT: Predicted lung dose ({lung_dose:.1f} Gy) exceeds safe limit of {MAX_LUNG_DOSE_SINGLE_SESSION_GY:.0f} Gy!")

    if desired_dose_gy < 80.0:
        notes.append(f"Note: Desired dose {desired_dose_gy:.0f} Gy is lower than standard therapeutic target for HCC (typically 100 - 150 Gy).")
    elif desired_dose_gy > 250.0:
        notes.append(f"Note: Desired dose {desired_dose_gy:.0f} Gy is high (radiation segmentectomy / ablative range).")

    return MIRDResult(
        target_volume_cc=round(target_volume_cc, 1),
        target_mass_kg=round(target_mass_kg, 4),
        desired_dose_gy=round(desired_dose_gy, 1),
        lung_shunt_pct=round(lung_shunt_pct, 2),
        calculated_activity_gbq=round(calculated_activity, 3),
        calculated_activity_mbq=round(calculated_activity * 1000.0, 1),
        anticipated_waste_pct=round(residual_waste_pct, 1),
        vial_activity_gbq=round(vial_activity, 3),
        vial_activity_mbq=round(vial_activity * 1000.0, 1),
        estimated_lung_dose_gy=round(lung_dose, 2),
        lung_dose_safe=lung_safe,
        dose_constant_used=dose_constant,
        notes=notes
    )


def calculate_mird_dose_from_activity(
    injected_activity_gbq: float,
    target_mass_kg: float,
    lung_shunt_pct: float = 0.0,
    lung_mass_kg: float = DEFAULT_LUNG_MASS_KG,
    exact_constant: bool = False
) -> tuple[float, float]:
    """
    Forward calculation: given known injected activity, calculate target dose and lung dose.
    Returns: (target_dose_gy, lung_dose_gy)
    """
    dose_constant = DOSE_CONSTANT_GY_KG_PER_GBQ if exact_constant else DOSE_CONSTANT_MIRD_APPROX
    lsf = lung_shunt_pct / 100.0
    target_dose = (injected_activity_gbq * (1.0 - lsf) * dose_constant) / target_mass_kg
    lung_dose = (injected_activity_gbq * lsf * dose_constant) / lung_mass_kg
    return round(target_dose, 2), round(lung_dose, 2)
