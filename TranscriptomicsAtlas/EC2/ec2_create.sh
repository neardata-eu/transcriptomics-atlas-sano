#!/usr/bin/env bash

# Instance Store mount
# sudo mkfs -t xfs /dev/nvme1n1
# sudo mkdir /istore
# sudo mount /dev/nvme1n1 /istore
# sudo chown ubuntu /istore -R

# https://askubuntu.com/questions/1367139/apt-get-upgrade-auto-restart-services
sudo apt-get remove needrestart -y

sudo apt-get update
sudo apt-get install awscli -y

### SRA-TOOLKIT
wget https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/current/sratoolkit.current-ubuntu64.tar.gz -O - | tar -zx -C /home/ubuntu/sratoolkit/
#TODO check how to apply config using cli
#mkdir -p /istore/sratoolkit/local
#vdb-config --report-cloud-indentity yes  # TODO is it needed?

echo 'export PATH="$PATH":/home/ubuntu/sratoolkit/sratoolkit.3.0.1-ubuntu64/bin' >> ~/.bashrc

### SALMON
wget https://github.com/COMBINE-lab/salmon/releases/download/v1.10.0/salmon-1.10.0_linux_x86_64.tar.gz -O - | tar -zx -C /home/ubuntu/
echo 'export PATH="$PATH":/home/ubuntu/salmon-latest_linux_x86_64/bin' >> ~/.bashrc

### PYTHON MODULES
sudo apt install python3-pip -y
pip3 install boto3 watchtower

### R
wget -qO- https://cloud.r-project.org/bin/linux/ubuntu/marutter_pubkey.asc | sudo tee -a /etc/apt/trusted.gpg.d/cran_ubuntu_key.asc
sudo add-apt-repository "deb https://cloud.r-project.org/bin/linux/ubuntu $(lsb_release -cs)-cran40/" -y
sudo apt install --no-install-recommends r-base-dev -y

### R packages

# 'DESeq2' and 'RCurl' (library required by DESeq2) requires
sudo apt install libxml2-dev libssl-dev libcurl4-openssl-dev -y

# 'RcppArmadillo' (library required by DESeq2) requires
sudo apt-get install libopenblas-dev -y

sudo chmod o+w /usr/local/lib/R/site-library/
Rscript -e 'install.packages(c("readr", "dplyr", "BiocManager"))'
Rscript -e 'BiocManager::install(c("DESeq2", "tximport"))'

### CWAGENT
sudo wget https://s3.amazonaws.com/amazoncloudwatch-agent/debian/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c ssm:cloudwatch_agent_config_neardata -s
sudo rm amazon-cloudwatch-agent.deb
