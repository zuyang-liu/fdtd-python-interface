# Supplementary Code: Photonic Device Simulation with Lumerical and Tidy3D

This repository contains simulation scripts and utilities used in the publication:

**"Comparison of Lumerical FDTD and Tidy3D for three-dimensional FDTD simulations of passive components on SOI platforms"**  
*Author(s): Zuyang Liu, et al.*  

---

## Overview

This code enables reproducible 3D FDTD simulations of silicon photonic devices using:

- **GDSFactory** for layout processing  
- **Lumerical FDTD** (desktop solver)  
- **Tidy3D** (cloud solver)  

Supported devices include directional couplers, waveguide crossings, MMIs, mode converters, and polarization splitter-rotators.

---

## Environment Setup

Create the environment using:

```bash
conda env create -f environment.yml
conda activate fdtd_sim
```

External requirements:
- Ansys Lumerical FDTD (locally installed)
- Flexcompute Tidy3D (with API access)

---

## Configuration

Before running simulations, edit `config.json` to match your local environment and preferences.

> ⚠️ **Ensure `lumapi_path` correctly points to your Lumerical API installation directory.**

This file provides shared defaults for simulation scripts. Device-specific settings like resolution, sweep span, and GDS paths are still set per script.

---

## Running Simulations

Each device has its own script located at:

```
projects/FDTD_solvers/<device_name>/<device_name>.py
```

Output files will be saved to:
```
projects/FDTD_solvers/<device_name>/Data/<solver>/
```

---

## Contact

**Zuyang Liu**  
The Edward S. Rogers Sr. Department of Electrical and Computer Engineering, University of Toronto  
📧 zuyang.liu@utoronto.ca

---

## License

This code is provided for peer review and academic reproducibility. Please cite the paper if you use or adapt this work.
