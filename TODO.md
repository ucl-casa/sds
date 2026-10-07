# To Dos

## 2026 Academic Year Roadmap & Architecture Recommendations

- [ ] **Multi-Arch OCI Manifest & Unified Student Distribution**:
  - Publish unified multi-architecture manifest lists for GitHub Packages (`ghcr.io/ucl-casa/sds:2026`) and Docker Hub (`jreades/sds:2026`).
  - Standardize student documentation so all 6 platforms (Mac Intel/ARM, Windows Intel/ARM, Linux Intel/ARM) run the exact same `podman run` command without needing separate architecture tabs.
- [ ] **R Stack Strategy (Layered Extension vs Base Image)**:
  - Keep the base `sds:2026` image lean for Python Spatial Data Science.
  - If R geospatial packages (`sf`, `stars`, `tidyverse`, `IRkernel`) are needed for term 2 or specific modules, build a layered downstream image (e.g. `jreades/sds-r:2026`) inheriting from `FROM jreades/sds:2026` rather than bloating the base container by +3–4GB for all students.
- [ ] **UCL CASA Data Server Certificate & Static Mirroring**:
  - [x] Renew expired SSL/TLS certificate on `orca.casa.ucl.ac.uk` (Renewed and verified valid through Dec 31, 2026; HTTPS data downloads confirmed working).
  - [ ] Mirror teaching datasets (e.g., `2023-09-06-listings.parquet`, `Greenspace.gpkg`) to GitHub Releases or an S3/Cloudflare R2 bucket with sha256 checksums to prevent single-point-of-failure network errors during student coursework.
- [ ] **CI/CD Vulnerability Scanning**:
  - Add an automated CVE scanner step (e.g. Aquasecurity Trivy or Anchore Grype) to `.github/workflows/build-and-release.yml` to audit base packages and Python wheels prior to annual release.
- [ ] **Induction Week Pre-Flight Smoke Testing**:
  - Have PGTAs run `./tests/run_tests.sh` on reference departmental laptops (Mac Apple Silicon, Windows 11 WSL2, Ubuntu Desktop) during induction week to catch any OS-level regressions.
- [ ] **Image Size Optimization & Layer Slimming (~1.3 GB Savings)**:
  - See [IMAGE_OPTIMIZATION.md](IMAGE_OPTIMIZATION.md) for full audit.
  - Eliminate the OverlayFS Copy-on-Write duplicate copy of TinyTeX (~450 MB).
  - Strip Python package test suites (`find ... -name "tests"`) (~300 MB).
  - Prune `/opt/conda/include` headers & CMake metadata (~180 MB).
  - Audit `arm_pyart` dependency on `vtk` / `qt6` (~350 MB).
- [ ] **Native Linux Rootless Guidance in Docs**:
  - Keep `setup/_running.qmd` updated with `--userns=keep-id:uid=1000,gid=100` and `-v "$(pwd):/home/jovyan/work:z"` for native Linux students.

---

## Historical Notes (2023–2025)

1. Work out why the Intel (AMD64) image is so much larger than the Apple Silicon (ARM64) image. I can get a decent report using `docker history --format "{{.Size}}\t{{.CreatedBy}}" --no-trunc jreades/sds:2023-intel | grep -e "[G]B"` which traces the difference back to just two layers:
   - 6.52GB	`RUN |2 USERNAME=jovyan TARGETPLATFORM=linux/amd64 /bin/bash -c mamba env update -n base --quiet --file ./${yaml_nm}     && conda clean --all --yes --force-pkgs-dirs     && find /opt/conda/ -follow -type f -name '*.a' -delete     && find /opt/conda/ -follow -type f -name '*.pyc' -delete     && find /opt/conda/ -follow -type f -name '*.js.map' -delete     && pip cache purge     && rm -rf /home/$NB_USER/.cache/pip     && rm ./${yaml_nm} # buildkit`
   - 5.48GB	`RUN |2 USERNAME=jovyan TARGETPLATFORM=linux/amd64 /bin/bash -c fix-permissions $CONDA_DIR     && fix-permissions $HOME # buildkit`
   - My *guess* is that the second command's effect *depends* on the effects of the first: there are a *lot* of files modified by the `mamba` update but they end up with a different/wrong set of permissions from what the `fix-permissions` script is expecting so it then has to modify the permissions on *all* of them which almost doubles the size of image.

## Using UCL JupyterHub

### **Creating an Environment (Staff)**

1. Start up the UCL VPN.
2. Connect to [JupyterHub](https://jupyter.data-science.rc.ucl.ac.uk/)
3. Authenticate using UCL credentials.
4. Create a new terminal: File > New > Terminal

##### Incorrect Instructions from ISD

I *think* that these instructions are not correct (see below for the alternative) in the sense the use of a symlink can cause problems and duplicated environments down the line: 

```shell
course_name="casa0013"

ln -s /shared/.../casa/${course_name} $HOME/${course_name}

conda config --add envs_dirs /shared/groups/.../casa/${course_name}/envs

curl -o /tmp/casa0013.yml https://raw.githubusercontent.com/jreades/sds_env/master/conda/environment_py.yml

conda env create -n casa0013 -f /tmp/casa0013.yml
```

##### Revised Instructions

I *now* think that the correct way to do this is:

```shell
course_name="casa0013"

conda config --add envs_dirs /shared/groups/.../casa/envs

curl -o /tmp/casa0013.yml https://raw.githubusercontent.com/jreades/sds_env/master/conda/environment_py.yml

conda env create -p /shared/groups/.../casa/envs -f /tmp/casa0013.yml
```

However, note that this now means you have `.../casa/casa0013/envs/casa0013...` so it might be more sensible to set `envs_dirs` to just `...casa/envs` and then have per-module environments underneath that.

#### **Tweaks to environyment_py.yml:**

Two shortcomings in the existing approach of generating `environment_py.yml` were identified and need to be tweaked in the Makefile:

1. Remove anything with ‘linux’ in it 
2. Remove SOMPY and `mrmr`
3. Remove version from gitpython.
4. Remove python-graphviz entirely.

Additional issues may exist with replication to non-Linux systems.

### **Connecting to an Existing Environment (PGTAs & Students)**

To connect to JupyterHub:

1. Start up the UCL VPN.
2. Connect to [JupyterHub](https://jupyter.data-science.rc.ucl.ac.uk/)
3. Authenticate using UCL credentials.
4. If you see a URL that ends in `tree?` please replace this with `lab?` to get the JupyterLab interface and not the original Jupyter Notebook interface.
5. Create a new terminal: File > New > Terminal

Note that you need to replace `...` with the appropriate path (this will be obvious logged in):

```shell
course_name="casa0013"

conda config --append envs_dirs /shared/groups/.../casa/envs

jupyter contrib nbextension install --user
```

## Citing

This draws heavily on Dani Arribas-Bel's work for Liverpool. If you use this, you should cite him.

[![DOI](https://zenodo.org/badge/65582539.svg)](https://zenodo.org/badge/latestdoi/65582539)

```bibtex
@software{hadoop,
  author = {{Dani Arribas-Bel}},
  title = {\texttt{gds_env}: A containerised platform for Geographic Data Science},
  url = {https://github.com/darribas/gds_env},
  version = {3.0},
  date = {2019-08-06},
}
```

- 
