# Author: Sandeep Chowdary
# Project: ParkPulse Telemetry Engine
# Description: CLI execution runner for pipeline and Streamlit UI.

import argparse
import subprocess
from data_pipeline.engine import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="ParkPulse Runner")
    parser.add_argument("--data-only", action="store_true", help="Execute DuckDB pipeline without starting Streamlit")
    args = parser.parse_args()
    
    print("Executing ParkPulse data transformation pipeline...")
    run_pipeline()
    
    if args.data_only:
        return
        
    print("Starting Streamlit server...")
    try:
        subprocess.run(["streamlit", "run", "web_app/app.py"], check=True)
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
