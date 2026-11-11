"""Utilidades para formateo y parseo de marcas de tiempo."""

def seconds_to_hhmmss(seconds: float, include_brackets: bool = False) -> str:
    """Convierte segundos a formato HH:MM:SS."""
    seconds_int = int(round(seconds))
    hours = seconds_int // 3600
    minutes = (seconds_int % 3600) // 60
    secs = seconds_int % 60
    res = f"{hours:02d}:{minutes:02d}:{secs:02d}"
    if include_brackets:
        return f"[{res}]"
    return res

def seconds_to_tag(seconds: float) -> str:
    """Convierte segundos a formato compacto para nombres de archivo: 013420 (01h 34m 20s)."""
    seconds_int = int(round(seconds))
    hours = seconds_int // 3600
    minutes = (seconds_int % 3600) // 60
    secs = seconds_int % 60
    return f"{hours:02d}{minutes:02d}{secs:02d}"

def hhmmss_to_seconds(hhmmss: str) -> float:
    """Convierte una cadena HH:MM:SS o MM:SS a segundos en punto flotante."""
    cleaned = hhmmss.strip("[] ()")
    parts = [float(p) for p in cleaned.split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 1:
        return parts[0]
    return 0.0
