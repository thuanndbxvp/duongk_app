import paramiko
import os

key_path = os.path.expanduser("~/.ssh/id_ed25519")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("161.248.4.99", username="root", key_filename=key_path)

print("Now fetching logs...")
stdin, stdout, stderr = client.exec_command("docker logs appdk-omnivoice-1 | grep -i upload")
print(stdout.read().decode())
print(stderr.read().decode())

client.close()
