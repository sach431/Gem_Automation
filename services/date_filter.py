import pandas as pd

# =================================================
# SAFE DATE CONVERTER (ONE SOURCE OF TRUTH)
# =================================================
def _to_timestamp(d):
    if d is None or d == "" or pd.isna(d):
        return None
    try:
        return pd.to_datetime(d)
    except Exception:
        return None


# =================================================
# QUARTER RANGE (GEM – CALENDAR QUARTER)
# =================================================
def get_quarter_range(from_date):
    """
    Returns:
    - quarter_start
    - quarter_end
    - quarter_label
    """

    ts = _to_timestamp(from_date)
    if ts is None:
        return None, None, None

    y, m = ts.year, ts.month

    if m <= 3:
        return pd.Timestamp(y, 1, 1), pd.Timestamp(y, 3, 31), f"Q1 {y}"
    elif m <= 6:
        return pd.Timestamp(y, 4, 1), pd.Timestamp(y, 6, 30), f"Q2 {y}"
    elif m <= 9:
        return pd.Timestamp(y, 7, 1), pd.Timestamp(y, 9, 30), f"Q3 {y}"
    else:
        return pd.Timestamp(y, 10, 1), pd.Timestamp(y, 12, 31), f"Q4 {y}"


# =================================================
# APPLY DATE FILTER (FINAL – GEM BEHAVIOUR)
# =================================================
def apply_date_filter(
    df,
    date_col,
    from_date=None,
    to_date=None,
    mode="quarter"   # "quarter" | "custom"
):
    """
    FINAL GEM RULES:
    ----------------
    1. Default = QUARTER
    2. Custom ONLY if mode="custom"
    3. If from_date missing → dataset MIN date
    4. To date optional for quarter
    """

    # ---------- BASIC SAFETY ----------
    if df is None or df.empty or date_col not in df.columns:
        return df, None, None, None

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    if df[date_col].dropna().empty:
        return df, None, None, None

    # ---------- NORMALIZE MODE ----------
    mode = (mode or "quarter").lower().strip()

    # =================================================
    # QUARTER MODE (DEFAULT – GEM STYLE)
    # =================================================
    if mode == "quarter":

        if from_date is None or _to_timestamp(from_date) is None:
            from_date = df[date_col].min()

        q_start, q_end, q_label = get_quarter_range(from_date)

        if q_start is None:
            return df, None, None, None

        mask = (df[date_col] >= q_start) & (df[date_col] <= q_end)
        return df.loc[mask], q_label, q_start, q_end

    # =================================================
    # CUSTOM MODE (USER OVERRIDE)
    # =================================================
    start_ts = _to_timestamp(from_date)
    end_ts   = _to_timestamp(to_date)

    if start_ts is None or end_ts is None:
        return df, None, None, None

    # 🔒 SAFETY: swap if user gives wrong order
    if end_ts < start_ts:
        start_ts, end_ts = end_ts, start_ts

    mask = (df[date_col] >= start_ts) & (df[date_col] <= end_ts)
    return df.loc[mask], "Custom Period", start_ts, end_ts
