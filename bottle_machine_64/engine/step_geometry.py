"""
STEP assembly -> per-part wireframe.

Reads a STEP file with OpenCascade (through the small `cascadio` wheel), keeps the
assembly's own part names and nesting, and returns for every part instance its
world-space feature edges (sharp edges + open boundaries) plus bounding box.

Nothing here guesses: if the file cannot be read or contains no solid geometry the
functions raise StepReadError with a message meant to be shown to the user.
"""
import json
import math
import os
import tempfile

import numpy as np
import trimesh

try:
    import cascadio
except ImportError as e:  # pragma: no cover
    cascadio = None
    _IMPORT_ERROR = e


class StepReadError(Exception):
    pass


def _check_header(path):
    try:
        with open(path, "rb") as f:
            head = f.read(2048).decode("latin-1", errors="replace")
    except OSError as e:
        raise StepReadError(f"Cannot open the STEP file: {e}")
    if "ISO-10303-21" not in head:
        raise StepReadError("This is not a STEP file (missing the ISO-10303-21 header). "
                            "In SolidWorks use File > Save As > STEP AP214 (or AP242) for the assembly.")


def _feature_edges(mesh, sharp_deg, smooth_lines=16):
    """Edges worth drawing: where neighbouring faces fold sharper than sharp_deg,
    plus open boundary edges. Returns (n,2,3) array of segments."""
    m = mesh.copy()
    m.merge_vertices(merge_tex=True, merge_norm=True)
    if len(m.faces) == 0:
        return np.zeros((0, 2, 3))
    adj = m.face_adjacency
    ang = m.face_adjacency_angles
    sharp = m.face_adjacency_edges[ang > math.radians(sharp_deg)]
    # Round parts (shafts, pulleys, rollers) have almost no sharp edges, so they would
    # show only their end circles. Add an evenly thinned set of the gently curved edges
    # so they read as cylinders.
    smooth = m.face_adjacency_edges[(ang > math.radians(0.3)) & (ang <= math.radians(sharp_deg))]
    if len(smooth) > smooth_lines:
        smooth = smooth[:: max(1, len(smooth) // smooth_lines)]
    if len(smooth):
        sharp = np.vstack([sharp, smooth]) if len(sharp) else smooth
    # boundary edges = used by exactly one face
    es = m.edges_sorted
    uniq, counts = np.unique(es, axis=0, return_counts=True)
    boundary = uniq[counts == 1]
    pairs = np.vstack([sharp, boundary]) if len(boundary) else sharp
    if len(pairs) == 0:
        return np.zeros((0, 2, 3))
    pairs = np.unique(np.sort(pairs, axis=1), axis=0)
    return m.vertices[pairs]


def extract(step_path, sharp_deg=25.0):
    if cascadio is None:
        raise StepReadError(f"CAD reader is not installed: {_IMPORT_ERROR}")
    _check_header(step_path)
    with tempfile.TemporaryDirectory() as tmp:
        glb = os.path.join(tmp, "model.glb")
        try:
            cascadio.step_to_glb(step_path, glb, tol_linear=0.2, tol_angular=0.5)
        except Exception as e:
            raise StepReadError(f"The STEP file could not be read: {e}")
        if not os.path.exists(glb) or os.path.getsize(glb) == 0:
            raise StepReadError("The STEP file was read but contains no 3D solids.")
        scene = trimesh.load(glb, force="scene")

    graph = scene.graph
    parents = graph.transforms.parents
    base = graph.base_frame

    def ancestors(node):
        out, cur = [], parents.get(node)
        while cur is not None and cur != base:
            out.append(cur)
            cur = parents.get(cur)
        return list(reversed(out))

    parts = []
    seen_ids = {}
    all_pts = []
    for node in graph.nodes_geometry:
        transform, geom_name = graph.get(node)
        mesh = scene.geometry[geom_name]
        world = mesh.copy()
        world.apply_transform(transform)
        segs = _feature_edges(world, sharp_deg) * 1000.0  # metres -> millimetres
        verts = world.vertices * 1000.0
        if len(verts) == 0:
            continue
        pid = node
        seen_ids[pid] = seen_ids.get(pid, 0) + 1
        if seen_ids[pid] > 1:
            pid = f"{node}#{seen_ids[pid]}"
        lo, hi = verts.min(axis=0), verts.max(axis=0)
        all_pts.append(verts)
        parts.append({
            "id": pid,
            "name": node,
            "path": ancestors(node),
            "bbox_mm": [np.round(lo, 3).tolist(), np.round(hi, 3).tolist()],
            "triangles": int(len(world.faces)),
            "edge_count": int(len(segs)),
            "edges": np.round(segs.reshape(-1), 3).tolist(),
        })
    if not parts:
        raise StepReadError("The STEP file contains no solid parts to draw.")
    pts = np.vstack(all_pts)
    return {
        "source": os.path.basename(step_path),
        "unit": "mm",
        "sharp_angle_deg": sharp_deg,
        "bounds_mm": [np.round(pts.min(axis=0), 3).tolist(), np.round(pts.max(axis=0), 3).tolist()],
        "part_count": len(parts),
        "edge_total": int(sum(p["edge_count"] for p in parts)),
        "parts": parts,
    }


if __name__ == "__main__":
    import sys
    import time
    t = time.time()
    data = extract(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else None
    print(f"{data['source']}: {data['part_count']} parts, {data['edge_total']} edges, {time.time()-t:.2f}s")
    if out:
        with open(out, "w") as f:
            json.dump(data, f)
