import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('161.248.4.99', username='deploy', password='hJ%ExH;V_#|6')

cmd = """docker exec appdk-omnivoice-1 python -c "
import boto3, os, sys
try:
    print('start')
    s3=boto3.client('s3', endpoint_url=os.environ['R2_ENDPOINT'], aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'], aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'], region_name='auto')
    print('client created')
    print(s3.list_buckets())
    print('success')
except Exception as e:
    print('ERROR:', str(e))
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
for line in stdout:
    print("OUT:", line.strip())
for line in stderr:
    print("ERR:", line.strip())
