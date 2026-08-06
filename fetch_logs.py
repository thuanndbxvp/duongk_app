import paramiko

def fetch_logs():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect("161.248.4.99", username="deploy", password="hJ%ExH;V_#|6")
        stdin, stdout, stderr = ssh.exec_command("cd /opt/appdk && docker compose -f docker-compose.prod.yml logs omnivoice")
        out = stdout.read().decode()
        err = stderr.read().decode()
        print("STDOUT:")
        print(out)
        print("STDERR:")
        print(err)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    fetch_logs()
