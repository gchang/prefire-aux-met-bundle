"""Split MERRA-2 daily files into single-time files named like GEOS-IT equal-angle files,
so that PREFIRE_AUX_MET can run on public MERRA-2 in its GEOSIT_equal_angle mode.

Usage: python merra2_as_geosit.py MERRA2_DIR OUT_DIR HH [HH ...]

  MERRA2_DIR  folder holding the MERRA-2 files of one UTC day (inst3_3d_asm_Nv,
              inst1_2d_asm_Nx, tavg1_2d_lnd_Nx, tavg1_2d_ocn_Nx) and the constant
              file const_2d_asm_Nx
  OUT_DIR     folder to write to (created if needed); use it as MET_AN_DIR
  HH          every UTC hour that the orbit's frames fall in, for example 7 8 9 for
              an orbit from 07:57 to 09:33. The 1-hourly collections keep these hours
              and the hour on each side; the 3-hourly collection keeps the 3-hourly
              steps that bracket them.

This is a stand-in, not the product's real input. The operational AUX-MET product is
made from GEOS-IT, which GMAO provides only to approved instrument teams. MERRA-2 comes
from the same GEOS-5 system and uses the same file conventions, variable names and
0.625 x 0.5 degree grid (576 x 361) as GEOS-IT's equal-angle files, so the code reads it
unchanged. The values are those of a different reanalysis, so every field that comes
from the analysis differs from the official product, as two reanalyses do.

Only the variables AUX-MET reads are copied, unchanged (same type, packing and fill
value). The output names follow the GEOS-IT pattern the code searches for
(GEOS.it.asm.<collection>_glo_L576x361_<slv|v72>.GEOS*.<YYYY-MM-DDTHHMM>.V01.nc4); the
code takes the analysis time from the name. The constant file gets a fixed time stamp,
since the code finds it by "*asm_const_*nc4" alone.
"""
import glob
import os
import sys

import netCDF4

COLLECTIONS = {
    # MERRA-2 collection: (GEOS-IT collection it stands in for, variables AUX-MET reads)
    "inst3_3d_asm_Nv": ("asm_inst_3hr_glo_L576x361_v72",
                        ["PHIS", "T", "QV", "O3", "H", "U", "V", "OMEGA"]),
    "inst1_2d_asm_Nx": ("asm_inst_1hr_glo_L576x361_slv",
                        ["TS", "T2M", "T10M", "PS", "TQV", "U10M", "V10M"]),
    "tavg1_2d_lnd_Nx": ("lnd_tavg_1hr_glo_L576x361_slv", ["TSURF", "FRSNO"]),
    "tavg1_2d_ocn_Nx": ("ocn_tavg_1hr_glo_L576x361_slv", ["FRSEAICE"]),
    "const_2d_asm_Nx": ("asm_const_0hr_glo_L576x361_slv", ["FRLAND", "FRLANDICE"]),
}

USAGE = "usage: python merra2_as_geosit.py MERRA2_DIR OUT_DIR HH [HH ...]"


def write_one(src, ti, out_fpath, varnames):
    """Write time step ti of the given variables of src to a new file."""
    with netCDF4.Dataset(out_fpath, "w", format="NETCDF4") as dst:
        dst.setncatts({k: src.getncattr(k) for k in src.ncattrs()})
        for d in ("lon", "lat", "lev"):
            if d in src.dimensions:
                dst.createDimension(d, len(src.dimensions[d]))
        dst.createDimension("time", 1)
        for cv in ("lon", "lat", "lev", "time"):
            if cv not in src.variables:
                continue
            v = src.variables[cv]
            o = dst.createVariable(cv, v.dtype, v.dimensions)
            o.setncatts({k: v.getncattr(k) for k in v.ncattrs()})
            o[:] = v[ti:ti + 1] if cv == "time" else v[:]
        for vn in varnames:
            v = src.variables[vn]
            fill = v.getncattr("_FillValue") if "_FillValue" in v.ncattrs() else None
            o = dst.createVariable(vn, v.dtype, v.dimensions, zlib=True, complevel=1,
                                   fill_value=fill)
            o.setncatts({k: v.getncattr(k) for k in v.ncattrs() if k != "_FillValue"})
            v.set_auto_maskandscale(False)
            o.set_auto_maskandscale(False)
            o[:] = v[ti:ti + 1]


def keep_time(mname, t, hours):
    """Whether the time step t of collection mname is needed for the given hours."""
    if mname.startswith("inst3"):
        # 3-hourly: the steps within 3 hours of an orbit hour, plus the next one
        return any(abs(t.hour - h) < 3 or t.hour == h - (h % 3) + 3 for h in hours)
    # 1-hourly: the orbit hours and the hour on each side
    return t.hour in hours or t.hour + 1 in hours or t.hour - 1 in hours


def main(in_dir, out_dir, hours):
    os.makedirs(out_dir, exist_ok=True)
    for mname, (gname, varnames) in COLLECTIONS.items():
        fpaths = sorted(glob.glob(os.path.join(in_dir, f"MERRA2_*.{mname}.*.nc4")))
        if not fpaths:
            sys.exit(f"merra2_as_geosit.py: no MERRA2_*.{mname}.*.nc4 file in {in_dir}")
        if mname.startswith("const"):
            fpaths = fpaths[:1]
        for fpath in fpaths:
            with netCDF4.Dataset(fpath) as src:
                times = netCDF4.num2date(src.variables["time"][:],
                                         src.variables["time"].units)
                for ti, t in enumerate(times):
                    if mname.startswith("const"):
                        stamp = "2000-01-01T0000"
                    elif keep_time(mname, t, hours):
                        stamp = t.strftime("%Y-%m-%dT%H%M")
                    else:
                        continue
                    out = os.path.join(out_dir,
                                       f"GEOS.it.asm.{gname}.GEOS5124.{stamp}.V01.nc4")
                    write_one(src, ti, out, varnames)
                    print(out, os.path.getsize(out))
                    if mname.startswith("const"):
                        break


if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[1] in ("-h", "--help"):
        sys.exit(USAGE)
    try:
        hours = [int(h) for h in sys.argv[3:]]
    except ValueError:
        sys.exit(USAGE)
    if any(h < 0 or h > 23 for h in hours):
        sys.exit(USAGE)
    main(sys.argv[1], sys.argv[2], hours)
