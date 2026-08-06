import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('161.248.4.99', username='deploy', password='hJ%ExH;V_#|6')
cmd = "echo 'hJ%ExH;V_#|6' | sudo -S sh -c 'echo \"INFERENCE_TIMEOUT_SEC=1200\" >> /opt/appdk/.env.production && echo \"HTTP_REQUEST_TIMEOUT_SEC=1205\" >> /opt/appdk/.env.production && cd /opt/appdk && docker compose -f docker-compose.prod.yml up -d --build omnivoice'"
stdin, stdout, stderr = ssh.exec_command(cmd)
for line in stdout:
    print(line.strip())
for line in stderr:
    print(line.strip())
