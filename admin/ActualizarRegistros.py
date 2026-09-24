#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de informe de glucosa — GUI (Tkinter, single file).

Uso:
    python glucosa_app.py [ruta_al_json]

Sin argumentos abre la ventana vacía; usa Archivo → Abrir... o arrastra
el fichero a la ventana. Sólo depende de la stdlib (tkinter incluido).

Soporta múltiples medicamentos y operaciones masivas (historial de toma,
aplicar ánimos/dieta/meal a todos los registros de un rango).
"""
from __future__ import annotations

import json
import os
import random
import shutil
import string
import sys
import tkinter as tk
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


# --------------------------------------------------------------------------
# Constantes
# --------------------------------------------------------------------------

SLOTS = {
    "morning":   {"label": "Mañana",    "hour": 8},
    "afternoon": {"label": "Tarde",     "hour": 14},
    "evening":   {"label": "Noche",     "hour": 20},
    "night":     {"label": "Madrugada", "hour": 23},
}

SEVERITY_LABELS = {
    "":         "Ninguna",
    "mild":     "Leve",
    "moderate": "Moderada",
    "urgent":   "Urgente",
}


def _in_range(value: float, key: str) -> bool:
    if key == "tbr2": return value < 54
    if key == "tbr1": return 54 <= value < 70
    if key == "tir":  return 70 <= value <= 180
    if key == "tar1": return 180 < value <= 250
    if key == "tar2": return value > 250
    return False


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def gen_log_id() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"mlog-{int(datetime.now().timestamp() * 1000)}-{suffix}"


def gen_record_id() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=12))


def gen_med_id(nregistro: str = "", fuente: str = "manual") -> str:
    if nregistro and fuente == "cima":
        return f"cima-{nregistro}"
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"med-{int(datetime.now().timestamp() * 1000)}-{suffix}"


def calc_age(dob_str: str, ref: date) -> int:
    dob = date.fromisoformat(dob_str)
    return ref.year - dob.year - ((ref.month, ref.day) < (dob.month, dob.day))


def dt_for_slot(date_str: str, slot: str) -> str:
    d = date.fromisoformat(date_str)
    h = SLOTS[slot]["hour"]
    return datetime(d.year, d.month, d.day, h, 0, 0).isoformat(timespec="milliseconds") + "Z"


def slot_of(iso_str: str) -> str:
    try:
        h = datetime.fromisoformat(iso_str.replace("Z", "+00:00")).hour
    except Exception:
        return "morning"
    if 5 <= h < 12:  return "morning"
    if 12 <= h < 18: return "afternoon"
    if 18 <= h < 22: return "evening"
    return "night"


def parse_float_or_none(s) -> float | None:
    if s is None:
        return None
    s = str(s).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_int_or_none(s) -> int | None:
    if s is None:
        return None
    s = str(s).strip()
    if s == "":
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def fmt_glucose(v) -> str:
    return "-" if v is None else f"{v:g}"


def valid_date_or_none(s: str) -> str | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        date.fromisoformat(s)
        return s
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Persistencia
# --------------------------------------------------------------------------

def load_json(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str | Path, data: dict) -> None:
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def backup_file(path: str | Path) -> Path | None:
    path = Path(path)
    if not path.exists():
        return None
    bdir = path.parent / "backups"
    bdir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = bdir / f"{path.stem}_{ts}.json"
    shutil.copy2(path, dest)
    return dest


# --------------------------------------------------------------------------
# Canonical
# --------------------------------------------------------------------------

class Canonical:
    def __init__(self, data: dict) -> None:
        records = data.get("records", []) or []
        meds = data.get("medicamentos", []) or []

        self.moods = sorted({m for r in records for m in (r.get("moods") or [])})
        self.meals = sorted({r["meal"] for r in records if r.get("meal")})
        self.exercise_types = sorted({
            r["exercise"]["type"] for r in records
            if isinstance(r.get("exercise"), dict) and r["exercise"].get("type")
        })
        self.severities = sorted({r["severity"] for r in records if r.get("severity")})
        self.diet_contexts = sorted({
            d for r in records for d in (r.get("dietContext") or [])
        })
        self.medicine_units = sorted({
            m.get("unidadPredeterminada") for m in meds
            if m.get("unidadPredeterminada")
        })

        if not self.meals: self.meals = ["breakfast", "lunch", "dinner", "snack"]
        if not self.exercise_types: self.exercise_types = ["walking"]
        if not self.severities: self.severities = ["mild", "moderate", "urgent"]
        if not self.diet_contexts: self.diet_contexts = ["plan_recomendado"]
        if not self.medicine_units: self.medicine_units = ["ui"]

    def all_medicine_units(self) -> list[str]:
        base = ["ui", "U", "mg", "ml", "unidades"]
        out = list(self.medicine_units)
        for b in base:
            if b not in out:
                out.append(b)
        return out


# --------------------------------------------------------------------------
# Cálculos
# --------------------------------------------------------------------------

def glucose_values(record: dict) -> list[float]:
    vals = []
    for k in ("glucoseBefore", "glucoseAfter", "glucoseNight"):
        v = record.get(k)
        if isinstance(v, (int, float)):
            vals.append(float(v))
    return vals


def suggest_severity(record: dict) -> str | None:
    vals = glucose_values(record)
    if not vals:
        return None
    m = max(vals)
    if m > 250: return "urgent"
    if m > 180: return "moderate"
    if m > 160: return "mild"
    return None


def recalc_tir(data: dict) -> None:
    values: list[float] = []
    for r in data.get("records", []):
        values.extend(glucose_values(r))

    counts = {k: 0 for k in ("tbr2", "tbr1", "tir", "tar1", "tar2")}
    for v in values:
        for k in counts:
            if _in_range(v, k):
                counts[k] += 1
                break

    total = len(values) or 1
    tr = data.setdefault("tiempoEnRango", {})
    cats = tr.setdefault("categorias", [])
    existing = {c.get("key"): c for c in cats}
    defaults = [
        ("tbr2", "Muy bajo", "Muy bajo (<54 mg/dL)"),
        ("tbr1", "Bajo",     "Bajo (54-69 mg/dL)"),
        ("tir",  "En rango", "En rango (70-180 mg/dL)"),
        ("tar1", "Alto",     "Alto (181-250 mg/dL)"),
        ("tar2", "Muy alto", "Muy alto (>250 mg/dL)"),
    ]
    new_cats = []
    for key, short, label in defaults:
        c = existing.get(key) or {
            "key": key, "shortLabel": short, "label": label,
            "value": "", "extrapolated": False,
        }
        c["count"] = counts[key]
        c["pct"] = counts[key] / total * 100.0
        new_cats.append(c)
    tr["categorias"] = new_cats


def get_record(data: dict, date_str: str) -> dict | None:
    for r in data.get("records", []):
        if r.get("date") == date_str:
            return r
    return None


def ensure_record(data: dict, date_str: str) -> dict:
    r = get_record(data, date_str)
    if r:
        return r

    last = data["records"][-1] if data.get("records") else {}
    weather = deepcopy(last.get("weather") or {})
    weather["date"] = date_str
    for k in ("temp", "humidity", "precipitation", "pressure", "wind"):
        if k in weather:
            weather[k] = None
    weather.setdefault("location", "")

    p = data.get("patient", {})
    rec = {
        "id": gen_record_id(),
        "patientId": p.get("id", ""),
        "profile": {
            "diabetesType": p.get("diabetesType", ""),
            "patientGroup": p.get("patientGroup", ""),
            "pregnancyStatus": p.get("pregnancyStatus", ""),
            "pregnancyCategory": p.get("pregnancyCategory", ""),
        },
        "date": date_str,
        "meal": (data["records"][-1]["meal"] if data.get("records") else "breakfast"),
        "glucoseBefore": None,
        "glucoseAfter": None,
        "glucoseNight": None,
        "exercise": None,
        "comments": "",
        "mood": None,
        "moods": [],
        "weather": weather,
        "example": False,
        "severity": None,
        "createdAt": now_iso(),
        "dietContext": [],
        "medicationLogIds": [],
    }
    data.setdefault("records", []).append(rec)
    data["records"].sort(key=lambda x: x.get("date", ""))
    return rec


def _new_log(med_id: str, med_name: str, dose: str, unit: str,
             fecha_iso: str, omitted: bool, note: str) -> dict:
    return {
        "id": gen_log_id(),
        "medId": med_id,
        "nombre": med_name,
        "dosis": str(dose),
        "unidad": unit,
        "fecha": fecha_iso,
        "omitida": bool(omitted),
        "nota": note,
    }


def add_medication_log(data: dict, med_id: str, dose: str, unit: str,
                       date_str: str, slot: str,
                       omitted: bool = False, note: str = "") -> dict:
    med = next((m for m in data.get("medicamentos", []) if m.get("id") == med_id), None)
    log = _new_log(med_id, (med or {}).get("nombre", ""), dose, unit,
                   dt_for_slot(date_str, slot), omitted, note)
    data.setdefault("registroTomas", []).append(log)
    rec = ensure_record(data, date_str)
    rec.setdefault("medicationLogIds", []).append(log["id"])
    return log


def add_medication_log_to_record(data: dict, record: dict, med_id: str,
                                 dose: str, unit: str, slot: str,
                                 omitted: bool = False, note: str = "") -> dict:
    med = next((m for m in data.get("medicamentos", []) if m.get("id") == med_id), None)
    log = _new_log(med_id, (med or {}).get("nombre", ""), dose, unit,
                   dt_for_slot(record["date"], slot), omitted, note)
    data.setdefault("registroTomas", []).append(log)
    record.setdefault("medicationLogIds", []).append(log["id"])
    return log


def save_all(data: dict, path: str | Path) -> None:
    recalc_tir(data)
    data["totalRegistros"] = len(data.get("records", []))
    data["exportedAt"] = now_iso()

    p = data.get("patient", {})
    if p.get("dateOfBirth"):
        data["edadEnEsteInforme"] = calc_age(p["dateOfBirth"], date.today())

    if "medicamentos" in data:
        p["medicines"] = deepcopy(data["medicamentos"])
    if "registroTomas" in data:
        p["medicationLog"] = deepcopy(data["registroTomas"])

    backup_file(path)
    save_json(path, data)


# --------------------------------------------------------------------------
# Operaciones masivas
# --------------------------------------------------------------------------

def _in_date_range(d: str | None, date_from: str | None, date_to: str | None) -> bool:
    if not d:
        return False
    if date_from and d < date_from:
        return False
    if date_to and d > date_to:
        return False
    return True


def _find_med(data: dict, med_id: str) -> dict | None:
    return next((m for m in data.get("medicamentos", []) if m.get("id") == med_id), None)


def bulk_generate_medication_history(
    data: dict, med_id: str, slot: str, dose: str, unit: str,
    date_from: str | None = None, date_to: str | None = None,
    replace_existing: bool = False, skip_existing_slot: bool = True,
    omitted: bool = False, note: str = "",
) -> dict:
    med = _find_med(data, med_id)
    if not med:
        return {"created": 0, "removed": 0, "skipped": 0, "total": 0,
                "error": "Medicamento no encontrado"}

    target_records = [
        r for r in data.get("records", [])
        if _in_date_range(r.get("date"), date_from, date_to)
    ]
    if not target_records:
        return {"created": 0, "removed": 0, "skipped": 0, "total": 0}

    target_dates = {r["date"] for r in target_records}

    removed = 0
    if replace_existing:
        removed_ids: set[str] = set()
        kept_logs = []
        for log in data.get("registroTomas", []):
            log_date = (log.get("fecha") or "")[:10]
            if log.get("medId") == med_id and log_date in target_dates:
                removed += 1
                removed_ids.add(log.get("id"))
                continue
            kept_logs.append(log)
        data["registroTomas"] = kept_logs
        for r in target_records:
            ids = r.get("medicationLogIds") or []
            if ids:
                r["medicationLogIds"] = [i for i in ids if i not in removed_ids]

    existing_keys: set[tuple[str, str]] = set()
    for log in data.get("registroTomas", []):
        if log.get("medId") == med_id:
            d = (log.get("fecha") or "")[:10]
            s = slot_of(log.get("fecha") or "")
            existing_keys.add((d, s))

    created = 0
    skipped = 0
    for r in target_records:
        d = r.get("date")
        if skip_existing_slot and (d, slot) in existing_keys:
            skipped += 1
            continue
        add_medication_log_to_record(data, r, med_id, dose, unit, slot,
                                     omitted=omitted, note=note)
        existing_keys.add((d, slot))
        created += 1

    return {"created": created, "removed": removed, "skipped": skipped,
            "total": len(target_records)}


def bulk_delete_medication_logs(
    data: dict, med_id: str,
    date_from: str | None = None, date_to: str | None = None,
) -> int:
    removed_ids: set[str] = set()
    kept_logs = []
    for log in data.get("registroTomas", []):
        d = (log.get("fecha") or "")[:10]
        if log.get("medId") == med_id and _in_date_range(d, date_from, date_to):
            removed_ids.add(log.get("id"))
            continue
        kept_logs.append(log)
    data["registroTomas"] = kept_logs

    for r in data.get("records", []):
        ids = r.get("medicationLogIds") or []
        if ids and any(i in removed_ids for i in ids):
            r["medicationLogIds"] = [i for i in ids if i not in removed_ids]
    return len(removed_ids)


def bulk_apply_list_field(
    data: dict, field: str, values: list[str],
    date_from: str | None = None, date_to: str | None = None,
    mode: str = "replace",
) -> int:
    count = 0
    for r in data.get("records", []):
        if not _in_date_range(r.get("date"), date_from, date_to):
            continue
        if mode == "replace":
            r[field] = list(values)
        else:
            cur = list(r.get(field) or [])
            for v in values:
                if v not in cur:
                    cur.append(v)
            r[field] = cur
        count += 1
    return count


def bulk_apply_scalar_field(
    data: dict, field: str, value,
    date_from: str | None = None, date_to: str | None = None,
) -> int:
    count = 0
    for r in data.get("records", []):
        if not _in_date_range(r.get("date"), date_from, date_to):
            continue
        r[field] = value
        count += 1
    return count


# --------------------------------------------------------------------------
# Diálogo de medicamento
# --------------------------------------------------------------------------

class MedicineDialog(tk.Toplevel):
    def __init__(self, parent, canonical: Canonical,
                 existing: dict | None = None):
        super().__init__(parent)
        self.title("Editar medicamento" if existing else "Añadir medicamento")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.result: dict | None = None
        self._existing = existing or {}

        self.vars = {
            "id":                     tk.StringVar(value=self._existing.get("id", "")),
            "nregistro":              tk.StringVar(value=self._existing.get("nregistro", "")),
            "nombre":                 tk.StringVar(value=self._existing.get("nombre", "")),
            "principio_activo":       tk.StringVar(value=self._existing.get("principio_activo", "—")),
            "laboratorio":            tk.StringVar(value=self._existing.get("laboratorio", "—")),
            "clase":                  tk.StringVar(value=self._existing.get("clase", "—")),
            "via":                    tk.StringVar(value=self._existing.get("via", "—")),
            "unidad":                 tk.StringVar(value=self._existing.get("unidad", "mg")),
            "dosisPredeterminada":    tk.StringVar(value=self._existing.get("dosisPredeterminada", "10")),
            "unidadPredeterminada":   tk.StringVar(value=self._existing.get("unidadPredeterminada",
                                                                            (canonical.medicine_units or ["ui"])[0])),
            "fuente":                 tk.StringVar(value=self._existing.get("fuente", "cima")),
            "riesgo_hipo":            tk.BooleanVar(value=bool(self._existing.get("riesgo_hipo", False))),
        }

        body = ttk.Frame(self, padding=12)
        body.pack(fill="both", expand=True)

        def row(r: int, label: str, widget):
            ttk.Label(body, text=label).grid(row=r, column=0, sticky="w", pady=3)
            widget.grid(row=r, column=1, sticky="we", padx=4, pady=3)

        row(0, "ID interno:", ttk.Entry(body, textvariable=self.vars["id"], width=28))
        row(1, "Nombre:", ttk.Entry(body, textvariable=self.vars["nombre"], width=60))
        row(2, "Nº registro (nregistro):", ttk.Entry(body, textvariable=self.vars["nregistro"], width=20))
        row(3, "Fuente:", ttk.Combobox(body, textvariable=self.vars["fuente"],
                                       values=["cima", "manual"], state="readonly", width=14))
        row(4, "Principio activo:", ttk.Entry(body, textvariable=self.vars["principio_activo"], width=40))
        row(5, "Laboratorio:", ttk.Entry(body, textvariable=self.vars["laboratorio"], width=40))
        row(6, "Clase:", ttk.Entry(body, textvariable=self.vars["clase"], width=40))
        row(7, "Vía:", ttk.Entry(body, textvariable=self.vars["via"], width=40))
        row(8, "Unidad base:", ttk.Entry(body, textvariable=self.vars["unidad"], width=14))
        row(9, "Dosis por defecto:", ttk.Entry(body, textvariable=self.vars["dosisPredeterminada"], width=14))
        row(10, "Unidad por defecto:",
            ttk.Combobox(body, textvariable=self.vars["unidadPredeterminada"],
                         values=canonical.all_medicine_units(), width=14))
        ttk.Checkbutton(body, text="Riesgo de hipoglucemia",
                        variable=self.vars["riesgo_hipo"]).grid(
            row=11, column=1, sticky="w", padx=4, pady=3)

        ttk.Label(body, text="Si el ID está vacío se genera automáticamente "
                             "(cima-<nregistro> si la fuente es cima).",
                  foreground="#666", wraplength=520).grid(
            row=12, column=0, columnspan=2, sticky="w", pady=(6, 0))

        btns = ttk.Frame(self, padding=(12, 6))
        btns.pack(fill="x")
        ttk.Button(btns, text="Guardar", command=self._on_ok).pack(side="right", padx=4)
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(side="right")

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self.destroy())
        body.columnconfigure(1, weight=1)
        self.update_idletasks()
        self.geometry(f"+{parent.winfo_rootx() + 80}+{parent.winfo_rooty() + 80}")

    def _on_ok(self):
        nombre = self.vars["nombre"].get().strip()
        if not nombre:
            messagebox.showerror("Falta nombre", "El nombre no puede estar vacío.", parent=self)
            return
        nreg = self.vars["nregistro"].get().strip()
        fuente = self.vars["fuente"].get().strip() or "cima"
        mid = self.vars["id"].get().strip()
        if not mid:
            mid = gen_med_id(nreg, fuente)

        result = {
            "id": mid,
            "nregistro": nreg,
            "nombre": nombre,
            "marcas": self._existing.get("marcas") or nombre,
            "principio_activo": self.vars["principio_activo"].get().strip() or "—",
            "laboratorio": self.vars["laboratorio"].get().strip() or "—",
            "clase": self.vars["clase"].get().strip() or "—",
            "via": self.vars["via"].get().strip() or "—",
            "unidad": self.vars["unidad"].get().strip() or "mg",
            "riesgo_hipo": bool(self.vars["riesgo_hipo"].get()),
            "fuente": fuente,
            "posibles_dosis": self._existing.get("posibles_dosis") or [
                {"valor": self.vars["dosisPredeterminada"].get().strip() or "0",
                 "unidad": self.vars["unidadPredeterminada"].get().strip() or "ui"}
            ],
            "dosisPredeterminada": self.vars["dosisPredeterminada"].get().strip() or "0",
            "unidadPredeterminada": self.vars["unidadPredeterminada"].get().strip() or "ui",
        }
        self.result = result
        self.destroy()


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------

class GlucosaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestor de informe de glucosa")
        self.geometry("1160x820")
        self.minsize(980, 640)

        self.path: Path | None = None
        self.data: dict = {}
        self.canonical: Canonical | None = None
        self.dirty: bool = False
        self._current_record: dict | None = None
        self._current_medlog_ids: list[str] = []

        # Vars del formulario diario
        self._daily_date_var = tk.StringVar(value=date.today().isoformat())
        self._glucose_before_var = tk.StringVar()
        self._glucose_after_var = tk.StringVar()
        self._glucose_night_var = tk.StringVar()
        self._meal_var = tk.StringVar()
        self._exercise_type_var = tk.StringVar()
        self._exercise_duration_var = tk.StringVar()
        self._exercise_steps_var = tk.StringVar()
        self._severity_var = tk.StringVar()
        self._log_count_var = tk.StringVar(value="Tomas asociadas: 0")
        self._mood_vars: dict[str, tk.BooleanVar] = {}
        self._diet_vars: dict[str, tk.BooleanVar] = {}

        # Vars de asignación de medicación (individual)
        self._med_date_var = tk.StringVar(value=date.today().isoformat())
        self._med_id_var = tk.StringVar()
        self._med_slot_var = tk.StringVar(value="morning")
        self._med_dose_var = tk.StringVar()
        self._med_unit_var = tk.StringVar()
        self._med_omitted_var = tk.BooleanVar(value=False)
        self._med_note_var = tk.StringVar()

        # Vars de operaciones masivas
        self._bulk_med_id_var = tk.StringVar()
        self._bulk_med_slot_var = tk.StringVar(value="morning")
        self._bulk_med_dose_var = tk.StringVar()
        self._bulk_med_unit_var = tk.StringVar()
        self._bulk_med_omitted_var = tk.BooleanVar(value=False)
        self._bulk_med_note_var = tk.StringVar()
        self._bulk_med_from_var = tk.StringVar()
        self._bulk_med_to_var = tk.StringVar()
        self._bulk_med_all_var = tk.BooleanVar(value=True)
        self._bulk_med_replace_var = tk.BooleanVar(value=False)
        self._bulk_med_skip_var = tk.BooleanVar(value=True)

        self._bulk_moods_from_var = tk.StringVar()
        self._bulk_moods_to_var = tk.StringVar()
        self._bulk_moods_all_var = tk.BooleanVar(value=True)
        self._bulk_moods_mode_var = tk.StringVar(value="replace")
        self._bulk_mood_vars: dict[str, tk.BooleanVar] = {}

        self._bulk_diet_from_var = tk.StringVar()
        self._bulk_diet_to_var = tk.StringVar()
        self._bulk_diet_all_var = tk.BooleanVar(value=True)
        self._bulk_diet_mode_var = tk.StringVar(value="replace")
        self._bulk_diet_vars: dict[str, tk.BooleanVar] = {}

        self._bulk_meal_from_var = tk.StringVar()
        self._bulk_meal_to_var = tk.StringVar()
        self._bulk_meal_all_var = tk.BooleanVar(value=True)
        self._bulk_meal_value_var = tk.StringVar()

        self._status_var = tk.StringVar(value="Listo. Archivo → Abrir... para cargar un JSON.")

        self._build_menu()
        self._build_ui()
        self._build_statusbar()

        self.protocol("WM_DELETE_WINDOW", self.on_exit)

        self.after(120, self._auto_open_if_single)

    # -------------------- Construcción de la UI --------------------

    def _build_menu(self):
        menubar = tk.Menu(self)

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Abrir...", command=self.on_open, accelerator="Ctrl+O")
        filemenu.add_command(label="Guardar", command=self.on_save, accelerator="Ctrl+S")
        filemenu.add_command(label="Guardar como...", command=self.on_save_as)
        filemenu.add_separator()
        filemenu.add_command(label="Salir", command=self.on_exit)
        menubar.add_cascade(label="Archivo", menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Acerca de", command=self._show_about)
        menubar.add_cascade(label="Ayuda", menu=helpmenu)

        self.config(menu=menubar)
        self.bind_all("<Control-o>", lambda e: self.on_open())
        self.bind_all("<Control-s>", lambda e: self.on_save())

    def _build_ui(self):
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True, padx=6, pady=(6, 0))

        self._tab_patient = ttk.Frame(self._notebook, padding=10)
        self._tab_medicines = ttk.Frame(self._notebook, padding=10)
        self._tab_assign = ttk.Frame(self._notebook, padding=10)
        self._tab_daily = ttk.Frame(self._notebook, padding=10)
        self._tab_bulk = ttk.Frame(self._notebook, padding=10)
        self._tab_tir = ttk.Frame(self._notebook, padding=10)
        self._tab_records = ttk.Frame(self._notebook, padding=10)

        self._notebook.add(self._tab_patient, text="Paciente")
        self._notebook.add(self._tab_medicines, text="Medicamentos")
        self._notebook.add(self._tab_assign, text="Asignar medicación")
        self._notebook.add(self._tab_daily, text="Registro diario")
        self._notebook.add(self._tab_bulk, text="Operaciones masivas")
        self._notebook.add(self._tab_tir, text="Tiempo en rango")
        self._notebook.add(self._tab_records, text="Registros")

        self._build_patient_tab()
        self._build_medicines_tab()
        self._build_assign_tab()
        self._build_daily_tab()
        self._build_bulk_tab()
        self._build_tir_tab()
        self._build_records_tab()

    def _build_statusbar(self):
        bar = ttk.Frame(self, padding=(8, 4))
        bar.pack(fill="x", side="bottom")
        ttk.Label(bar, textvariable=self._status_var, anchor="w").pack(side="left", fill="x", expand=True)

    # -------- Pestaña Paciente --------

    def _build_patient_tab(self):
        f = self._tab_patient
        self._patient_text = tk.Text(f, wrap="word", height=20, relief="flat", bg=self.cget("bg"))
        self._patient_text.pack(fill="both", expand=True)
        self._patient_text.configure(state="disabled")

    def _refresh_patient(self):
        t = self._patient_text
        t.configure(state="normal")
        t.delete("1.0", "end")
        if not self.data:
            t.insert("1.0", "(Sin datos cargados)")
        else:
            p = self.data.get("patient", {})
            lines = [
                f"Nombre:              {p.get('name', '')}",
                f"DNI:                 {p.get('dni', '')}",
                f"Seguridad Social:    {p.get('socialSecurity', '') or '-'}",
                f"Fecha nacimiento:    {p.get('dateOfBirth', '')}",
                f"Edad en el informe:  {self.data.get('edadEnEsteInforme', '')}",
                f"Género:              {p.get('gender', '')}",
                f"Tipo de diabetes:    {p.get('diabetesType', '')}",
                f"Grupo de paciente:   {p.get('patientGroup', '')}",
                f"Embarazo:            {p.get('pregnancyStatus', '')}",
                f"Unidad de glucosa:   {p.get('glucoseUnit', '')}",
                "",
                f"Medicamentos:        {len(self.data.get('medicamentos', []))}",
                f"Registros totales:   {self.data.get('totalRegistros', len(self.data.get('records', [])))}",
                f"Tomas registradas:   {len(self.data.get('registroTomas', []))}",
                f"Exportado:           {self.data.get('exportedAt', '')}",
            ]
            t.insert("1.0", "\n".join(lines))
        t.configure(state="disabled")

    # -------- Pestaña Medicamentos --------

    def _build_medicines_tab(self):
        f = self._tab_medicines

        toolbar = ttk.Frame(f)
        toolbar.pack(fill="x", pady=(0, 6))
        ttk.Button(toolbar, text="Añadir...", command=self._on_add_medicine).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Editar...", command=self._on_edit_medicine).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Eliminar", command=self._on_delete_medicine).pack(side="left", padx=2)
        ttk.Label(toolbar, text="(doble clic en una fila para editar)",
                  foreground="#666").pack(side="left", padx=12)

        cols = ("id", "nombre", "dosis", "unidad", "riesgo", "fuente")
        self._med_tree = ttk.Treeview(f, columns=cols, show="headings", height=16)
        for c, w, txt in (
            ("id", 170, "ID"),
            ("nombre", 420, "Nombre"),
            ("dosis", 70, "Dosis"),
            ("unidad", 70, "Unidad"),
            ("riesgo", 80, "Riesgo hipo"),
            ("fuente", 80, "Fuente"),
        ):
            self._med_tree.heading(c, text=txt)
            self._med_tree.column(c, width=w, anchor="w")
        self._med_tree.pack(fill="both", expand=True, side="left")
        sb = ttk.Scrollbar(f, orient="vertical", command=self._med_tree.yview)
        sb.pack(side="right", fill="y")
        self._med_tree.configure(yscrollcommand=sb.set)
        self._med_tree.bind("<Double-1>", lambda e: self._on_edit_medicine())

    def _refresh_medicines(self):
        self._med_tree.delete(*self._med_tree.get_children())
        for m in self.data.get("medicamentos", []):
            self._med_tree.insert("", "end", values=(
                m.get("id", ""),
                m.get("nombre", ""),
                m.get("dosisPredeterminada", ""),
                m.get("unidadPredeterminada", ""),
                "Sí" if m.get("riesgo_hipo") else "No",
                m.get("fuente", ""),
            ))

    def _selected_medicine_id(self) -> str | None:
        sel = self._med_tree.selection()
        if not sel:
            return None
        values = self._med_tree.item(sel[0], "values")
        return values[0] if values else None

    def _on_add_medicine(self):
        if not self.data:
            messagebox.showwarning("Sin archivo", "Abre primero un informe JSON.")
            return
        dlg = MedicineDialog(self, self.canonical)
        self.wait_window(dlg)
        if not dlg.result:
            return
        existing_ids = {m.get("id") for m in self.data.get("medicamentos", [])}
        new_id = dlg.result["id"]
        while new_id in existing_ids:
            new_id = gen_med_id(dlg.result.get("nregistro", ""), "manual")
        dlg.result["id"] = new_id
        self.data.setdefault("medicamentos", []).append(dlg.result)
        self.dirty = True
        self._rebuild_canonical()
        self._refresh_all()
        self._update_status()

    def _on_edit_medicine(self):
        mid = self._selected_medicine_id()
        if not mid:
            messagebox.showinfo("Selecciona", "Selecciona un medicamento de la lista.")
            return
        med = _find_med(self.data, mid)
        if not med:
            return
        dlg = MedicineDialog(self, self.canonical, existing=med)
        self.wait_window(dlg)
        if not dlg.result:
            return
        meds = self.data.get("medicamentos", [])
        for i, m in enumerate(meds):
            if m.get("id") == mid:
                meds[i] = dlg.result
                break
        old_name = med.get("nombre", "")
        new_id = dlg.result["id"]
        for log in self.data.get("registroTomas", []):
            if log.get("medId") == mid:
                log["medId"] = new_id
                log["nombre"] = dlg.result.get("nombre", old_name)
        self.dirty = True
        self._rebuild_canonical()
        self._refresh_all()
        self._update_status()

    def _on_delete_medicine(self):
        mid = self._selected_medicine_id()
        if not mid:
            messagebox.showinfo("Selecciona", "Selecciona un medicamento de la lista.")
            return
        n_logs = sum(1 for l in self.data.get("registroTomas", []) if l.get("medId") == mid)
        msg = f"¿Eliminar el medicamento '{mid}'?"
        if n_logs:
            msg += f"\n\nHay {n_logs} tomas asociadas. Se eliminarán también y se desenlazarán de los registros."
        if not messagebox.askyesno("Confirmar", msg):
            return
        removed_ids = set()
        kept = []
        for log in self.data.get("registroTomas", []):
            if log.get("medId") == mid:
                removed_ids.add(log.get("id"))
                continue
            kept.append(log)
        self.data["registroTomas"] = kept
        for r in self.data.get("records", []):
            ids = r.get("medicationLogIds") or []
            if ids and any(i in removed_ids for i in ids):
                r["medicationLogIds"] = [i for i in ids if i not in removed_ids]
        self.data["medicamentos"] = [m for m in self.data.get("medicamentos", []) if m.get("id") != mid]
        self.dirty = True
        self._rebuild_canonical()
        self._refresh_all()
        self._update_status()

    # -------- Pestaña Asignar medicación --------

    def _build_assign_tab(self):
        f = self._tab_assign

        box = ttk.LabelFrame(f, text="Nueva toma (una sola)", padding=10)
        box.pack(fill="x", anchor="n")

        r = 0
        ttk.Label(box, text="Fecha (YYYY-MM-DD):").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Entry(box, textvariable=self._med_date_var, width=14).grid(row=r, column=1, sticky="w", padx=4)
        ttk.Button(box, text="Hoy", command=lambda: self._med_date_var.set(date.today().isoformat())).grid(row=r, column=2, sticky="w", padx=2)
        r += 1
        ttk.Label(box, text="Medicamento:").grid(row=r, column=0, sticky="w", pady=3)
        self._med_combo = ttk.Combobox(box, textvariable=self._med_id_var, state="readonly", width=80)
        self._med_combo.grid(row=r, column=1, columnspan=2, sticky="we", padx=4, pady=3)
        self._med_combo.bind("<<ComboboxSelected>>", self._on_med_selected)
        r += 1
        ttk.Label(box, text="Franja:").grid(row=r, column=0, sticky="w", pady=3)
        self._slot_combo = ttk.Combobox(box, textvariable=self._med_slot_var, state="readonly", width=30)
        self._slot_combo["values"] = [f"{k} — {v['label']} (~{v['hour']:02d}:00)" for k, v in SLOTS.items()]
        self._slot_combo.current(0)
        self._slot_combo.grid(row=r, column=1, sticky="w", padx=4, pady=3)
        r += 1
        ttk.Label(box, text="Dosis:").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Entry(box, textvariable=self._med_dose_var, width=12).grid(row=r, column=1, sticky="w", padx=4, pady=3)
        r += 1
        ttk.Label(box, text="Unidad:").grid(row=r, column=0, sticky="w", pady=3)
        self._unit_combo = ttk.Combobox(box, textvariable=self._med_unit_var, width=10)
        self._unit_combo.grid(row=r, column=1, sticky="w", padx=4, pady=3)
        r += 1
        ttk.Label(box, text="Omitida:").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Checkbutton(box, variable=self._med_omitted_var).grid(row=r, column=1, sticky="w", padx=4, pady=3)
        r += 1
        ttk.Label(box, text="Nota:").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Entry(box, textvariable=self._med_note_var, width=60).grid(row=r, column=1, columnspan=2, sticky="we", padx=4, pady=3)
        r += 1
        ttk.Button(box, text="Registrar toma", command=self._on_assign_med).grid(row=r, column=1, sticky="w", padx=4, pady=8)

        box.columnconfigure(1, weight=1)

        help_txt = (
            "Crea un registro en 'registroTomas' y lo enlaza al día (creándolo si no existe).\n"
            "Para generar el historial completo usa la pestaña 'Operaciones masivas'."
        )
        ttk.Label(f, text=help_txt, foreground="#555", justify="left").pack(anchor="w", pady=(12, 0))

    def _on_med_selected(self, _evt=None):
        raw = self._med_combo.get()
        med_id = raw.split(" — ", 1)[0] if " — " in raw else raw
        med = _find_med(self.data, med_id)
        if med:
            self._med_id_var.set(med_id)
            self._med_dose_var.set(med.get("dosisPredeterminada") or "")
            self._med_unit_var.set(med.get("unidadPredeterminada") or
                                   (self.canonical.medicine_units[0] if self.canonical else "ui"))

    def _refresh_assign(self):
        if not self.canonical:
            return
        values = [f"{m.get('id')} — {m.get('nombre', '')}" for m in self.data.get("medicamentos", [])]
        self._med_combo["values"] = values
        if values:
            self._med_combo.current(0)
            self._on_med_selected()
        else:
            self._med_id_var.set("")
        self._unit_combo["values"] = self.canonical.all_medicine_units()
        if not self._med_unit_var.get():
            self._med_unit_var.set(self.canonical.medicine_units[0] if self.canonical.medicine_units else "ui")
        self._med_date_var.set(date.today().isoformat())
        self._med_omitted_var.set(False)
        self._med_note_var.set("")

    def _on_assign_med(self):
        if not self.data:
            messagebox.showwarning("Sin archivo", "Abre primero un informe JSON.")
            return
        date_str = self._med_date_var.get().strip()
        if not valid_date_or_none(date_str):
            messagebox.showerror("Fecha inválida", "Usa el formato YYYY-MM-DD.")
            return
        med_id = self._med_id_var.get().strip()
        if not med_id or not _find_med(self.data, med_id):
            messagebox.showerror("Medicamento", "Selecciona un medicamento válido.")
            return
        dose = self._med_dose_var.get().strip() or "10"
        unit = self._med_unit_var.get().strip() or "ui"
        slot_display = self._med_slot_var.get()
        slot = slot_display.split(" — ", 1)[0] if " — " in slot_display else "morning"
        if slot not in SLOTS:
            slot = "morning"
        omitted = bool(self._med_omitted_var.get())
        note = self._med_note_var.get().strip()

        add_medication_log(self.data, med_id, dose, unit, date_str, slot,
                           omitted=omitted, note=note)
        self.dirty = True
        self._update_status()
        self._refresh_records()
        self._refresh_tir()
        if self._current_record and self._current_record.get("date") == date_str:
            self._current_record = get_record(self.data, date_str)
            self._refresh_daily_meds_list()
        messagebox.showinfo("Toma registrada",
                            f"Añadida toma de {dose} {unit} en {slot_display} para {date_str}.")

    # -------- Pestaña Registro diario --------

    def _build_daily_tab(self):
        f = self._tab_daily

        top = ttk.Frame(f)
        top.pack(fill="x", pady=(0, 6))
        ttk.Label(top, text="Fecha (YYYY-MM-DD):").pack(side="left")
        ttk.Entry(top, textvariable=self._daily_date_var, width=14).pack(side="left", padx=4)
        ttk.Button(top, text="Hoy", command=lambda: self._daily_date_var.set(date.today().isoformat())).pack(side="left", padx=2)
        ttk.Button(top, text="Cargar / Crear", command=self._load_daily).pack(side="left", padx=8)
        ttk.Button(top, text="Guardar cambios del día", command=self._save_daily).pack(side="left", padx=2)
        ttk.Button(top, text="Sugerir severidad", command=self._suggest_severity_gui).pack(side="left", padx=8)
        ttk.Label(top, textvariable=self._log_count_var, foreground="#555").pack(side="right")

        body = ttk.Frame(f)
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))

        gf = ttk.LabelFrame(left, text="Glucosa (mg/dL)", padding=6)
        gf.pack(fill="x", pady=4)
        ttk.Label(gf, text="Antes:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(gf, textvariable=self._glucose_before_var, width=10).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(gf, text="Después:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(gf, textvariable=self._glucose_after_var, width=10).grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(gf, text="Noche:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(gf, textvariable=self._glucose_night_var, width=10).grid(row=2, column=1, sticky="w", padx=4)

        mf = ttk.LabelFrame(left, text="Comida y severidad", padding=6)
        mf.pack(fill="x", pady=4)
        ttk.Label(mf, text="Meal:").grid(row=0, column=0, sticky="w", pady=2)
        self._meal_combo = ttk.Combobox(mf, textvariable=self._meal_var, width=20)
        self._meal_combo.grid(row=0, column=1, sticky="w", padx=4, pady=2)
        ttk.Label(mf, text="Severidad:").grid(row=1, column=0, sticky="w", pady=2)
        self._severity_combo = ttk.Combobox(mf, textvariable=self._severity_var, width=20, state="readonly")
        self._severity_combo.grid(row=1, column=1, sticky="w", padx=4, pady=2)

        ef = ttk.LabelFrame(left, text="Ejercicio (vacío = sin ejercicio)", padding=6)
        ef.pack(fill="x", pady=4)
        ttk.Label(ef, text="Tipo:").grid(row=0, column=0, sticky="w", pady=2)
        self._exercise_type_combo = ttk.Combobox(ef, textvariable=self._exercise_type_var, width=20)
        self._exercise_type_combo.grid(row=0, column=1, sticky="w", padx=4, pady=2)
        ttk.Label(ef, text="Duración (min):").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(ef, textvariable=self._exercise_duration_var, width=10).grid(row=1, column=1, sticky="w", padx=4, pady=2)
        ttk.Label(ef, text="Pasos:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(ef, textvariable=self._exercise_steps_var, width=10).grid(row=2, column=1, sticky="w", padx=4, pady=2)

        cf = ttk.LabelFrame(left, text="Comentarios", padding=6)
        cf.pack(fill="both", expand=True, pady=4)
        self._comments_text = tk.Text(cf, height=5, wrap="word")
        self._comments_text.pack(fill="both", expand=True)

        mf2 = ttk.LabelFrame(right, text="Ánimos", padding=6)
        mf2.pack(fill="x", pady=4)
        self._moods_frame = ttk.Frame(mf2)
        self._moods_frame.pack(fill="x")

        df = ttk.LabelFrame(right, text="Dieta", padding=6)
        df.pack(fill="x", pady=4)
        self._diet_frame = ttk.Frame(df)
        self._diet_frame.pack(fill="x")

        lf = ttk.LabelFrame(right, text="Medicación vinculada al día", padding=6)
        lf.pack(fill="x", pady=4)
        self._meds_listbox = tk.Listbox(lf, height=5, activestyle="none")
        self._meds_listbox.pack(fill="x", expand=True, side="top")
        btns = ttk.Frame(lf)
        btns.pack(fill="x", pady=(4, 0))
        ttk.Button(btns, text="Quitar seleccionada", command=self._remove_selected_log).pack(side="left")
        ttk.Button(btns, text="Refrescar", command=self._refresh_daily_meds_list).pack(side="left", padx=4)

        sf = ttk.LabelFrame(right, text="Resumen", padding=6)
        sf.pack(fill="both", expand=True, pady=4)
        self._summary_text = tk.Text(sf, height=10, wrap="word", relief="flat", bg=self.cget("bg"))
        self._summary_text.pack(fill="both", expand=True)
        self._summary_text.configure(state="disabled")

    def _refresh_daily_structure(self):
        if not self.canonical:
            return
        for w in self._moods_frame.winfo_children():
            w.destroy()
        self._mood_vars = {}
        for i, m in enumerate(self.canonical.moods):
            var = tk.BooleanVar(value=False)
            self._mood_vars[m] = var
            ttk.Checkbutton(self._moods_frame, text=m, variable=var).grid(
                row=i // 3, column=i % 3, sticky="w", padx=4, pady=2)

        for w in self._diet_frame.winfo_children():
            w.destroy()
        self._diet_vars = {}
        for i, d in enumerate(self.canonical.diet_contexts):
            var = tk.BooleanVar(value=False)
            self._diet_vars[d] = var
            ttk.Checkbutton(self._diet_frame, text=d, variable=var).grid(
                row=0, column=i, sticky="w", padx=4, pady=2)

        self._meal_combo["values"] = self.canonical.meals
        self._exercise_type_combo["values"] = [""] + self.canonical.exercise_types
        self._severity_combo["values"] = [""] + self.canonical.severities
        self._clear_daily_form()

    def _clear_daily_form(self):
        self._glucose_before_var.set("")
        self._glucose_after_var.set("")
        self._glucose_night_var.set("")
        self._meal_var.set("")
        self._exercise_type_var.set("")
        self._exercise_duration_var.set("")
        self._exercise_steps_var.set("")
        self._severity_var.set("")
        self._comments_text.delete("1.0", "end")
        for v in self._mood_vars.values():
            v.set(False)
        for v in self._diet_vars.values():
            v.set(False)
        self._current_record = None
        self._current_medlog_ids = []
        self._meds_listbox.delete(0, "end")
        self._log_count_var.set("Tomas asociadas: 0")
        self._render_summary()

    def _load_daily(self):
        if not self.data:
            messagebox.showwarning("Sin archivo", "Abre primero un informe JSON.")
            return
        date_str = self._daily_date_var.get().strip()
        if not valid_date_or_none(date_str):
            messagebox.showerror("Fecha inválida", "Usa el formato YYYY-MM-DD.")
            return
        rec = get_record(self.data, date_str)
        if rec is None:
            if not messagebox.askyesno("No existe", f"No hay registro para {date_str}.\n¿Crear uno nuevo?"):
                return
            rec = ensure_record(self.data, date_str)
            self.dirty = True
            self._update_status()
            self._refresh_records()
        self._current_record = rec
        self._populate_daily_form(rec)
        self._refresh_daily_meds_list()
        self._render_summary()

    def _populate_daily_form(self, rec: dict):
        self._glucose_before_var.set("" if rec.get("glucoseBefore") is None else str(rec["glucoseBefore"]))
        self._glucose_after_var.set("" if rec.get("glucoseAfter") is None else str(rec["glucoseAfter"]))
        self._glucose_night_var.set("" if rec.get("glucoseNight") is None else str(rec["glucoseNight"]))
        self._meal_var.set(rec.get("meal") or "")
        ex = rec.get("exercise") or {}
        self._exercise_type_var.set(ex.get("type") or "")
        self._exercise_duration_var.set("" if ex.get("duration") is None else str(ex["duration"]))
        self._exercise_steps_var.set("" if ex.get("steps") is None else str(ex["steps"]))
        current_moods = set(rec.get("moods") or [])
        for m, v in self._mood_vars.items():
            v.set(m in current_moods)
        current_diet = set(rec.get("dietContext") or [])
        for d, v in self._diet_vars.items():
            v.set(d in current_diet)
        self._severity_var.set(rec.get("severity") or "")
        self._comments_text.delete("1.0", "end")
        self._comments_text.insert("1.0", rec.get("comments") or "")

    def _refresh_daily_meds_list(self):
        self._meds_listbox.delete(0, "end")
        self._current_medlog_ids = []
        rec = self._current_record
        if not rec:
            self._log_count_var.set("Tomas asociadas: 0")
            return
        logs_by_id = {l.get("id"): l for l in self.data.get("registroTomas", [])}
        for lid in rec.get("medicationLogIds") or []:
            log = logs_by_id.get(lid)
            if not log:
                continue
            self._current_medlog_ids.append(lid)
            med = _find_med(self.data, log.get("medId", ""))
            med_name = (med or {}).get("nombre") or log.get("nombre") or log.get("medId", "")
            if len(med_name) > 40:
                med_name = med_name[:37] + "..."
            slot_disp = SLOTS.get(slot_of(log.get("fecha", "")), {}).get("label", "?")
            hora = (log.get("fecha") or "")[11:16]
            prefix = "[OMITIDA] " if log.get("omitida") else ""
            self._meds_listbox.insert(
                "end",
                f"{prefix}{med_name} · {log.get('dosis')} {log.get('unidad')} · "
                f"{slot_disp} {hora}"
            )
        self._log_count_var.set(f"Tomas asociadas: {len(self._current_medlog_ids)}")

    def _remove_selected_log(self):
        if not self._current_record:
            return
        sel = self._meds_listbox.curselection()
        if not sel:
            messagebox.showinfo("Selecciona", "Selecciona una toma de la lista.")
            return
        idx = sel[0]
        if idx >= len(self._current_medlog_ids):
            return
        lid = self._current_medlog_ids[idx]
        label = self._meds_listbox.get(idx)
        if not messagebox.askyesno("Eliminar toma",
                                   f"¿Eliminar esta toma?\n\n{label}"):
            return
        self.data["registroTomas"] = [l for l in self.data.get("registroTomas", []) if l.get("id") != lid]
        ids = self._current_record.get("medicationLogIds") or []
        self._current_record["medicationLogIds"] = [i for i in ids if i != lid]
        self.dirty = True
        self._refresh_daily_meds_list()
        self._render_summary()
        self._refresh_records()
        self._update_status()

    def _save_daily(self):
        if not self.data:
            messagebox.showwarning("Sin archivo", "Abre primero un informe JSON.")
            return
        date_str = self._daily_date_var.get().strip()
        if not valid_date_or_none(date_str):
            messagebox.showerror("Fecha inválida", "Usa el formato YYYY-MM-DD.")
            return
        rec = get_record(self.data, date_str) or ensure_record(self.data, date_str)
        rec["glucoseBefore"] = parse_float_or_none(self._glucose_before_var.get())
        rec["glucoseAfter"] = parse_float_or_none(self._glucose_after_var.get())
        rec["glucoseNight"] = parse_float_or_none(self._glucose_night_var.get())
        rec["meal"] = self._meal_var.get().strip() or rec.get("meal") or "breakfast"
        ex_type = self._exercise_type_var.get().strip()
        if ex_type:
            rec["exercise"] = {
                "type": ex_type,
                "duration": parse_int_or_none(self._exercise_duration_var.get()),
                "steps": parse_int_or_none(self._exercise_steps_var.get()),
            }
        else:
            rec["exercise"] = None
        rec["moods"] = [m for m, v in self._mood_vars.items() if v.get()]
        rec["dietContext"] = [d for d, v in self._diet_vars.items() if v.get()]
        rec["severity"] = self._severity_var.get().strip() or None
        rec["comments"] = self._comments_text.get("1.0", "end").rstrip("\n")
        self._current_record = rec
        self.dirty = True
        self._update_status()
        self._refresh_records()
        self._refresh_tir()
        self._render_summary()
        self._refresh_daily_meds_list()
        messagebox.showinfo("Aplicado",
                            "Cambios aplicados en memoria.\nUsa Archivo → Guardar para escribir en disco.")

    def _suggest_severity_gui(self):
        pseudo = {
            "glucoseBefore": parse_float_or_none(self._glucose_before_var.get()),
            "glucoseAfter": parse_float_or_none(self._glucose_after_var.get()),
            "glucoseNight": parse_float_or_none(self._glucose_night_var.get()),
        }
        sug = suggest_severity(pseudo)
        label = SEVERITY_LABELS.get(sug or "", sug or "Ninguna")
        if messagebox.askyesno("Sugerencia", f"Severidad sugerida: {label}\n¿Aplicar?"):
            self._severity_var.set(sug or "")

    def _render_summary(self):
        t = self._summary_text
        t.configure(state="normal")
        t.delete("1.0", "end")
        rec = self._current_record
        if not rec:
            t.insert("1.0", "(Sin registro cargado)")
        else:
            ex = rec.get("exercise")
            ex_txt = "-" if not ex else f"{ex.get('type')} · {ex.get('duration')} min · {ex.get('steps') or '-'} pasos"
            lines = [
                f"ID:         {rec.get('id')}",
                f"Fecha:      {rec.get('date')}",
                f"Antes:      {fmt_glucose(rec.get('glucoseBefore'))}",
                f"Después:    {fmt_glucose(rec.get('glucoseAfter'))}",
                f"Noche:      {fmt_glucose(rec.get('glucoseNight'))}",
                f"Meal:       {rec.get('meal')}",
                f"Ejercicio:  {ex_txt}",
                f"Severidad:  {rec.get('severity') or '-'}",
                f"Dieta:      {', '.join(rec.get('dietContext') or []) or '-'}",
                f"Ánimos:     {', '.join(rec.get('moods') or []) or '-'}",
                f"Tomas:      {len(rec.get('medicationLogIds') or [])}",
            ]
            t.insert("1.0", "\n".join(lines))
        t.configure(state="disabled")

    # -------- Pestaña Operaciones masivas --------

    def _build_bulk_tab(self):
        f = self._tab_bulk

        canvas = tk.Canvas(f, highlightthickness=0)
        vbar = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        # ---- Historial de medicación ----
        med_box = ttk.LabelFrame(inner, text="Generar historial de medicación", padding=10)
        med_box.pack(fill="x", pady=(0, 10), padx=2)

        r = 0
        ttk.Label(med_box, text="Medicamento:").grid(row=r, column=0, sticky="w", pady=3)
        self._bulk_med_combo = ttk.Combobox(med_box, textvariable=self._bulk_med_id_var,
                                            state="readonly", width=80)
        self._bulk_med_combo.grid(row=r, column=1, columnspan=3, sticky="we", padx=4, pady=3)
        self._bulk_med_combo.bind("<<ComboboxSelected>>", self._on_bulk_med_selected)
        r += 1
        ttk.Label(med_box, text="Franja:").grid(row=r, column=0, sticky="w", pady=3)
        self._bulk_med_slot_combo = ttk.Combobox(med_box, textvariable=self._bulk_med_slot_var,
                                                 state="readonly", width=30)
        self._bulk_med_slot_combo["values"] = [
            f"{k} — {v['label']} (~{v['hour']:02d}:00)" for k, v in SLOTS.items()
        ]
        self._bulk_med_slot_combo.current(0)
        self._bulk_med_slot_combo.grid(row=r, column=1, sticky="w", padx=4, pady=3)
        r += 1
        ttk.Label(med_box, text="Dosis:").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Entry(med_box, textvariable=self._bulk_med_dose_var, width=12).grid(row=r, column=1, sticky="w", padx=4, pady=3)
        ttk.Label(med_box, text="Unidad:").grid(row=r, column=2, sticky="e", pady=3)
        self._bulk_med_unit_combo = ttk.Combobox(med_box, textvariable=self._bulk_med_unit_var, width=10)
        self._bulk_med_unit_combo.grid(row=r, column=3, sticky="w", padx=4, pady=3)
        r += 1
        ttk.Checkbutton(med_box, text="Marcar tomas como omitidas",
                        variable=self._bulk_med_omitted_var).grid(row=r, column=1, sticky="w", padx=4, pady=3)
        r += 1
        ttk.Label(med_box, text="Nota (opcional):").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Entry(med_box, textvariable=self._bulk_med_note_var, width=50).grid(row=r, column=1, columnspan=3, sticky="we", padx=4, pady=3)
        r += 1

        ttk.Label(med_box, text="Desde (YYYY-MM-DD):").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Entry(med_box, textvariable=self._bulk_med_from_var, width=14).grid(row=r, column=1, sticky="w", padx=4, pady=3)
        ttk.Label(med_box, text="Hasta:").grid(row=r, column=2, sticky="e", pady=3)
        ttk.Entry(med_box, textvariable=self._bulk_med_to_var, width=14).grid(row=r, column=3, sticky="w", padx=4, pady=3)
        r += 1
        ttk.Checkbutton(med_box, text="Todas las fechas (ignorar rango)",
                        variable=self._bulk_med_all_var).grid(row=r, column=1, columnspan=3, sticky="w", padx=4, pady=3)
        r += 1
        ttk.Checkbutton(med_box,
                        text="Saltar días que ya tienen este medicamento en esta franja",
                        variable=self._bulk_med_skip_var).grid(row=r, column=1, columnspan=3, sticky="w", padx=4, pady=3)
        r += 1
        ttk.Checkbutton(med_box,
                        text="Reemplazar tomas existentes de este medicamento en el rango",
                        variable=self._bulk_med_replace_var).grid(row=r, column=1, columnspan=3, sticky="w", padx=4, pady=3)
        r += 1

        btns = ttk.Frame(med_box)
        btns.grid(row=r, column=0, columnspan=4, sticky="we", pady=(8, 0))
        ttk.Button(btns, text="Generar historial",
                   command=self._on_bulk_generate_med).pack(side="left", padx=2)
        ttk.Button(btns, text="Eliminar tomas del medicamento...",
                   command=self._on_bulk_delete_med).pack(side="left", padx=2)
        r += 1
        ttk.Label(med_box,
                  text="Sólo se generan tomas para días que ya tienen un registro diario en el informe.",
                  foreground="#666", wraplength=760).grid(row=r, column=0, columnspan=4, sticky="w", pady=(4, 0))

        med_box.columnconfigure(1, weight=1)
        med_box.columnconfigure(3, weight=1)

        # ---- Ánimos a todos ----
        moods_box = ttk.LabelFrame(inner, text="Aplicar ánimos a todos los registros", padding=10)
        moods_box.pack(fill="x", pady=(0, 10), padx=2)

        mr = 0
        ttk.Label(moods_box, text="Desde (YYYY-MM-DD):").grid(row=mr, column=0, sticky="w", pady=3)
        ttk.Entry(moods_box, textvariable=self._bulk_moods_from_var, width=14).grid(row=mr, column=1, sticky="w", padx=4, pady=3)
        ttk.Label(moods_box, text="Hasta:").grid(row=mr, column=2, sticky="e", pady=3)
        ttk.Entry(moods_box, textvariable=self._bulk_moods_to_var, width=14).grid(row=mr, column=3, sticky="w", padx=4, pady=3)
        mr += 1
        ttk.Checkbutton(moods_box, text="Todas las fechas",
                        variable=self._bulk_moods_all_var).grid(row=mr, column=1, columnspan=3, sticky="w", padx=4, pady=3)
        mr += 1
        ttk.Label(moods_box, text="Ánimos a aplicar:").grid(row=mr, column=0, sticky="nw", pady=3)
        self._bulk_moods_grid = ttk.Frame(moods_box)
        self._bulk_moods_grid.grid(row=mr, column=1, columnspan=3, sticky="w", padx=4, pady=3)
        mr += 1
        mode_frame = ttk.Frame(moods_box)
        mode_frame.grid(row=mr, column=1, columnspan=3, sticky="w", padx=4, pady=3)
        ttk.Radiobutton(mode_frame, text="Reemplazar", variable=self._bulk_moods_mode_var,
                        value="replace").pack(side="left", padx=2)
        ttk.Radiobutton(mode_frame, text="Añadir", variable=self._bulk_moods_mode_var,
                        value="add").pack(side="left", padx=2)
        mr += 1
        ttk.Button(moods_box, text="Aplicar a todos",
                   command=self._on_bulk_apply_moods).grid(row=mr, column=1, sticky="w", padx=4, pady=(6, 0))

        # ---- Dieta a todos ----
        diet_box = ttk.LabelFrame(inner, text="Aplicar dieta a todos los registros", padding=10)
        diet_box.pack(fill="x", pady=(0, 10), padx=2)
        dr = 0
        ttk.Label(diet_box, text="Desde (YYYY-MM-DD):").grid(row=dr, column=0, sticky="w", pady=3)
        ttk.Entry(diet_box, textvariable=self._bulk_diet_from_var, width=14).grid(row=dr, column=1, sticky="w", padx=4, pady=3)
        ttk.Label(diet_box, text="Hasta:").grid(row=dr, column=2, sticky="e", pady=3)
        ttk.Entry(diet_box, textvariable=self._bulk_diet_to_var, width=14).grid(row=dr, column=3, sticky="w", padx=4, pady=3)
        dr += 1
        ttk.Checkbutton(diet_box, text="Todas las fechas",
                        variable=self._bulk_diet_all_var).grid(row=dr, column=1, columnspan=3, sticky="w", padx=4, pady=3)
        dr += 1
        ttk.Label(diet_box, text="Dieta a aplicar:").grid(row=dr, column=0, sticky="nw", pady=3)
        self._bulk_diet_grid = ttk.Frame(diet_box)
        self._bulk_diet_grid.grid(row=dr, column=1, columnspan=3, sticky="w", padx=4, pady=3)
        dr += 1
        mode_frame2 = ttk.Frame(diet_box)
        mode_frame2.grid(row=dr, column=1, columnspan=3, sticky="w", padx=4, pady=3)
        ttk.Radiobutton(mode_frame2, text="Reemplazar", variable=self._bulk_diet_mode_var,
                        value="replace").pack(side="left", padx=2)
        ttk.Radiobutton(mode_frame2, text="Añadir", variable=self._bulk_diet_mode_var,
                        value="add").pack(side="left", padx=2)
        dr += 1
        ttk.Button(diet_box, text="Aplicar a todos",
                   command=self._on_bulk_apply_diet).grid(row=dr, column=1, sticky="w", padx=4, pady=(6, 0))

        # ---- Meal a todos ----
        meal_box = ttk.LabelFrame(inner, text="Aplicar comida (meal) a todos los registros", padding=10)
        meal_box.pack(fill="x", pady=(0, 10), padx=2)
        kr = 0
        ttk.Label(meal_box, text="Desde (YYYY-MM-DD):").grid(row=kr, column=0, sticky="w", pady=3)
        ttk.Entry(meal_box, textvariable=self._bulk_meal_from_var, width=14).grid(row=kr, column=1, sticky="w", padx=4, pady=3)
        ttk.Label(meal_box, text="Hasta:").grid(row=kr, column=2, sticky="e", pady=3)
        ttk.Entry(meal_box, textvariable=self._bulk_meal_to_var, width=14).grid(row=kr, column=3, sticky="w", padx=4, pady=3)
        kr += 1
        ttk.Checkbutton(meal_box, text="Todas las fechas",
                        variable=self._bulk_meal_all_var).grid(row=kr, column=1, columnspan=3, sticky="w", padx=4, pady=3)
        kr += 1
        ttk.Label(meal_box, text="Comida:").grid(row=kr, column=0, sticky="w", pady=3)
        self._bulk_meal_combo = ttk.Combobox(meal_box, textvariable=self._bulk_meal_value_var, width=24)
        self._bulk_meal_combo.grid(row=kr, column=1, sticky="w", padx=4, pady=3)
        kr += 1
        ttk.Button(meal_box, text="Aplicar a todos",
                   command=self._on_bulk_apply_meal).grid(row=kr, column=1, sticky="w", padx=4, pady=(6, 0))

        # ---- Mantenimiento ----
        fix_box = ttk.LabelFrame(inner, text="Mantenimiento", padding=10)
        fix_box.pack(fill="x", pady=(0, 10), padx=2)
        ttk.Button(fix_box, text="Limpiar referencias huérfanas en registroTomas/registro diario",
                   command=self._on_cleanup_orphans).pack(side="left", padx=2)
        ttk.Label(fix_box,
                  text="Elimina enlaces a tomas que ya no existen y tomas cuyo medicamento fue eliminado.",
                  foreground="#666", wraplength=760).pack(side="left", padx=12)

    def _rebuild_canonical(self):
        self.canonical = Canonical(self.data) if self.data else None

    def _refresh_bulk(self):
        if not self.canonical:
            return
        med_values = [f"{m.get('id')} — {m.get('nombre', '')}" for m in self.data.get("medicamentos", [])]
        self._bulk_med_combo["values"] = med_values
        if med_values:
            self._bulk_med_combo.current(0)
            self._on_bulk_med_selected()
        else:
            self._bulk_med_id_var.set("")
        self._bulk_med_unit_combo["values"] = self.canonical.all_medicine_units()

        for w in self._bulk_moods_grid.winfo_children():
            w.destroy()
        self._bulk_mood_vars = {}
        for i, m in enumerate(self.canonical.moods):
            var = tk.BooleanVar(value=False)
            self._bulk_mood_vars[m] = var
            ttk.Checkbutton(self._bulk_moods_grid, text=m, variable=var).grid(
                row=i // 4, column=i % 4, sticky="w", padx=4, pady=2)

        for w in self._bulk_diet_grid.winfo_children():
            w.destroy()
        self._bulk_diet_vars = {}
        for i, d in enumerate(self.canonical.diet_contexts):
            var = tk.BooleanVar(value=False)
            self._bulk_diet_vars[d] = var
            ttk.Checkbutton(self._bulk_diet_grid, text=d, variable=var).grid(
                row=0, column=i, sticky="w", padx=4, pady=2)

        self._bulk_meal_combo["values"] = self.canonical.meals
        if not self._bulk_meal_value_var.get():
            self._bulk_meal_value_var.set(self.canonical.meals[0] if self.canonical.meals else "breakfast")

    def _on_bulk_med_selected(self, _evt=None):
        raw = self._bulk_med_combo.get()
        med_id = raw.split(" — ", 1)[0] if " — " in raw else raw
        med = _find_med(self.data, med_id)
        if med:
            self._bulk_med_id_var.set(med_id)
            self._bulk_med_dose_var.set(med.get("dosisPredeterminada") or "")
            self._bulk_med_unit_var.set(med.get("unidadPredeterminada") or
                                        (self.canonical.medicine_units[0] if self.canonical else "ui"))

    def _resolve_range(self, from_var, to_var, all_var):
        if all_var.get():
            return None, None, None
        f = from_var.get().strip()
        t = to_var.get().strip()
        if f and not valid_date_or_none(f):
            return None, None, "Fecha 'desde' inválida (YYYY-MM-DD)."
        if t and not valid_date_or_none(t):
            return None, None, "Fecha 'hasta' inválida (YYYY-MM-DD)."
        if f and t and f > t:
            return None, None, "La fecha 'desde' es posterior a 'hasta'."
        return (f or None), (t or None), None

    def _count_records_in_range(self, date_from, date_to) -> int:
        return sum(1 for r in self.data.get("records", [])
                   if _in_date_range(r.get("date"), date_from, date_to))

    def _on_bulk_generate_med(self):
        if not self.data:
            messagebox.showwarning("Sin archivo", "Abre primero un informe JSON.")
            return
        med_id = self._bulk_med_id_var.get().strip()
        if not med_id or not _find_med(self.data, med_id):
            messagebox.showerror("Medicamento", "Selecciona un medicamento válido.")
            return
        slot_raw = self._bulk_med_slot_combo.get()
        slot = slot_raw.split(" — ", 1)[0] if " — " in slot_raw else "morning"
        if slot not in SLOTS:
            slot = "morning"
        dose = self._bulk_med_dose_var.get().strip() or "10"
        unit = self._bulk_med_unit_var.get().strip() or "ui"
        omitted = bool(self._bulk_med_omitted_var.get())
        note = self._bulk_med_note_var.get().strip()

        df, dt, err = self._resolve_range(self._bulk_med_from_var, self._bulk_med_to_var, self._bulk_med_all_var)
        if err:
            messagebox.showerror("Rango inválido", err)
            return

        n_target = self._count_records_in_range(df, dt)
        if n_target == 0:
            messagebox.showinfo("Sin registros", "No hay registros en ese rango.")
            return

        replace = bool(self._bulk_med_replace_var.get())
        skip = bool(self._bulk_med_skip_var.get())
        msg = (
            f"Vas a generar el historial de '{med_id}'.\n\n"
            f"Franja: {SLOTS[slot]['label']} (~{SLOTS[slot]['hour']:02d}:00)\n"
            f"Dosis: {dose} {unit}\n"
            f"Rango: {df or 'principio'} → {dt or 'fin'}\n"
            f"Registros diarios afectables: {n_target}\n\n"
            f"Reemplazar tomas existentes: {'Sí' if replace else 'No'}\n"
            f"Saltar días ya cubiertos: {'Sí' if skip else 'No'}\n\n"
            "¿Continuar?"
        )
        if not messagebox.askyesno("Confirmar", msg):
            return

        res = bulk_generate_medication_history(
            self.data, med_id, slot, dose, unit,
            date_from=df, date_to=dt,
            replace_existing=replace, skip_existing_slot=skip,
            omitted=omitted, note=note,
        )
        self.dirty = True
        self._refresh_all()
        self._update_status()
        messagebox.showinfo("Historial generado",
                            f"Creadas:   {res['created']}\n"
                            f"Saltadas:  {res['skipped']}\n"
                            f"Eliminadas por reemplazo: {res['removed']}\n"
                            f"Registros objetivo: {res['total']}")

    def _on_bulk_delete_med(self):
        if not self.data:
            return
        med_id = self._bulk_med_id_var.get().strip()
        if not med_id or not _find_med(self.data, med_id):
            messagebox.showerror("Medicamento", "Selecciona un medicamento válido.")
            return
        df, dt, err = self._resolve_range(self._bulk_med_from_var, self._bulk_med_to_var, self._bulk_med_all_var)
        if err:
            messagebox.showerror("Rango inválido", err)
            return
        if not messagebox.askyesno(
                "Confirmar",
                f"¿Eliminar TODAS las tomas de '{med_id}' en el rango "
                f"{df or 'principio'} → {dt or 'fin'}?\n\n"
                "Los registros diarios quedarán desenlazados."):
            return
        n = bulk_delete_medication_logs(self.data, med_id, df, dt)
        self.dirty = True
        self._refresh_all()
        self._update_status()
        messagebox.showinfo("Eliminadas", f"Tomas eliminadas: {n}")

    def _on_bulk_apply_moods(self):
        if not self.data:
            return
        values = [m for m, v in self._bulk_mood_vars.items() if v.get()]
        df, dt, err = self._resolve_range(self._bulk_moods_from_var, self._bulk_moods_to_var, self._bulk_moods_all_var)
        if err:
            messagebox.showerror("Rango inválido", err)
            return
        mode = self._bulk_moods_mode_var.get() or "replace"
        if mode == "replace" and not values:
            if not messagebox.askyesno("Vaciar ánimos",
                                       "No has marcado ánimos. Con 'Reemplazar' esto dejará "
                                       "la lista de ánimos vacía en todos los registros del rango.\n\n"
                                       "¿Continuar?"):
                return
        n = self._count_records_in_range(df, dt)
        if n == 0:
            messagebox.showinfo("Sin registros", "No hay registros en ese rango.")
            return
        if not messagebox.askyesno(
                "Confirmar",
                f"Modo: {'Reemplazar' if mode == 'replace' else 'Añadir'}\n"
                f"Ánimos: {', '.join(values) or '(vacío)'}\n"
                f"Registros afectados: {n}\n\n¿Continuar?"):
            return
        changed = bulk_apply_list_field(self.data, "moods", values, df, dt, mode)
        self.dirty = True
        self._refresh_all()
        self._update_status()
        messagebox.showinfo("Aplicado", f"Registros modificados: {changed}")

    def _on_bulk_apply_diet(self):
        if not self.data:
            return
        values = [d for d, v in self._bulk_diet_vars.items() if v.get()]
        df, dt, err = self._resolve_range(self._bulk_diet_from_var, self._bulk_diet_to_var, self._bulk_diet_all_var)
        if err:
            messagebox.showerror("Rango inválido", err)
            return
        mode = self._bulk_diet_mode_var.get() or "replace"
        if mode == "replace" and not values:
            if not messagebox.askyesno("Vaciar dieta",
                                       "No has marcado dietas. Con 'Reemplazar' esto dejará "
                                       "la lista de dieta vacía en todos los registros del rango.\n\n"
                                       "¿Continuar?"):
                return
        n = self._count_records_in_range(df, dt)
        if n == 0:
            messagebox.showinfo("Sin registros", "No hay registros en ese rango.")
            return
        if not messagebox.askyesno(
                "Confirmar",
                f"Modo: {'Reemplazar' if mode == 'replace' else 'Añadir'}\n"
                f"Dieta: {', '.join(values) or '(vacío)'}\n"
                f"Registros afectados: {n}\n\n¿Continuar?"):
            return
        changed = bulk_apply_list_field(self.data, "dietContext", values, df, dt, mode)
        self.dirty = True
        self._refresh_all()
        self._update_status()
        messagebox.showinfo("Aplicado", f"Registros modificados: {changed}")

    def _on_bulk_apply_meal(self):
        if not self.data:
            return
        value = self._bulk_meal_value_var.get().strip()
        if not value:
            messagebox.showerror("Comida", "Selecciona una comida.")
            return
        df, dt, err = self._resolve_range(self._bulk_meal_from_var, self._bulk_meal_to_var, self._bulk_meal_all_var)
        if err:
            messagebox.showerror("Rango inválido", err)
            return
        n = self._count_records_in_range(df, dt)
        if n == 0:
            messagebox.showinfo("Sin registros", "No hay registros en ese rango.")
            return
        if not messagebox.askyesno(
                "Confirmar",
                f"Comida: {value}\nRegistros afectados: {n}\n\n¿Continuar?"):
            return
        changed = bulk_apply_scalar_field(self.data, "meal", value, df, dt)
        self.dirty = True
        self._refresh_all()
        self._update_status()
        messagebox.showinfo("Aplicado", f"Registros modificados: {changed}")

    def _on_cleanup_orphans(self):
        if not self.data:
            return
        valid_med_ids = {m.get("id") for m in self.data.get("medicamentos", [])}
        kept = []
        removed_logs = 0
        for l in self.data.get("registroTomas", []):
            if l.get("medId") not in valid_med_ids:
                removed_logs += 1
                continue
            kept.append(l)
        self.data["registroTomas"] = kept
        valid_log_ids = {l.get("id") for l in kept}
        fixed_links = 0
        for r in self.data.get("records", []):
            ids = r.get("medicationLogIds") or []
            new_ids = [i for i in ids if i in valid_log_ids]
            if len(new_ids) != len(ids):
                fixed_links += len(ids) - len(new_ids)
                r["medicationLogIds"] = new_ids
        if removed_logs == 0 and fixed_links == 0:
            messagebox.showinfo("Sin cambios", "No había referencias huérfanas.")
            return
        self.dirty = True
        self._refresh_all()
        self._update_status()
        messagebox.showinfo("Limpieza completada",
                            f"Tomas eliminadas (medicamento inexistente): {removed_logs}\n"
                            f"Enlaces huérfanos eliminados: {fixed_links}")

    # -------- Pestaña TIR --------

    def _build_tir_tab(self):
        f = self._tab_tir
        self._tir_info = tk.StringVar()
        ttk.Label(f, textvariable=self._tir_info, justify="left").pack(anchor="w", pady=(0, 8))
        cols = ("cat", "rango", "n", "pct", "objetivo")
        self._tir_tree = ttk.Treeview(f, columns=cols, show="headings", height=10)
        for c, w, txt in (
            ("cat", 110, "Categoría"),
            ("rango", 280, "Rango"),
            ("n", 60, "N"),
            ("pct", 90, "%"),
            ("objetivo", 120, "Objetivo"),
        ):
            self._tir_tree.heading(c, text=txt)
            self._tir_tree.column(c, width=w, anchor="w")
        self._tir_tree.pack(fill="both", expand=True)

    def _refresh_tir(self):
        self._tir_tree.delete(*self._tir_tree.get_children())
        if not self.data:
            self._tir_info.set("(Sin datos cargados)")
            return
        recalc_tir(self.data)
        tr = self.data.get("tiempoEnRango", {})
        cats = tr.get("categorias", [])
        total = sum(c.get("count", 0) for c in cats)
        self._tir_info.set(
            f"Población: {tr.get('poblacion', '')}\n"
            f"Banda:     {tr.get('banda', '')}\n"
            f"Lecturas:  {total}"
        )
        for c in cats:
            self._tir_tree.insert("", "end", values=(
                c.get("shortLabel", ""),
                c.get("label", ""),
                c.get("count", 0),
                f"{c.get('pct', 0):.2f}%",
                c.get("value", ""),
            ))

    # -------- Pestaña Registros --------

    def _build_records_tab(self):
        f = self._tab_records
        cols = ("date", "before", "after", "night", "meal", "severity", "moods", "meds", "exercise")
        self._rec_tree = ttk.Treeview(f, columns=cols, show="headings", height=18)
        for c, w, txt in (
            ("date", 100, "Fecha"),
            ("before", 70, "Antes"),
            ("after", 70, "Después"),
            ("night", 70, "Noche"),
            ("meal", 90, "Meal"),
            ("severity", 90, "Severidad"),
            ("moods", 180, "Ánimos"),
            ("meds", 60, "Tomas"),
            ("exercise", 160, "Ejercicio"),
        ):
            self._rec_tree.heading(c, text=txt)
            self._rec_tree.column(c, width=w, anchor="w")
        self._rec_tree.pack(fill="both", expand=True, side="left")
        sb = ttk.Scrollbar(f, orient="vertical", command=self._rec_tree.yview)
        sb.pack(side="right", fill="y")
        self._rec_tree.configure(yscrollcommand=sb.set)
        self._rec_tree.bind("<Double-1>", self._on_record_double_click)

    def _refresh_records(self):
        self._rec_tree.delete(*self._rec_tree.get_children())
        if not self.data:
            return
        for r in self.data.get("records", []):
            ex = r.get("exercise")
            ex_txt = "-" if not ex else f"{ex.get('type')} · {ex.get('duration')} min"
            self._rec_tree.insert("", "end", values=(
                r.get("date", ""),
                fmt_glucose(r.get("glucoseBefore")),
                fmt_glucose(r.get("glucoseAfter")),
                fmt_glucose(r.get("glucoseNight")),
                r.get("meal", ""),
                r.get("severity") or "-",
                ", ".join(r.get("moods") or []) or "-",
                len(r.get("medicationLogIds") or []),
                ex_txt,
            ))

    def _on_record_double_click(self, _evt):
        sel = self._rec_tree.selection()
        if not sel:
            return
        values = self._rec_tree.item(sel[0], "values")
        if not values:
            return
        date_str = values[0]
        self._daily_date_var.set(date_str)
        self._notebook.select(self._tab_daily)
        self._load_daily()

    # -------------------- Archivo --------------------

    def _auto_open_if_single(self):
        here = Path.cwd()
        self_name = Path(__file__).name
        candidates = [p for p in sorted(here.glob("*.json")) if p.is_file() and p.name != self_name]
        if len(candidates) == 1:
            try:
                self.load_file(candidates[0])
                self._status_var.set(f"Cargado automáticamente: {candidates[0].name}")
            except Exception as e:
                print(f"No se pudo cargar automáticamente: {e}")

    def load_file(self, path: Path):
        data = load_json(path)
        self.path = path
        self.data = data
        self.canonical = Canonical(data)
        self.dirty = False
        self._current_record = None
        self._refresh_all()
        self._update_status()

    def _refresh_all(self):
        self._refresh_patient()
        self._refresh_medicines()
        self._refresh_assign()
        self._refresh_daily_structure()
        self._refresh_bulk()
        self._refresh_tir()
        self._refresh_records()

    def _update_status(self):
        parts = []
        parts.append(f"Archivo: {self.path.name}" if self.path else "Sin archivo")
        parts.append("Cambios sin guardar" if self.dirty else "Guardado")
        self._status_var.set("   |   ".join(parts))
        base = "Gestor de informe de glucosa"
        if self.path:
            base += f" — {self.path.name}"
        if self.dirty:
            base += " *"
        self.title(base)

    def on_open(self):
        if self.dirty and not messagebox.askyesno(
            "Cambios sin guardar", "Hay cambios sin guardar. ¿Descartarlos?"):
            return
        p = filedialog.askopenfilename(
            title="Abrir informe de glucosa",
            filetypes=[("JSON", "*.json"), ("Todos los archivos", "*.*")],
        )
        if not p:
            return
        try:
            self.load_file(Path(p))
        except Exception as e:
            messagebox.showerror("Error al abrir", f"No se pudo abrir el archivo:\n{e}")

    def on_save(self):
        if not self.data:
            messagebox.showwarning("Sin datos", "No hay nada que guardar.")
            return
        if not self.path:
            return self.on_save_as()
        try:
            save_all(self.data, self.path)
            self.dirty = False
            self._refresh_all()
            self._update_status()
            messagebox.showinfo("Guardado", f"Guardado en:\n{self.path}")
        except Exception as e:
            messagebox.showerror("Error al guardar", str(e))

    def on_save_as(self):
        if not self.data:
            messagebox.showwarning("Sin datos", "No hay nada que guardar.")
            return
        p = filedialog.asksaveasfilename(
            title="Guardar informe como",
            defaultextension=".json",
            initialfile=(self.path.name if self.path else "informe_glucosa.json"),
            filetypes=[("JSON", "*.json"), ("Todos los archivos", "*.*")],
        )
        if not p:
            return
        self.path = Path(p)
        self.on_save()

    def on_exit(self):
        if self.dirty:
            ans = messagebox.askyesnocancel(
                "Salir",
                "Hay cambios sin guardar. ¿Quieres guardar antes de salir?")
            if ans is None:
                return
            if ans:
                self.on_save()
                if self.dirty:
                    return
        self.destroy()

    def _show_about(self):
        messagebox.showinfo(
            "Acerca de",
            "Gestor de informe de glucosa\n\n"
            "Editor del JSON exportado por la app.\n"
            "· Soporta varios medicamentos en el array 'medicamentos'.\n"
            "· Pestaña 'Operaciones masivas': historial de tomas, ánimos,\n"
            "  dieta y meal aplicados a rangos de fechas.\n"
            "· Al guardar: backup en ./backups/ y recálculo automático\n"
            "  de TIR, totalRegistros, exportedAt y edad."
        )


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def main() -> int:
    app = GlucosaApp()
    if len(sys.argv) > 1:
        raw = " ".join(sys.argv[1:]).strip().strip('"').strip("'")
        p = Path(raw)
        if p.is_file():
            try:
                app.load_file(p)
            except Exception as e:
                print(f"No se pudo abrir {p}: {e}")
        else:
            print(f"Ruta no válida: {p}")
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
