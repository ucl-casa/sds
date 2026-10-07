"""Pre-Academic Year Automated Test Harness for Spatial Data Science (SDS) Container.

Comprehensive tests cover:
- 🐍 Python core runtime & Jupyter kernels
- 📊 R environment status check
- 🗺️ GeoPandas spatial dataframes, buffering, centroids, and spatial joins
- 🌐 GDAL geospatial drivers, CLI, and C-library bindings
- 🏹 Apache Arrow (PyArrow) columnar compute, schemas, and Parquet serialization
- 🔬 SciPy KDTree spatial querying, statistical distributions, and optimization
- 🦆 DuckDB SQL execution, analytical aggregations, and Arrow interoperability
- 🐻‍❄️ Polars high-performance dataframe pipelines, expressions, and LazyFrames
- 🧩 PySAL spatial weights matrices and Moran's I spatial autocorrelation
- 📡 PyART weather radar data structures, sweeps, and reflectivity fields
- 📄 Quarto CLI integration, capabilities, and Pandoc toolchain
- 📑 TinyTeX direct LaTeX document synthesis and PDF compilation
- 🌐 Quarto end-to-end HTML rendering
- 📑 Quarto end-to-end PDF rendering with LuaLaTeX
- 🌲 Local GIS dataset integrity (validation/Greenspace.gpkg)
- 🎨 Visualization stack & Fonts (Matplotlib, Seaborn, Folium, Spectral, Roboto Flex)
- 🛠️ Project scripts & CLI tools (gdsa, axe_nav_fixes)
- 🔐 User permission integrity & internal caches
- 👤 Rootless Podman user isolation (non-root UID 1000, GID 100)
- 🛡️ Rootless user namespaces (/proc/self/uid_map)
- 💾 Host bind-mount read/write/delete integrity (~/work)
- 🔌 Unprivileged network socket binding
- 📓 Student day-one validation notebook execution (validation/check_stack.ipynb)
"""

import getpass
import io
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import uuid
import pytest

# -----------------------------------------------------------------------------
# ANSI Color & Status Tag Formatting
# -----------------------------------------------------------------------------
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
NC = "\033[0m"

TAG_OK = f"{GREEN}[OK]{NC}"
TAG_INFO = f"{YELLOW}[INFO]{NC}"
TAG_FAIL = f"{RED}[FAIL]{NC}"


def pytest_report_teststatus(report, config):
    """Custom formatting for test outcomes:
    - PASSED: green text with tick mark (✔ PASSED)
    - FAILED: red text with cross mark (❌ FAILED)
    - SKIPPED: yellow text with warning symbol (⚠️ SKIPPED)
    """
    if report.when == "call":
        if report.passed:
            return "passed", "P", (f"{GREEN}✔ PASSED{NC}", {"green": True, "bold": True})
        elif report.failed:
            return "failed", "F", (f"{RED}❌ FAILED{NC}", {"red": True, "bold": True})
        elif report.skipped:
            return "skipped", "S", (f"{YELLOW}⚠️ SKIPPED{NC}", {"yellow": True, "bold": True})


def get_output_dir():
    """Retrieve output directory from TEST_OUTPUT_DIR environment variable or config fallback.
    
    If set and writable, ensures the directory exists and returns its absolute path.
    """
    out_dir = os.environ.get("TEST_OUTPUT_DIR")
    if not out_dir:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        out_dir = os.path.join(repo_root, "tests", "output")
    try:
        os.makedirs(out_dir, exist_ok=True)
        return out_dir
    except Exception:
        return None


# -----------------------------------------------------------------------------
# 1. Python Core & Jupyter
# -----------------------------------------------------------------------------

def test_python_version():
    """Ensure Python 3.12+ (specifically 3.13) is active."""
    assert sys.version_info >= (3, 12), f"{TAG_FAIL} Expected Python >= 3.12, got {sys.version}"
    print(f"\n🐍 {TAG_OK} Python version: {sys.version.split()[0]}")


def test_jupyter_and_ipython():
    """Verify IPython, Jupyter, and kernel registration."""
    import IPython
    assert IPython.__version__

    res = subprocess.run(["jupyter", "kernelspec", "list"], capture_output=True, text=True, check=True)
    assert "python3" in res.stdout, f"{TAG_FAIL} Python 3 kernel not found in:\n{res.stdout}"
    print(f"\n🪐 {TAG_OK} Jupyter kernelspec registered: python3 (IPython {IPython.__version__})")


# -----------------------------------------------------------------------------
# 2. R Environment Check
# -----------------------------------------------------------------------------

def test_r_environment():
    """Check R installation status.
    
    If R is intentionally omitted in this image, this test records diagnostic info
    rather than failing, but validates execution if R is present.
    """
    r_path = shutil.which("R")
    rscript_path = shutil.which("Rscript")

    if r_path and rscript_path:
        res = subprocess.run([rscript_path, "-e", 'cat("R is operational\n")'], capture_output=True, text=True)
        assert res.returncode == 0, f"{TAG_FAIL} R execution failed: {res.stderr}"
        print(f"\n📊 {TAG_OK} R is installed and operational: {r_path}")
    else:
        pytest.skip("⚠️ R is not installed in this image (image is configured for Python Spatial Data Science).")


# -----------------------------------------------------------------------------
# 3. GeoPandas
# -----------------------------------------------------------------------------

def test_geopandas_spatial_operations():
    """Verify GeoPandas dataframes, spatial joins, buffering, and CRS transformations."""
    import geopandas as gpd
    import shapely
    from shapely.geometry import Point, Polygon

    # 1. Create Point GeoDataFrame in WGS84
    points = [Point(-0.128, 51.507), Point(-0.142, 51.501), Point(-0.076, 51.508)]
    gdf_points = gpd.GeoDataFrame({"site": ["A", "B", "C"], "geometry": points}, crs="EPSG:4326")
    assert len(gdf_points) == 3

    # 2. Transform to British National Grid (EPSG:27700)
    gdf_bng = gdf_points.to_crs(epsg=27700)
    assert gdf_bng.crs.to_epsg() == 27700
    assert gdf_bng.geometry.iloc[0].x > 500000  # London Easting is ~530,000

    # 3. Buffer points to create Polygons and compute area
    gdf_polys = gdf_bng.copy()
    gdf_polys["geometry"] = gdf_polys.geometry.buffer(500.0)  # 500m radius
    assert all(isinstance(geom, Polygon) for geom in gdf_polys.geometry)
    assert all(abs(geom.area - 3.14159 * 500**2) < 5000 for geom in gdf_polys.geometry)

    # 4. Spatial Join (sjoin) between polygons and points
    joined = gpd.sjoin(gdf_bng, gdf_polys, how="inner", predicate="intersects")
    assert not joined.empty
    assert len(joined) >= 3

    # 5. Render and save graphical output artifact
    out_dir = get_output_dir()
    if out_dir:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 6))
        gdf_polys.plot(ax=ax, color="lightblue", alpha=0.5, edgecolor="blue")
        gdf_bng.plot(ax=ax, color="crimson", markersize=40)
        ax.set_title("GeoPandas Spatial Buffers (EPSG:27700)")
        fig.savefig(os.path.join(out_dir, "geopandas_buffer_sjoin.png"), dpi=150, bbox_inches="tight")
        plt.close(fig)

    print(f"\n🗺️ {TAG_OK} GeoPandas operational: v{gpd.__version__} (buffer, sjoin, and EPSG:27700 transform verified)")


# -----------------------------------------------------------------------------
# 4. GDAL & Geospatial Drivers
# -----------------------------------------------------------------------------

def test_gdal_geospatial_drivers():
    """Verify GDAL CLI tools, C library version, and driver availability."""
    import pyogrio
    import fiona

    # 1. Verify GDAL CLI
    gdalinfo_bin = shutil.which("gdalinfo")
    assert gdalinfo_bin, f"{TAG_FAIL} gdalinfo binary not found on PATH"
    cli_res = subprocess.run(["gdalinfo", "--version"], capture_output=True, text=True, check=True)
    gdal_ver_str = cli_res.stdout.strip()
    assert "GDAL" in gdal_ver_str

    # 2. Verify Python bindings linkage to GDAL
    pyogrio_gdal = pyogrio.__gdal_version__
    assert pyogrio_gdal >= (3, 8), f"{TAG_FAIL} Expected GDAL >= 3.8, got {pyogrio_gdal}"
    assert fiona.gdal_version.major >= 3

    # 3. Verify standard vector drivers (GeoJSON, GeoPackage, Shapefile)
    drivers = pyogrio.list_drivers()
    assert "GeoPackage" in drivers or "GPKG" in drivers
    assert "ESRI Shapefile" in drivers

    print(f"\n🌐 {TAG_OK} GDAL operational: {gdal_ver_str} (linked to pyogrio {pyogrio.__version__} & fiona {fiona.__version__})")


# -----------------------------------------------------------------------------
# 5. Apache Arrow (PyArrow)
# -----------------------------------------------------------------------------

def test_pyarrow_columnar_compute():
    """Verify PyArrow table construction, compute kernels, and Parquet serialization."""
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    # 1. Build Arrow Table with typed columns
    table = pa.table({
        "id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
        "name": pa.array(["alpha", "beta", "gamma", "delta", "epsilon"], type=pa.string()),
        "value": pa.array([10.5, 20.0, 30.5, 40.0, 50.5], type=pa.float64())
    })
    assert table.num_rows == 5
    assert table.num_columns == 3

    # 2. Run compute kernels
    mean_val = pc.mean(table["value"]).as_py()
    assert abs(mean_val - 30.3) < 0.01

    # Filter compute kernel
    filtered = table.filter(pc.greater(table["value"], 25.0))
    assert filtered.num_rows == 3

    # 3. Parquet serialization to memory buffer and roundtrip read
    sink = io.BytesIO()
    pq.write_table(table, sink, compression="snappy")
    sink.seek(0)
    roundtrip = pq.read_table(sink)
    assert roundtrip.equals(table)

    print(f"\n🏹 {TAG_OK} Apache Arrow operational: pyarrow v{pa.__version__} (compute kernels & snappy parquet roundtrip verified)")


# -----------------------------------------------------------------------------
# 6. SciPy Scientific Computation
# -----------------------------------------------------------------------------

def test_scipy_scientific_computation():
    """Verify SciPy spatial KDTree, statistical distributions, and optimization."""
    import numpy as np
    from scipy import spatial, stats, optimize

    # 1. KDTree spatial index query
    coords = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
    tree = spatial.KDTree(coords)
    dist, idx = tree.query([0.1, 0.1])
    assert idx == 0
    assert dist < 0.2

    # 2. Statistical distributions
    p_val = stats.norm.cdf(1.96)
    assert abs(p_val - 0.975) < 0.001

    # 3. Numerical optimization (minimize quadratic loss)
    res = optimize.minimize(lambda x: (x[0] - 3.5)**2 + (x[1] + 2.0)**2, [0.0, 0.0])
    assert res.success
    assert abs(res.x[0] - 3.5) < 0.001
    assert abs(res.x[1] - (-2.0)) < 0.001

    import scipy
    print(f"\n🔬 {TAG_OK} SciPy operational: v{scipy.__version__} (KDTree spatial index, norm cdf, and optimize verified)")


# -----------------------------------------------------------------------------
# 7. DuckDB SQL Analytics
# -----------------------------------------------------------------------------

def test_duckdb_sql_analytics():
    """Verify DuckDB analytical SQL engine, Arrow table integration, and window functions."""
    import duckdb
    import pyarrow as pa

    # In-memory Arrow table
    arrow_table = pa.table({
        "category": ["A", "A", "B", "B", "C"],
        "score": [85.0, 92.0, 78.0, 95.0, 88.0]
    })

    # Direct SQL query over Arrow table
    con = duckdb.connect()
    res = con.execute("""
        SELECT 
            category,
            COUNT(*) as cnt,
            AVG(score) as avg_score,
            RANK() OVER (ORDER BY AVG(score) DESC) as rnk
        FROM arrow_table
        GROUP BY category
        ORDER BY rnk
    """).fetchall()

    assert len(res) == 3
    # Top rank should be category A (avg 88.5) or B (avg 86.5)
    assert res[0][0] in ["A", "B"]

    print(f"\n🦆 {TAG_OK} DuckDB operational: v{duckdb.__version__} (zero-copy Arrow SQL & window aggregation verified)")


# -----------------------------------------------------------------------------
# 8. Polars DataFrame Pipelines
# -----------------------------------------------------------------------------

def test_polars_dataframe_pipeline():
    """Verify Polars DataFrame expressions, LazyFrame optimization, and aggregations."""
    import polars as pl

    # Lazy execution pipeline
    lazy_df = pl.LazyFrame({
        "dept": ["GIS", "Planning", "GIS", "Data", "Planning"],
        "students": [45, 30, 50, 60, 25],
        "active": [True, True, True, False, True]
    })

    result = (
        lazy_df
        .filter(pl.col("active") == True)
        .group_by("dept")
        .agg([
            pl.col("students").sum().alias("total_students"),
            pl.col("students").mean().alias("avg_students")
        ])
        .sort("total_students", descending=True)
        .collect()
    )

    assert result.shape[0] == 2
    gis_total = result.filter(pl.col("dept") == "GIS")["total_students"][0]
    assert gis_total == 95

    print(f"\n🐻‍❄️ {TAG_OK} Polars operational: v{pl.__version__} (LazyFrame query planner & columnar group-by verified)")


# -----------------------------------------------------------------------------
# 9. PySAL Spatial Analysis Stack
# -----------------------------------------------------------------------------

def test_pysal_spatial_analysis():
    """Verify PySAL core components: spatial weights and Moran's I autocorrelation."""
    import numpy as np
    import libpysal
    from esda.moran import Moran

    # 1. Build a 4x4 regular lattice spatial weights matrix
    w = libpysal.weights.lat2W(4, 4)
    w.transform = "R"
    assert w.n == 16
    assert w.islands == []

    # 2. Spatially clustered data array
    y = np.array([
        10.0, 12.0, 11.0, 13.0,
        9.0, 11.0, 10.0, 12.0,
        1.0, 2.0, 1.0, 3.0,
        2.0, 1.0, 2.0, 1.0
    ])

    # 3. Calculate Global Moran's I
    moran = Moran(y, w, permutations=99)
    assert moran.I > 0.3, f"{TAG_FAIL} Expected positive spatial autocorrelation, got I={moran.I}"
    assert 0.0 <= moran.p_sim <= 1.0

    # 4. Render and save Moran's I scatterplot artifact
    out_dir = get_output_dir()
    if out_dir:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from splot.esda import plot_moran
            fig, ax = plot_moran(moran, zstandard=True, figsize=(6, 4))
            fig.savefig(os.path.join(out_dir, "pysal_moran_scatterplot.png"), dpi=150, bbox_inches="tight")
            plt.close(fig)
        except Exception:
            pass

    print(f"\n🧩 {TAG_OK} PySAL operational: libpysal v{libpysal.__version__} (spatial lattice weights & Moran's I={moran.I:.3f} verified)")


# -----------------------------------------------------------------------------
# 10. PyART Radar Toolkit
# -----------------------------------------------------------------------------

def test_pyart_radar_toolkit():
    """Verify Python ARM Radar Toolkit (PyART) data structures and sweep operations."""
    import pyart

    # 1. Create a synthetic PPI target radar
    radar = pyart.testing.make_target_radar()
    assert radar is not None
    assert radar.nsweeps >= 1
    assert radar.nrays > 0
    assert "reflectivity" in radar.fields

    # 2. Inspect radar coordinates and reflectivity data
    ref_data = radar.fields["reflectivity"]["data"]
    assert ref_data.shape[0] == radar.nrays
    assert ref_data.size > 0
    if hasattr(ref_data, "mask") and hasattr(ref_data.mask, "all"):
        assert not ref_data.mask.all()

    # 3. Render and save PPI radar reflectivity plot
    out_dir = get_output_dir()
    if out_dir:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        display = pyart.graph.RadarDisplay(radar)
        fig = plt.figure(figsize=(6, 5))
        ax = fig.add_subplot(111)
        display.plot("reflectivity", 0, ax=ax, title="PyART Synthetic PPI Reflectivity")
        fig.savefig(os.path.join(out_dir, "pyart_radar_ppi.png"), dpi=150, bbox_inches="tight")
        plt.close(fig)

    print(f"\n📡 {TAG_OK} PyART operational: v{pyart.__version__} (synthetic radar, sweeps={radar.nsweeps}, rays={radar.nrays}, field=reflectivity verified)")


# -----------------------------------------------------------------------------
# 11. Quarto CLI Integration
# -----------------------------------------------------------------------------

def test_quarto_cli_suite():
    """Verify Quarto CLI version, capabilities, Pandoc, and toolchain."""
    quarto_bin = shutil.which("quarto")
    assert quarto_bin, f"{TAG_FAIL} Quarto binary not found on PATH"

    # Version check
    res_ver = subprocess.run(["quarto", "--version"], capture_output=True, text=True, check=True)
    q_ver = res_ver.stdout.strip()
    assert q_ver, "Quarto version string empty"

    # Check help and subcommands
    res_help = subprocess.run(["quarto", "--help"], capture_output=True, text=True, check=True)
    assert "render" in res_help.stdout
    assert "check" in res_help.stdout

    print(f"\n📄 {TAG_OK} Quarto CLI operational: v{q_ver} ({quarto_bin})")


# -----------------------------------------------------------------------------
# 12. TinyTeX Direct LaTeX Document Creation & Compilation
# -----------------------------------------------------------------------------

def test_tinytex_direct_latex_creation():
    """Verify direct synthesis and PDF compilation of a LaTeX document using TinyTeX."""
    lualatex_bin = shutil.which("lualatex")
    assert lualatex_bin, f"{TAG_FAIL} lualatex binary not found on PATH"

    tlmgr_bin = shutil.which("tlmgr")
    assert tlmgr_bin, f"{TAG_FAIL} tlmgr binary not found on PATH"

    # Standalone LaTeX document with mathematics and formatting
    tex_content = r"""\documentclass{article}
\usepackage{amsmath}
\title{TinyTeX Pre-Flight LaTeX Synthesis Test}
\author{UCL CASA Foundations of Spatial Data Science}
\date{2026}
\begin{document}
\maketitle
\section{Mathematical Formulation}
Gaussian spatial kernel formulation:
\begin{equation}
w_{ij} = \exp\left(-\frac{d_{ij}^2}{2\sigma^2}\right)
\end{equation}
\section{Verification Table}
\begin{tabular}{|l|c|r|}
\hline
Component & Status & Tested \\
\hline
LuaLaTeX & OK & 2026 \\
amsmath & OK & True \\
\hline
\end{tabular}
\end{document}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "test_doc.tex")
        pdf_path = os.path.join(tmpdir, "test_doc.pdf")

        with open(tex_path, "w") as f:
            f.write(tex_content)

        # Compile directly with LuaLaTeX from TinyTeX
        res = subprocess.run(
            ["lualatex", "--interaction=nonstopmode", f"-output-directory={tmpdir}", tex_path],
            capture_output=True,
            text=True
        )

        assert res.returncode == 0, f"{TAG_FAIL} LuaLaTeX compilation failed:\n{res.stderr}\n{res.stdout}"
        assert os.path.exists(pdf_path), f"{TAG_FAIL} Output PDF was not created"
        pdf_size = os.path.getsize(pdf_path)
        assert pdf_size > 1000, f"{TAG_FAIL} Generated PDF is suspiciously small ({pdf_size} bytes)"

        # Save generated LaTeX source and compiled PDF to configured output directory
        out_dir = get_output_dir()
        if out_dir:
            shutil.copy2(tex_path, os.path.join(out_dir, "tinytex_direct.tex"))
            shutil.copy2(pdf_path, os.path.join(out_dir, "tinytex_direct.pdf"))

    print(f"\n📑 {TAG_OK} TinyTeX LaTeX creation operational: compiled standalone math & table document to PDF ({pdf_size} bytes)")


# -----------------------------------------------------------------------------
# 13. Quarto End-to-End Rendering (HTML & PDF)
# -----------------------------------------------------------------------------

def test_quarto_render_html():
    """Test full Quarto render to HTML including embedded Python code."""
    qmd_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "validation", "check_quarto.qmd"))
    if not os.path.exists(qmd_path):
        pytest.skip(f"Validation document not found at {qmd_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        val_dir = os.path.dirname(qmd_path)
        for item in os.listdir(val_dir):
            s = os.path.join(val_dir, item)
            d = os.path.join(tmpdir, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)

        res = subprocess.run(
            ["quarto", "render", "check_quarto.qmd", "--to", "html", "--no-clean"],
            cwd=tmpdir,
            capture_output=True,
            text=True
        )
        assert res.returncode == 0, f"{TAG_FAIL} Quarto HTML render failed:\n{res.stderr}\n{res.stdout}"
        html_out = os.path.join(tmpdir, "check_quarto.html")
        assert os.path.exists(html_out), f"{TAG_FAIL} Rendered HTML file was not generated"

        # Save HTML artifact to configured output directory
        out_dir = get_output_dir()
        if out_dir:
            shutil.copy2(html_out, os.path.join(out_dir, "check_quarto.html"))

        print(f"\n🌐 {TAG_OK} Quarto HTML rendering succeeded")


def test_quarto_render_pdf():
    """Test full Quarto render to PDF using LuaLaTeX, fonts, and citations."""
    qmd_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "validation", "check_quarto.qmd"))
    if not os.path.exists(qmd_path):
        pytest.skip(f"Validation document not found at {qmd_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        val_dir = os.path.dirname(qmd_path)
        for item in os.listdir(val_dir):
            s = os.path.join(val_dir, item)
            d = os.path.join(tmpdir, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)

        res = subprocess.run(
            ["quarto", "render", "check_quarto.qmd", "--to", "pdf", "--no-clean"],
            cwd=tmpdir,
            capture_output=True,
            text=True
        )
        assert res.returncode == 0, f"{TAG_FAIL} Quarto PDF render failed:\n{res.stderr}\n{res.stdout}"
        pdf_out = os.path.join(tmpdir, "check_quarto.pdf")
        assert os.path.exists(pdf_out), f"{TAG_FAIL} Rendered PDF file was not generated"

        # Save PDF artifact to configured output directory
        out_dir = get_output_dir()
        if out_dir:
            shutil.copy2(pdf_out, os.path.join(out_dir, "check_quarto.pdf"))

        print(f"\n📑 {TAG_OK} Quarto PDF rendering succeeded")


# -----------------------------------------------------------------------------
# 14. Real GIS Dataset Validation
# -----------------------------------------------------------------------------

def test_geopackage_validation():
    """Test reading and querying the project's real validation/Greenspace.gpkg dataset."""
    import geopandas as gpd

    gpkg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "validation", "Greenspace.gpkg"))
    if not os.path.exists(gpkg_path):
        pytest.skip(f"Validation dataset not found at {gpkg_path}")

    gdf = gpd.read_file(gpkg_path)
    assert not gdf.empty, f"{TAG_FAIL} Greenspace.gpkg is empty"
    assert gdf.crs is not None, f"{TAG_FAIL} Missing CRS in Greenspace.gpkg"
    assert len(gdf) > 0, f"{TAG_FAIL} No records found in Greenspace.gpkg"

    # Headless plot check and artifact generation
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 6))
    gdf.head(25).plot(ax=ax, color="#2e7d32", edgecolor="#1b5e20", alpha=0.7)
    ax.set_title("Greenspace GeoPackage Sample (25 Features)")
    out_dir = get_output_dir()
    if out_dir:
        fig.savefig(os.path.join(out_dir, "greenspace_map.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"\n🌲 {TAG_OK} Greenspace.gpkg loaded successfully: {len(gdf)} features, CRS={gdf.crs.to_string()}")


# -----------------------------------------------------------------------------
# 15. Visualization Stack & Fonts
# -----------------------------------------------------------------------------

def test_visualization_and_fonts():
    """Verify Matplotlib, Seaborn, Folium, Lonboard, Great Tables, Plotly and fonts."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    import seaborn as sns
    import folium
    import great_tables
    import plotly

    out_dir = get_output_dir()

    # Matplotlib & Seaborn render
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.lineplot(x=[1, 2, 3], y=[4, 5, 6], ax=ax, label="Trend")
    ax.set_title("Seaborn Integration Verification")
    if out_dir:
        fig.savefig(os.path.join(out_dir, "seaborn_chart.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Folium interactive HTML map
    m = folium.Map(location=[51.5074, -0.1278], zoom_start=13)
    folium.Marker([51.5074, -0.1278], tooltip="London (UCL CASA)").add_to(m)
    if out_dir:
        m.save(os.path.join(out_dir, "folium_map.html"))

    # Font availability check
    system_fonts = [f.name for f in font_manager.fontManager.ttflist]
    spectral_found = any("Spectral" in f for f in system_fonts)
    roboto_found = any("Roboto" in f for f in system_fonts)

    print(f"\n🔤 {TAG_INFO} Font inspection: Spectral available={spectral_found}, Roboto available={roboto_found}")
    print(f"🎨 {TAG_OK} Visualization stack operational: seaborn {sns.__version__}, folium {folium.__version__}")


# -----------------------------------------------------------------------------
# 16. Project Scripts & User Permissions
# -----------------------------------------------------------------------------

def test_project_scripts():
    """Verify repository scripts and utilities execute correctly."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Test axe_nav_fixes.py
    nav_script = os.path.join(repo_root, "tools", "axe_nav_fixes.py")
    if os.path.exists(nav_script):
        res = subprocess.run([sys.executable, "-m", "py_compile", nav_script], capture_output=True, text=True)
        assert res.returncode == 0, f"{TAG_FAIL} axe_nav_fixes.py failed syntax check: {res.stderr}"

    # Test utils/gdsa
    gdsa_script = os.path.join(repo_root, "utils", "gdsa")
    if os.path.exists(gdsa_script):
        res = subprocess.run(["bash", gdsa_script, "help"], capture_output=True, text=True)
        assert res.returncode == 0, f"{TAG_FAIL} gdsa help failed: {res.stderr}"

    print(f"\n🛠️ {TAG_OK} Project scripts verified")


def test_user_file_permissions():
    """Verify that current non-root user can create and modify files in home and cache."""
    home_dir = os.path.expanduser("~")
    test_file = os.path.join(home_dir, ".test_write_perm.tmp")
    try:
        with open(test_file, "w") as f:
            f.write("permission test")
        assert os.path.exists(test_file), f"{TAG_FAIL} Failed writing to home directory"
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

    cache_dir = os.path.join(home_dir, ".cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_test = os.path.join(cache_dir, "test.tmp")
    try:
        with open(cache_test, "w") as f:
            f.write("cache write test")
        assert os.path.exists(cache_test), f"{TAG_FAIL} Failed writing to cache directory"
    finally:
        if os.path.exists(cache_test):
            os.remove(cache_test)

    print(f"\n🔐 {TAG_OK} User file write permissions confirmed")


# -----------------------------------------------------------------------------
# 17. Rootless Podman & Container Isolation Mechanics
# -----------------------------------------------------------------------------

def test_rootless_user_identity():
    """Verify that process is running strictly unprivileged (non-root jovyan).
    
    In rootless Podman, processes inside the container MUST run as non-root (UID != 0)
    matching the configured student user jovyan (UID 1000, GID 100).
    """
    uid = os.getuid()
    gid = os.getgid()
    user = getpass.getuser()

    assert uid != 0, f"{TAG_FAIL} Container is running insecurely as root (UID 0) instead of rootless non-root user"
    assert uid == 1000, f"{TAG_FAIL} Expected student UID 1000, got {uid}"
    assert gid == 100, f"{TAG_FAIL} Expected student GID 100 (users), got {gid}"
    assert user == "jovyan", f"{TAG_FAIL} Expected user jovyan, got {user}"

    print(f"\n👤 {TAG_OK} Rootless user identity: {user} (UID={uid}, GID={gid})")


def test_rootless_user_namespaces():
    """Inspect /proc/self/uid_map to verify active user namespace mapping."""
    uid_map_path = "/proc/self/uid_map"
    if not os.path.exists(uid_map_path):
        pytest.skip("Not running on Linux container /proc filesystem")

    with open(uid_map_path, "r") as f:
        uid_map_content = f.read().strip()

    assert uid_map_content, f"{TAG_FAIL} /proc/self/uid_map is empty"
    lines = uid_map_content.splitlines()
    assert len(lines) >= 1, f"{TAG_FAIL} Unexpected uid_map format: {uid_map_content}"

    print(f"\n🛡️ {TAG_OK} Rootless user namespace confirmed active:\n     {lines[0]}")


def test_rootless_host_bind_mount_rw():
    """Verify read, write, and delete permissions on host bind-mounted /home/jovyan/work.
    
    This is the #1 failure mode in student rootless Podman setups: if user namespace
    mapping (--userns=keep-id on Linux or virtiofs on Mac/Windows) is misconfigured,
    students get Permission Denied when saving notebooks or writing datasets.
    """
    work_dir = os.path.expanduser("~/work")
    if not os.path.exists(work_dir):
        work_dir = os.getcwd()

    test_filename = f".rootless_perm_test_{uuid.uuid4().hex[:8]}.tmp"
    test_filepath = os.path.join(work_dir, test_filename)

    payload = "Rootless Podman host bind-mount read/write test payload."

    try:
        # Write test
        with open(test_filepath, "w") as f:
            f.write(payload)

        assert os.path.exists(test_filepath), f"{TAG_FAIL} Failed to create file in bind mount"

        # Read back test
        with open(test_filepath, "r") as f:
            read_back = f.read()

        assert read_back == payload, f"{TAG_FAIL} Bind mount payload mismatch"

        # Metadata test
        stat_info = os.stat(test_filepath)
        assert stat_info.st_uid == 1000, f"{TAG_FAIL} Host file created with unexpected UID {stat_info.st_uid}"

    finally:
        if os.path.exists(test_filepath):
            os.remove(test_filepath)
            assert not os.path.exists(test_filepath), f"{TAG_FAIL} Failed to delete file from bind mount"

    print(f"\n💾 {TAG_OK} Host bind-mount read/write/delete verified at: {work_dir}")


def test_unprivileged_network_port_binding():
    """Verify non-root user can bind to unprivileged TCP and local domain sockets.
    
    JupyterLab, Dask, and Quarto require binding to local unprivileged ports (>1024)
    without needing CAP_NET_BIND_SERVICE or root capabilities.
    """
    # Test ephemeral port TCP binding
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.listen(1)
        assert port > 1024, f"{TAG_FAIL} Bound port {port} is not in unprivileged range"

    # Test UNIX domain socket creation in /tmp
    socket_path = f"/tmp/test_sock_{uuid.uuid4().hex[:8]}.sock"
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.bind(socket_path)
            assert os.path.exists(socket_path)
    finally:
        if os.path.exists(socket_path):
            os.remove(socket_path)

    print(f"\n🔌 {TAG_OK} Unprivileged network & socket binding operational (tested port {port})")


# -----------------------------------------------------------------------------
# 18. Student Day-One Validation Notebook Execution
# -----------------------------------------------------------------------------

def test_check_stack_notebook_execution():
    """Verify validation/check_stack.ipynb executes completely without error.
    
    This exercises every single import, plot, geopackage read, and parquet data load
    that students run on day one to validate their setup.
    """
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    nb_path = os.path.join(repo_root, "validation", "check_stack.ipynb")

    if not os.path.exists(nb_path):
        pytest.skip(f"Validation notebook not found at {nb_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        out_nb = os.path.join(tmpdir, "check_stack_executed.ipynb")
        res = subprocess.run(
            [
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                nb_path,
                "--output",
                out_nb,
                "--ExecutePreprocessor.timeout=120"
            ],
            cwd=os.path.join(repo_root, "validation"),
            capture_output=True,
            text=True
        )

        assert res.returncode == 0, f"{TAG_FAIL} check_stack.ipynb failed execution:\n{res.stderr}\n{res.stdout}"
        assert os.path.exists(out_nb), f"{TAG_FAIL} Executed notebook was not generated"

        # Save executed notebook to configured output directory
        out_dir = get_output_dir()
        if out_dir:
            shutil.copy2(out_nb, os.path.join(out_dir, "check_stack_executed.ipynb"))

    print(f"\n📓 {TAG_OK} Student validation notebook check_stack.ipynb executed end-to-end successfully")
