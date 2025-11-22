import os
import sys
import json
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from glob import glob


def load_dotenv(dotenv_path='.env'):
    """Lightweight dotenv loader: read KEY=VALUE lines and set os.environ if not already set.

    This avoids adding an external dependency. It will ignore blank lines and lines
    starting with #.
    """
    if not os.path.exists(dotenv_path):
        return
    try:
        with open(dotenv_path, 'r') as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # Only set if not already in environment
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception as e:
        print(f"Warning: failed to read {dotenv_path}: {e}")


# Load .env file if present so users can keep paths out of the repo
load_dotenv('.env')

# Configuration: DATA_PATH and PROJECT_PATH should be provided via environment
# variables (from .env or exported in the shell). Defaults are placeholders.
DATA_DIR = os.environ.get('DATA_PATH', 'data_path')
PROJECT_PATH = os.environ.get('PROJECT_PATH', 'project_path')
REDUCER_DIR = os.path.join(PROJECT_PATH, 'outputs')

def mapper(file_path):
    """
    Reads a data file, counts the frequency of each integer, and returns a dictionary.
    """
    print(f"Mapper started for {file_path}")
    counts = defaultdict(int)
    try:
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    num = int(line.strip())
                    counts[num] += 1
                except ValueError:
                    # Skip lines that are not valid integers
                    continue
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return {}

    print(f"Mapper finished for {file_path}")
    return dict(counts)

def run_mappers():
    """
    Runs the mapper function on all data files and saves the results as JSON.
    """
    # Create the reducer directory if it doesn't exist
    os.makedirs(REDUCER_DIR, exist_ok=True)

    # Get a list of all data files to process and filter out directories
    all_paths = glob(os.path.join(DATA_DIR, '*'))
    data_files = [path for path in all_paths if os.path.isfile(path)]

    if not data_files:
        print("Error: No data files found in the specified directory.")
        return

    # Use a process pool for parallel execution (up to 4 processes)
    with ProcessPoolExecutor(max_workers=4) as executor:
        mapper_results = list(executor.map(mapper, data_files))

    # Save each mapper's result to a JSON file
    for i, result in enumerate(mapper_results):
        output_file_path = os.path.join(REDUCER_DIR, f'mapper_output_{i}.json')
        with open(output_file_path, 'w') as f:
            json.dump(result, f)
        print(f"Saved mapper output to {output_file_path}")

    print("All mappers have completed.")

def reducer():
    """
    Reads all mapper output files, aggregates the counts, and prints/saves the top 6.
    """
    # Get a list of all mapper output files
    mapper_files = glob(os.path.join(REDUCER_DIR, '*.json'))
    if not mapper_files:
        print("Error: No mapper output files found in the reducer directory. Run 'mapper' first.")
        return

    print("Reducer started...")
    final_counts = defaultdict(int)

    # Aggregate the counts from all mapper files
    for file_path in mapper_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                for num, count in data.items():
                    final_counts[int(num)] += count
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error processing {file_path}: {e}")
            continue

    # Sort the items by frequency in descending order
    sorted_counts = sorted(final_counts.items(), key=lambda item: item[1], reverse=True)

    print("\nTop 6 elements with the highest frequencies:")

    # Save the output to a text file
    output_file_path = os.path.join(REDUCER_DIR, 'final_output.txt')
    with open(output_file_path, 'w') as f:
        f.write("Top 6 elements with the highest frequencies:\n")
        for num, count in sorted_counts[:6]:
            output_line = f"Number: {num}, Frequency: {count}"
            print(output_line)
            f.write(output_line + "\n")

    print(f"\nFinal output saved to {output_file_path}")
    print("Reducer finished.")

def main():
    """
    Main function to run mapper and reducer stages.
    Configure DATA_PATH and PROJECT_PATH environment variables, or edit the top of this file.
    """
    run_mappers()
    reducer()

if __name__ == "__main__":
    main()
