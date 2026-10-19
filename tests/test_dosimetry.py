import unittest
from open_y90_dosimetry import (
    calculate_bsa_dubois,
    plan_bsa_activity,
    plan_mird_activity,
    calculate_mird_dose_from_activity,
    plan_partition_activity,
    evaluate_partition_doses,
    calculate_tnr_from_counts,
    calculate_lung_shunt_planar,
    calculate_lung_shunt_spect,
    calculate_voxel_ldm_dosimetry,
    generate_synthetic_phantom,
    LSFStatus
)


class TestY90DosimetrySuite(unittest.TestCase):

    def test_bsa_dubois(self):
        # 1.75 m, 70 kg -> BSA ~ 1.84 m^2
        bsa = calculate_bsa_dubois(1.75, 70.0)
        self.assertAlmostEqual(bsa, 1.84, delta=0.02)

    def test_bsa_activity_planning(self):
        # Standard clinical case: 1.75 m, 75 kg, V_target = 1500 cc, V_tumor = 300 cc, LSF = 5%
        res = plan_bsa_activity(
            height_m=1.75,
            weight_kg=75.0,
            tumor_volume_cc=300.0,
            target_volume_cc=1500.0,
            total_liver_volume_cc=1500.0,
            lung_shunt_pct=5.0
        )
        self.assertGreater(res.bsa_m2, 1.8)
        self.assertAlmostEqual(res.tumor_involvement_pct, 20.0, delta=0.1)
        # unscaled activity: BSA - 0.2 + 0.20 = BSA
        self.assertAlmostEqual(res.unscaled_activity_gbq, res.bsa_m2, delta=0.01)
        self.assertEqual(res.lsf_reduction_pct, 0.0)
        self.assertTrue(res.lung_dose_safe)

    def test_bsa_lsf_tiers(self):
        # 12% LSF -> 20% reduction
        res_12 = plan_bsa_activity(1.70, 70.0, 100.0, 1000.0, lung_shunt_pct=12.0)
        self.assertEqual(res_12.lsf_reduction_pct, 20.0)
        self.assertEqual(res_12.lsf_status, LSFStatus.MODERATE)

        # 18% LSF -> 40% reduction
        res_18 = plan_bsa_activity(1.70, 70.0, 100.0, 1000.0, lung_shunt_pct=18.0)
        self.assertEqual(res_18.lsf_reduction_pct, 40.0)
        self.assertEqual(res_18.lsf_status, LSFStatus.HIGH)

        # 22% LSF -> Contraindicated
        res_22 = plan_bsa_activity(1.70, 70.0, 100.0, 1000.0, lung_shunt_pct=22.0)
        self.assertEqual(res_22.lsf_status, LSFStatus.CONTRAINDICATED)

    def test_mird_planning(self):
        # Desired dose 120 Gy, Target mass 1.0 kg, LSF 0%
        # Act = (120 * 1.0) / (50 * 1) = 2.40 GBq
        res = plan_mird_activity(desired_dose_gy=120.0, target_mass_kg=1.0, lung_shunt_pct=0.0)
        self.assertEqual(res.calculated_activity_gbq, 2.40)
        self.assertEqual(res.estimated_lung_dose_gy, 0.0)

        # With 10% LSF: Act = 120 / (50 * 0.9) = 2.667 GBq
        # Lung dose = 2.667 * 0.10 * 50 = 13.33 Gy
        res_lsf = plan_mird_activity(desired_dose_gy=120.0, target_mass_kg=1.0, lung_shunt_pct=10.0)
        self.assertAlmostEqual(res_lsf.calculated_activity_gbq, 2.667, delta=0.01)
        self.assertAlmostEqual(res_lsf.estimated_lung_dose_gy, 13.33, delta=0.1)
        self.assertTrue(res_lsf.lung_dose_safe)

    def test_mird_waste(self):
        # 10% residual waste
        res = plan_mird_activity(desired_dose_gy=100.0, target_mass_kg=1.0, residual_waste_pct=10.0)
        self.assertEqual(res.calculated_activity_gbq, 2.0)
        self.assertAlmostEqual(res.vial_activity_gbq, 2.0 / 0.9, delta=0.01)

    def test_partition_model(self):
        # V_target = 1500 cc, V_tumor = 300 cc, TNR = 3.0, LSF = 5%
        res = plan_partition_activity(
            tumor_volume_cc=300.0,
            target_volume_cc=1500.0,
            tnr=3.0,
            lung_shunt_pct=5.0,
            desired_tumor_dose_gy=150.0,
            normal_liver_dose_limit_gy=45.0
        )
        self.assertGreater(res.recommended_activity_gbq, 0.5)
        # Check tumor dose vs normal liver dose theorem: D_tumor = TNR * D_normal
        doses = res.recommended_doses
        self.assertAlmostEqual(doses.tumor_dose_gy / doses.normal_liver_dose_gy, 3.0, delta=0.05)
        self.assertLessEqual(doses.normal_liver_dose_gy, 45.1)
        self.assertLessEqual(doses.lung_dose_gy, 30.0)

    def test_lung_shunt_calculations(self):
        # 2D Planar conjugate: Lung ant=1000, post=1000 -> G=1000. Liver ant=9000, post=9000 -> G=9000
        # Total = 10000 -> LSF = 10%
        planar = calculate_lung_shunt_planar(1000, 1000, 9000, 9000)
        self.assertEqual(planar.lung_shunt_pct, 10.0)
        self.assertEqual(planar.recommended_activity_reduction_pct, 20.0)

        # 3D SPECT: Lung=5000, Liver=45000 -> LSF = 10%
        spect = calculate_lung_shunt_spect(5000, 45000)
        self.assertEqual(spect.lung_shunt_pct, 10.0)

    def test_voxel_ldm_and_dvh(self):
        # Synthetic phantom
        phantom = generate_synthetic_phantom(matrix_size=16, tumor_radius_voxels=3.0, liver_radius_voxels=6.0)
        res = calculate_voxel_ldm_dosimetry(
            voxel_counts=phantom,
            voxel_size_mm=(3.0, 3.0, 3.0),
            injected_activity_gbq=1.5,
            residual_waste_pct=5.0,
            lung_shunt_pct=5.0
        )
        self.assertIn("Tumor", res.regions)
        self.assertIn("Normal Liver", res.regions)
        t_stats = res.regions["Tumor"]
        nl_stats = res.regions["Normal Liver"]
        self.assertGreater(t_stats.mean_dose_gy, nl_stats.mean_dose_gy)
        self.assertGreater(len(t_stats.dvh_curve), 10)


class TestPublishedWorkedExamples(unittest.TestCase):
    """
    Verification tests against published worked examples from manufacturer package inserts
    and peer-reviewed literature (Gulec et al. 2006, Chiesa et al. 2021).
    """

    def test_sir_spheres_published_bsa_example(self):
        # Reference: SIR-Spheres Product Monograph / Package Insert
        # Patient: 1.75 m, 70 kg -> BSA = 0.20247 * 1.75^0.725 * 70^0.425 = 1.848 m^2
        # Tumor volume = 250 cc, Target liver = 1000 cc -> Tumor involvement = 25% (0.25)
        # Expected Unscaled Activity = 1.848 - 0.2 + 0.25 = 1.898 GBq (~1.90 GBq)
        res = plan_bsa_activity(
            height_m=1.75,
            weight_kg=70.0,
            tumor_volume_cc=250.0,
            target_volume_cc=1000.0,
            total_liver_volume_cc=1000.0,
            lung_shunt_pct=0.0
        )
        self.assertAlmostEqual(res.bsa_m2, 1.85, delta=0.01)
        self.assertAlmostEqual(res.tumor_involvement_pct, 25.0, delta=0.1)
        self.assertAlmostEqual(res.unscaled_activity_gbq, 1.90, delta=0.01)
        self.assertAlmostEqual(res.prescribed_activity_gbq, 1.90, delta=0.01)

        # With 12% Lung Shunt -> 20% Reduction
        res_shunt = plan_bsa_activity(
            height_m=1.75,
            weight_kg=70.0,
            tumor_volume_cc=250.0,
            target_volume_cc=1000.0,
            total_liver_volume_cc=1000.0,
            lung_shunt_pct=12.0
        )
        expected_reduced = 1.898 * 0.8  # ~1.518 GBq
        self.assertAlmostEqual(res_shunt.prescribed_activity_gbq, expected_reduced, delta=0.01)

    def test_therasphere_published_mird_example(self):
        # Reference: TheraSphere User Manual / Package Insert (Boston Scientific)
        # Target volume = 1000 cc, density = 1.05 g/cm3 -> Mass = 1.05 kg
        # Desired Dose = 120 Gy, Lung Shunt = 5% (0.05)
        # Formula: A = (D * M) / [50 * (1 - LSF)] = (120 * 1.05) / (50 * 0.95) = 126 / 47.5 = 2.6526 GBq
        res = plan_mird_activity(
            desired_dose_gy=120.0,
            target_volume_cc=1000.0,
            lung_shunt_pct=5.0,
            residual_waste_pct=0.0,
            exact_constant=False  # Standard TheraSphere 50.0 constant
        )
        self.assertAlmostEqual(res.target_mass_kg, 1.05, places=3)
        self.assertAlmostEqual(res.calculated_activity_gbq, 2.653, places=3)
        # Expected Lung Dose = 2.6526 * 0.05 * 50 / 1.0 = 6.63 Gy
        self.assertAlmostEqual(res.estimated_lung_dose_gy, 6.63, places=2)

    def test_partition_model_published_literature_example(self):
        # Reference: Gulec et al. 2006 (J Nucl Med) & Ho et al. 1996
        # Target volume = 1400 cc (Tumor = 200 cc, Normal Liver = 1200 cc)
        # Density = 1.05 g/cm3 -> Mass_T = 0.21 kg, Mass_N = 1.26 kg
        # TNR = 4.0, LSF = 5% (0.05)
        # Normal liver dose limit = 40.0 Gy
        # Denominator = (4.0 * 0.21) + 1.26 = 2.10 kg
        # Expected Activity = (40 * 2.10) / [49.67 * (1 - 0.05)] = 84 / 47.1865 = 1.780 GBq
        # Expected Tumor Dose = TNR * Normal Liver Dose = 4.0 * 40.0 = 160.0 Gy
        res = plan_partition_activity(
            tumor_volume_cc=200.0,
            target_volume_cc=1400.0,
            tnr=4.0,
            lung_shunt_pct=5.0,
            normal_liver_dose_limit_gy=40.0,
            desired_tumor_dose_gy=160.0
        )
        self.assertAlmostEqual(res.recommended_activity_gbq, 1.780, places=2)
        doses = res.recommended_doses
        self.assertAlmostEqual(doses.normal_liver_dose_gy, 40.0, places=1)
        self.assertAlmostEqual(doses.tumor_dose_gy, 160.0, places=1)
        # Expected Lung Dose = 1.780 * 0.05 * 49.67 / 1.0 = 4.42 Gy
        self.assertAlmostEqual(doses.lung_dose_gy, 4.42, places=1)


if __name__ == "__main__":
    unittest.main()

