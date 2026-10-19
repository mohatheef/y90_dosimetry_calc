"""
Partition Model (Multi-Compartment Dosimetry) for Y-90 Microspheres.
Implements standardized formulas from clinical consensus guidelines and the SIR-Spheres package insert.
Solves simultaneous linear compartment equations for Tumor, Normal Liver, and Lungs.
"""

from dataclasses import dataclass
from typing import Optional
from .constants import (
    DOSE_CONSTANT_GY_KG_PER_GBQ,
    DEFAULT_LIVER_DENSITY_G_PER_CC,
    DEFAULT_TUMOR_DENSITY_G_PER_CC,
    DEFAULT_LUNG_MASS_KG,
    DEFAULT_NORMAL_LIVER_LIMIT_CIRRHOTIC_GY,
    DEFAULT_NORMAL_LIVER_LIMIT_NON_CIRRHOTIC_GY,
    MAX_LUNG_DOSE_SINGLE_SESSION_GY
)


@dataclass
class PartitionDoseProfile:
    activity_gbq: float
    tumor_dose_gy: float
    normal_liver_dose_gy: float
    lung_dose_gy: float
    tumor_activity_gbq: float
    normal_liver_activity_gbq: float
    lung_activity_gbq: float


@dataclass
class PartitionResult:
    tumor_volume_cc: float
    normal_liver_volume_cc: float
    total_target_volume_cc: float
    tumor_mass_kg: float
    normal_liver_mass_kg: float
    tumor_involvement_pct: float
    tnr: float
    lung_shunt_pct: float

    # Threshold-based calculated activities
    activity_normal_liver_limit_gbq: float
    activity_lung_limit_gbq: float
    activity_desired_tumor_dose_gbq: float

    # Recommended safe prescription
    recommended_activity_gbq: float
    recommended_activity_mbq: float
    recommended_doses: PartitionDoseProfile

    # Safety status
    normal_liver_safe: bool
    lung_safe: bool
    therapeutic_tumor_dose: bool
    notes: list[str]


def calculate_tnr_from_counts(
    tumor_counts: float,
    tumor_mass_kg: float,
    normal_liver_counts: float,
    normal_liver_mass_kg: float
) -> float:
    """
    Calculate Tumor-to-Normal Ratio (TNR) from SPECT or PET counts:
    TNR = (TotalCNTS_tumor / Mass_tumor) / (TotalCNTS_normal_liver / Mass_normal_liver)
    """
    if tumor_mass_kg <= 0 or normal_liver_mass_kg <= 0:
        raise ValueError("Masses must be positive.")
    if normal_liver_counts <= 0:
        raise ValueError("Normal liver counts must be positive.")
    tumor_conc = tumor_counts / tumor_mass_kg
    normal_conc = normal_liver_counts / normal_liver_mass_kg
    return tumor_conc / normal_conc


def evaluate_partition_doses(
    activity_gbq: float,
    tumor_mass_kg: float,
    normal_liver_mass_kg: float,
    tnr: float,
    lung_shunt_pct: float,
    lung_mass_kg: float = DEFAULT_LUNG_MASS_KG
) -> PartitionDoseProfile:
    """
    Given a known activity and compartment parameters, compute absorbed doses:
      Denominator = (TNR * Mass_tumor) + Mass_normal_liver
      Activity_normal = Activity * (1 - LSF) * Mass_normal / Denominator
      Activity_tumor  = Activity * (1 - LSF) * TNR * Mass_tumor / Denominator
      Activity_lung   = Activity * LSF
      Dose_tissue = (49.67 * Activity_tissue) / Mass_tissue
    """
    lsf = lung_shunt_pct / 100.0
    denominator = (tnr * tumor_mass_kg) + normal_liver_mass_kg
    if denominator <= 0:
        raise ValueError("Invalid mass or TNR values resulting in non-positive denominator.")

    act_liver = activity_gbq * (1.0 - lsf)
    act_normal = (act_liver * normal_liver_mass_kg) / denominator
    act_tumor = (act_liver * tnr * tumor_mass_kg) / denominator
    act_lung = activity_gbq * lsf

    dose_normal = (DOSE_CONSTANT_GY_KG_PER_GBQ * act_normal) / normal_liver_mass_kg
    dose_tumor = (DOSE_CONSTANT_GY_KG_PER_GBQ * act_tumor) / tumor_mass_kg
    dose_lung = (DOSE_CONSTANT_GY_KG_PER_GBQ * act_lung) / lung_mass_kg

    return PartitionDoseProfile(
        activity_gbq=round(activity_gbq, 3),
        tumor_dose_gy=round(dose_tumor, 2),
        normal_liver_dose_gy=round(dose_normal, 2),
        lung_dose_gy=round(dose_lung, 2),
        tumor_activity_gbq=round(act_tumor, 3),
        normal_liver_activity_gbq=round(act_normal, 3),
        lung_activity_gbq=round(act_lung, 3)
    )


def plan_partition_activity(
    tumor_volume_cc: float,
    target_volume_cc: float,
    tnr: float,
    lung_shunt_pct: float,
    desired_tumor_dose_gy: float = 120.0,
    normal_liver_dose_limit_gy: float = DEFAULT_NORMAL_LIVER_LIMIT_CIRRHOTIC_GY,
    lung_dose_limit_gy: float = MAX_LUNG_DOSE_SINGLE_SESSION_GY,
    density_tumor_g_per_cc: float = DEFAULT_TUMOR_DENSITY_G_PER_CC,
    density_normal_g_per_cc: float = DEFAULT_LIVER_DENSITY_G_PER_CC,
    lung_mass_kg: float = DEFAULT_LUNG_MASS_KG
) -> PartitionResult:
    """
    Calculate planned Y-90 activity using the Partition Model (Multi-Compartment Dosimetry).

    Formulas:
      Tumor Involvement [%] = (Volume_tumor / Volume_target) * 100
      Mass_tumor = Volume_tumor * density_tumor / 1000
      Mass_normal = (Volume_target - Volume_tumor) * density_normal / 1000

      Based on Normal Liver Limiting Dose (D_normal):
        Activity_NL = [D_normal * (TNR * Mass_tumor + Mass_normal)] / [49.67 * (1 - LSF)]

      Based on Desired Tumor Dose (D_tumor):
        Activity_T = [D_tumor * (TNR * Mass_tumor + Mass_normal)] / [49.67 * TNR * (1 - LSF)]

      Based on Lung Limiting Dose (D_lung):
        Activity_L = [D_lung * Mass_lung] / [49.67 * LSF]
    """
    notes = []
    if target_volume_cc <= 0:
        raise ValueError("Target volume must be positive.")
    if tumor_volume_cc <= 0:
        raise ValueError("Tumor volume must be positive for Partition Model.")
    if tumor_volume_cc >= target_volume_cc:
        raise ValueError("Tumor volume cannot equal or exceed entire target volume.")
    if tnr <= 0:
        raise ValueError("Tumor-to-Normal Ratio (TNR) must be positive.")

    normal_volume_cc = target_volume_cc - tumor_volume_cc
    tumor_mass_kg = (tumor_volume_cc * density_tumor_g_per_cc) / 1000.0
    normal_mass_kg = (normal_volume_cc * density_normal_g_per_cc) / 1000.0
    tumor_involvement = (tumor_volume_cc / target_volume_cc) * 100.0

    lsf = lung_shunt_pct / 100.0
    if lsf >= 1.0:
        raise ValueError("Lung shunt percentage cannot be 100% or greater.")

    denominator = (tnr * tumor_mass_kg) + normal_mass_kg

    # 1. Activity based on Normal Liver Limiting Dose
    act_nl_limit = (normal_liver_dose_limit_gy * denominator) / (DOSE_CONSTANT_GY_KG_PER_GBQ * (1.0 - lsf))

    # 2. Activity based on Desired Tumor Dose
    act_tumor_target = (desired_tumor_dose_gy * denominator) / (DOSE_CONSTANT_GY_KG_PER_GBQ * tnr * (1.0 - lsf))

    # 3. Activity based on Lung Limiting Dose
    if lsf > 0:
        act_lung_limit = (lung_dose_limit_gy * lung_mass_kg) / (DOSE_CONSTANT_GY_KG_PER_GBQ * lsf)
    else:
        act_lung_limit = 999.0  # Infinite if 0 shunt

    # Prescribed Activity is constrained by the safest upper threshold
    max_safe_activity = min(act_nl_limit, act_lung_limit)
    recommended_activity = min(act_tumor_target, max_safe_activity)

    if act_tumor_target > max_safe_activity:
        notes.append(
            f"Caution: Desired tumor dose ({desired_tumor_dose_gy:.0f} Gy) requires {act_tumor_target:.2f} GBq, "
            f"which exceeds the safe limit ({max_safe_activity:.2f} GBq). Activity was capped to prevent normal tissue toxicity."
        )

    # Evaluate doses under recommended activity
    doses = evaluate_partition_doses(
        activity_gbq=recommended_activity,
        tumor_mass_kg=tumor_mass_kg,
        normal_liver_mass_kg=normal_mass_kg,
        tnr=tnr,
        lung_shunt_pct=lung_shunt_pct,
        lung_mass_kg=lung_mass_kg
    )

    nl_safe = doses.normal_liver_dose_gy <= normal_liver_dose_limit_gy + 0.1
    lung_safe = doses.lung_dose_gy <= lung_dose_limit_gy + 0.1
    tumor_therapeutic = doses.tumor_dose_gy >= 100.0

    if not tumor_therapeutic:
        notes.append(f"Notice: Resulting tumor dose ({doses.tumor_dose_gy:.1f} Gy) is below 100 Gy (subtherapeutic threshold).")

    return PartitionResult(
        tumor_volume_cc=round(tumor_volume_cc, 1),
        normal_liver_volume_cc=round(normal_volume_cc, 1),
        total_target_volume_cc=round(target_volume_cc, 1),
        tumor_mass_kg=round(tumor_mass_kg, 4),
        normal_liver_mass_kg=round(normal_mass_kg, 4),
        tumor_involvement_pct=round(tumor_involvement, 2),
        tnr=round(tnr, 2),
        lung_shunt_pct=round(lung_shunt_pct, 2),
        activity_normal_liver_limit_gbq=round(act_nl_limit, 3),
        activity_lung_limit_gbq=round(act_lung_limit, 3),
        activity_desired_tumor_dose_gbq=round(act_tumor_target, 3),
        recommended_activity_gbq=round(recommended_activity, 3),
        recommended_activity_mbq=round(recommended_activity * 1000.0, 1),
        recommended_doses=doses,
        normal_liver_safe=nl_safe,
        lung_safe=lung_safe,
        therapeutic_tumor_dose=tumor_therapeutic,
        notes=notes
    )
