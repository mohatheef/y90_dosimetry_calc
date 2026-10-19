"""
Physical constants, radiobiological parameters, and clinical safety thresholds
for Yttrium-90 (Y-90) microsphere radioembolization / Selective Internal Radiation Therapy (SIRT).
Calibrated against international clinical consensus guidelines and standard radiopharmaceutical monographs.
"""

from typing import Final

# Physical Properties of Yttrium-90 (Y-90)
RADIONUCLIDE: Final[str] = "Yttrium-90 (Y-90)"
HALF_LIFE_HOURS: Final[float] = 64.1  # 2.671 days
HALF_LIFE_DAYS: Final[float] = 64.1 / 24.0
MEAN_BETA_ENERGY_MEV: Final[float] = 0.9337
MAX_BETA_ENERGY_MEV: Final[float] = 2.28
MEAN_TISSUE_RANGE_MM: Final[float] = 2.5
MAX_TISSUE_RANGE_MM: Final[float] = 11.0

# Absorbed Dose Equilibrium Constants:
# 1 GBq completely decayed in 1 kg of tissue yields:
# Integral decays = (1e9 * 64.1 * 3600 / ln(2)) = 3.329e14 decays
# Total Energy = 3.329e14 * (0.9337 * 1.60218e-13 J) = 49.88 J -> 49.67 - 49.88 Gy*kg/GBq
DOSE_CONSTANT_GY_KG_PER_GBQ: Final[float] = 49.67
DOSE_CONSTANT_GY_G_PER_GBQ: Final[float] = 49670.0  # Standard multi-compartment partition model equilibrium constant
DOSE_CONSTANT_MIRD_APPROX: Final[float] = 50.0      # Standard TheraSphere package insert approximation

# Tissue Densities & Default Anatomical Reference Masses
DEFAULT_LIVER_DENSITY_G_PER_CC: Final[float] = 1.05  # g/cm3 (range: 1.03 - 1.06)
DEFAULT_TUMOR_DENSITY_G_PER_CC: Final[float] = 1.05  # g/cm3
DEFAULT_LUNG_MASS_KG: Final[float] = 1.0             # Reference lung mass (ICRP standard)
DEFAULT_LUNG_MASS_G: Final[float] = 1000.0

# Clinical Safety Thresholds & Guidelines (EANM / CIRSE / FDA / CE)
MAX_LUNG_DOSE_SINGLE_SESSION_GY: Final[float] = 30.0  # Safe threshold to avoid radiation pneumonitis
MAX_LUNG_DOSE_CUMULATIVE_GY: Final[float] = 50.0
DEFAULT_NORMAL_LIVER_LIMIT_CIRRHOTIC_GY: Final[float] = 40.0
DEFAULT_NORMAL_LIVER_LIMIT_NON_CIRRHOTIC_GY: Final[float] = 70.0
DEFAULT_TARGET_TUMOR_DESIRED_DOSE_GY: Final[float] = 120.0
DEFAULT_ABLATIVE_TUMOR_DOSE_GY: Final[float] = 205.0   # Radiation segmentectomy target

# Sirtex SIR-Spheres Lung Shunt Fraction (LSF) Activity Reduction Tiers
LSF_TIER_NORMAL_MAX: Final[float] = 10.0      # LSF < 10%: No reduction (100%)
LSF_TIER_MODERATE_MAX: Final[float] = 15.0    # 10% <= LSF < 15%: 20% reduction (80%)
LSF_TIER_HIGH_MAX: Final[float] = 20.0        # 15% <= LSF <= 20%: 40% reduction (60%)
# LSF > 20%: Contraindicated unless specifically proven lung dose < 30 Gy
