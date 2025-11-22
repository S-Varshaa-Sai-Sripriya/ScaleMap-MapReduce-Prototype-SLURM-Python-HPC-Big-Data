## ScaleMap: MapReduce Prototype (SLURM + Python)

## Summary — Seawulf and cluster setup

This work was developed and tested on Seawulf, Stony Brook University's research computing cluster. Seawulf is an HPC environment that provides login nodes, batch scheduling (SLURM), and shared parallel filesystems (GPFS). Typical usage pattern on Seawulf:

- Login node: interactive management, editing, submitting jobs (avoid heavy compute on login nodes).
- Compute nodes: where SBATCH batch jobs run; they do not usually provide interactive access.
- Shared file system (GPFS): store input datasets and job outputs; paths often look like `/gpfs/projects/<project>/...`.

Seawulf quick link: https://rci.stonybrook.edu/HPC

When you prepare to run on Seawulf, pick the right partition/queue, ensure your project allocation has quota, and use `sbatch` to submit `mapper_reducer.slurm` from a login node.

## MapReduce summary

ScaleMap is a small MapReduce-style prototype implemented in Python. It implements two stages:

- Mapper: read input files (one or more), produce per-file frequency counts of integer values, and write intermediate JSON outputs.
- Reducer: read mapper JSON outputs, aggregate counts across mappers, and write the final top-N results (top 6 by frequency in the current implementation).

The prototype is intentionally minimal and educational — it demonstrates the map + reduce pattern and a simple cluster submission flow (SLURM). It is not a production distributed shuffle or fault-tolerant framework; for production use, consider Spark/Hadoop or introduce persistent checkpointing.

## Design & architecture — code summary

scale_map.py (driver)

- Configuration: reads runtime paths from environment variables `DATA_PATH` and `PROJECT_PATH`. To keep secrets/paths out of the repository you can create a local `.env` file (see `.env.example`). The script includes a small `load_dotenv()` helper that parses simple KEY=VALUE lines so no external dependency is required.
- Mapper stage: `mapper(file_path)` reads a single file, parses lines as integers (skips non-integer lines), and returns a dictionary of counts for that file.
- Parallel execution: `run_mappers()` enumerates data files under `DATA_PATH` and uses `concurrent.futures.ProcessPoolExecutor` (default max_workers=4) to run `mapper()` across files in parallel. Each mapper writes a JSON file into `PROJECT_PATH/outputs` (configured via `PROJECT_PATH`).
- Reducer stage: `reducer()` loads all mapper JSON files from `PROJECT_PATH/outputs`, aggregates counts into a single counter, sorts by frequency, prints and writes the top-6 results to `PROJECT_PATH/outputs/final_output.txt`.
- Outputs: per-mapper JSON files (`mapper_output_*.json`) and `final_output.txt` saved under the outputs directory.

mapper_reducer.slurm (job submission)

- Purpose: example SLURM submission script to run `scale_map.py` on a compute node.
- .env sourcing: the script looks for a `.env` file in the job submission directory and sources it to export `DATA_PATH` and `PROJECT_PATH` into the job environment. This avoids hard-coding personal/cluster paths in repository files.
- SBATCH output: the script writes standard output to `${PROJECT_PATH}/logs/%x-%j.out` (job name and job id), so logs live under your project workspace.
- Adjustments: you should update partition, time, memory, and module load lines to match Seawulf's available partitions and environment modules.

## Note: replace variables with your paths

1. `.env`:

```text
DATA_PATH=/gpfs/projects/your_project/inputs
PROJECT_PATH=/gpfs/projects/your_project/scale_map
```

2. `.env` is in `.gitignore` by default.

3. Alternatively you can export environment variables in your shell or in the SLURM job submission environment:

```bash
export DATA_PATH=/gpfs/projects/your_project/inputs
export PROJECT_PATH=/gpfs/projects/your_project/scale_map
sbatch mapper_reducer.slurm
```

## How to run on Seawulf (step-by-step)

1. Sync or copy the repository to Seawulf (use `scp`, `rsync`, or clone from your git remote on the login node). Work from a project directory under your allocation (GPFS).

2. Create a `.env` file on Seawulf and set `DATA_PATH` and `PROJECT_PATH` to GPFS paths under your project allocation.

3. Prepare your Python environment on Seawulf. Example using modules/conda (Seawulf-specific environments vary):

```bash
# on a Seawulf login node
module load anaconda/3
conda create -n scalemap python=3.9 -y
conda activate scalemap
# If you add external packages, install them now (or use requirements.txt)
# pip install -r requirements.txt
```

4. (Optional) Test locally on a small dataset interactively on a login node (keep resource usage low):

```bash
python scale_map.py
```

5. Submit the job with SLURM from a login node:

```bash
# Ensure .env exists in the current directory or export variables in the shell
sbatch mapper_reducer.slurm
```

6. Monitor job status with `squeue -u $USER` or `sacct` (depending on your cluster setup). Check job logs under `${PROJECT_PATH}/logs/` and outputs under `${PROJECT_PATH}/outputs`.

7. If you need more runtime or memory, adjust SBATCH directives in `mapper_reducer.slurm` (time, partition, nodes, memory) and resubmit.

## Troubleshooting tips

- If `scale_map.py` fails to find files, confirm `DATA_PATH` points to existing files and that `PROJECT_PATH` is writable.
- For permission/space issues on GPFS, check your project quota and file permissions.
- If SLURM complains about modules or Python, load the appropriate modules or use your own conda environment and point `python` in the SLURM script to the full path of the interpreter if needed.

---

If you'd like, I can now:

- create a small `examples/` dataset and a smoke test that runs in <30s, or
- add a small `scripts/setup_env.sh` helper to copy `.env.example` to `.env` and prompt for values, or
- remove the deprecated `project1 (2).py` file entirely.

Tell me which you'd like next and I will implement it.
