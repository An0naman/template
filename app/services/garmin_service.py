"""
Garmin Connect Integration Service
Fetches health and activity data from Garmin Connect using the garminconnect library.
"""

import json
import logging
import time
from datetime import datetime, date, timezone

from ..db import get_connection

logger = logging.getLogger(__name__)


# ── Field registry ─────────────────────────────────────────────────────────────
# Maps a flat key (used for column mapping) to metadata.
GARMIN_FIELDS = [
    # Daily summary / steps / distance
    {"key": "total_steps",               "label": "Total Steps",               "column_type": "number", "group": "Activity",      "unit": "steps"},
    {"key": "daily_step_goal",           "label": "Daily Step Goal",           "column_type": "number", "group": "Activity",      "unit": "steps"},
    {"key": "total_distance_km",         "label": "Total Distance",            "column_type": "number", "group": "Activity",      "unit": "km"},
    {"key": "floors_ascended",           "label": "Floors Ascended",           "column_type": "number", "group": "Activity",      "unit": "floors"},
    {"key": "active_calories",           "label": "Active Calories",           "column_type": "number", "group": "Activity",      "unit": "kcal"},
    {"key": "total_calories",            "label": "Total Calories Burned",     "column_type": "number", "group": "Activity",      "unit": "kcal"},
    {"key": "bmr_calories",              "label": "BMR Calories",              "column_type": "number", "group": "Activity",      "unit": "kcal"},
    {"key": "moderately_active_minutes", "label": "Moderately Active Minutes", "column_type": "number", "group": "Activity",      "unit": "min"},
    {"key": "highly_active_minutes",     "label": "Highly Active Minutes",     "column_type": "number", "group": "Activity",      "unit": "min"},
    # Heart rate
    {"key": "resting_heart_rate",        "label": "Resting Heart Rate",        "column_type": "number", "group": "Heart Rate",    "unit": "bpm"},
    {"key": "max_heart_rate",            "label": "Max Heart Rate",            "column_type": "number", "group": "Heart Rate",    "unit": "bpm"},
    {"key": "min_heart_rate",            "label": "Min Heart Rate",            "column_type": "number", "group": "Heart Rate",    "unit": "bpm"},
    # Sleep
    {"key": "sleep_duration_hours",      "label": "Sleep Duration",            "column_type": "number", "group": "Sleep",         "unit": "hours"},
    {"key": "sleep_score",               "label": "Sleep Score",               "column_type": "number", "group": "Sleep",         "unit": ""},
    {"key": "light_sleep_hours",         "label": "Light Sleep",               "column_type": "number", "group": "Sleep",         "unit": "hours"},
    {"key": "deep_sleep_hours",          "label": "Deep Sleep",                "column_type": "number", "group": "Sleep",         "unit": "hours"},
    {"key": "rem_sleep_hours",           "label": "REM Sleep",                 "column_type": "number", "group": "Sleep",         "unit": "hours"},
    {"key": "awake_hours",               "label": "Awake Time",                "column_type": "number", "group": "Sleep",         "unit": "hours"},
    # Stress / Body Battery
    {"key": "avg_stress_level",          "label": "Avg Stress Level",          "column_type": "number", "group": "Stress",        "unit": ""},
    {"key": "max_stress_level",          "label": "Max Stress Level",          "column_type": "number", "group": "Stress",        "unit": ""},
    {"key": "body_battery_high",         "label": "Body Battery High",         "column_type": "number", "group": "Stress",        "unit": ""},
    {"key": "body_battery_low",          "label": "Body Battery Low",          "column_type": "number", "group": "Stress",        "unit": ""},
    # Body metrics
    {"key": "weight_kg",                 "label": "Weight",                    "column_type": "number", "group": "Body Metrics",  "unit": "kg"},
    {"key": "bmi",                       "label": "BMI",                       "column_type": "number", "group": "Body Metrics",  "unit": ""},
    {"key": "body_fat_percent",          "label": "Body Fat %",                "column_type": "number", "group": "Body Metrics",  "unit": "%"},
    {"key": "muscle_mass_kg",            "label": "Muscle Mass",               "column_type": "number", "group": "Body Metrics",  "unit": "kg"},
    # Fitness
    {"key": "vo2_max",                   "label": "VO2 Max",                   "column_type": "number", "group": "Fitness",       "unit": "ml/kg/min"},
    {"key": "training_status",           "label": "Training Status",           "column_type": "text",   "group": "Fitness",       "unit": ""},
    {"key": "training_load",             "label": "Training Load",             "column_type": "number", "group": "Fitness",       "unit": ""},
    {"key": "training_readiness",        "label": "Training Readiness Score",  "column_type": "number", "group": "Fitness",       "unit": ""},
    {"key": "training_readiness_desc",   "label": "Training Readiness",        "column_type": "text",   "group": "Fitness",       "unit": ""},
    {"key": "endurance_score",           "label": "Endurance Score",           "column_type": "number", "group": "Fitness",       "unit": ""},
    {"key": "hill_score",                "label": "Hill Score",                "column_type": "number", "group": "Fitness",       "unit": ""},
    {"key": "fitness_age",               "label": "Fitness Age",               "column_type": "number", "group": "Fitness",       "unit": "years"},
    {"key": "hrv_weekly_avg",            "label": "HRV Weekly Avg",            "column_type": "number", "group": "Fitness",       "unit": "ms"},
    # SpO2
    {"key": "spo2_avg",                  "label": "SpO2 Average",              "column_type": "number", "group": "Wellness",      "unit": "%"},
    {"key": "spo2_min",                  "label": "SpO2 Min",                  "column_type": "number", "group": "Wellness",      "unit": "%"},
    # Respiration
    {"key": "avg_respiration",           "label": "Avg Respiration Rate",      "column_type": "number", "group": "Wellness",      "unit": "br/min"},
    # Blood pressure
    {"key": "bp_systolic",               "label": "Blood Pressure Systolic",   "column_type": "number", "group": "Wellness",      "unit": "mmHg"},
    {"key": "bp_diastolic",              "label": "Blood Pressure Diastolic",  "column_type": "number", "group": "Wellness",      "unit": "mmHg"},
    {"key": "bp_pulse",                  "label": "Blood Pressure Pulse",      "column_type": "number", "group": "Wellness",      "unit": "bpm"},
    # Hydration
    {"key": "hydration_intake_ml",       "label": "Hydration Intake",          "column_type": "number", "group": "Wellness",      "unit": "mL"},
    {"key": "hydration_goal_ml",         "label": "Hydration Goal",            "column_type": "number", "group": "Wellness",      "unit": "mL"},
]


def _get_system_param(conn, param_name):
    cursor = conn.cursor()
    cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = ?", (param_name,))
    row = cursor.fetchone()
    return row["parameter_value"] if row else None


def _set_system_param(conn, param_name, param_value):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
        (param_name, str(param_value)),
    )


def _as_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _secs_to_hours(seconds):
    if seconds is None:
        return None
    try:
        return round(float(seconds) / 3600, 2)
    except (TypeError, ValueError):
        return None


def _apply_field_mapping(entry_id, field_values, field_mapping, conn):
    """Write Garmin field values into CustomColumnValue rows per the saved mapping.
    Returns (written_count, error_list)."""
    if not field_mapping:
        return 0, []
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    written = 0
    field_errors = []
    for field_key, column_id in field_mapping.items():
        if not column_id:
            continue
        value = field_values.get(field_key)
        if value is None:
            continue
        try:
            cursor.execute(
                """INSERT OR REPLACE INTO CustomColumnValue
                       (custom_column_id, entry_id, value, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (int(column_id), entry_id, str(value), now, now),
            )
            written += 1
        except Exception as exc:
            msg = f"{field_key}->col{column_id}: {exc}"
            logger.warning("Garmin: failed to write col value %s", msg)
            field_errors.append(msg)
    return written, field_errors


def _flatten_garmin_data(stats, sleep_data, stress_data, body_data, hrv_data, spo2_data, respiration_data, bp_data=None,
                         training_status_data=None, training_readiness_data=None, hydration_data=None,
                         fitness_age_data=None, endurance_data=None, hill_data=None):
    """Flatten all Garmin API responses into the flat GARMIN_FIELDS key space."""
    out = {}

    # Daily stats
    if stats:
        out["total_steps"]               = stats.get("totalSteps")
        out["daily_step_goal"]           = stats.get("dailyStepGoal")
        out["floors_ascended"]           = stats.get("floorsAscended")
        out["active_calories"]           = stats.get("activeKilocalories")
        out["total_calories"]            = stats.get("totalKilocalories")
        out["bmr_calories"]              = stats.get("bmrKilocalories")
        out["moderately_active_minutes"] = stats.get("moderateIntensityMinutes")
        out["highly_active_minutes"]     = stats.get("vigorousIntensityMinutes")
        out["resting_heart_rate"]        = stats.get("restingHeartRate")
        out["max_heart_rate"]            = stats.get("maxHeartRate")
        out["min_heart_rate"]            = stats.get("minHeartRate")
        out["avg_stress_level"]          = stats.get("averageStressLevel")
        out["max_stress_level"]          = stats.get("maxStressLevel")
        out["body_battery_high"]         = stats.get("bodyBatteryHighestValue")
        out["body_battery_low"]          = stats.get("bodyBatteryLowestValue")
        out["avg_respiration"]           = stats.get("avgWakingRespirationValue")
        out["spo2_avg"]                  = stats.get("averageSpo2")
        out["spo2_min"]                  = stats.get("lowestSpo2")
        dist_m = stats.get("totalDistanceMeters")
        out["total_distance_km"]         = round(dist_m / 1000, 2) if dist_m else None

    # Sleep
    if sleep_data:
        daily = sleep_data.get("dailySleepDTO") or {}
        out["sleep_score"]       = daily.get("sleepScores", {}).get("overall") if isinstance(daily.get("sleepScores"), dict) else daily.get("sleepScore")
        out["light_sleep_hours"] = _secs_to_hours(daily.get("lightSleepSeconds"))
        out["deep_sleep_hours"]  = _secs_to_hours(daily.get("deepSleepSeconds"))
        out["rem_sleep_hours"]   = _secs_to_hours(daily.get("remSleepSeconds"))
        out["awake_hours"]       = _secs_to_hours(daily.get("awakeSleepSeconds"))
        total_secs = (
            (daily.get("lightSleepSeconds") or 0)
            + (daily.get("deepSleepSeconds") or 0)
            + (daily.get("remSleepSeconds") or 0)
        )
        out["sleep_duration_hours"] = _secs_to_hours(total_secs) if total_secs else None

    # Blood pressure — average of day's readings
    if bp_data:
        readings = bp_data.get("measurementSummaries") or []
        if readings:
            systolics  = [r.get("systolic")  for r in readings if r.get("systolic")]
            diastolics = [r.get("diastolic") for r in readings if r.get("diastolic")]
            pulses     = [r.get("pulse")     for r in readings if r.get("pulse")]
            if systolics:
                out["bp_systolic"]  = round(sum(systolics)  / len(systolics),  1)
            if diastolics:
                out["bp_diastolic"] = round(sum(diastolics) / len(diastolics), 1)
            if pulses:
                out["bp_pulse"]     = round(sum(pulses)     / len(pulses),     1)

    # Body composition
    if body_data:
        weight_grams = body_data.get("weight")
        out["weight_kg"]       = round(weight_grams / 1000, 2) if weight_grams else None
        out["bmi"]             = _as_float(body_data.get("bmi"))
        out["body_fat_percent"]= _as_float(body_data.get("bodyFatPercentage"))
        muscle = body_data.get("muscleMass")
        out["muscle_mass_kg"]  = round(muscle / 1000, 2) if muscle else None

    # HRV
    if hrv_data:
        summary = hrv_data.get("hrvSummary") or {}
        out["hrv_weekly_avg"] = _as_float(summary.get("weeklyAvg"))

    # VO2 Max / training load (from stats)
    if stats:
        out["vo2_max"]       = _as_float(stats.get("vo2MaxValue") or stats.get("maxMetValue"))
        out["training_load"] = _as_float(stats.get("trainingLoadBalance"))

    # Training status (dedicated endpoint — fixes missing extraction bug)
    if training_status_data:
        ts = training_status_data[0] if isinstance(training_status_data, list) and training_status_data else \
             training_status_data if isinstance(training_status_data, dict) else {}
        raw = (ts.get("trainingStatusFeedback") or ts.get("latestTrainingStatus")
               or ts.get("trainingStatus"))
        if isinstance(raw, dict):
            raw = raw.get("trainingStatusFeedbackPhrase") or raw.get("key") or raw.get("value")
        out["training_status"] = str(raw).replace("_", " ").title() if raw else None

    # Training readiness
    if training_readiness_data:
        tr = training_readiness_data[0] if isinstance(training_readiness_data, list) and training_readiness_data else \
             training_readiness_data if isinstance(training_readiness_data, dict) else {}
        out["training_readiness"]      = _as_float(tr.get("score") or tr.get("trainingReadinessScore") or tr.get("value"))
        desc = tr.get("feedbackPhrase") or tr.get("levelDescription") or tr.get("description")
        out["training_readiness_desc"] = str(desc).replace("_", " ").title() if desc else None

    # Hydration
    if hydration_data:
        out["hydration_intake_ml"] = _as_float(hydration_data.get("totalIntakeInML") or hydration_data.get("valueInML"))
        out["hydration_goal_ml"]   = _as_float(hydration_data.get("goalInML"))

    # Fitness age
    if fitness_age_data:
        out["fitness_age"] = _as_float(
            fitness_age_data.get("fitnessAge") or fitness_age_data.get("fitnessAgeRounded")
            or fitness_age_data.get("biologicalAge")
        )

    # Endurance score
    if endurance_data:
        out["endurance_score"] = _as_float(
            endurance_data.get("enduranceScore") or endurance_data.get("overallScore") or endurance_data.get("score")
        )

    # Hill score
    if hill_data:
        out["hill_score"] = _as_float(
            hill_data.get("hillScore") or hill_data.get("overallScore") or hill_data.get("score")
        )

    # Remove None values
    return {k: v for k, v in out.items() if v is not None}


def sync_garmin_data(target_date=None):
    """
    Pull today's (or a specified date's) Garmin data, apply field mapping to
    a new Entry if one is configured, and persist last-sync timestamp.
    Returns a status dict.
    """
    try:
        from garminconnect import Garmin, GarminConnectAuthenticationError
    except ImportError:
        return {"status": "error", "message": "garminconnect library not installed. Add it to requirements.txt and rebuild the container."}

    conn = get_connection()

    username = _get_system_param(conn, "garmin_username")
    password = _get_system_param(conn, "garmin_password")
    if not username or not password:
        conn.close()
        return {"status": "error", "message": "Garmin credentials not configured."}

    if target_date is None:
        target_date = date.today().isoformat()

    try:
        client = Garmin(username, password)
        client.login()
    except Exception as e:
        conn.close()
        return {"status": "error", "message": f"Garmin login failed: {e}"}

    # Fetch all data sources in parallel-friendly sequential calls
    stats = sleep_data = stress_data = body_data = hrv_data = spo2_data = respiration_data = bp_data = None
    training_status_data = training_readiness_data = hydration_data = None
    fitness_age_data = endurance_data = hill_data = None
    errors = []

    try:
        stats = client.get_stats_and_body(target_date)
    except Exception as e:
        errors.append(f"stats: {e}")

    try:
        sleep_data = client.get_sleep_data(target_date)
    except Exception as e:
        errors.append(f"sleep: {e}")

    try:
        body_data = client.get_body_composition(target_date)
        if isinstance(body_data, dict) and "totalAverage" in body_data:
            body_data = body_data["totalAverage"]
    except Exception as e:
        errors.append(f"body: {e}")

    try:
        hrv_data = client.get_hrv_data(target_date)
    except Exception as e:
        errors.append(f"hrv: {e}")

    try:
        bp_data = client.get_blood_pressure(target_date, target_date)
    except Exception as e:
        errors.append(f"bp: {e}")

    try:
        training_status_data = client.get_training_status(target_date)
    except Exception as e:
        errors.append(f"training_status: {e}")

    try:
        training_readiness_data = client.get_training_readiness(target_date)
    except Exception as e:
        errors.append(f"training_readiness: {e}")

    try:
        hydration_data = client.get_hydration_data(target_date)
    except Exception as e:
        errors.append(f"hydration: {e}")

    try:
        fitness_age_data = client.get_fitnessage_data(target_date)
    except Exception as e:
        errors.append(f"fitness_age: {e}")

    try:
        endurance_data = client.get_endurance_score(target_date)
    except Exception as e:
        errors.append(f"endurance: {e}")

    try:
        hill_data = client.get_hill_score(target_date)
    except Exception as e:
        errors.append(f"hill: {e}")

    flat = _flatten_garmin_data(
        stats, sleep_data, stress_data, body_data, hrv_data, spo2_data, respiration_data, bp_data,
        training_status_data=training_status_data,
        training_readiness_data=training_readiness_data,
        hydration_data=hydration_data,
        fitness_age_data=fitness_age_data,
        endurance_data=endurance_data,
        hill_data=hill_data,
    )

    if not flat:
        conn.close()
        return {"status": "warning", "message": "No Garmin data returned for this date.", "errors": errors}

    # Load field mapping
    mapping_raw = _get_system_param(conn, "garmin_field_mapping") or "{}"
    try:
        field_mapping = json.loads(mapping_raw)
    except Exception:
        field_mapping = {}

    # Derive entry_type_id from the mapped columns' CustomColumnAssignment rather
    # than requiring a separately stored garmin_entry_type_id parameter.
    entry_type_id = _get_system_param(conn, "garmin_entry_type_id")
    if not entry_type_id and field_mapping:
        # Look up which entry type owns the first mapped column.
        mapped_col_ids = [v for v in field_mapping.values() if v]
        if mapped_col_ids:
            try:
                cursor = conn.cursor()
                placeholders = ",".join(["?" for _ in mapped_col_ids])
                cursor.execute(
                    f"SELECT entry_type_id FROM CustomColumnAssignment WHERE custom_column_id IN ({placeholders}) LIMIT 1",
                    mapped_col_ids,
                )
                row = cursor.fetchone()
                if row:
                    entry_type_id = row["entry_type_id"]
                    # Persist so future syncs don't need to query again.
                    _set_system_param(conn, "garmin_entry_type_id", str(entry_type_id))
                    conn.commit()
            except Exception as e:
                errors.append(f"entry_type lookup: {e}")

    synced_entry_id = None
    entry_was_created = False
    written_count = 0
    if entry_type_id:
        try:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            # Each sync creates a new snapshot entry with a timestamp in the title
            sync_time = datetime.now(timezone.utc).strftime("%H:%M")
            entry_title = f"Health {target_date} {sync_time}"

            cursor.execute(
                "INSERT INTO Entry (entry_type_id, title, created_at) VALUES (?, ?, ?)",
                (int(entry_type_id), entry_title, now),
            )
            synced_entry_id = cursor.lastrowid
            entry_was_created = True
            conn.commit()

            if field_mapping:
                written_count, field_errors = _apply_field_mapping(synced_entry_id, flat, field_mapping, conn)
                errors.extend(field_errors)
                conn.commit()

            # Find-or-create a day entry and link the Garmin data entry to it
            day_entry_type_id = _get_system_param(conn, "garmin_day_entry_type_id")
            rel_def_id        = _get_system_param(conn, "garmin_relationship_def_id")
            day_entry_id      = None
            day_entry_created = False
            day_linked        = False
            if day_entry_type_id and rel_def_id:
                try:
                    day_title = f"Day {target_date}"
                    cursor.execute(
                        "SELECT id FROM Entry WHERE entry_type_id = ? AND title = ? LIMIT 1",
                        (int(day_entry_type_id), day_title),
                    )
                    day_row = cursor.fetchone()
                    if day_row:
                        day_entry_id = day_row["id"]
                    else:
                        cursor.execute(
                            "INSERT INTO Entry (entry_type_id, title, created_at) VALUES (?, ?, ?)",
                            (int(day_entry_type_id), day_title, now),
                        )
                        day_entry_id = cursor.lastrowid
                        day_entry_created = True
                        conn.commit()

                    # Determine relationship direction from the definition
                    cursor.execute(
                        "SELECT entry_type_id_from, entry_type_id_to FROM RelationshipDefinition WHERE id = ?",
                        (int(rel_def_id),),
                    )
                    rel_def_row = cursor.fetchone()
                    if rel_def_row and int(rel_def_row["entry_type_id_from"]) == int(day_entry_type_id):
                        src_id, tgt_id = day_entry_id, synced_entry_id
                    else:
                        src_id, tgt_id = synced_entry_id, day_entry_id

                    cursor.execute(
                        """INSERT OR IGNORE INTO EntryRelationship
                               (source_entry_id, target_entry_id, relationship_type, created_at)
                           VALUES (?, ?, ?, ?)""",
                        (src_id, tgt_id, int(rel_def_id), now),
                    )
                    day_linked = cursor.rowcount > 0
                    conn.commit()
                except Exception as exc:
                    errors.append(f"day_link: {exc}")
        except Exception as e:
            errors.append(f"entry creation: {e}")
    else:
        errors.append("no_entry_type: No entry type configured — go to Settings > Garmin Connect > Field Mapping, select an entry type and click 'Auto-create all columns'.")

    _set_system_param(conn, "garmin_last_sync_timestamp", str(int(time.time())))
    _set_system_param(conn, "garmin_last_sync_date", target_date)
    conn.commit()
    conn.close()

    mapped_count = len([v for v in field_mapping.values() if v]) if field_mapping else 0
    if synced_entry_id:
        action = "created" if entry_was_created else "updated"
        msg = f"Synced {len(flat)} Garmin fields for {target_date}. Entry #{synced_entry_id} {action}, {written_count}/{mapped_count} column values written."
        if day_entry_id:
            day_action = "created" if day_entry_created else "found"
            link_action = "linked" if day_linked else "already linked"
            msg += f" Day entry #{day_entry_id} {day_action} and {link_action}."
    elif entry_type_id:
        msg = f"Fetched {len(flat)} Garmin fields for {target_date} but failed to create entry: {'; '.join(errors)}"
    else:
        msg = f"Fetched {len(flat)} Garmin fields for {target_date} but no entry created — go to Settings > Garmin Connect, select an Entry Type and click 'Auto-create all columns'."

    return {
        "status": "success" if synced_entry_id else "warning",
        "date": target_date,
        "fields_fetched": list(flat.keys()),
        "entry_id": synced_entry_id,
        "entry_created": entry_was_created,
        "day_entry_id": day_entry_id,
        "day_entry_created": day_entry_created,
        "errors": errors,
        "message": msg,
    }

