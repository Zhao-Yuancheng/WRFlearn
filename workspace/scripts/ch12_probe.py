"""ch12 素材探测：检查本地 nc 文件中的辐射相关变量。"""
import netCDF4 as nc

FILES = [
    r"d:\Code\Learn\WRF\workspace\data\ch10\wrfinput_d01.nc",
    r"d:\Code\Learn\WRF\workspace\data\ch09_io\io2_wrfout_d01_0000.nc",
    r"d:\Code\Learn\WRF\workspace\data\ch10\met_em.d01.2025-07-12_00.nc",
    r"d:\Code\Learn\WRF\workspace\data\wrfrst_d01_2025-07-12_00_05_24.nc",
]
KEYS = ["COSZEN", "SWDOWN", "SWDN", "SWUP", "GLW", "OLR", "LWUP", "LWDN",
        "O3", "CO2", "GHG", "XLAT", "XLONG", "T2", "PSFC", "SOLCON", "DECLIN",
        "AOD", "AEROD", "OA", "OL", "HRANG", "JULIAN", "XTIME", "TSK", "EMISS"]

for f in FILES:
    try:
        d = nc.Dataset(f)
    except Exception as e:
        print(f, "OPEN FAIL", e)
        continue
    vs = list(d.variables)
    hits = [v for v in vs if any(k in v.upper() for k in KEYS)]
    print("=" * 70)
    print(f)
    print("  nvars =", len(vs))
    print("  hits  =", hits)
    # Times and dims for the interesting ones
    for t in ("Times", "XTIME"):
        if t in vs:
            try:
                print(f"  {t}: {d.variables[t][:].ravel()[:3]}")
            except Exception:
                pass
    for v in hits[:8]:
        var = d.variables[v]
        try:
            print(f"    {v}: shape={var.shape} units={getattr(var, 'units', '?')} desc={getattr(var, 'description', '')[:60]}")
        except Exception:
            pass
    d.close()