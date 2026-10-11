"""ch12 子探针：O3RAD 廓线量级核查 + julian 判定。"""
import numpy as np
from pathlib import Path
from netCDF4 import Dataset

ROOT = Path(r"d:\Code\Learn\WRF")
RUN = ROOT / "source" / "WRFv4.8.0" / "WRFV4.8.0" / "run"
DATA = ROOT / "workspace" / "data"

ds = Dataset(DATA / "wrfrst_d01_2025-07-12_00_05_24.nc")
xlat = np.asarray(ds.variables["XLAT"][0]); xlon = np.asarray(ds.variables["XLONG"][0])
ij = np.unravel_index(np.argmin((xlat - 36.05) ** 2 + (xlon - 103.78) ** 2), xlat.shape)
o3 = np.asarray(ds.variables["O3RAD"][0])
p = (np.asarray(ds.variables["P"][0]) + np.asarray(ds.variables["PB"][0])) / 100.0
print("P shape:", p.shape, " top p =", p[0, ij[0], ij[1]], "hPa  surface p =", p[-1, ij[0], ij[1]], "hPa")
prof = o3[:, ij[0], ij[1]]
print("k   p(hPa)    O3RAD")
for k in range(0, p.shape[0], 3):
    print(f"{k:3d} {p[k, ij[0], ij[1]]:9.3f}  {prof[k]:.4e}")
print("last:", f"{p[-1, ij[0], ij[1]]:.3f}", f"{prof[-1]:.4e}")

# 域内极值
print("O3RAD domain min/max:", o3.min(), o3.max())
# 各层 max
for k in (0, 5, 10, 15, 20):
    print(f"  level {k}: max={o3[k].max():.4e}")

# CAM 气候学
oz = np.loadtxt(RUN / "ozone.formatted").reshape(12, 64, 59)
lat_oz = np.loadtxt(RUN / "ozone_lat.formatted")
plev = np.loadtxt(RUN / "ozone_plev.formatted")
j = int(np.argmin(np.abs(lat_oz - 36.05)))
print("\nCAM climatology July @", lat_oz[j], "N")
for k in range(0, 59, 4):
    print(f"  p={plev[k]:9.3f} hPa  O3={oz[6, j, k]:.4e}")

# 检查 e_vert 与 eta
print("\nZNW top/bottom:", np.asarray(ds.variables["ZNW"]).ravel()[:2], np.asarray(ds.variables["ZNW"]).ravel()[-2:])
print("P_TOP:", np.asarray(ds.variables["P_TOP"]).ravel() if "P_TOP" in ds.variables else "n/a")
ds.close()