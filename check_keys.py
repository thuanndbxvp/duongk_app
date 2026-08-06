import paramiko
import sys
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('161.248.4.99', username='deploy', password='hJ%ExH;V_#|6')

cmd = """docker exec appdk-omnivoice-1 python -c "
from omnivoice.models.omnivoice import OmniVoiceGenerationConfig
import dataclasses
if dataclasses.is_dataclass(OmniVoiceGenerationConfig):
    print([f.name for f in dataclasses.fields(OmniVoiceGenerationConfig)])
else:
    print(OmniVoiceGenerationConfig().__dict__.keys())
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:", stdout.read().decode('utf-8'))
print("STDERR:", stderr.read().decode('utf-8'))
