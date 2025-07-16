import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8888"
backlog = 2048

# Worker processes
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gevent")
worker_connections = 1000
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", 100))
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"
errorlog = "-"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
loglevel = "info"

# Process naming
proc_name = "ipanel"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = "ipanel"
group = "ipanel"
tmp_upload_dir = None

# SSL
# keyfile = "/etc/ssl/private/server.key"
# certfile = "/etc/ssl/certs/server.crt"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Application
pythonpath = "/app"
chdir = "/app"

# Preload application for better performance
preload_app = True

# Enable garbage collection
enable_stdio_inheritance = True

# Worker process management
worker_tmp_dir = "/dev/shm"

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called just after a worker has been killed."""
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    pass

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("worker received SIGABRT signal")
