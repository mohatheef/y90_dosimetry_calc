"""
Lung Shunt Fraction (LSF) calculation for Y-90 pre-treatment MAA workup.
Supports both 2D Planar Scintigraphy (Geometric Mean) and 3D SPECT/CT volume integration.
Implements standardized clinical formulas from nuclear medicine guidelines.
"""

from dataclasses import dataclass
import math
from typing import Optional
from .bsa import evaluate_lsf_tier, LSFStatus


@dataclass
class LungShuntResult:
    method: str
    lung_counts: float
    liver_counts: float
    lung_shunt_pct: float
    status: LSFStatus
    recommended_activity_reduction_pct: float
    is_safe_to_treat: bool
    clinical_recommendation: str
    notes: list[str]


def calculate_planar_geometric_mean(anterior_counts: float, posterior_counts: float) -> float:
    """Calculate geometric mean: sqrt(anterior * posterior)."""
    if anterior_counts < 0 or posterior_counts < 0:
        raise ValueError("Counts cannot be negative.")
    return math.sqrt(anterior_counts * posterior_counts)


def calculate_lung_shunt_planar(
    lung_ant_counts: float,
    lung_post_counts: float,
    liver_ant_counts: float,
    liver_post_counts: float
) -> LungShuntResult:
    """
    Calculate Lung Shunt Fraction from 2D Planar scintigraphy using conjugate view geometric mean.

    Formula:
      G_lung  = sqrt(Lung_Ant * Lung_Post)
      G_liver = sqrt(Liver_Ant * Liver_Post)
      LSF [%] = [G_lung / (G_lung + G_liver)] * 100
    """
    notes = []
    g_lung = calculate_planar_geometric_mean(lung_ant_counts, lung_post_counts)
    g_liver = calculate_planar_geometric_mean(liver_ant_counts, liver_post_counts)

    total_g = g_lung + g_liver
    if total_g <= 0:
        raise ValueError("Total counts in liver and lung must be greater than zero.")

    lsf_pct = (g_lung / total_g) * 100.0
    reduction_pct, status = evaluate_lsf_tier(lsf_pct)

    if status == LSFStatus.NORMAL:
        rec = "Safe to proceed with standard prescribed activity (0% reduction)."
        safe = True
    elif status == LSFStatus.MODERATE:
        rec = "Moderate shunt: Reduce activity by 20% to safeguard lung tissue."
        safe = True
    elif status == LSFStatus.HIGH:
        rec = "High shunt: Reduce activity by 40% and verify lung dose is strictly under 30 Gy."
        safe = True
    else:
        rec = "Contraindicated: Shunt > 20% carries unacceptable risk of radiation pneumonitis. Do not treat without formal dosimetric exception."
        safe = False
        notes.append("ALERT: High hepatopulmonary shunting detected.")

    return LungShuntResult(
        method="2D Planar (Conjugate View Geometric Mean)",
        lung_counts=round(g_lung, 1),
        liver_counts=round(g_liver, 1),
        lung_shunt_pct=round(lsf_pct, 2),
        status=status,
        recommended_activity_reduction_pct=reduction_pct,
        is_safe_to_treat=safe,
        clinical_recommendation=rec,
        notes=notes
    )


def calculate_lung_shunt_spect(
    total_lung_counts: float,
    total_liver_counts: float
) -> LungShuntResult:
    """
    Calculate Lung Shunt Fraction from 3D SPECT/CT volume integration.

    Formula:
      LSF [%] = [Total Lung Counts / (Total Lung Counts + Total Liver Counts)] * 100
    """
    notes = []
    total = total_lung_counts + total_liver_counts
    if total <= 0:
        raise ValueError("Total volume counts must be greater than zero.")

    lsf_pct = (total_lung_counts / total) * 100.0
    reduction_pct, status = evaluate_lsf_tier(lsf_pct)

    if status == LSFStatus.NORMAL:
        rec = "Safe to proceed with standard prescribed activity (0% reduction)."
        safe = True
    elif status == LSFStatus.MODERATE:
        rec = "Moderate shunt: Reduce activity by 20% to safeguard lung tissue."
        safe = True
    elif status == LSFStatus.HIGH:
        rec = "High shunt: Reduce activity by 40% and verify lung dose is strictly under 30 Gy."
        safe = True
    else:
        rec = "Contraindicated: Shunt > 20% carries severe radiation pneumonitis risk."
        safe = False
        notes.append("ALERT: High hepatopulmonary shunting detected on 3D SPECT.")

    return LungShuntResult(
        method="3D SPECT/CT Volume Integration",
        lung_counts=round(total_lung_counts, 1),
        liver_counts=round(total_liver_counts, 1),
        lung_shunt_pct=round(lsf_pct, 2),
        status=status,
        recommended_activity_reduction_pct=reduction_pct,
        is_safe_to_treat=safe,
        clinical_recommendation=rec,
        notes=notes
    )
