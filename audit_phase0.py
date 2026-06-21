import pandas as pd

path = r"Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
df = pd.read_csv(path, low_memory=False)

print("=== EVENT TYPE ===")
print(df["event_type"].value_counts().to_string())

print("\n=== EVENT CAUSE (top 15) ===")
print(df["event_cause"].value_counts().head(15).to_string())

print("\n=== STATUS ===")
print(df["status"].value_counts().to_string())

print("\n=== PRIORITY ===")
print(df["priority"].value_counts().to_string())

print("\n=== POLICE STATIONS ===")
print(f"Unique stations: {df['police_station'].nunique()}")
print(df["police_station"].value_counts().head(10).to_string())

print("\n=== CORRIDORS (top 10) ===")
print(df["corridor"].value_counts().head(10).to_string())

print("\n=== VEH TYPE (top 10) ===")
print(df["veh_type"].value_counts(dropna=False).head(10).to_string())

print("\n=== MODULE 6.2 GATE (truck columns) ===")
for col in ["age_of_truck", "cargo_material", "reason_breakdown"]:
    print(f"{col}: {df[col].notna().mean() * 100:.1f}% filled")

bd = df[df["event_cause"] == "vehicle_breakdown"]
print(f"\nvehicle_breakdown events: {len(bd)} ({len(bd) / len(df) * 100:.1f}%)")
for col in ["age_of_truck", "cargo_material", "reason_breakdown", "veh_type"]:
    print(f"  {col} in breakdowns: {bd[col].notna().mean() * 100:.1f}% filled")

for col in ["start_datetime", "created_date", "resolved_datetime", "closed_datetime"]:
    df[f"{col}_p"] = pd.to_datetime(df[col], utc=True, errors="coerce")

print("\n=== TIMESTAMP PARSE RATES ===")
for col in ["start_datetime", "created_date", "resolved_datetime", "closed_datetime"]:
    print(f"{col}: {df[f'{col}_p'].notna().mean() * 100:.1f}% parseable")

df["resolution_time"] = (
    df["resolved_datetime_p"] - df["start_datetime_p"]
).dt.total_seconds() / 60
df["clearance_time"] = (
    df["closed_datetime_p"] - df["created_date_p"]
).dt.total_seconds() / 60

print(
    f"\nresolution_time available: {df['resolution_time'].notna().sum()} "
    f"({df['resolution_time'].notna().mean() * 100:.1f}%)"
)
print(
    f"clearance_time available: {df['clearance_time'].notna().sum()} "
    f"({df['clearance_time'].notna().mean() * 100:.1f}%)"
)
if df["resolution_time"].notna().sum() > 0:
    print(
        f"resolution_time median: {df['resolution_time'].median():.1f} min, "
        f"mean: {df['resolution_time'].mean():.1f} min"
    )
if df["clearance_time"].notna().sum() > 0:
    print(
        f"clearance_time median: {df['clearance_time'].median():.1f} min, "
        f"mean: {df['clearance_time'].mean():.1f} min"
    )

print("\n=== ASSIGNED TO POLICE (dispatch module) ===")
print(f"assigned_to_police_id filled: {df['assigned_to_police_id'].notna().mean() * 100:.1f}%")

print("\n=== DATE RANGE ===")
print(f"created_date: {df['created_date_p'].min()} to {df['created_date_p'].max()}")

print("\n=== REQUIRES ROAD CLOSURE ===")
print(df["requires_road_closure"].value_counts().to_string())

print("\n=== ZONE / JUNCTION ===")
print(f"zone filled: {df['zone'].notna().mean() * 100:.1f}%")
print(f"junction filled: {df['junction'].notna().mean() * 100:.1f}%")
