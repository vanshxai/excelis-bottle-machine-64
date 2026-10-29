"""Twin representation -- a thin, structural wrapper around a twin's
constants dict. This is new code, not a relocation: no equivalent object
existed before this refactor (every layer just passed a plain dict
around). Kept intentionally trivial for Phase 1 -- it does not validate,
transform, or attach behavior beyond naming the shape, so existing code
that expects a plain dict (every physics/signature function) keeps
working unchanged whether it's handed a Twin's .constants or a raw dict.
"""


class Twin:
    """constants: the sampled/verified values for every soft constraint
    in constraint_registry_metal.json. signatures/dynamic_signatures/
    I_baseline_A/verified_at/round are optional, present once a twin has
    been through Calibration's search+verify loop."""

    def __init__(self, constants, signatures=None, dynamic_signatures=None,
                 i_baseline_a=None, verified_at=None, round_=None):
        self.constants = constants
        self.signatures = signatures
        self.dynamic_signatures = dynamic_signatures
        self.i_baseline_a = i_baseline_a
        self.verified_at = verified_at
        self.round = round_

    @classmethod
    def from_verified_record(cls, record):
        """Builds a Twin from the dict shape twin/store.load_verified()
        returns (i.e. gearsystem_metal_verified_twin.json's own shape,
        unchanged by this refactor -- see the migration plan's
        out-of-scope section on that file's contents).

        Note: to_record() reconstructs only the 6 fields this class
        tracks -- a load-then-save round trip through Twin would drop any
        other keys present in the raw JSON (e.g. the verified twin file's
        currently-stale capless/output_gear_removed/rpm_yellow_status
        fields). Nothing in this Phase-1 refactor's actual data flow
        performs that round trip -- calibration.search.verify() still
        builds and saves a fresh record dict directly -- so this is a
        latent caveat for a future caller, not a current behavior
        change."""
        return cls(
            constants=record["constants"],
            signatures=record.get("signatures"),
            dynamic_signatures=record.get("dynamic_signatures"),
            i_baseline_a=record.get("I_baseline_A"),
            verified_at=record.get("verified_at"),
            round_=record.get("round"),
        )

    def to_record(self):
        """Inverse of from_verified_record -- the dict shape
        twin/store.save_verified() expects."""
        return {
            "constants": self.constants,
            "signatures": self.signatures,
            "I_baseline_A": self.i_baseline_a,
            "verified_at": self.verified_at,
            "round": self.round,
            "dynamic_signatures": self.dynamic_signatures,
        }
