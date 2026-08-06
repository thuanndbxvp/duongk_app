import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("161.248.4.99", username="deploy", password="hJ%ExH;V_#|6")
stdin, stdout, stderr = ssh.exec_command("echo 'hJ%ExH;V_#|6' | sudo -S docker exec appdk-omnivoice-1 ls -la /app/voices")
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
