"""
Launch an ISOLATED instance of the Yanthros Formula Brain on port 5052.

The user's own Brain is already serving on 5051 (likely under app.py). We do
not want to mutate that running service, and we do not want /brain/extend to
persist 45 piston-filler formulas into their repo's brain_extensions.json as a
side effect of this build. So: same code, same 333 formulas, same solver --
but bound to a different port with the extensions file redirected to the
scratchpad. Everything the Brain learns here is saved to a file the user can
copy into faulter-formula-brain/ if they want it to become permanent.
"""
import os
import sys

BRAIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "faulter-formula-brain")
SCRATCH = os.environ.get("TWIN_SCRATCH", "/tmp")

sys.path.insert(0, BRAIN_DIR)
import brain  # noqa: E402

# Redirect persistence away from the user's repo before anything loads.
brain.EXTENSIONS_FILE = os.path.join(SCRATCH, "brain_extensions.json")

brain.load_extensions()
graph = brain.get_graph(rebuild=True)
print(f"isolated Formula Brain on port 5052 | nodes={graph['node_count']} edges={graph['edge_count']}")
print(f"extensions persist to: {brain.EXTENSIONS_FILE}")
sys.stdout.flush()

brain.app.run(host="127.0.0.1", port=5052, debug=False, use_reloader=False)
