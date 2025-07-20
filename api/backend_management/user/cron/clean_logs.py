import os


def clean_logs():
    log_dir = 'logs/'

    no_delete = {
        'autoreload.log',
        'db_backends.log',
        'error.log',
        'info.log',
        'request.log',
        'root.log',
        'server.log',
        'warning.log'
    }

    for file_name in os.listdir(log_dir):
        if file_name not in no_delete:
            file_path = os.path.join(log_dir, file_name)
            os.remove(file_path)
