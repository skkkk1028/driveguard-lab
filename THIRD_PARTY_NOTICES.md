# Third-party notices

DriveGuard Lab source code is licensed under Apache-2.0. It depends on separate
third-party projects under their own terms. This file records direct runtime and
experiment dependencies verified for the v1.0 release candidate; transitive
dependency metadata remains available from Python package metadata and
`frontend/package-lock.json`.

| Component | v1.0 candidate version/range | License | Use |
| --- | --- | --- | --- |
| FastAPI | `>=0.115,<1` (verified 0.139.2 and 0.140.0) | MIT | Backend HTTP API |
| typing-extensions | `>=4.12` on Python <3.12 (verified 4.16.0) | PSF-2.0 | Python 3.11 typing compatibility |
| Uvicorn | `>=0.34,<1` (verified 0.51.0) | BSD-3-Clause | ASGI development server |
| React | 19.2.7 | MIT | Dashboard UI |
| React DOM | 19.2.7 | MIT | Dashboard rendering |
| Eclipse SUMO | 1.27.1, optional | EPL-2.0 OR GPL-2.0-or-later | Isolated headless experiments |

The repository does not copy or redistribute Eclipse SUMO binaries or source.
Installing the optional `sumo` dependency downloads its separately licensed
package. Development and test tools are not runtime requirements of the released
application; their exact resolved metadata is recorded by the relevant package
manager environment.

Project links:

- [FastAPI](https://github.com/fastapi/fastapi)
- [typing-extensions](https://github.com/python/typing_extensions)
- [Uvicorn](https://www.uvicorn.org/)
- [React](https://react.dev/)
- [Eclipse SUMO](https://sumo.dlr.de/docs/Downloads.php)
