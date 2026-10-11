import numpy as np
from netCDF4 import Dataset
m = Dataset(r"d:\Code\Learn\WRF\workspace\data\ch10\met_em.d01.2025-07-12_00.nc")
mi = mj = 44
pres = np.asarray(m.variables["PRES"][0, :, mi, mj])
ght = np.asarray(m.variables["GHT"][0, :, mi, mj])
psfc = float(m.variables["PSFC"][0, mi, mj])
print("PSFC=", psfc, " HGT_M=", float(m.variables["HGT_M"][0, mi, mj]))
for k in range(pres.size):
    print(f"  k={k:2d} p={pres[k]:8.0f}  GHT={ght[k]:8.1f}")
cand = np.argsort(np.abs(np.log(pres/psfc)))[:2]
cand = cand[np.argsort(-pres[cand])]
print("cand:", cand, "p=", pres[cand], "ght=", ght[cand])
