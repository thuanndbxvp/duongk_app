import paramiko
import sys
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('161.248.4.99', username='deploy', password='hJ%ExH;V_#|6')
stdin, stdout, stderr = ssh.exec_command("docker logs appdk-caddy-1 2>&1 | grep EOF | tail -n 5")
print(stdout.read().decode('utf-8', errors='replace'))
