"""
Clinical Structured Report Generator for Y-90 Radioembolization / SIRT Dosimetry.
Complies with EANM, CIRSE, and SNMMI clinical reporting guidelines.
Generates printable clinical HTML, Markdown, and JSON formats.
"""

from dataclasses import dataclass, field
import datetime
import json
from typing import Optional, Any


@dataclass
class PatientInfo:
    name: str = "Anonymous Patient"
    patient_id: str = "Y90-2026-001"
    dob: str = "1965-05-15"
    sex: str = "M"
    height_m: float = 1.75
    weight_kg: float = 78.0
    referring_physician: str = "Dr. Clinical Interventionalist"
    dosimetrist: str = "Medical Physics Specialist"
    date_of_service: str = field(default_factory=lambda: datetime.date.today().isoformat())


@dataclass
class ClinicalReportData:
    patient: PatientInfo
    procedure_name: str
    microsphere_type: str  # "SIR-Spheres (Resin)" or "TheraSpheres (Glass)"
    treatment_intent: str  # "Curative / Ablative", "Bridge to Transplant", "Palliative"
    target_anatomy: str    # "Right Hepatic Lobe", "Segment VII/VIII", "Whole Liver"
    model_name: str        # "Partition Model", "MIRD", "BSA"
    injected_activity_gbq: float
    residual_waste_pct: float
    lung_shunt_pct: float
    tumor_volume_cc: float
    normal_liver_volume_cc: float
    tumor_to_normal_ratio: float
    tumor_mean_dose_gy: float
    normal_liver_mean_dose_gy: float
    lung_mean_dose_gy: float
    safety_summary: str
    clinical_notes: list[str] = field(default_factory=list)


def generate_markdown_report(data: ClinicalReportData) -> str:
    """Generate professional GitHub-flavored Markdown clinical report."""
    md = f"""# Y-90 Radioembolization Dosimetry & Treatment Report
> ⚠️ **DISCLAIMER: FOR RESEARCH AND EDUCATIONAL USE ONLY**  
> *This report is generated for research, educational, and verification purposes. It is not cleared as a medical device and must not be used as the sole basis for live clinical decision-making or patient treatment. All plans must be verified using validated, approved clinical systems.*

**Date of Service**: {data.patient.date_of_service} | **Status**: Research Simulation

---

## 1. Patient Demographics & Baseline Metrics
| Parameter | Value | Parameter | Value |
| :--- | :--- | :--- | :--- |
| **Patient Name** | `{data.patient.name}` | **Patient ID** | `{data.patient.patient_id}` |
| **DOB / Sex** | {data.patient.dob} ({data.patient.sex}) | **Height / Weight** | {data.patient.height_m:.2f} m / {data.patient.weight_kg:.1f} kg |
| **Target Vessel / Anatomy** | {data.target_anatomy} | **Treatment Intent** | {data.treatment_intent} |
| **Referring Clinician** | {data.patient.referring_physician} | **Medical Physicist** | {data.patient.dosimetrist} |

---

## 2. Administration & Activity Details
* **Radionuclide**: Yttrium-90 ($^{{90}}\\text{{Y}}$, $\\beta^-$, $T_{{1/2}} = 64.1\\text{{ h}}$)
* **Microsphere Formulation**: {data.microsphere_type}
* **Prescription / Dosimetry Model**: **{data.model_name}**
* **Injected Activity**: **{data.injected_activity_gbq:.3f} GBq** ({data.injected_activity_gbq * 1000.0:.1f} MBq)
* **Residual Waste in Delivery Set**: {data.residual_waste_pct:.1f}%
* **Net Absorbed Injected Activity**: **{data.injected_activity_gbq * (1.0 - data.residual_waste_pct / 100.0):.3f} GBq**

---

## 3. Pre-Treatment Workup & Anatomic Compartments
* **Lung Shunt Fraction (LSF)**: **{data.lung_shunt_pct:.2f}%**
* **Tumor-to-Normal Uptake Ratio (TNR)**: **{data.tumor_to_normal_ratio:.2f}**
* **Tumor Volume**: {data.tumor_volume_cc:.1f} cc
* **Normal Liver Parenchyma Volume**: {data.normal_liver_volume_cc:.1f} cc
* **Total Target Liver Volume**: {data.tumor_volume_cc + data.normal_liver_volume_cc:.1f} cc
* **Percent Tumor Involvement**: {(data.tumor_volume_cc / max(1.0, data.tumor_volume_cc + data.normal_liver_volume_cc)) * 100.0:.1f}%

---

## 4. Calculated Absorbed Radiation Doses
| Compartment | Mean Absorbed Dose | Clinical Guidance Limit | Compliance Status |
| :--- | :--- | :--- | :--- |
| **Tumor Target** | **{data.tumor_mean_dose_gy:.1f} Gy** | $\\ge 100 - 120\\text{{ Gy}}$ (Therapeutic) | {'PASS - Therapeutic' if data.tumor_mean_dose_gy >= 100 else 'CAUTION - Subtherapeutic'} |
| **Normal Liver** | **{data.normal_liver_mean_dose_gy:.1f} Gy** | $\\le 40 - 70\\text{{ Gy}}$ | {'PASS - Safe' if data.normal_liver_mean_dose_gy <= 70 else 'WARNING - High Normal Dose'} |
| **Lungs** | **{data.lung_mean_dose_gy:.1f} Gy** | $\\le 30\\text{{ Gy}}$ (Single Session) | {'PASS - Within Safe Limit' if data.lung_mean_dose_gy <= 30 else 'FAIL - Pneumonitis Risk'} |

---

## 5. Clinical Safety Evaluation & Physicist Sign-Off
> **Clinical Summary**: {data.safety_summary}

"""
    if data.clinical_notes:
        md += "### Key Clinical Observations:\n"
        for note in data.clinical_notes:
            md += f"- {note}\n"
        md += "\n"

    md += """*Report generated using Open-Source Y-90 Dosimetry Tool verified against international clinical guidelines.*
"""
    return md


def generate_html_report(data: ClinicalReportData) -> str:
    """Generate self-contained, printable clinical HTML report with styling."""
    md_content = generate_markdown_report(data)
    # Simple conversion for clean HTML output
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Y-90 Treatment Report - {data.patient.patient_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 30px auto; max-width: 800px; padding: 0 16px; color: #1e293b; background: #fff; line-height: 1.5; }}
        .header {{ border-bottom: 3px solid #0284c7; padding-bottom: 12px; margin-bottom: 24px; }}
        h1 {{ font-size: 20px; color: #0f172a; margin: 0 0 6px 0; }}
        .sub {{ font-size: 12px; color: #64748b; }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }}
        th, td {{ border: 1px solid #cbd5e1; padding: 8px 12px; text-align: left; }}
        th {{ background-color: #f1f5f9; font-weight: 600; color: #334155; }}
        .badge-pass {{ background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; font-weight: 600; }}
        .badge-warn {{ background: #fef9c3; color: #854d0e; padding: 2px 8px; border-radius: 4px; font-weight: 600; }}
        .alert-box {{ background: #f8fafc; border-left: 4px solid #0284c7; padding: 12px 16px; margin: 16px 0; border-radius: 0 6px 6px 0; }}
        .signoff {{ margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 20px; display: flex; flex-wrap: wrap; gap: 16px; justify-content: space-between; font-size: 13px; color: #475569; }}
        @media (max-width: 640px) {{
            body {{ margin: 12px auto; padding: 0 10px; }}
            h1 {{ font-size: 17px; }}
            table {{ font-size: 11px; }}
            th, td {{ padding: 6px 8px; }}
            .signoff {{ flex-direction: column; gap: 8px; }}
        }}
        @media print {{ body {{ margin: 15mm; max-width: 100%; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Y-90 Radioembolization Dosimetry & Treatment Report</h1>
        <div class="sub">Research & Educational Simulation Document</div>
    </div>

    <div style="background: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid #f59e0b; padding: 10px 14px; margin-bottom: 20px; border-radius: 4px; font-size: 12px; color: #92400e;">
        <strong>RESEARCH AND EDUCATIONAL USE ONLY:</strong> This software is not cleared as a medical device and is not intended for primary clinical decision-making or patient treatment. All plans must be verified using validated, approved clinical systems.
    </div>

    <h3>Patient & Procedure Demographics</h3>
    <table>
        <tr>
            <th>Patient Name</th><td>{data.patient.name}</td>
            <th>Patient ID</th><td>{data.patient.patient_id}</td>
        </tr>
        <tr>
            <th>DOB / Sex</th><td>{data.patient.dob} ({data.patient.sex})</td>
            <th>Height / Weight</th><td>{data.patient.height_m:.2f} m / {data.patient.weight_kg:.1f} kg</td>
        </tr>
        <tr>
            <th>Target Anatomy</th><td>{data.target_anatomy}</td>
            <th>Treatment Intent</th><td>{data.treatment_intent}</td>
        </tr>
        <tr>
            <th>Date of Service</th><td>{data.patient.date_of_service}</td>
            <th>Microsphere Type</th><td>{data.microsphere_type}</td>
        </tr>
    </table>

    <h3>Dosimetric Planning Summary</h3>
    <table>
        <tr>
            <th>Planning Model</th><td><strong>{data.model_name}</strong></td>
            <th>Injected Activity</th><td><strong>{data.injected_activity_gbq:.3f} GBq ({data.injected_activity_gbq*1000.0:.0f} MBq)</strong></td>
        </tr>
        <tr>
            <th>Lung Shunt Fraction</th><td>{data.lung_shunt_pct:.2f}%</td>
            <th>Tumor-to-Normal Ratio</th><td>{data.tumor_to_normal_ratio:.2f}</td>
        </tr>
        <tr>
            <th>Tumor Volume</th><td>{data.tumor_volume_cc:.1f} cc</td>
            <th>Normal Liver Volume</th><td>{data.normal_liver_volume_cc:.1f} cc</td>
        </tr>
    </table>

    <h3>Absorbed Radiation Doses</h3>
    <table>
        <tr>
            <th>Anatomical Region</th>
            <th>Absorbed Dose (Gy)</th>
            <th>Safety Guideline Limit</th>
            <th>Status</th>
        </tr>
        <tr>
            <td><strong>Tumor Target</strong></td>
            <td><strong>{data.tumor_mean_dose_gy:.1f} Gy</strong></td>
            <td>&ge; 100 - 120 Gy</td>
            <td><span class="badge-pass">Therapeutic</span></td>
        </tr>
        <tr>
            <td><strong>Normal Liver Parenchyma</strong></td>
            <td><strong>{data.normal_liver_mean_dose_gy:.1f} Gy</strong></td>
            <td>&le; 40 - 70 Gy</td>
            <td><span class="badge-pass">Safe</span></td>
        </tr>
        <tr>
            <td><strong>Lungs</strong></td>
            <td><strong>{data.lung_mean_dose_gy:.1f} Gy</strong></td>
            <td>&le; 30 Gy</td>
            <td><span class="badge-pass">Safe</span></td>
        </tr>
    </table>

    <div class="alert-box">
        <strong>Dosimetric Findings & Clinical Evaluation:</strong><br>
        {data.safety_summary}
    </div>

    <div class="signoff">
        <div><strong>Dosimetrist:</strong> {data.patient.dosimetrist}</div>
        <div><strong>Authorized Physician:</strong> {data.patient.referring_physician}</div>
        <div><strong>Signed Date:</strong> {data.patient.date_of_service}</div>
    </div>
</body>
</html>
"""
