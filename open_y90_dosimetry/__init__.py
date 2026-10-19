"""
Open Y-90 Dosimetry: Open-Source Internal Radiation Therapy (SIRT) Calculation Suite.
Calibrated against international clinical guidelines and radiopharmaceutical monographs.
"""

from .constants import (
    RADIONUCLIDE,
    HALF_LIFE_HOURS,
    DOSE_CONSTANT_GY_KG_PER_GBQ,
    DOSE_CONSTANT_GY_G_PER_GBQ,
    DOSE_CONSTANT_MIRD_APPROX,
    DEFAULT_LIVER_DENSITY_G_PER_CC,
    DEFAULT_LUNG_MASS_KG,
    MAX_LUNG_DOSE_SINGLE_SESSION_GY,
    MAX_LUNG_DOSE_CUMULATIVE_GY,
    DEFAULT_NORMAL_LIVER_LIMIT_CIRRHOTIC_GY,
    DEFAULT_NORMAL_LIVER_LIMIT_NON_CIRRHOTIC_GY
)
from .bsa import (
    calculate_bsa_dubois,
    calculate_bsa_mosteller,
    evaluate_lsf_tier,
    plan_bsa_activity,
    BSAResult,
    LSFStatus
)
from .mird import (
    plan_mird_activity,
    calculate_mird_dose_from_activity,
    MIRDResult
)
from .partition import (
    calculate_tnr_from_counts,
    evaluate_partition_doses,
    plan_partition_activity,
    PartitionResult,
    PartitionDoseProfile
)
from .lung_shunt import (
    calculate_planar_geometric_mean,
    calculate_lung_shunt_planar,
    calculate_lung_shunt_spect,
    LungShuntResult
)
from .ldm_voxel import (
    calculate_voxel_ldm_dosimetry,
    compute_dvh,
    generate_synthetic_phantom,
    LDMDosimetryResult,
    RegionDosimetryStats,
    DVHPoint
)
from .report import (
    PatientInfo,
    ClinicalReportData,
    generate_markdown_report,
    generate_html_report
)

__version__ = "1.0.0"
__all__ = [
    "RADIONUCLIDE",
    "HALF_LIFE_HOURS",
    "DOSE_CONSTANT_GY_KG_PER_GBQ",
    "DOSE_CONSTANT_GY_G_PER_GBQ",
    "DOSE_CONSTANT_MIRD_APPROX",
    "DEFAULT_LIVER_DENSITY_G_PER_CC",
    "DEFAULT_LUNG_MASS_KG",
    "MAX_LUNG_DOSE_SINGLE_SESSION_GY",
    "MAX_LUNG_DOSE_CUMULATIVE_GY",
    "DEFAULT_NORMAL_LIVER_LIMIT_CIRRHOTIC_GY",
    "DEFAULT_NORMAL_LIVER_LIMIT_NON_CIRRHOTIC_GY",
    "calculate_bsa_dubois",
    "calculate_bsa_mosteller",
    "evaluate_lsf_tier",
    "plan_bsa_activity",
    "BSAResult",
    "LSFStatus",
    "plan_mird_activity",
    "calculate_mird_dose_from_activity",
    "MIRDResult",
    "calculate_tnr_from_counts",
    "evaluate_partition_doses",
    "plan_partition_activity",
    "PartitionResult",
    "PartitionDoseProfile",
    "calculate_planar_geometric_mean",
    "calculate_lung_shunt_planar",
    "calculate_lung_shunt_spect",
    "LungShuntResult",
    "calculate_voxel_ldm_dosimetry",
    "compute_dvh",
    "generate_synthetic_phantom",
    "LDMDosimetryResult",
    "RegionDosimetryStats",
    "DVHPoint",
    "PatientInfo",
    "ClinicalReportData",
    "generate_markdown_report",
    "generate_html_report"
]
