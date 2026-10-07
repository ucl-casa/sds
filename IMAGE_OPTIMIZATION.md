# Container Image Size Optimization & Slimming Recommendations

**Target Image**: `localhost/jreades/sds:2026-arm64` / `jreades/sds:2026-amd64`  
**Current Size**: **6.12 GB** (uncompressed) / ~2.2 GB (compressed download)  
**Estimated Post-Optimization Size**: **~4.7 GB** (uncompressed) / ~1.6 GB (compressed download)  
**Total Target Reduction**: **~1.3 GB to 1.5 GB (~25% reduction)**  

---

## 1. Storage Breakdown (Current Baseline)

Inspection of `localhost/jreades/sds:2026-arm64` via `podman history` and container disk usage:

| Layer / Directory | Current Size | Contents & Purpose |
| :--- | :---: | :--- |
| **Conda Environment** (`/opt/conda`) | **3.2 GB** | Python 3.13, geospatial C libraries (GDAL, GEOS, PROJ, Arrow), PySAL, DuckDB, Polars. |
| **Base Jupyter Notebook** | **1.76 GB** | `quay.io/jupyter/minimal-notebook:notebook-7.6.2` base layer. |
| **System Libraries & Tools** (`/usr`) | **1.2 GB** | Debian base utilities, Quarto CLI (`/usr/lib/quarto`), compiler packages from `apt-base.sh`. |
| **TinyTeX LaTeX Toolchain** (`/home/jovyan/.TinyTeX`) | **452 MB** | TeX Live distribution installed by Quarto for PDF rendering. |
| **OverlayFS Duplication Layer** (`finalize.sh`) | **457 MB** | **Duplicate layer copy** caused by `chown -R jovyan` over `/home/jovyan`. |

---

## 2. Priority 1: Eliminate the OverlayFS Layer Duplication (~450 MB)

### The Issue
1. In `docker/installers/quarto.sh` (Layer 18), `quarto update tool tinytex` runs as `root`, placing **452 MB** of TinyTeX files into `/home/jovyan/.TinyTeX`.
2. In `docker/installers/finalize.sh` (Layer 28), `chown -R jovyan:users /home/jovyan` runs in a **separate RUN instruction**.
3. In container engines (Podman/Docker), modifying file ownership in a later layer copies every single modified file up into that new layer. As a result, the entire 452 MB of TinyTeX is stored **twice** inside the image.

### Recommended Action
Install TinyTeX directly as user `jovyan` (`$NB_UID`), or install it to a system-wide path (`/opt/tinytex` or `/usr/local/share/tinytex`) and symlink it to `/usr/local/bin`:
```dockerfile
# Instead of installing to /home/jovyan/.TinyTeX as root:
ENV TINYTEX_DIR=/opt/tinytex
RUN quarto install tool tinytex --no-prompt \
    && ln -s /opt/tinytex/bin/* /usr/local/bin/
```
* **Estimated Reduction**: **~450 MB** (Layer 28 drops from 457 MB to <10 MB).

---

## 3. Priority 2: Strip Python Package Test Suites (~250–350 MB)

### The Issue
Major scientific Python packages (`pandas`, `scipy`, `shapely`, `pyarrow`, `scikit-learn`, `geopandas`, `matplotlib`) ship with comprehensive internal unit tests, mock datasets, and test images inside `/opt/conda/lib/python3.13/site-packages/`. These are never imported during student teaching or coursework.

### Recommended Action
Add a cleanup step at the end of `docker/installers/conda-env.sh` (in the same `RUN` command before the layer commits):
```bash
find /opt/conda/lib/python*/site-packages/ -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find /opt/conda/lib/python*/site-packages/ -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
```
* **Estimated Reduction**: **~250 MB – 350 MB**

---

## 4. Priority 3: Prune Unused C/C++ Headers and Static Libraries (~180 MB)

### The Issue
Conda-forge packages include development headers and static archives:
- `/opt/conda/include`: **158 MB** (AWS C++ SDK headers, Arrow C++ headers, GDAL/GEOS headers).
- `/opt/conda/lib/cmake`: **19 MB** of CMake metadata.
- `/opt/conda/lib/*.a`: Static archive libraries.

Students in this module write Python and Quarto documents; they do not compile native C++ extensions against Arrow or AWS SDK headers.

### Recommended Action
In `docker/installers/conda-env.sh`, strip headers and static archives:
```bash
find /opt/conda/ -follow -type f -name '*.a' -delete
find /opt/conda/ -follow -type f -name '*.js.map' -delete
rm -rf /opt/conda/include/*
rm -rf /opt/conda/lib/cmake
```
* **Estimated Reduction**: **~180 MB**

---

## 5. Priority 4: Audit Unused Heavy Conda Dependencies (~350 MB)

### The Issue
In `conda/conda.podman.yml`, `arm_pyart` (Python ARM Radar Toolkit) is specified. Reverse dependency analysis shows `arm_pyart` pulls in:
- `vtk` and `vtk-base` (~250 MB of 3D OpenGL visualization libraries)
- `qt6` and `qt6-main` (~133 MB of desktop GUI toolkits)

In a headless container environment running JupyterLab inside a web browser, native Qt6 desktop windows and VTK OpenGL displays are unused.

### Recommended Action
Verify if `arm_pyart` is actually taught in CASA0013. If it was added for a single week or legacy project:
1. Remove `arm_pyart` from `conda.podman.yml`.
2. Alternatively, create an optional downstream extension image (e.g. `sds-radar:2026`) for students taking that specific module.
* **Estimated Reduction**: **~350 MB – 400 MB**

---

## 6. Priority 5: Apt Compiler & Build Tool Cleanup (~150 MB)

### The Issue
`docker/installers/apt-base.sh` installs `build-essential`, `gfortran`, `musl-dev`, and other compilation tools (435 MB). Since all Python geospatial dependencies are installed as pre-compiled binaries via `conda-forge`, runtime compilers are rarely needed.

### Recommended Action
Use `--no-install-recommends` on all `apt-get install` commands and purge build-time packages before the layer finishes:
```bash
apt-get install -y --no-install-recommends \
    git \
    curl \
    gdebi-core \
    ...
```
* **Estimated Reduction**: **~100 MB – 150 MB**

---

## 7. Priority 6: Build-Time Layer Squashing

### Recommended Action
When publishing the production images, use Podman's `--squash` flag in `Makefile`:
```makefile
build: check-arch
	podman build --squash --arch $(ARCH) --build-arg TARGETARCH=$(ARCH) -t $(IMG_NM) -f ./docker/Podman.master --format docker .
```
This automatically collapses all intermediate layer deletions, whiteouts, and permission changes into a single clean layer.

---

## 8. Summary of Optimization Potential

| Action | Difficulty | Safety | Disk Space Saved |
| :--- | :---: | :---: | :---: |
| Fix TinyTeX OverlayFS duplication | Low | Completely Safe | **~450 MB** |
| Prune Python package `tests/` directories | Low | Completely Safe | **~300 MB** |
| Strip `/opt/conda/include` & CMake files | Low | Completely Safe | **~180 MB** |
| Audit & remove `arm_pyart` / `vtk` / `qt6` | Medium | Verify Syllabus | **~350 MB** |
| Apt `--no-install-recommends` | Low | Completely Safe | **~100 MB** |
| **Total Cumulative Reduction** | | | **~1.38 GB** |

### Verification Protocol
After applying any size reduction step, run the verification harness to ensure no runtime regressions:
```bash
make test-harness
```
All 17 environment checks (Python, Geospatial, Quarto HTML/PDF rendering, Rootless permissions, and JupyterLab live web server) must pass.
