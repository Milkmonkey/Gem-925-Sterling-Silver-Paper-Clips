#!/usr/bin/env bash
set -euo pipefail
task_source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v openscad >/dev/null
openscad --version
python3 -m venv --system-site-packages /workspace/.venvs/silver-clip
export PIP_CACHE_DIR=/workspace/.cache/silver-clip-pip
/workspace/.venvs/silver-clip/bin/python -m pip install --disable-pip-version-check -r "$task_source_dir/requirements.txt"
MPLCONFIGDIR=/tmp/silver-clip-matplotlib XDG_CACHE_HOME=/tmp/silver-clip-cache \
  /workspace/.venvs/silver-clip/bin/python -c 'import cadquery, numpy, matplotlib, PIL, vtk, trimesh, shapely; print("CAD, plotting, VTK and geometry checks import successfully")'
