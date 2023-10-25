import os
import subprocess

nproc = subprocess.run(["nproc"], capture_output=True, text=True).stdout.strip()
my_env = {**os.environ, 'PATH': '/opt/TAtlas/sratoolkit.3.0.1-ubuntu64/bin:'
                                '/opt/TAtlas/salmon-latest_linux_x86_64/bin:' + os.environ['PATH']}
work_dir = "/home/ubuntu/TAtlas"

os.makedirs(work_dir)
