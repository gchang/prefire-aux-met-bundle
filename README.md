# PREFIRE_AUX_MET bundle

The PREFIRE AUX-MET product interpolates a meteorological analysis in space and time to every footprint of the PREFIRE TIRS spectrometers: 101-level temperature, water vapor, ozone and wind profiles, surface temperature and pressure, sea ice and snow, xCO2 and xCH4, VIIRS IGBP surface type fractions, Antarctic land and ice shelf fractions, and a preliminary surface type. It is the first product after Level 1B and feeds the mission's Level 2 products. The code is split across four repositories. This repository holds them side by side as git submodules, each pinned to the commit that was checked, so the whole algorithm can be cloned in one step:

```sh
git clone --recurse-submodules https://github.com/gchang/prefire-aux-met-bundle.git
```

## The analysis input: GEOS-IT, and MERRA-2 as a stand-in

**The official product is made from GEOS-IT, which is not public.** GMAO says GEOS-IT "is not publicly available, but is available to approved instrument teams through the NASA GES DISC"; it is not in CMR, and an ordinary Earthdata login cannot download it. Anyone outside the PREFIRE team therefore cannot run the operational mode for a PREFIRE date.

This bundle runs the code on **MERRA-2 as a stand-in for GEOS-IT**. MERRA-2 is public at GES DISC and comes from the same GEOS-5 system: same file conventions, same variable names, and the same 0.625 x 0.5 degree grid (576 x 361) as GEOS-IT's equal-angle files. `tools/merra2_as_geosit.py` splits MERRA-2 daily files into single-time files named like GEOS-IT equal-angle files, and the code then runs unchanged in its supported `GEOSIT_equal_angle` mode with ESMF interpolation. No science code is changed.

What this means for the results:

- Fields that do not come from the analysis match the official product. After the finalization step below, VIIRS surface type, xCO2, xCH4, the Antarctic land and ice shelf fractions, the pressure grid and the land fraction data source are all identical to it. In the raw file before finalization, the Antarctic fractions agree within 3e-5 and xCO2 within 0.004 ppm, which is the archive's rounding.
- **Every field that comes from the analysis differs from the official product, as two reanalyses do.** For SAT1 orbit 01877 (2024-10-07, 52,880 footprints): `temp_profile` mean absolute difference 1.2 K (r = 0.994), `skin_temp` 1.05 K, `surface_pressure` 0.45 hPa, `total_column_wv` 1.2 mm, winds 1.7 to 1.9 m/s (r = 0.97), `omega_profile` r = 0.75. `merged_surface_type_prelim` gives the same class at 96.4% of footprints; the rest differ in sea ice and snow classes, which come from the analysis.
- The product records its analysis in the `met_analysis_ID` attribute of the `Aux-Met` group, so a MERRA-2 run is labeled with the MERRA-2 collection titles and `GEOSIT_equal_angle`, not "GEOS-IT".

A team member with GEOS-IT access runs the same code on GEOS-IT files instead (see "Operational mode" below).

## Submodules

| Submodule | Upstream | Commit | Role |
|---|---|---|---|
| `PREFIRE_AUX_MET` | https://github.com/UW-PREFIRE/PREFIRE_AUX_MET | 19cdc59ade9c96c2742a475b77fefcaa1629dcab (tag `R01`) | the AUX-MET product code (`dist/produce_AUX.py`) |
| `PREFIRE_PRD_GEN` | https://github.com/UW-PREFIRE/PREFIRE_PRD_GEN | e3933a389894d1af081b3d0bbac4aa0eb27019bc (tag `R01`) | NetCDF read and write helpers, and the finalization step |
| `PREFIRE_tools` | https://github.com/UW-PREFIRE/PREFIRE_tools | 3b590a6eba09ce596e193ad1e04f636a8b7c3d58 (tag `R01`) | time and file utilities |
| `PREFIRE_sim_tools` | https://github.com/gchang/prefire-sim-tools (copy of https://github.com/UW-PREFIRE/PREFIRE_sim_tools at R01, 9cf1becfbd4ffab850766bcf828c3ec0364d2ef0) | 5bcf206c9fef3e7737551ed1f026ebce4e21df05 (R01.post2) | pressure-level interpolation and the 101-level PCRTM pressure grid |

Nothing inside the submodules is changed. Three are the mission's R01 releases as published. `PREFIRE_sim_tools` is a copy of the R01 release with one change: its `utils/__init__.py` no longer imports `hsremis` when the package loads. `hsremis.py` opens `UWiremis_labeigvects.nc` at import time, that data file is not public, and with the original import every program that loads `PREFIRE_sim_tools.utils` stops with `FileNotFoundError`. AUX-MET never uses `hsremis` (it uses `utils.level_interp` and `paths`), so results do not change. The copy's `MAAP_CHANGES.md` describes the change. `MAAP_CHANGES.md` in this repository lists every choice made in this bundle.

All four repositories are MIT-licensed by the PREFIRE Mission Team; each keeps its own LICENSE. The official ASDC R01 AUX-MET products report `PREFIRE_AUX_MET 1.0.8`, the version in `PREFIRE_AUX_MET/VERSION.txt` at this commit.

## Finding the sibling packages

`PREFIRE_AUX_MET`'s README offers two ways to find its siblings: symbolic links in `PREFIRE_AUX_MET/source/`, or adding each sibling's Python source directory to `PYTHONPATH`. This bundle uses `PYTHONPATH`:

```sh
source bundle_env.sh    # from the bundle root
```

`bundle_env.sh` also sets `PYTHONDONTWRITEBYTECODE=1`: `PREFIRE_tools` tracks three `.pyc` files, and if Python rewrites them the product's provenance says `(modified)`.

## Software

Python 3.10 from conda-forge with the packages in `PREFIRE_AUX_MET/README.md`, plus git (to record the code versions in the product) and unzip. `environment.yml` at the bundle root lists exactly this set. From the bundle root:

```sh
conda env create -f environment.yml    # creates the conda env prefire_aux_met; the solve took 1.5 minutes
conda activate prefire_aux_met
```

The pinned versions in `PREFIRE_AUX_MET/conda_env.list` (esmf 8.4.2, h5py 3.10, netcdf4 1.6.5) no longer solve together on conda-forge, so the file is unpinned. It gave python 3.10.22, numpy 2.2.6, scipy 1.15.2, netcdf4 1.7.4, h5py 3.16.0, esmf/esmpy 8.9.1 (MPICH build), mpich 5.0.2, cartopy 0.25.0 and shapely 2.1.2. mpi4py and pyhdf, also named in that README, are left out: nothing on the run path imports them.

CPU only, one core. No GPU, scheduler or licensed software. MPI is needed only in the operational cubed-sphere mode, below.

## Data

All public. ASDC and GES DISC need an Earthdata login (for example a `~/.netrc` entry for `urs.earthdata.nasa.gov` and `curl -n -L -c cookies -b cookies -O <url>`); GES DISC also asks each Earthdata account to approve its application once ("NASA GESDISC DATA ARCHIVE", under Applications in the Earthdata profile). Zenodo needs no login.

| What | Where | Size |
|---|---|---|
| Ancillary data: VIIRS IGBP surface type 2020 to 2023, BAS Antarctic coastlines, CO2 and CH4 fits, GEOS-5 level coefficients | `PREFIRE_AUX_MET-larger_ancillary-rev_2025-01-06.zip`, Zenodo record 17080630 (https://zenodo.org/records/17080630), CC-BY-4.0, md5 4bbb8b1c1075729c68339b5bcb2a9540 | 129 MB |
| The orbit's PREFIRE 1B-RAD granule | NASA LaRC ASDC, collection `PREFIRE_SAT1_1B-RAD` or `PREFIRE_SAT2_1B-RAD`, version R01 | about 27 MB |
| MERRA-2, the UTC day of the orbit: 3-hourly model-level state `inst3_3d_asm_Nv` (M2I3NVASM), hourly single-level `inst1_2d_asm_Nx` (M2I1NXASM), hourly land `tavg1_2d_lnd_Nx` (M2T1NXLND), hourly ocean `tavg1_2d_ocn_Nx` (M2T1NXOCN) | GES DISC, version 5.12.4 | 2.26 GB + 201 MB + 213 MB + 117 MB |
| MERRA-2 constants `const_2d_asm_Nx` (M2C0NXASM) | GES DISC, version 5.12.4 | 1.2 MB |

For the example orbit, SAT1 01877 on 2024-10-07:

```
https://zenodo.org/api/records/17080630/files/PREFIRE_AUX_MET-larger_ancillary-rev_2025-01-06.zip/content
https://data.asdc.earthdata.nasa.gov/asdc-prod-protected/PREFIRE/PREFIRE_SAT1_1B-RAD_R01/2024.10.07/PREFIRE_SAT1_1B-RAD_R01_P00_20241007075724_01877.nc
https://data.gesdisc.earthdata.nasa.gov/data/MERRA2/M2I3NVASM.5.12.4/2024/10/MERRA2_400.inst3_3d_asm_Nv.20241007.nc4
https://data.gesdisc.earthdata.nasa.gov/data/MERRA2/M2I1NXASM.5.12.4/2024/10/MERRA2_400.inst1_2d_asm_Nx.20241007.nc4
https://data.gesdisc.earthdata.nasa.gov/data/MERRA2/M2T1NXLND.5.12.4/2024/10/MERRA2_400.tavg1_2d_lnd_Nx.20241007.nc4
https://data.gesdisc.earthdata.nasa.gov/data/MERRA2/M2T1NXOCN.5.12.4/2024/10/MERRA2_400.tavg1_2d_ocn_Nx.20241007.nc4
https://data.gesdisc.earthdata.nasa.gov/data/MERRA2_MONTHLY/M2C0NXASM.5.12.4/1980/MERRA2_101.const_2d_asm_Nx.00000000.nc4
```

For another date, change the date in the four daily MERRA-2 URLs (`YYYY/MM/` folder and `YYYYMMDD` in the name). The stream number in the name is `400` for most dates since 2011, but a few reprocessed months use `401`, so check the name in the GES DISC folder listing. The constant file is the same for every date. An orbit that crosses midnight UTC needs both days; the helper below has only been checked with one day.

The official product, for comparison: `https://data.asdc.earthdata.nasa.gov/asdc-prod-protected/PREFIRE/PREFIRE_SAT1_AUX-MET_R01/2024.10.07/PREFIRE_SAT1_AUX-MET_R01_P00_20241007075724_01877.nc` (58 MB; collection `PREFIRE_SAT1_AUX-MET`, R01).

## Running one orbit

From the bundle root, with the downloads in `/path/to/downloads` (the four MERRA-2 daily files and the constant file together in `/path/to/downloads/merra2`). Every other folder below is created by the commands.

```sh
source bundle_env.sh

# Ancillary data, unpacked where the code looks for it (PREFIRE_AUX_MET/dist/ancillary/, ignored by git)
(cd PREFIRE_AUX_MET/dist && unzip -q /path/to/downloads/PREFIRE_AUX_MET-larger_ancillary-rev_2025-01-06.zip)

# Record the code versions in PREFIRE_AUX_MET/dist/prdgit_version.txt; produce_AUX.py needs it
python PREFIRE_AUX_MET/dist/determine_prdgit.py

# The MERRA-2 stand-in: one file per analysis time, named like GEOS-IT equal-angle files.
# The hours are every UTC hour the orbit spans: orbit 01877 starts at 07:57:24 (the time in the
# granule's name) and ends about 95 minutes later, at 09:33.
python tools/merra2_as_geosit.py /path/to/downloads/merra2 /path/to/met 7 8 9

mkdir -p /path/to/raw /path/to/tmp
export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PACKAGE_TOP_DIR=$PWD/PREFIRE_AUX_MET ANCILLARY_DATA_DIR=$PWD/PREFIRE_AUX_MET/dist/ancillary \
       OUTPUT_DIR=/path/to/raw TMP_DIR=/path/to/tmp \
       ANALYSIS_SOURCE=GEOSIT_equal_angle INTERP_METHOD=ESMF MET_AN_DIR=/path/to/met \
       ANCSIM_MODE=NONE PRODUCT_FULLVER=R01_P00 \
       ATRACK_IDX_RANGE_0BI=ATRACK_IDXRANGE_0BASED_INCLUSIVE:0:END \
       L1B_RAD_FILE=/path/to/downloads/PREFIRE_SAT1_1B-RAD_R01_P00_20241007075724_01877.nc
python PREFIRE_AUX_MET/dist/produce_AUX.py
```

The product is `/path/to/raw/raw-PREFIRE_SAT1_AUX-MET_R01_P00_20241007075724_01877.nc` (about 97 MB). The helper writes 19 files (541 MB) for this orbit in about half a minute: the constants, the 3-hourly state at 06, 09 and 12 UTC, and the hourly single-level, land and ocean fields from 06 to 10 UTC; the code uses those that bracket the orbit and stops with `FileNotFoundError` naming the file if one is missing. The configuration is read only from these environment variables; `produce_AUX.py` takes no arguments. `PREFIRE_AUX_MET/README.md` describes each variable.

The mission's own test script, `PREFIRE_AUX_MET/test/run.sh`, sets the same variables for two short frame ranges (SAT1 01877 and SAT2 02040) in cubed-sphere mode, with inputs in `PREFIRE_AUX_MET/test/inputs/`. To use it with the stand-in, copy it to `my-run.sh`, set `ANALYSIS_SOURCE="GEOSIT_equal_angle"`, and point `L1B_cfg_str1` and `MET_AN_DIR` at your files.

### Finalization into the archived form

The mission archives AUX-MET after a second step in `PREFIRE_PRD_GEN`, which rounds the fields to their `least_significant_digit`, compresses them and adds the archive's metadata. From the bundle root, after `source bundle_env.sh`:

```sh
python PREFIRE_PRD_GEN/dist/determine_prdgit.py    # once; the finalization step needs it
mkdir -p /path/to/final
export PACKAGE_TOP_DIR=$PWD/PREFIRE_PRD_GEN ANCILLARY_DATA_DIR=$PWD/PREFIRE_PRD_GEN/dist/ancillary \
       OUTPUT_PRODUCT_DIR=/path/to/final OUTPUT_OPTIONS="" PRD_GEN_BASIC_ONLY=1 \
       INPUT_FPATH_OR_FPREFIX=/path/to/raw/raw-PREFIRE_SAT1_AUX-MET_R01_P00_20241007075724_01877.nc
python PREFIRE_PRD_GEN/dist/produce_PRD.py
```

`PRD_GEN_BASIC_ONLY=1` skips the browse image and the CMR metadata file, which need matplotlib, cartopy's Natural Earth downloads, geopandas and other packages that are not in `environment.yml`.

## Operational mode (GEOS-IT, cubed sphere)

The mission runs `ANALYSIS_SOURCE=GEOSIT_cubed_sphere` with `INTERP_METHOD=ESMF` on GEOS-IT C180 files. With GEOS-IT access, put these files for the orbit's times in `MET_AN_DIR` (flat, or one subfolder level) and skip the helper:

- `GEOS.it.asm.asm_const_0hr_glo_C180x180x6_slv.GEOS*.nc4` (constants, any date)
- `GEOS.it.asm.asm_inst_1hr_glo_C180x180x6_slv.GEOS*.<YYYY-MM-DDTHH00>.V01.nc4`, every hour from the hour before the orbit to the hour after
- `GEOS.it.asm.lnd_tavg_1hr_glo_C180x180x6_slv...` and `ocn_tavg_1hr...` at HH30 bracketing the orbit
- `GEOS.it.asm.asm_inst_3hr_glo_C180x180x6_v72...` at the 3-hourly times bracketing the orbit

In this mode `PREFIRE_AUX_MET/source/PREFIRE_AUX_MET/utils/interp_ESMF.py` (lines 283 to 290) starts `mpirun -n 6 python run_ESMF_cube_mpi-GEOSIT.py`, one MPI process per cube face, using the `mpirun` on `PATH` (MPICH from `environment.yml`). It is one machine only; the six processes ran fine on two cores in an earlier check. The equal-angle mode used above needs no MPI. The equal-angle GEOS-IT files (`L576x361`) also work, in the mode used above.

An earlier check ran the cubed-sphere ESMF step under `mpirun -n 6` on the same orbit with GMAO's public GEOS-IT C180 sample files (2018): the time-invariant land fraction matched the official product within 1.1e-4 (its rounding) at all 52,880 footprints.

## Run time, memory and disk

About 21 to 24 minutes on one core for a full orbit (6,610 frames, 52,880 footprints), peak memory 4.7 GB; finalization takes a few seconds and 0.5 GB. About 19 to 22 minutes of that is the VIIRS surface type classification, which does not depend on the analysis, so a GEOS-IT run takes about as long. Peak memory is about 4 GB even for a few hundred frames. The code supports frame ranges (`ATRACK_IDX_RANGE_0BI`, for example `ATRACK_IDXRANGE_0BASED_INCLUSIVE:0:3304`), and each range writes its own raw file named after the range, so an orbit can be split across processes; merging such parts with the finalization step was not checked for AUX-MET.

Disk: 2.8 GB of MERRA-2 downloads, 541 MB of stand-in files, 129 MB zip plus 138 MB unpacked ancillary data, and the 97 MB raw product. The MERRA-2 daily files can be deleted once the helper has run.

## Known issue: fill values in two fields

`land_surface_temp` and `snow_cover` can hold values up to about 1e11 at a few coastal footprints. GEOS land fields are 1e15 over water, and `interp_ESMF.py` (line 195 for equal-angle, 345 for cubed sphere) marks an interpolated value as missing only above `fill * 1e-4`, so a small bilinear weight on a water neighbor gets through. The official R01 granule has the same two footprints (7.06e10) in orbit 01877. This bundle leaves the R01 code as released.

## Checked on 2026-10-27

From a fresh `git clone --recurse-submodules` placed under a folder path of 221 characters, with the environment from `environment.yml` and without `UWiremis_labeigvects.nc`, the commands above ran as written for SAT1 orbit 01877 (all 6,610 frames) on the MERRA-2 stand-in for 2024-10-07, with no network. `produce_AUX.py` took 23 min 54 s on one core with a 4.73 GB peak, and finalization took 5 s. The product's provenance lists the pinned commits with no `(modified)`, and the submodules stayed clean. The comparison with the official ASDC R01 granule is the same, field for field, as an earlier run of the same R01 code on the same stand-in, made outside this bundle: 6,610 of 6,610 frames matched, and the numbers are the ones given under "The analysis input" above. After finalization, every field that does not depend on the analysis is identical to the official granule.
