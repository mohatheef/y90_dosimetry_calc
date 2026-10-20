"""
Lightweight REST API & Static Server for Open Y-90 Dosimetry Web Application.
Built entirely on Python standard library (http.server, json, urllib).
No external pip dependencies required to launch.
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import sys
from urllib.parse import urlparse

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from open_y90_dosimetry import (
    plan_bsa_activity,
    plan_mird_activity,
    plan_partition_activity,
    calculate_lung_shunt_planar,
    calculate_lung_shunt_spect,
    calculate_voxel_ldm_dosimetry,
    generate_synthetic_phantom,
    PatientInfo,
    ClinicalReportData,
    generate_markdown_report,
    generate_html_report
)


class Y90RequestHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        super().__init__(*args, directory=static_dir, **kwargs)

    def _send_json_response(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        payload = json.loads(body.decode("utf-8")) if body else {}

        try:
            if path == "/api/bsa":
                res = plan_bsa_activity(
                    height_m=float(payload.get("height_m", 1.75)),
                    weight_kg=float(payload.get("weight_kg", 75.0)),
                    tumor_volume_cc=float(payload.get("tumor_volume_cc", 200.0)),
                    target_volume_cc=float(payload.get("target_volume_cc", 1400.0)),
                    total_liver_volume_cc=float(payload.get("total_liver_volume_cc", 1400.0)),
                    lung_shunt_pct=float(payload.get("lung_shunt_pct", 5.0)),
                    formula=payload.get("formula", "dubois")
                )
                self._send_json_response({
                    "bsa_m2": res.bsa_m2,
                    "tumor_involvement_pct": res.tumor_involvement_pct,
                    "unscaled_activity_gbq": res.unscaled_activity_gbq,
                    "target_scaling_fraction": res.target_scaling_fraction,
                    "calculated_activity_gbq": res.calculated_activity_gbq,
                    "lsf_reduction_pct": res.lsf_reduction_pct,
                    "lsf_status": res.lsf_status.value,
                    "prescribed_activity_gbq": res.prescribed_activity_gbq,
                    "prescribed_activity_mbq": res.prescribed_activity_mbq,
                    "estimated_lung_dose_gy": res.estimated_lung_dose_gy,
                    "lung_dose_safe": res.lung_dose_safe,
                    "notes": res.notes
                })

            elif path == "/api/mird":
                res = plan_mird_activity(
                    desired_dose_gy=float(payload.get("desired_dose_gy", 120.0)),
                    target_volume_cc=float(payload.get("target_volume_cc", 1200.0)),
                    lung_shunt_pct=float(payload.get("lung_shunt_pct", 5.0)),
                    residual_waste_pct=float(payload.get("residual_waste_pct", 3.0)),
                    exact_constant=bool(payload.get("exact_constant", False))
                )
                self._send_json_response({
                    "target_volume_cc": res.target_volume_cc,
                    "target_mass_kg": res.target_mass_kg,
                    "desired_dose_gy": res.desired_dose_gy,
                    "lung_shunt_pct": res.lung_shunt_pct,
                    "calculated_activity_gbq": res.calculated_activity_gbq,
                    "calculated_activity_mbq": res.calculated_activity_mbq,
                    "anticipated_waste_pct": res.anticipated_waste_pct,
                    "vial_activity_gbq": res.vial_activity_gbq,
                    "vial_activity_mbq": res.vial_activity_mbq,
                    "estimated_lung_dose_gy": res.estimated_lung_dose_gy,
                    "lung_dose_safe": res.lung_dose_safe,
                    "dose_constant_used": res.dose_constant_used,
                    "notes": res.notes
                })

            elif path == "/api/partition":
                res = plan_partition_activity(
                    tumor_volume_cc=float(payload.get("tumor_volume_cc", 250.0)),
                    target_volume_cc=float(payload.get("target_volume_cc", 1500.0)),
                    tnr=float(payload.get("tnr", 3.5)),
                    lung_shunt_pct=float(payload.get("lung_shunt_pct", 5.0)),
                    desired_tumor_dose_gy=float(payload.get("desired_tumor_dose_gy", 140.0)),
                    normal_liver_dose_limit_gy=float(payload.get("normal_liver_dose_limit_gy", 45.0)),
                    lung_dose_limit_gy=float(payload.get("lung_dose_limit_gy", 30.0))
                )
                self._send_json_response({
                    "tumor_volume_cc": res.tumor_volume_cc,
                    "normal_liver_volume_cc": res.normal_liver_volume_cc,
                    "total_target_volume_cc": res.total_target_volume_cc,
                    "tumor_mass_kg": res.tumor_mass_kg,
                    "normal_liver_mass_kg": res.normal_liver_mass_kg,
                    "tumor_involvement_pct": res.tumor_involvement_pct,
                    "tnr": res.tnr,
                    "lung_shunt_pct": res.lung_shunt_pct,
                    "activity_normal_liver_limit_gbq": res.activity_normal_liver_limit_gbq,
                    "activity_lung_limit_gbq": res.activity_lung_limit_gbq,
                    "activity_desired_tumor_dose_gbq": res.activity_desired_tumor_dose_gbq,
                    "recommended_activity_gbq": res.recommended_activity_gbq,
                    "recommended_activity_mbq": res.recommended_activity_mbq,
                    "recommended_doses": {
                        "activity_gbq": res.recommended_doses.activity_gbq,
                        "tumor_dose_gy": res.recommended_doses.tumor_dose_gy,
                        "normal_liver_dose_gy": res.recommended_doses.normal_liver_dose_gy,
                        "lung_dose_gy": res.recommended_doses.lung_dose_gy,
                        "tumor_activity_gbq": res.recommended_doses.tumor_activity_gbq,
                        "normal_liver_activity_gbq": res.recommended_doses.normal_liver_activity_gbq,
                        "lung_activity_gbq": res.recommended_doses.lung_activity_gbq
                    },
                    "normal_liver_safe": res.normal_liver_safe,
                    "lung_safe": res.lung_safe,
                    "therapeutic_tumor_dose": res.therapeutic_tumor_dose,
                    "notes": res.notes
                })

            elif path == "/api/lung_shunt":
                mode = payload.get("mode", "planar")
                if mode == "planar":
                    res = calculate_lung_shunt_planar(
                        lung_ant_counts=float(payload.get("lung_ant", 1500.0)),
                        lung_post_counts=float(payload.get("lung_post", 1600.0)),
                        liver_ant_counts=float(payload.get("liver_ant", 18000.0)),
                        liver_post_counts=float(payload.get("liver_post", 17500.0))
                    )
                else:
                    res = calculate_lung_shunt_spect(
                        total_lung_counts=float(payload.get("total_lung_counts", 6000.0)),
                        total_liver_counts=float(payload.get("total_liver_counts", 75000.0))
                    )
                self._send_json_response({
                    "method": res.method,
                    "lung_counts": res.lung_counts,
                    "liver_counts": res.liver_counts,
                    "lung_shunt_pct": res.lung_shunt_pct,
                    "status": res.status.value,
                    "recommended_activity_reduction_pct": res.recommended_activity_reduction_pct,
                    "is_safe_to_treat": res.is_safe_to_treat,
                    "clinical_recommendation": res.clinical_recommendation,
                    "notes": res.notes
                })

            elif path == "/api/voxel_ldm":
                matrix_size = int(payload.get("matrix_size", 24))
                tnr = float(payload.get("tnr", 3.5))
                phantom = generate_synthetic_phantom(
                    matrix_size=matrix_size,
                    tumor_radius_voxels=float(payload.get("tumor_radius", 4.0)),
                    liver_radius_voxels=float(payload.get("liver_radius", 9.0)),
                    tumor_to_normal_count_ratio=tnr
                )
                # Scale voxel volume to represent standard adult liver (~1400 cc)
                target_liver_cc = 1400.0
                n_liver_voxels = max(len(phantom.get("Normal Liver", [])), 1)
                voxel_cc = target_liver_cc / n_liver_voxels
                voxel_dim_mm = (voxel_cc * 1000.0) ** (1.0 / 3.0)

                res = calculate_voxel_ldm_dosimetry(
                    voxel_counts=phantom,
                    voxel_size_mm=(voxel_dim_mm, voxel_dim_mm, voxel_dim_mm),
                    injected_activity_gbq=float(payload.get("injected_activity_gbq", 1.8)),
                    residual_waste_pct=float(payload.get("residual_waste_pct", 3.0)),
                    lung_shunt_pct=float(payload.get("lung_shunt_pct", 5.0))
                )

                regions_out = {}
                for name, s in res.regions.items():
                    regions_out[name] = {
                        "volume_cc": s.volume_cc,
                        "mean_dose_gy": s.mean_dose_gy,
                        "min_dose_gy": s.min_dose_gy,
                        "max_dose_gy": s.max_dose_gy,
                        "d50_gy": s.d50_gy,
                        "d70_gy": s.d70_gy,
                        "d90_gy": s.d90_gy,
                        "v30_pct": s.v30_pct,
                        "v50_pct": s.v50_pct,
                        "v100_pct": s.v100_pct,
                        "v120_pct": s.v120_pct,
                        "dvh_curve": [{"dose": p.dose_gy, "pct": p.volume_pct} for p in s.dvh_curve[::2]]
                    }

                self._send_json_response({
                    "injected_activity_gbq": res.injected_activity_gbq,
                    "residual_waste_pct": res.residual_waste_pct,
                    "net_injected_activity_gbq": res.net_injected_activity_gbq,
                    "total_absorbed_energy_joules": res.total_absorbed_energy_joules,
                    "regions": regions_out,
                    "notes": res.notes
                })

            elif path == "/api/report":
                p_dict = payload.get("patient", {})
                patient = PatientInfo(
                    name=p_dict.get("name", "John Doe"),
                    patient_id=p_dict.get("patient_id", "MRN-109482"),
                    dob=p_dict.get("dob", "1960-03-24"),
                    sex=p_dict.get("sex", "M"),
                    height_m=float(p_dict.get("height_m", 1.75)),
                    weight_kg=float(p_dict.get("weight_kg", 80.0)),
                    referring_physician=p_dict.get("referring_physician", "Dr. A. Smith, IR"),
                    dosimetrist=p_dict.get("dosimetrist", "Medical Physicist")
                )
                rep_data = ClinicalReportData(
                    patient=patient,
                    procedure_name=payload.get("procedure_name", "Y-90 SIRT / TARE Treatment"),
                    microsphere_type=payload.get("microsphere_type", "SIR-Spheres (Resin)"),
                    treatment_intent=payload.get("treatment_intent", "Curative / Ablative"),
                    target_anatomy=payload.get("target_anatomy", "Right Hepatic Lobe"),
                    model_name=payload.get("model_name", "Partition Model"),
                    injected_activity_gbq=float(payload.get("injected_activity_gbq", 1.65)),
                    residual_waste_pct=float(payload.get("residual_waste_pct", 3.0)),
                    lung_shunt_pct=float(payload.get("lung_shunt_pct", 5.2)),
                    tumor_volume_cc=float(payload.get("tumor_volume_cc", 210.0)),
                    normal_liver_volume_cc=float(payload.get("normal_liver_volume_cc", 1250.0)),
                    tumor_to_normal_ratio=float(payload.get("tumor_to_normal_ratio", 3.5)),
                    tumor_mean_dose_gy=float(payload.get("tumor_mean_dose_gy", 142.0)),
                    normal_liver_mean_dose_gy=float(payload.get("normal_liver_mean_dose_gy", 40.5)),
                    lung_mean_dose_gy=float(payload.get("lung_mean_dose_gy", 4.3)),
                    safety_summary=payload.get("safety_summary", "Absorbed doses to normal liver and lungs are well within tolerance limits.")
                )
                md = generate_markdown_report(rep_data)
                html = generate_html_report(rep_data)
                self._send_json_response({"markdown": md, "html": html})

            else:
                self._send_json_response({"error": f"Unknown endpoint: {path}"}, status=404)

        except Exception as e:
            self._send_json_response({"error": str(e)}, status=400)


def run_server(host: str = "localhost", port: int = 8080):
    server_address = (host, port)
    httpd = HTTPServer(server_address, Y90RequestHandler)
    print(f"Y-90 Dosimetry Web App server running on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    h = "localhost"
    p = 8080
    if len(sys.argv) > 1:
        if sys.argv[1].isdigit():
            p = int(sys.argv[1])
        else:
            h = sys.argv[1]
            if len(sys.argv) > 2 and sys.argv[2].isdigit():
                p = int(sys.argv[2])
    run_server(host=h, port=p)
