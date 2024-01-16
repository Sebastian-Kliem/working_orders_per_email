import csv
import logging
import os
from ftplib import FTP
from typing import Tuple, List

from pyexcel_ods import get_data
from app.Library.Classes.Order import order_class


def download_files_from_ftp(orders_file: str,
                            stock_file: str,
                            destination: str,
                            server: str,
                            username: str,
                            password: str,
                            port: int = 21) -> None:
    """
    Downloads the file with orders and the file with own stock from ftp.

    :param destination: directory for the downloaded files
    :param orders_file: the file with orders exported from JTL
    :param stock_file: the file with the own stock
    :param server: host address of the ftp server
    :param username: username of the ftp
    :param password: password of the ftp
    :param port: port to connect to the ftp server
    :return:
    """

    if not os.path.exists(destination):
        os.makedirs(destination)

    try:
        ftp = FTP()
        ftp.connect(server, port)
        ftp.login(username, password)
        logging.debug("Ftp connection established")

        # change to subdirectory
        ftp.cwd('/BestandsdateienPerEmail/')

        contents = ftp.nlst()

        # orders file
        with open(f"{destination}/{orders_file}", 'wb') as local_file:
            ftp.retrbinary('RETR ' + orders_file, local_file.write)
        logging.debug(f"Download complete oders-file: {orders_file}")

        # stock file
        with open(f"{destination}/{stock_file}", 'wb') as local_file:
            ftp.retrbinary('RETR ' + stock_file, local_file.write)

        logging.debug(f"Download complete stock-file: {stock_file}")
        return

    except Exception as exception:
        logging.error(f"error during download files. Massege: {exception}")
        exit()


def get_own_stock_main(file_name: str,
                       table_name: str
                       ) -> dict:
    """
    Read the stockfile to get a list of stock.
    A .ods file is required
    :param file_name: Filename
    :param table_name: Name of table in File
    :return: Dictionary in this format: {'articlenumber': 'in_stock'}
    """

    file_data = get_data(file_name)

    if table_name in file_data.keys():
        sheet = file_data[table_name]

        in_stock = {}
        for item in sheet:
            if len(item) >= 3:
                in_stock[str(item[1])] = item[2]

        logging.debug("In_stock main already loaded.")
        return in_stock

    logging.error("Reading in_stock_file not working")
    exit()


def get_in_stock_belts(file_name: str,
                       table_name: str
                       ) -> dict:
    """
    Read the stockfile to get a list of belts in stock.
    A .ods file is required
    :param file_name: Filename
    :param table_name: Name of table in File
    :return: Dictionary in this format: {'articlenumber': 'in_stock'}
    """

    file_data = get_data(file_name)

    if table_name in file_data.keys():
        sheet = file_data[table_name]

        in_stock = {}
        for item in sheet:
            if len(item) >= 3:
                in_stock[str(item[0])] = item[1]

        logging.debug("In_stock belts already loaded.")
        return in_stock

    logging.error("Reading in_stock_file not working")
    exit()


def read_orders(file_name: str) -> tuple[list[order_class], list[order_class]]:
    """Files
    Read the orderfile to get a list of oders
    :param file_name:
    :return: List oder-classes.
    """
    order_names = []
    orders_to_work = []
    orders_manually_check = []
    orders = {}
    with open(file_name, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            if "Versandposition" in row['Positionstyp']:
                continue

            name = (row['L_Vorname'], row['L_Nachname'])
            order_names.append(name)
            del name

            order_number = row["Bestell Nr."]
            if order_number not in orders:
                orders[order_number] = []


            orders[order_number].append(row)

    double_orders_names = set()
    for name in order_names:
        if order_names.count(name) > 1:
            double_orders_names.add(name)



    for key, value in orders.items():

        positions = []
        for item in value:
            article = {"articlename": item['Artikelname'],
                       "article_number": item['Artikelnummer'],
                       "amount": item["Menge"].split(".")[0]}
            positions.append(article)


        order = order_class(ordernumber=key,
                            company=value[0]['L_Firma'],
                            address_addition=value[0]['L_Adresszusatz'],
                            first_name=value[0]['L_Vorname'],
                            last_name=value[0]['L_Nachname'],
                            street=value[0]['L_Straße'],
                            zip_code=value[0]['L_PLZ'],
                            city=value[0]['L_Ort'],
                            country=value[0]['L_Land'],
                            phone=value[0]['L_Phone'],
                            plattform=value[0]['Plattform'],
                            positions=positions
                            )


        if (order.first_name, order.last_name) in double_orders_names:
            orders_manually_check.append(order)
        else:
            orders_to_work.append(order)
    logging.debug("File with orders finally read")
    return orders_to_work, orders_manually_check


def read_already_worked_orders(filepath: str) -> list:
    """
    Read already worked orders from file.
    :param filepath:
    :return: Listwith worked orders.
    """
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            worked_orders = file.read().split('\n')
        logging.debug("File with worked orders finally loaded.")
        return worked_orders

    return []

