"""Physics Layer -- gear-train kinematics/dynamics and the mechanical-to-
electrical current conversion. Leaf layer: no dependency on twin/,
calibration/, signature/, or detection/.

disturbance.py is still a Phase-1 stub. electrical.py implements motor_1
(V=Ri+L*di/dt+Ke*omega) as a standalone function as of the Stage 1
migration step -- not yet called by anything else in this package; see
electrical.py's own docstring. motor_2/motor_3 remain unimplemented (no
motor datasheet exists for this rig; see gear_train.py's module
docstring)."""
