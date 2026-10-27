# Choices and changes in this bundle

This bundle holds PREFIRE_AUX_MET at its R01 release (https://github.com/UW-PREFIRE/PREFIRE_AUX_MET, commit `19cdc59ade9c96c2742a475b77fefcaa1629dcab`) with the three sibling repositories it needs. Nothing inside the submodules is edited. These are the deliberate choices, why each was made, and who asked for it.

## 1. PREFIRE_sim_tools comes from a copy that does not import `hsremis` at load time

- **What:** the `PREFIRE_sim_tools` submodule points to https://github.com/gchang/prefire-sim-tools at `bcbdd0b`, not to the upstream repository. That copy is upstream R01 (`9cf1becfbd4ffab850766bcf828c3ec0364d2ef0`) with one line removed: `from . import hsremis` in `PREFIRE_sim_tools/utils/__init__.py`. Its own `MAAP_CHANGES.md` has the details.
- **Why:** `hsremis.py` opens `UWiremis_labeigvects.nc` as soon as it is imported. That file is excluded by the repository's `.gitignore` and is in no public archive, so with the upstream code `dist/produce_AUX.py` stops with `FileNotFoundError` before reading any input. AUX-MET uses only `PREFIRE_sim_tools.utils.level_interp` and `PREFIRE_sim_tools.paths`; nothing in PREFIRE_AUX_MET, PREFIRE_PRD_GEN or PREFIRE_tools refers to `hsremis`. No results change.
- **Who asked:** our own change, made at the lead's request on 2026-10-27. We found the failure in our own test of AUX-MET. The registration wizard's analysis of AUX-MET did not report it: it did not read the sibling repositories.

## 2. MERRA-2 stands in for GEOS-IT

- **What:** `tools/merra2_as_geosit.py` splits public MERRA-2 daily files into single-time files named like GEOS-IT equal-angle files. The README runs the code in its supported `GEOSIT_equal_angle` + `ESMF` mode on those files. No science code is changed.
- **Why:** the operational input, GEOS-IT, is available only to approved instrument teams (GMAO), so no one outside the PREFIRE team can run the product for a PREFIRE date. MERRA-2 is public and uses the same GEOS-5 conventions, variable names and grid. This is a stated caveat, not a replacement: every field that comes from the analysis differs from the official product as two reanalyses do (README, "The analysis input"). Fields that do not depend on the analysis match the official product.
- **Who asked:** the lead's decision, 2026-10-27. The registration wizard had said GEOS-IT was behind an Earthdata login, which is wrong: an ordinary Earthdata login cannot download it.

## 3. environment.yml, unpinned

- **What:** `environment.yml` lists the packages from `PREFIRE_AUX_MET/README.md` without version pins, with the MPICH build of ESMF, plus mpich, shapely, git and unzip. mpi4py and pyhdf are left out because nothing on the run path imports them.
- **Why:** the versions pinned in `PREFIRE_AUX_MET/conda_env.list` no longer solve together on conda-forge (an hdf5, h5py and python_abi conflict). The unpinned list solves in about a minute and a half and reproduces the official product wherever the inputs agree. git is needed by `dist/determine_prdgit.py`, mpich provides the `mpirun` that the cubed-sphere mode starts, and unzip unpacks the Zenodo ancillary data.
- **Who asked:** our own choice. The registration wizard's recommendations asked for an environment file that matches `conda_env.list`, which does not solve.

## 4. PYTHONPATH and bytecode (bundle_env.sh)

- **What:** `bundle_env.sh` puts the siblings on `PYTHONPATH`, one of the two methods in `PREFIRE_AUX_MET/README.md`, and sets `PYTHONDONTWRITEBYTECODE=1`.
- **Why:** `PREFIRE_tools` tracks three `.pyc` files. If Python rewrites them, `determine_prdgit.py` stamps the product's provenance `(modified)`.
- **Who asked:** our own choice, the same as in the other PREFIRE bundles.
