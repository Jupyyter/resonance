"""Dates written in Romanian, e.g. "Joi, 2 Octombrie 2025".

Written once here and imported wherever a date is shown (the /info page, the Accesare class,
later the /log page), so the same code never exists in two places.

Python's strftime() would give English names ("Thursday", "October"), and switching the
whole computer to a Romanian locale is fragile (it differs between Windows and Linux).
So the names come from our own lists instead.
"""

from datetime import datetime

ZILE = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]  # weekday() 0 = Monday
LUNI = [
    "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie",
    "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie",
]

# The format the lab asks for: [zi din săptămână], [zi din lună] [numele lunii] [an]
FORMAT_DATA = "%A, %-d %B %Y"
FORMAT_ORA = "%H:%M:%S"


def formateaza_data(moment: datetime, format: str = FORMAT_DATA) -> str:
    """Like moment.strftime(format), but with Romanian day and month names.

    Understands every strftime code (%Y, %H, %M ...) plus:
      %A / %a  the weekday, in full / first 3 letters  (Joi / Joi)
      %B / %b  the month, in full / first 3 letters    (Octombrie / Oct)
      %-d, %-m, %-H ...  the number without a leading zero (2 instead of 02).
      Python on Linux understands "%-d" but Windows doesn't, so we handle it ourselves.
    """
    parts = []
    i = 0
    while i < len(format):
        if format[i] != "%" or i + 1 == len(format):
            parts.append(format[i])  # ordinary text is copied as it is
            i += 1
            continue

        code = format[i + 1]
        no_leading_zero = code == "-" and i + 2 < len(format)
        if no_leading_zero:
            code = format[i + 2]

        if code == "A":
            text = ZILE[moment.weekday()]
        elif code == "a":
            text = ZILE[moment.weekday()][:3]
        elif code == "B":
            text = LUNI[moment.month - 1]
        elif code == "b":
            text = LUNI[moment.month - 1][:3]
        else:
            # Any other code: let Python do it. One code at a time, so strftime() only ever
            # sees plain ASCII (Windows has trouble with letters like "ă" inside formats).
            text = moment.strftime("%" + code)

        if no_leading_zero:
            text = text.lstrip("0") or "0"
        parts.append(text)
        i += 3 if no_leading_zero else 2

    return "".join(parts)
