import logging
import os
import smtplib
from Library.Functions import Files
from Library.Classes.Order import order_class
from typing import List
from Library.Config.Config import Config
from Library.Config import Logging

Config.setup(
    root_path=os.path.dirname(os.path.abspath(__file__))
)

Logging.setup_logging()

logging.info("----------------- Script is startet -----------------")

# Files.download_files_from_ftp(orders_file=Config.ORDERS_FILE_NAME,
#                               stock_file=Config.STOCK_FILE_NAME,
#                               destination=Config.DOWNLOAD_DESTINATION,
#                               server=Config.FTP_SERVER,
#                               username=Config.FTP_USER,
#                               password=Config.FTP_PASSWORD)

in_stock_main = Files.get_own_stock_main(file_name=Config.STOCK_FILE_PATH,
                                         table_name="Tabelle1"
                                         )

in_stock_belts = Files.get_in_stock_belts(file_name=Config.STOCK_FILE_PATH,
                                          table_name="Guertel"
                                          )

in_stock = {**in_stock_main, **in_stock_belts}

# ########################################################################################################################
# read file Bestellungen.csv and create order_objects
orders: List[order_class] = Files.read_orders(Config.ORDERS_FILE_PATH)

# ########################################################################################################################
# open the connection to mail-server
smtp_server = Config.MAIL_SERVER
smtp_port = 587
sender_email = Config.MAIL_USER
sender_password = Config.MAIL_PASSWORD

eMail_server = smtplib.SMTP(smtp_server, smtp_port)
eMail_server.starttls()  # Starten Sie eine sichere TLS-Verbindung
eMail_server.login(sender_email, sender_password)

# ########################################################################################################################
# read the already finished orders
worked_orders = Files.read_already_worked_orders(Config.WORKED_ORDERS_FILE_PATH)

for order in orders:
    order.check_already_worked(worked_orders)
    if order.already_worked:
        continue

    order.send_order_mail(mail_client=eMail_server,
                          sender_eMail=sender_email,
                          in_stock=in_stock,
                          )


