import codecs
with codecs.open('.env.production', 'r', 'utf-8', errors='ignore') as f:
    lines = f.read().split('LOG_LEVEL=INFO')[0]
with codecs.open('.env.production', 'w', 'utf-8') as f:
    f.write(lines + 'LOG_LEVEL=INFO\nINFERENCE_TIMEOUT_SEC=1200\nHTTP_REQUEST_TIMEOUT_SEC=1205\n')
