"""MCP server exposing safe, reversible tools for controlling the local Windows desktop.

Run standalone via stdio transport; spawned as a subprocess by GraphAgentService
through MultiServerMCPClient. Do not import this module elsewhere for its side
effects (it starts an MCP server when run as __main__), only its tool logic if reused.
"""

import base64
import io
import os
import subprocess

import psutil
from comtypes import CoInitialize, CoUninitialize
from mcp.server.fastmcp import FastMCP
from mss import MSS
from PIL import Image
from pycaw.pycaw import AudioUtilities

mcp_app = FastMCP("desktop-tools")


@mcp_app.tool()
def take_screenshot() -> str:
    """Capture the primary monitor and return a base64-encoded PNG image string."""
    try:
        with MSS() as sct:
            monitor = sct.monitors[1]
            shot = sct.grab(monitor)
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"failed to capture screenshot: {e}") from e


@mcp_app.tool()
def get_system_info() -> dict:
    """Return current CPU%, RAM usage, and GPU usage (if an NVIDIA GPU is present)."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
    except Exception as e:
        raise RuntimeError(f"failed to read CPU/RAM info: {e}") from e

    gpu: dict | str
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        util, mem_used, mem_total = (v.strip() for v in result.stdout.strip().split(","))
        gpu = {"gpu_percent": float(util), "vram_used_mb": float(mem_used), "vram_total_mb": float(mem_total)}
    except Exception:
        # Intentionally swallowed, not re-raised: no NVIDIA GPU / no driver is
        # an expected, normal condition on many machines, not a tool failure.
        gpu = "unavailable"

    return {
        "cpu_percent": cpu_percent,
        "ram_percent": mem.percent,
        "ram_used_gb": round(mem.used / (1024**3), 2),
        "ram_total_gb": round(mem.total / (1024**3), 2),
        "gpu": gpu,
    }


@mcp_app.tool()
def launch_app(target: str) -> str:
    """Launch an application, open a file, or open a URL.

    target can be an app name (e.g. 'notepad'), a full path to an executable
    or file, or a URL (e.g. 'https://example.com'). Uses the OS default
    handler, so files open in their associated application and URLs open in
    the default browser.
    """
    try:
        os.startfile(target)
        return f"Launched {target}"
    except FileNotFoundError:
        return f"Could not find or launch '{target}'"
    except OSError as e:
        return f"Failed to launch '{target}': {e}"


def _get_volume_interface():
    return AudioUtilities.GetSpeakers().EndpointVolume


@mcp_app.tool()
def get_volume() -> float:
    """Get the current system master volume as a percentage (0-100)."""
    CoInitialize()
    try:
        volume = _get_volume_interface()
        return round(volume.GetMasterVolumeLevelScalar() * 100, 1)
    finally:
        CoUninitialize()


@mcp_app.tool()
def set_volume(level: float) -> str:
    """Set the system master volume to a percentage (0-100, values outside this range are clamped)."""
    CoInitialize()
    try:
        clamped = max(0.0, min(100.0, level))
        volume = _get_volume_interface()
        volume.SetMasterVolumeLevelScalar(clamped / 100, None)
        return f"Volume set to {clamped}%"
    finally:
        CoUninitialize()


if __name__ == "__main__":
    mcp_app.run(transport="stdio")
