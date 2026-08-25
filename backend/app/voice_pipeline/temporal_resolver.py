import datetime

def resolve_promised_date(extraction: dict, call_date: datetime.datetime) -> datetime.datetime | None:
    """
    Deterministic, pure function that converts the 'temporal' object into an actual date.
    Has NO side effects and NO business/scheduling logic — only does date math.
    """
    if extraction.get("intent") == "payment_refusal":
        return None

    temporal = extraction.get("temporal", {})
    temp_type = temporal.get("type", "none")

    if temp_type == "relative":
        keyword = temporal.get("relative_keyword")
        offsets = {
            "tomorrow": 1,
            "day_after_tomorrow": 2,
            "yesterday": -1,
            "day_before_yesterday": -2,
            "next_week": 7
        }
        offset = offsets.get(keyword)
        if offset is not None:
            return call_date + datetime.timedelta(days=offset)
        return None

    elif temp_type == "explicit_date":
        day = temporal.get("explicit_day")
        month = temporal.get("explicit_month")
        tense = temporal.get("tense")

        if day is None or month is None:
            return None

        year = call_date.year

        def build_date(y, m, d):
            try:
                if isinstance(call_date, datetime.datetime):
                    return datetime.datetime(
                        y, m, d,
                        call_date.hour, call_date.minute, call_date.second,
                        call_date.microsecond, call_date.tzinfo
                    )
                else:
                    return datetime.date(y, m, d)
            except ValueError:
                return None

        candidate = build_date(year, month, day)

        if tense == "future":
            if candidate is None:
                candidate = build_date(year + 1, month, day)
            if candidate >= call_date:
                return candidate
            return build_date(year + 1, month, day)

        elif tense == "past":
            if candidate is None:
                candidate = build_date(year - 1, month, day)
            if candidate <= call_date:
                return candidate
            return build_date(year - 1, month, day)

        return None

    elif temp_type == "event_based":
        return None

    elif temp_type in ("vague_period", "none"):
        return None

    return None
