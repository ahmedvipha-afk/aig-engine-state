"""
patch_platform_wmi.py — must be imported BEFORE pandas on this machine.

Windows WMI (_wmi.exec_query) hangs indefinitely on this machine when queried
for Win32_OperatingSystem. platform.uname() triggers this via _win32_ver().
Patching _wmi_query to raise OSError forces the non-WMI fallback path.
We then pre-call platform.uname() to populate _uname_cache so every subsequent
call is a no-op cache hit.

Usage:
    import scripts.patch_platform_wmi  # or exec this file first
    import pandas  # now works
"""
import platform as _platform
import sys as _sys


def _wmi_bypass(*args, **kwargs):
    raise OSError("WMI bypassed (patch_platform_wmi.py)")


_platform._wmi_query = _wmi_bypass

if _platform._uname_cache is None:
    try:
        _platform._uname_cache = _platform.uname()
    except Exception:
        pass
