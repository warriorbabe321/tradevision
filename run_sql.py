import subprocess
import sys

def run_query(query):
    try:
        result = subprocess.check_output(['team-db', query], stderr=subprocess.STDOUT)
        print(result.decode())
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.output.decode()}")

if __name__ == "__main__":
    run_query(sys.argv[1])
