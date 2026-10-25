from datetime import date
from ..db import get_conn


def next_id(entity: str) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, prefix, next_no, reset_period, last_reset "
            "FROM naming_series WHERE entity = ?", (entity,)
        ).fetchone()
        if not row:
            raise ValueError(f"No naming series for '{entity}'")

        current_year = date.today().year
        year_suffix = f"{(current_year % 100):02d}{(current_year + 1) % 100:02d}"

        if row["reset_period"] == "yearly":
            last = row["last_reset"] or ""
            if not last.startswith(str(current_year)):
                conn.execute(
                    "UPDATE naming_series SET next_no = 1, last_reset = ? WHERE id = ?",
                    (str(date.today()), row["id"]),
                )
                next_no = 1
            else:
                next_no = row["next_no"]
        else:
            next_no = row["next_no"]

        result = f"{row['prefix']}-{year_suffix}-{next_no:05d}"
        conn.execute(
            "UPDATE naming_series SET next_no = next_no + 1 WHERE id = ?",
            (row["id"],),
        )
        conn.commit()
        return result
