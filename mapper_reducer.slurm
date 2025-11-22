#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=00:15:00
#SBATCH --partition=short-40core
#SBATCH --job-name=parallel_count_job
# NOTE: replace PROJECT_PATH with your project directory or export PROJECT_PATH before submission
#SBATCH --output=${PROJECT_PATH}/logs/%x-%j.out

#SBATCH -e stderr.txt
#SBATCH -o stdout.txt
#SBATCH --open-mode=append

#SBATCH --mail-type=BEGIN,END
# (removed personal email) To enable notifications set --mail-user to your email address
# SBATCH --mail-user=your_email@example.com

# Load required modules (adjust to your cluster's module system)
module load anaconda/3

# Load .env if present (this keeps user paths out of the repo)
if [ -f .env ]; then
	# Export variables defined in .env to the environment for this job
	set -a
	# shellcheck disable=SC1091
	source .env
	set +a
fi

echo "PROJECT_PATH=${PROJECT_PATH:-project_path}"
echo "DATA_PATH=${DATA_PATH:-data_path}"

# Run the mapper/reducer driver (script name updated to scale_map.py)
python scale_map.py