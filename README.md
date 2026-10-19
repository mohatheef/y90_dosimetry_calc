# Open Y-90 Dosimetry Suite

An open-source, scientifically rigorous clinical dosimetry calculation suite for **Yttrium-90 ($^{90}\text{Y}$) Selective Internal Radiation Therapy (SIRT) / Transarterial Radioembolization (TARE)**.

Calibrated against standard **SIR-Spheres (Sirtex)** and **TheraSpheres (Boston Scientific)** clinical monographs and EANM/CIRSE international guidelines.

---

## 🌟 Features & Implemented Models

1. **Partition Multi-Compartment Model (Personalized Dosimetry)**:
   - Solves simultaneous 3-compartment linear dose equations for **Tumor Target**, **Normal Liver Parenchyma**, and **Lungs**.
   - Solves safe prescribed activity bounded by normal liver dose limit ($D_{\text{NL}} \le 40 - 70\text{ Gy}$) and lung limit ($D_{\text{lung}} \le 30\text{ Gy}$).
   - Derives Tumor-to-Normal uptake ratio ($\text{TNR}$) from counts or direct user input.

2. **MIRD Single-Compartment Model (TheraSpheres / Glass)**:
   - Prescribes uniform absorbed dose to targeted liver mass/volume.
   - Calculates planned injected activity, vial activity compensation for residual delivery waste, and lung absorbed dose.

3. **BSA Model (SIR-Spheres / Resin)**:
   - Calculates empirical activity based on Du Bois or Mosteller Body Surface Area and percent tumor involvement ($\% \text{TI}$).
   - Supports whole liver vs. lobar/segmental scaling.
   - Evaluates Lung Shunt Fraction ($\text{LSF}$) reduction tiers ($<10\%$, $10-15\%$, $15-20\%$, $>20\%$).

4. **Lung Shunt Fraction (LSF) Workup**:
   - 2D Planar conjugate view geometric mean method: $\sqrt{\text{Ant} \times \text{Post}}$.
   - 3D SPECT/CT total volume count summation.
   - Automatic contraindication detection ($>20\%$).

5. **Local Deposition Model (LDM) Voxel Dosimetry**:
   - Voxel-based dose maps normalized to known administered activity.
   - Computes cumulative Dose-Volume Histograms (DVH) with $D_{50}, D_{70}, D_{90}, V_{30}, V_{50}, V_{100}, V_{120}$ metrics.
   - Includes 3D synthetic liver-tumor phantom generator for simulation and testing.

6. **Clinical Structured Report Generator**:
   - Generates standardized clinical treatment summaries in Markdown, JSON, and printable HTML/PDF format.

7. **Zero-Dependency Modern Web Application**:
   - Runs directly on Python 3 standard library with an interactive browser interface (Tailwind CSS, Chart.js for DVH curves).

---

## 📐 Mathematical Formulations

### 1. Partition Multi-Compartment Model
$$\text{Tumor Involvement [\%]} = \frac{V_{\text{tumor}}}{V_{\text{tumor}} + V_{\text{normal\_liver}}} \times 100$$

$$\text{TNR} = \frac{\text{TotalCounts}_{\text{tumor}} / M_{\text{tumor}}}{\text{TotalCounts}_{\text{normal}} / M_{\text{normal}}}$$

$$\text{Activity based on Normal Liver Limit } (D_{\text{NL}}): \quad A = \frac{D_{\text{NL}} \times [(\text{TNR} \times M_{\text{tumor}}) + M_{\text{normal}}]}{49.67 \times (1 - \text{LSF})}$$

$$\text{Activity based on Desired Tumor Dose } (D_T): \quad A = \frac{D_T \times [(\text{TNR} \times M_{\text{tumor}}) + M_{\text{normal}}]}{49.67 \times \text{TNR} \times (1 - \text{LSF})}$$

$$\text{Absorbed Dose to Tissue}: \quad D_{\text{tissue}} = \frac{49.67 \times A_{\text{tissue}}}{M_{\text{tissue}}}$$

---

### 2. MIRD Single-Compartment Model (TheraSpheres)
$$M_{\text{target}} [\text{kg}] = \frac{V_{\text{target}} [\text{cc}] \times 1.05}{1000}$$

$$A_{\text{calculated}} [\text{GBq}] = \frac{D_{\text{target}} [\text{Gy}] \times M_{\text{target}} [\text{kg}]}{50 \times (1 - \text{LSF})}$$

$$D_{\text{lung}} [\text{Gy}] = \frac{A_{\text{calculated}} \times \text{LSF} \times 50}{M_{\text{lung}} [\text{kg}]}$$

$$A_{\text{vial}} = \frac{A_{\text{calculated}}}{1 - \text{Waste\%}}$$

---

### 3. BSA Model (SIR-Spheres)
$$\text{BSA} [\text{m}^2] = 0.20247 \times (\text{Height [m]})^{0.725} \times (\text{Weight [kg]})^{0.425}$$

$$A_{\text{target}} [\text{GBq}] = \left[\text{BSA} - 0.2 + \frac{V_{\text{tumor}}}{V_{\text{target}}}\right] \times \frac{V_{\text{target}}}{V_{\text{liver}}}$$

**Lung Shunt Reduction Rules:**
- $\text{LSF} < 10\%$: 0% reduction
- $10\% \le \text{LSF} < 15\%$: 20% activity reduction
- $15\% \le \text{LSF} \le 20\%$: 40% activity reduction
- $\text{LSF} > 20\%$: Contraindicated

---

### 4. 2D Planar Geometric Mean Lung Shunt
$$G_{\text{lung}} = \sqrt{\text{Lung}_{\text{Ant}} \times \text{Lung}_{\text{Post}}}, \quad G_{\text{liver}} = \sqrt{\text{Liver}_{\text{Ant}} \times \text{Liver}_{\text{Post}}}$$

$$\text{LSF} [\%] = \frac{G_{\text{lung}}}{G_{\text{lung}} + G_{\text{liver}}} \times 100$$

---

## 🚀 Quickstart: Launching the Web App

Launch the interactive dashboard with a single command:

```bash
# Default (localhost:8080)
python3 web_app/server.py

# Or specify custom host/port:
python3 web_app/server.py [host] [port]
```

Then open your browser to:
👉 **`http://localhost:8080`** (or your designated host and port)

---

## 💻 Python SDK Usage

```python
from open_y90_dosimetry import (
    plan_partition_activity,
    plan_mird_activity,
    plan_bsa_activity,
    calculate_lung_shunt_planar
)

# 1. Partition Model Planning
res_pm = plan_partition_activity(
    tumor_volume_cc=250.0,
    target_volume_cc=1450.0,
    tnr=3.5,
    lung_shunt_pct=5.0,
    desired_tumor_dose_gy=140.0,
    normal_liver_dose_limit_gy=45.0
)
print(f"Recommended Activity: {res_pm.recommended_activity_gbq} GBq")
print(f"Tumor Dose: {res_pm.recommended_doses.tumor_dose_gy} Gy")
print(f"Normal Liver Dose: {res_pm.recommended_doses.normal_liver_dose_gy} Gy")
print(f"Lung Dose: {res_pm.recommended_doses.lung_dose_gy} Gy")

# 2. MIRD TheraSphere Planning
res_mird = plan_mird_activity(
    desired_dose_gy=120.0,
    target_volume_cc=1200.0,
    lung_shunt_pct=5.0,
    residual_waste_pct=3.0
)
print(f"MIRD Injected Activity: {res_mird.calculated_activity_gbq} GBq")
print(f"Vial Activity to Order: {res_mird.vial_activity_gbq} GBq")

# 3. BSA SIR-Spheres Planning
res_bsa = plan_bsa_activity(
    height_m=1.75,
    weight_kg=78.0,
    tumor_volume_cc=250.0,
    target_volume_cc=1500.0,
    lung_shunt_pct=6.5
)
print(f"BSA Prescribed Activity: {res_bsa.prescribed_activity_gbq} GBq")
```

---

## 🧪 Running Unit Tests

```bash
python3 -m unittest discover -s tests -v
```
