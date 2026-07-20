# DriveGuard Lab Development Rules

- Complete only the phase explicitly requested; do not implement later phases in
  advance.
- Use SI units for every physical calculation and data contract.
- Do not reference FastAPI or React from the domain layer.
- Do not scatter magic thresholds. Name, document, and centralize justified domain
  constants when they are introduced.
- Every addition of business logic must include corresponding tests.
- After changes, run tests, type checks, lint checks, and the production build.
- Do not automatically create, configure, or push to a remote repository.
- Do not integrate with real-vehicle control hardware.
- Do not describe this simulation project as a safety-certified product.
