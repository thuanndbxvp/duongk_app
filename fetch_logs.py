import paramiko

def fetch_logs():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect("161.248.4.99", username="deploy", password="hJ%ExH;V_#|6")
        
        # We need to sudo up -d because maybe it was interrupted
        stdin, stdout, stderr = ssh.exec_command("echo 'hJ%ExH;V_#|6' | sudo -S sh -c 'cd /opt/appdk && docker compose -f docker-compose.prod.yml up -d --build omnivoice'")
        
        # Read the stdout properly
        print(stdout.read().decode('utf-8', errors='replace'))
        print(stderr.read().decode('utf-8', errors='replace'))
        
        print("Now fetching logs...")
        stdin, stdout, stderr = ssh.exec_command("echo 'hJ%ExH;V_#|6' | sudo -S sh -c 'cd /opt/appdk && docker compose -f docker-compose.prod.yml logs omnivoice'")
        print(stdout.read().decode('utf-8', errors='replace'))
        print(stderr.read().decode('utf-8', errors='replace'))
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    fetch_logs()
