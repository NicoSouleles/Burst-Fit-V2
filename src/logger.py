import logging
from logging.handlers import RotatingFileHandler
import configparser
import os


conf = configparser.ConfigParser()
conf.read("log.conf")

stream_h = logging.StreamHandler()

if not os.path.isdir('logs'):
    os.mkdir('logs')

# TODO: If user changes name of logfile, delete existing logs with previous
# name; promp user if they want to do this.
# TODO: Make it so that the log from a single run of the program does not
# get split over multiple files when rollover occurs (how to do this???)
log_fname = os.path.splitext(conf['logfile']['log_file_name'])[0]
file_h = RotatingFileHandler(f"logs/{log_fname}.log", 
                             maxBytes=conf.getint('logfile', 'max_bytes'),
                             backupCount=conf.getint('logfile', 'backup_count'),
                             encoding="utf-8")

stream_h.setLevel(logging.WARN)
file_h.setLevel(logging.INFO)

formatter = logging.Formatter(fmt="[%(asctime)s - %(levelname)s]: %(message)s "
                              "(%(name)s line %(lineno)d)",
                              datefmt="%Y-%m-%d %H:%M:%S")
stream_h.setFormatter(formatter)
file_h.setFormatter(formatter)


def add_handlers(logger: logging.Logger):
    logger.addHandler(stream_h)
    logger.addHandler(file_h)
