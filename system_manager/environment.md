# Environment Report

## Workdir
- `/home/erwinpi/pantheon-agents/workdir/system_manager`

## OS / Kernel
- `uname -a`: Linux tag-308 5.15.0-161-generic #171-Ubuntu SMP Sat Oct 11 08:17:01 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
- Distro: Ubuntu 22.04.5 LTS (jammy)

## Python Runtime
- `python -V`: Python 3.10.19
- `pip --version`: pip 26.0.1 from /home/erwinpi/miniconda3/envs/gps/lib/python3.10/site-packages/pip (python 3.10)
- `sys.executable`: /home/erwinpi/miniconda3/envs/gps/bin/python

## Core Python Packages
| Package | Version |
| --- | --- |
| numpy | 2.0.2 |
| scipy | 1.15.3 |
| pandas | 2.2.3 |
| matplotlib | 3.10.7 |
| seaborn | 0.13.2 |
| numba | 0.60.0 |
| polars | 1.38.1 |
| scanpy | 1.11.5 |
| anndata | 0.11.4 |
| squidpy | 1.6.5 |
| anndata2ri | 1.3.2 |
| harmonypy | 0.0.10 |
| moscot | 0.5.0 |
| scvi-tools | 1.3.3 |
| scrublet | 0.2.3 |
| leidenalg | 0.11.0 |
| igraph | 1.0.0 |
| scikit-learn | 1.7.2 |
| scikit-image | 0.25.2 |
| scikit-misc | 0.5.2 |
| gseapy | 1.1.11 |
| pydeseq2 | 0.5.2 |
| decoupler | 2.1.4 |
| celltypist | 1.7.1 |
| scvelo | 0.3.3 |
| cellrank | 2.0.7 |
| palantir | 1.4.4 |

## GPU Acceleration
- `nvidia-smi`: NVIDIA A100-PCIE-40GB x4, Driver 570.133.20, CUDA 12.8
- `rapids-singlecell` detected: 0.13.1
- Current dask stack:
  - dask 2025.2.0
  - distributed 2025.2.0

## R Runtime
- `R --version`: R 4.5.1 (2025-06-13)

## R Packages
| Package | Version |
| --- | --- |
| BiocManager | 1.30.27 |
| SoupX | 1.6.2 |
| celda | 1.26.0 |

## Hardware
- CPU logical cores: 56
- CPU physical cores: 56
- Memory total: 1511.54 GB
- Memory available: 791.70 GB
- Disk total (/): 10158.19 GB
- Disk used (/): 9376.33 GB
- Disk free (/): 269.84 GB

## Notes
- `uv` is not installed (`uv --version` not found).
- GPU was detected and `rapids-singlecell[rapids12]` was verified as installed. Pip attempted to re-install and upgraded `dask`/`distributed` to 2025.2.0 (required by `rapids-dask-dependency`). This version conflicts with `squidpy` (requires dask<=2024.11.2) and `spatialdata`/`dask-expr`. Keep in mind when running workflows depending on those packages.
- Importing some packages surfaced CUDA runtime warnings (`libcudart.so` not found) even though GPUs are present; this may indicate missing CUDA runtime libraries in the environment.
