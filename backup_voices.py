import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("161.248.4.99", username="deploy", password="hJ%ExH;V_#|6")

# Copy from container to host
ssh.exec_command("echo 'hJ%ExH;V_#|6' | sudo -S docker cp appdk-omnivoice-1:/app/voices/minhquan_vb.mp3 /opt/appdk/apps/omnivoice/voices/minhquan_vb.mp3")
ssh.exec_command("echo 'hJ%ExH;V_#|6' | sudo -S docker cp appdk-omnivoice-1:/app/voices/ngochuyen_vb.mp3 /opt/appdk/apps/omnivoice/voices/ngochuyen_vb.mp3")
ssh.exec_command("echo 'hJ%ExH;V_#|6' | sudo -S docker cp appdk-omnivoice-1:/app/voice_registry.json /opt/appdk/apps/omnivoice/voice_registry.json")

import time
time.sleep(2)

# Now download to local
sftp = ssh.open_sftp()
try:
    sftp.get("/opt/appdk/apps/omnivoice/voices/minhquan_vb.mp3", "D:\\appDK\\apps\\omnivoice\\voices\\minhquan_vb.mp3")
    sftp.get("/opt/appdk/apps/omnivoice/voices/ngochuyen_vb.mp3", "D:\\appDK\\apps\\omnivoice\\voices\\ngochuyen_vb.mp3")
    sftp.get("/opt/appdk/apps/omnivoice/voice_registry.json", "D:\\appDK\\apps\\omnivoice\\voice_registry.json")
    print("Backup complete!")
except Exception as e:
    print(e)
sftp.close()
ssh.close()
