import os
import logging
from datetime import datetime
from app.Library.Config.Config import Config


def setup_logging():
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logfile_name = datetime.now().strftime("%Y-%m-%d")
    logfile_directory = f"{Config.ROOT_PATH}/Logs/"

    if not os.path.exists(logfile_directory):
        os.makedirs(logfile_directory)

    logging.basicConfig(filename=f"{logfile_directory}{logfile_name}.log",
                        level=Config.LOG_LEVEL,
                        format=log_format)
