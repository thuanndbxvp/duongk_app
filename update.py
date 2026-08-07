import sys
import paramiko

def update(service="omnivoice"):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect("161.248.4.99", username="deploy", password="hJ%ExH;V_#|6")
        target_service = "" if service == "all" else service
        print(f"Connected to VPS! Pulling latest code and rebuilding '{service}'...")
        cmd = f"echo 'hJ%ExH;V_#|6' | sudo -S sh -c 'cd /opt/appdk && git pull && docker compose -f docker-compose.prod.yml up -d --build {target_service}'"
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
    target = sys.argv[1] if len(sys.argv) > 1 else "omnivoice"
    update(target)
