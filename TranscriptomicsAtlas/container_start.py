import subprocess

if __name__=="__main__":
    print("Starting Agent")
    cwagent = subprocess.Popen(["/opt/aws/amazon-cloudwatch-agent/bin/start-amazon-cloudwatch-agent"])
    print("Staring consumer")
    subprocess.run(["python3", "/opt/TAtlas/Consumer/consumer.py"])
