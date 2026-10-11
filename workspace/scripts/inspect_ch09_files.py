# -*- coding: utf-8 -*-
"""本地解剖 ch09 拉回的四类 wrfout 样本（格式/维度/变量/属性/压缩/帧数）。"""
from pathlib import Path
from netCDF4 import Dataset, chartostring

d = Path(r"d:\Code\Learn\WRF\workspace\data\ch09_io")
files = {
    "io2q(netCDF4默认)": d / "io2q_wrfout_d01_0000.nc",
    "io2c(classic)": d / "io2c_wrfout_d01_0000.nc",
    "io11(pnetcdf)": d / "io11_wrfout_d01_0000.nc",
    "io102(multi补丁)": d / "io102_wrfout_d01_patch0003.nc",
}
for name, f in files.items():
    if not f.exists():
        print(f"[missing] {name}: {f}")
        continue
    ds = Dataset(f)
    dims = {k: len(v) for k, v in ds.dimensions.items()}
    nvars = len(ds.variables)
    attrs = {}
    for a in ("TITLE", "START_DATE", "GRID_ID", "DX", "DY", "MAP_PROJ", "WEST-EAST_GRID_DIMENSION",
              "SOUTH-NORTH_GRID_DIMENSION", "BOTTOM-TOP_GRID_DIMENSION", "WEST-EAST_PATCH_START_UNSTAG"):
        if a in ds.ncattrs():
            attrs[a] = ds.getncattr(a)
    print(f"== {name} ==  size={f.stat().st_size:,}  file_format={ds.file_format}  nvars={nvars}")
    print(f"   dims: Time={dims.get('Time')} bt={dims.get('bottom_top')} bt_stag={dims.get('bottom_top_stag')} "
          f"we={dims.get('west_east')} sn={dims.get('south_north')} soil={dims.get('soil_layers_stag')} DateStrLen={dims.get('DateStrLen')}")
    print(f"   attrs: {attrs}")
    for v in ("Times", "T2", "THM", "XLAT", "U"):
        if v in ds.variables:
            var = ds.variables[v]
            print(f"   var {v}: shape={var.shape} dtype={var.dtype} dims={var.dimensions}")
    if "Times" in ds.variables:
        print(f"   Times = {chartostring(ds.variables['Times'][:]).tolist()}")
    if ds.file_format not in ("NETCDF3_CLASSIC", "NETCDF3_64BIT_OFFSET", "NETCDF3_64BIT_DATA"):
        for v in ("T2", "THM"):
            if v in ds.variables:
                var = ds.variables[v]
                try:
                    print(f"   {v}: filters={var.filters()} chunking={var.chunking()}")
                except Exception as e:
                    print(f"   {v}: filter 查询失败 {e}")
    ds.close()

print()
print("== 单帧净数据量（按变量声明统计）与文件大小对比 ==")
for name, f in files.items():
    if not f.exists():
        continue
    ds = Dataset(f)
    tot = 0
    nt = len(ds.dimensions.get("Time", []))
    for v in ds.variables.values():
        dims = v.dimensions
        if dims and dims[0] == "Time":
            s = 1
            for dd in v.shape[1:]:
                s *= dd
        else:
            s = 1
            for dd in v.shape:
                s *= dd
        tot += s * v.dtype.itemsize
    print(f"{name}: Time={nt} 单帧净字节≈{tot/1e6:.2f} MB（按声明） 文件={f.stat().st_size/1e6:.2f} MB")
    ds.close()