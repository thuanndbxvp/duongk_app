import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("161.248.4.99", username="deploy", password="hJ%ExH;V_#|6")
stdin, stdout, stderr = ssh.exec_command("echo 'hJ%ExH;V_#|6' | sudo -S sh -c 'cd /opt/appdk && git fetch origin && git reset --hard origin/main && git clean -fd'")
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
