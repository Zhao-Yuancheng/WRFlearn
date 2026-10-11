#!/usr/bin/env bash
# 探测集群到 conda-forge / TUNA 的连通性（只读，5s 超时）
echo '--- conda.anaconda.org ---'
curl -sI -m 5 https://conda.anaconda.org/conda-forge/noarch/repodata.json | head -1 || echo 'FAIL anaconda.org'
echo '--- mirrors.tuna.tsinghua.edu.cn ---'
curl -sI -m 5 https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/noarch/repodata.json | head -1 || echo 'FAIL tuna'
echo '--- pypi ---'
curl -sI -m 5 https://pypi.org/simple/ | head -1 || echo 'FAIL pypi'
