import os
import time

log_path = '/tmp/app.log'
if os.path.exists(log_path):
    with open(log_path, 'r') as f:
        print(f.read())
else:
    print('Log file not found')
