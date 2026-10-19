# Open Y-90 Dosimetry Suite (`y90_dosimetry_calc`)

> ⚠️ **DISCLAIMER: FOR RESEARCH AND EDUCATIONAL PURPOSES ONLY**  
> *This software is an open-source educational and research toolkit. It is **NOT** a certified medical device and has not been cleared by the FDA, CE, or any regulatory agency for clinical use. It is **NOT** validated for primary clinical decision-making, diagnosis, or patient treatment. Radioembolization treatment planning must always be independently computed, verified, and administered using manufacturer-approved clinical methods and supervised by an authorized medical physicist, nuclear medicine physician, or interventional radiologist.*

An open-source calculation suite and interactive web workbench for **Yttrium-90 ($^{90}\text{Y}$) Selective Internal Radiation Therapy (SIRT) / Transarterial Radioembolization (TARE)**.

This project implements standardized mathematical methods for resin and glass microspheres based on published peer-reviewed medical physics literature and manufacturer package inserts.

---

## 🌟 Key Features

1. **Partition Multi-Compartment Model (Personalized Dosimetry)**:
   - Solves simultaneous 3-compartment linear dose equations for **Tumor Target**, **Normal Liver Parenchyma**, and **Lungs**.
   - Computes safe prescribed activity bounded by normal liver dose limit ($D_{\text{NL}} \le 40 - 70\text{ Gy}$) and lung limit ($D_{\text{lung}} \le 30\text{ Gy}$).
   - Accommodates Tumor-to-Normal uptake ratio ($\text{TNR}$) from SPECT/PET counts or direct input.

2. **MIRD Single-Compartment Model (Glass Microspheres)**:
   - Target mass-based planning implementing standard MIRD formulations (as used with TheraSpheres).
   - Accounts for nominal target dose, vial activity adjustment for residual delivery waste, and lung absorbed dose checks.

3. **BSA Model (Resin Microspheres)**:
   - Empirical activity planning based on Du Bois or Mosteller Body Surface Area and percent tumor involvement ($\% \text{TI}$) for SIR-Spheres.
   - Supports whole liver vs. lobar/segmental scaling.
   - Automated Lung Shunt Fraction ($\text{LSF}$) activity reduction tiers ($<10\%$, $10-15\%$, $15-20\%$, $>20\%$).

4. **Lung Shunt Fraction ($\text{LSF}$) Workup**:
   - 2D Planar conjugate view geometric mean method: $\sqrt{\text{Ant} \times \text{Post}}$.
   - 3D SPECT/CT total volume count summation.
   - Automated clinical contraindication threshold checking ($>20\%$).

5. **Local Deposition Model (LDM) Voxel Dosimetry**:
   - Voxel-level dose maps normalized to known administered activity.
   - Computes cumulative Dose-Volume Histograms (DVH) with key metrics ($D_{50}, D_{70}, D_{90}, V_{30}, V_{50}, V_{100}, V_{120}$).
   - Includes a 3D synthetic liver-tumor phantom generator for simulation and testing.

6. **Structured Report Generator**:
   - Formats dosimetric calculations into standardized clinical summaries in Markdown, JSON, and printable HTML/PDF formats.

---

## 📦 Dependencies & Architecture

* **Backend / Core Engine**: **Zero Python package dependencies**. Runs entirely on Python 3.10+ standard library (`math`, `dataclasses`, `http.server`, `json`, `urllib`).
* **Frontend UI**: Standalone single-page web application using modern HTML5, with **Tailwind CSS**, **Chart.js** (for real-time DVH curves), and **Lucide Icons** loaded via CDN (requires internet access for styling and chart rendering).

---

## 📐 Mathematical Formulations

### 1. Partition Multi-Compartment Model
$$\text{Tumor Involvement [\%]} = \frac{V_{\text{tumor}}}{V_{\text{tumor}} + V_{\text{normal\_liver}}} \times 100$$

$$\text{TNR} = \frac{\text{TotalCounts}_{\text{tumor}} / M_{\text{tumor}}}{\text{TotalCounts}_{\text{normal}} / M_{\text{normal}}}$$

$$\text{Activity based on Normal Liver Limit } (D_{\text{NL}}): \quad A = \frac{D_{\text{NL}} \times [(\text{TNR} \times M_{\text{tumor}}) + M_{\text{normal}}]}{49.67 \times (1 - \text{LSF})}$$

$$\text{Activity based on Desired Tumor Dose } (D_T): \quad A = \frac{D_T \times [(\text{TNR} \times M_{\text{tumor}}) + M_{\text{normal}}]}{49.67 \times \text{TNR} \times (1 - \text{LSF})}$$

$$\text{Absorbed Dose to Tissue}: \quad D_{\text{tissue}} = \frac{49.67 \times A_{\text{tissue}}}{M_{\text{tissue}}}$$

---

### 2. MIRD Single-Compartment Model (Glass Microspheres)
$$M_{\text{target}} [\text{kg}] = \frac{V_{\text{target}} [\text{cc}] \times 1.05\text{ g/cm}^3}{1000}$$

$$A_{\text{calculated}} [\text{GBq}] = \frac{D_{\text{target}} [\text{Gy}] \times M_{\text{target}} [\text{kg}]}{50 \times (1 - \text{LSF})}$$

$$D_{\text{lung}} [\text{Gy}] = \frac{A_{\text{calculated}} \times \text{LSF} \times 50}{M_{\text{lung}} [\text{kg}]}$$

$$A_{\text{vial}} = \frac{A_{\text{calculated}}}{1 - (\text{Waste\%} / 100)}$$

---

### 3. BSA Model (Resin Microspheres)
$$\text{BSA} [\text{m}^2] = 0.20247 \times (\text{Height [m]})^{0.725} \times (\text{Weight [kg]})^{0.425}$$

$$A_{\text{target}} [\text{GBq}] = \left[\text{BSA} - 0.2 + \frac{V_{\text{tumor}}}{V_{\text{target}}}\right] \times \frac{V_{\text{target}}}{V_{\text{liver}}}$$

**Lung Shunt Activity Adjustment:**
- $\text{LSF} < 10\%$: 0% reduction
- $10\% \le \text{LSF} < 15\%$: 20% activity reduction
- $15\% \le \text{LSF} \le 20\%$: 40% activity reduction
- $\text{LSF} > 20\%$: Contraindicated per manufacturer product monograph

---

### 4. 2D Planar Geometric Mean Lung Shunt
$$G_{\text{lung}} = \sqrt{\text{Lung}_{\text{Ant}} \times \text{Lung}_{\text{Post}}}, \quad G_{\text{liver}} = \sqrt{\text{Liver}_{\text{Ant}} \times \text{Liver}_{\text{Post}}}$$

$$\text{LSF} [\%] = \frac{G_{\text{lung}}}{G_{\text{lung}} + G_{\text{liver}}} \times 100$$

---

## 🚀 Quickstart: Launching the Web App

Launch the local interactive dashboard:

```bash
# Default (localhost:8080)
python3 web_app/server.py

# Or specify custom host and port:
python3 web_app/server.py localhost 8765
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

# 1. Partition Model Planning (Research / Verification)
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

## 🧪 Automated Testing & Validation

The calculation suite includes automated unit tests validating calculations against published worked examples from manufacturer monographs and peer-reviewed literature:

```bash
python3 -m unittest discover -s tests -v
```

**Validated test cases include:**
* **SIR-Spheres Monograph Worked Example**: Validates Du Bois BSA calculation (1.75 m, 70 kg $\to 1.848\text{ m}^2$), 25% tumor involvement, unscaled activity (1.90 GBq), and 20% shunt reduction tier.
* **TheraSpheres User Manual Worked Example**: Validates target mass (1.05 kg), 120 Gy target dose with 5% LSF ($2.653\text{ GBq}$), and lung dose calculation ($6.63\text{ Gy}$).
* **Gulec et al. (2006) Partition Model Example**: Validates simultaneous compartment activity ($1.78\text{ GBq}$), normal liver limit (40 Gy), tumor absorbed dose ($160\text{ Gy}$ with $\text{TNR} = 4.0$), and lung dose ($4.42\text{ Gy}$).
* **2D Planar Conjugate View & 3D SPECT Shunt Tests**: Validates geometric mean equations and safety tier assignments.
* **Local Deposition Model (LDM) & DVH Curve Tests**: Validates 3D voxel dose integration, percentile extractions ($D_{50}, D_{70}, D_{90}$), and volume thresholds ($V_{100}$).

---

## 📚 References & Scientific Literature

1. **Chiesa C, Maccauro M, Romito R, et al.** *Need, feasibility and convenience of dosimetric treatment planning in liver selective internal radiation therapy with $^{90}\text{Y}$ microspheres: the EANM guidelines.* Eur J Nucl Med Mol Imaging. 2021;48(11):3706-3730. doi:10.1007/s00259-021-05441-w.
2. **Salem R, Thurston KG.** *Radioembolization with $^{90}\text{Yttrium}$ microspheres: a state-of-the-art review.* J Vasc Interv Radiol. 2006;17(8):1251-1278. doi:10.1097/01.rvi.0000232023.75372.40.
3. **Gulec SA, Mesoloras G, Dezarn WA, McNeillie P, Kennedy AS.** *Dosimetry for $^{90}\text{Y}$ microsphere therapy with visual and quantitative assessment of target tissue partitioning.* J Nucl Med. 2006;47(11):1858-1865.
4. **Ho S, Lau WY, Leung TW, et al.** *Partition model for estimating radiation doses from yttrium-90 microspheres in treating hepatic tumours.* Eur J Nucl Med. 1996;23(8):947-952. doi:10.1007/bf01084369.
5. **Sirtex Medical.** *SIR-Spheres (Yttrium-90 Microspheres) Product Monograph & Package Insert.* Sirtex Medical Limited.
6. **Boston Scientific.** *TheraSphere (Yttrium-90 Glass Microspheres) User Manual & Package Insert.* Boston Scientific Corporation.
7. **Du Bois D, Du Bois EF.** *A formula to estimate the approximate surface area if height and weight be known.* Arch Intern Med. 1916;17(6):863-871.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
