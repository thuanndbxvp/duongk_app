import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('161.248.4.99', username='deploy', password='hJ%ExH;V_#|6')

cmd = """docker exec appdk-omnivoice-1 python -c "
import modal, os, sys
try:
    print('start modal check')
    f = modal.Function.from_name('ai-dubbing-pipeline', 'dub_srt')
    print('function lookup success')
except Exception as e:
    print('ERROR:', str(e))
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
for line in stdout:
    print("OUT:", line.strip())
for line in stderr:
    print("ERR:", line.strip())
