import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(dotenv_path)


class Config:
    """
    Read env-vars from .env file and set all needed configuration variables
    """
    # e-Mailserver
    MAIL_SERVER = os.getenv("mailServer")
    MAIL_USER = os.getenv("mailUser")
    MAIL_PASSWORD = os.getenv("mailPassword")

    # mail settings
    MAIL_ADDRESS_KWON = os.getenv("mail_address_kwon")
    MAIL_ADDRESS_JU_SPORTS = os.getenv("mail_address_ju_sports")
    MAIL_ADDRESS_DAX = os.getenv("mail_address_dax")
    MAIL_ADDRESS_PHOENIX = os.getenv("mail_address_phoenix")
    MAIL_CC = os.getenv("mail_CC")
    MAIL_FOR_MANUAL_HANDLING = os.getenv("mail_address_for_manual_handling")

    # ftp connection
    FTP_SERVER = os.getenv("ftp_server")
    FTP_USER = os.getenv("ftp_user")
    FTP_PASSWORD = os.getenv("ftp_password")

    # MongoDB connection
    MONGO_HOST = os.getenv('Mongo_Host')
    MONGO_PORT = os.getenv('Mongo_Port')
    MONGO_DB = os.getenv('Mongo_db')
    MONGO_USER = os.getenv('Mongo_user')
    MONGO_PASSWORD = os.getenv('Mongo_passwort')
    COLLECTION_NAME = os.getenv('Mongo_Collection')

    # logging level
    LOG_LEVEL = os.getenv('Log_level')

    STOCK_FILE_NAME = os.getenv("stock_file")
    ORDERS_FILE_NAME = os.getenv("orders_file")
    WORKED_ORDERS_FILE_NAME = os.getenv("worked_orders")

    ROOT_PATH = ""
    STOCK_FILE_PATH = ""
    ORDERS_FILE_PATH = ""
    WORKED_ORDERS_FILE_PATH = ""
    DOWNLOAD_DESTINATION = ""

    @classmethod
    def setup(cls, root_path: str):
        """
        Start Setup all Variables.
        :param root_path: path of the root directory.
        :return:
        """
        cls._set_file_paths(root_path=root_path)

    @classmethod
    def _set_file_paths(cls, root_path: str):
        """
        Setup file routes
        :param root_path: the root path of the script
        :return:
        """
        cls.ROOT_PATH = root_path
        cls.DOWNLOAD_DESTINATION = f"{root_path}/{os.getenv('download_directory')}"
        cls.STOCK_FILE_PATH = f"{cls.DOWNLOAD_DESTINATION}/{cls.STOCK_FILE_NAME}"
        cls.ORDERS_FILE_PATH = f"{cls.DOWNLOAD_DESTINATION}/{cls.ORDERS_FILE_NAME}"
        cls.WORKED_ORDERS_FILE_PATH = f"{root_path}/{cls.WORKED_ORDERS_FILE_NAME}"
