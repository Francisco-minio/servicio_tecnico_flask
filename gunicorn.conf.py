# Configuración básica
bind = "0.0.0.0:5000"
workers = 2
worker_class = 'sync'
threads = 1
timeout = 120
keepalive = 2
loglevel = "debug"
accesslog = "-"
errorlog = "-"

# Configuración de memoria
worker_tmp_dir = "/dev/shm"
max_requests = 1000
max_requests_jitter = 50

# Desactivar SSL completamente
keyfile = None
certfile = None
ssl_version = None
do_handshake_on_connect = False
secure_scheme_headers = {} 