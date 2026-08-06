import paramiko

def update():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect("161.248.4.99", username="deploy", password="hJ%ExH;V_#|6")
        print("Connected to VPS! Pulling latest code and rebuilding...")
        cmd = "echo 'hJ%ExH;V_#|6' | sudo -S sh -c 'cd /opt/appdk && git pull && docker compose -f docker-compose.prod.yml up -d --build omnivoice'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        # Wait for the command to finish and print output line by line
        for line in stdout:
            print("STDOUT:", line.strip())
        for line in stderr:
            print("STDERR:", line.strip())
            
        print("Update complete!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    update()
