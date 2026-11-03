#!/usr/bin/env python3
"""Read actual /proc process PSS as browser's own unprivileged UID.
Never claim zero for missing smaps_rollup or insufficient permissions.
The sampler process excludes itself to avoid contaminating measurements.
"""
import json,os
from browser_probe import process_memory
if __name__=="__main__":
    print(json.dumps(process_memory(os.geteuid(),exclude_pid=os.getpid())))
