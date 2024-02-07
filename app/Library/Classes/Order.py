import logging
import smtplib
import re
from email.mime.multipart import MIMEMultipart
import email.utils
from email.mime.text import MIMEText
from re import Match
from ..Config.Config import Config


class order_class:

    def __init__(self,
                 ordernumber: str,
                 company: str,
                 address_addition: str,
                 first_name: str,
                 last_name: str,
                 street: str,
                 zip_code: str,
                 city: str,
                 country: str,
                 phone: str,
                 plattform: str,
                 positions: list):

        self.already_worked = None
        self.ordernumber = ordernumber
        self.company = company
        self.address_addition = address_addition
        self.first_name = first_name
        self.last_name = last_name
        self.street = street
        self.zip_code = zip_code
        self.city = city
        self.country = country
        self.phone = phone
        self.plattform = plattform
        self.positions = positions

        self._check_articlenumbers_for_special_handling()

    def __str__(self):
        return f"""
            self.ordernumber: {self.ordernumber}
            self.company: {self.company}
            self.address_addition: {self.address_addition}
            self.first_name: {self.first_name}
            self.last_name: {self.last_name}
            self.street: {self.street}
            self.zip_code: {self.zip_code}
            self.city: {self.city}
            self.country: {self.country}
            self.phone: {self.phone}
            self.positions: {self.positions} 
            self.already_worked: {self.already_worked}
        """

    def check_already_worked(self,
                             worked_orders: list
                             ) -> None:
        """
        Checks if the order is already fulfilled to do not double-orders.
        :param worked_orders:
        :return:
        """
        if self.ordernumber in worked_orders:
            self.already_worked = True
            return

        self.already_worked = False

    def send_order_mail(self,
                        mail_client: smtplib.SMTP,
                        sender_eMail: str,
                        in_stock: dict,
                        ) -> None:
        """
        Sends mail to order the items or note that must be done manually.
        :param in_stock: Dict with the articles in own stock.
        :param sender_eMail: email address where log in.
        :param mail_client: smtp-client
        :return:
        """

        if self.already_worked:
            return

        subject = ""
        receiver_email = ""
        html_body = ""
        # in the new articlenumber system is used. For now there is a manual handling required
        if any(self._check_if_new_articlenumber_system(item["article_number"]) for item in self.positions):
            html_body = self._create_html_body_manually_working_required()
            receiver_email = Config.MAIL_FOR_MANUAL_HANDLING
            subject = "Bestellung manuell ausführen"

        # if just 1 position to deliver
        elif len(self.positions) == 1:
            #  if is order deliverable from own stock
            if self._check_own_stock(in_stock, self.positions[0]):
                html_body = self._create_html_body_manually_working_required(handling="from_own_stock")
                receiver_email = Config.MAIL_FOR_MANUAL_HANDLING
                subject = "Bestellung aus Lager versenden"

            # if supplier kwon by old system
            elif self._check_if_supplier_kwon_old_system():
                html_body = self._create_html_body_manually_working_required()
                receiver_email = Config.MAIL_FOR_MANUAL_HANDLING
                subject = "Bestellung manuell ausführen"

            # send mail to supplier
            else:
                html_body = self._create_html_body_for_mail_to_supplier()
                receiver_email = self._get_receiver_email_old_system(self.positions[0])
                subject = "Bestellung"

        # if more than one position
        elif len(self.positions) > 1:
            if self._check_suppliers_for_more_than_one_order_position():
                if self._check_if_supplier_kwon_old_system():
                    html_body = self._create_html_body_manually_working_required()
                    receiver_email = Config.MAIL_FOR_MANUAL_HANDLING
                    subject = "Bestellung manuell ausführen"
                else:
                    html_body = self._create_html_body_for_mail_to_supplier()
                    receiver_email = self._get_receiver_email_old_system(self.positions[0])
                    subject = "Bestellung"
            else:
                html_body = self._create_html_body_manually_working_required()
                receiver_email = Config.MAIL_FOR_MANUAL_HANDLING
                subject = "Bestellung manuell ausführen"

        self._send_mail(sender_eMail=sender_eMail,
                        receiver_email=receiver_email,
                        subject=subject,
                        html_body=html_body,
                        mail_client=mail_client)


    def send_mail_for_manually_check(self,
                                     mail_client: smtplib.SMTP,
                                     sender_eMail: str,
                                     in_stock: dict,
                                     ) -> None:
        """
        Sends mail with details for manually checking orders, because the customer have done two or more orders.
        :param in_stock: Dict with the articles in own stock.
        :param sender_eMail: email address where log in.
        :param mail_client: smtp-client
        :return:
        """

        if self.already_worked:
            return

        self._check_own_stock(in_stock, self.positions[0])

        html_body = self._create_html_body_for_manually_check()
        receiver_email = Config.MAIL_FOR_MANUAL_HANDLING
        subject = "Bestellung manuell prüfen, doppelte Namen"

        self._send_mail(sender_eMail=sender_eMail,
                        receiver_email=receiver_email,
                        subject=subject,
                        html_body=html_body,
                        mail_client=mail_client)


    def _send_mail(self,
                   sender_eMail: str,
                   receiver_email: str,
                   subject: str,
                   html_body: str,
                   mail_client: smtplib.SMTP
                   ):
        """
        Send the mail.
        :param sender_eMail:
        :param receiver_email:
        :param subject:
        :param html_body:
        :param mail_client:
        :return:
        """
        mail_CC = Config.MAIL_CC

        msg = MIMEMultipart()

        # set the sending time
        current_time = email.utils.formatdate(localtime=True)
        msg["Date"] = current_time

        msg["From"] = sender_eMail
        msg["Cc"] = mail_CC
        msg["To"] = receiver_email
        msg["Subject"] = subject

        body = MIMEText(html_body, "html")
        msg.attach(body)

        try:
            mail_client.sendmail(from_addr=sender_eMail,
                                 to_addrs=[receiver_email, mail_CC],
                                 msg=msg.as_string())

            with open(Config.WORKED_ORDERS_FILE_PATH, 'a') as datei:
                datei.write(self.ordernumber + "\n")
            logging.info(f"Bestellnummer {self.ordernumber} -- email sendet.")
        except smtplib.SMTPException as e:
            logging.error(f"{self.ordernumber} -- email not sendet: \n{e}")

    def _check_suppliers_for_more_than_one_order_position(self) -> bool:
        """
        Checks if the suppliers the same for all positions.
        :return: true if the suppliers are the same, false otherwise
        """
        first_position_supplier = self.positions[0]["article_number"].split("_")[0]
        for position in self.positions:
            if not position["article_number"].split("_")[0] == first_position_supplier:
                return False
        return True

    def _check_own_stock(self,
                         in_stock: dict,
                         position: dict
                         ) -> bool:
        """
        Checks if a given position in own Stock.
        :param in_stock: Dict with articles where in stock.
        :param position: dict of position
        :return:
        """
        if "Lageritem" in position['article_number']:
            position['article_number'] = position['article_number'].replace("Lageritem_", "")

        if "_" in position['article_number']:
            article_number = position['article_number'].split("_")[1]
        else:
            article_number = position['article_number']

        if article_number in in_stock:
            if int(in_stock[article_number]) >= int(position['amount']):
                return True
        return False

    def _check_if_supplier_kwon_old_system(self) -> bool:
        """
        Checks if the supplier of a given articlenumber in old format is kwon
        :return:
        """
        for item in self.positions:
            if "_" in item['article_number']:
                if "kwon" in item['article_number'].lower():
                    return True
            else:
                return True
        return False

    def _get_clean_article_name(self,
                                source_article_name: str
                                ) -> str:
        """
        Get the Articlename from given position.
        :param source_article_name:
        :return:
        """
        if "amazon" in self.plattform.lower():
            return source_article_name.split("(")[0]
        elif "ebay" in self.plattform.lower():
            return source_article_name.split("Angebots-Nr")[0]
        else:
            return source_article_name

    def _check_if_new_articlenumber_system(self, articlenumber) -> Match[str] | None:
        """
        checks if the Articlenumber is in new format.
        :param articlenumber:
        :return:
        """
        muster = r'^\d{10}-\d$'  # 0000000000-0
        return re.match(muster, articlenumber)

    def _create_html_body_manually_working_required(self,
                                                    handling: str | None = None,
                                                    new_article_number_system: bool = False
                                                    ) -> str:
        """
        creates the html-body for manually working required orders
        :param handling: set the headline for the order. None or from_own_stock
        :param new_article_number_system: if new number system is given set to true
        :return: html-body
        """

        if handling == 'from_own_stock':
            headline = "Diese Bestellung muss aus dem Lager versand werden. "
        else:
            headline = "Diese Bestellung muss manuell ausgeführt werden. "

        if new_article_number_system:
            articles_html_string = self._get_article_html_string_new_numbersystem()
        else:
            articles_html_string = self._get_article_html_string_old_numbersystem()

        body = f"""
        {headline} <br>
        <br>
        Bestellnummer: <strong>{self.ordernumber}</strong> <br>
        <br>
        Adresse: <br>
        <br>
        {self.company}<br>
        {self.first_name} {self.last_name}<br>
        {self.street}<br>
        {self.address_addition + '<br>' if self.address_addition else ""}
        {self.zip_code} {self.city}<br>
        {self.country}<br>
        <br>
        Telefon: <br>
        {self.phone}<br>
        <br>
        E-Mail zur Sendungsverfolgung: <br>
        {self.ordernumber}@sk-sporthandel.de <br>
        <br>
        <br>
        Artikel: <br>
        <br>
        {articles_html_string}
        """

        return body

    def _create_html_body_for_mail_to_supplier(self,
                                               new_article_number_system: bool = False
                                               ) -> str:
        """
        creates the html-body to send it to the supplier.
        :param new_article_number_system: if new number system is given set to true
        :return: html-body
        """
        if new_article_number_system:
            articles_html_string = self._get_article_html_string_new_numbersystem()
        else:
            articles_html_string = self._get_article_html_string_old_numbersystem()

        body = f"""
                Guten Tag. <br>
                <br>
                Bitte versenden sie folgende Artikel: <br> 
                <br> 
                <h3 style='color:red;'>Bitte teilen sie mir bitte umgehend mit, sollte der Artikel wider erwarten nicht lieferbar sein sollte</h3> <br>        
                <br><strong>
                {articles_html_string} <br>
                <br></strong>
                an folgende Adresse: <br>
                <br> <strong>
                {self.company}<br>
                {self.first_name} {self.last_name}<br>
                {self.street}<br>
                {self.address_addition + '<br>' if self.address_addition else ""}
                {self.zip_code} {self.city}<br>
                {self.country}<br>
                <br>
                Telefon: <br>
                {self.phone}<br>
                <br></strong>
                <br>
                Vielen Dank <br>
                <br>
                Sebastian Kliem <br>
                Geschäftsführer <br>
                SK-Sporthandel UG
                """

        return body

    def _create_html_body_for_manually_check(self,
                                             is_in_own_stock: bool = False,
                                             new_article_number_system: bool = False
                                             ) -> str:
        """
        Creates the html_string for manual checking for double names.
        :return:
        """
        if new_article_number_system:
            articles_html_string = self._get_article_html_string_new_numbersystem()
        else:
            articles_html_string = self._get_article_html_string_old_numbersystem()

        if is_in_own_stock:
            own_stock_html_string = "Wir haben den Artikel im Lager"
        else:
            own_stock_html_string = "Der Artikel ist nicht bei uns lagernd"

        body = f"""
                Die Bestellung muss manuell im System geprüft werden.<br>
                <br>
                {self.ordernumber}<br>
                <br>
                Der Name ist doppelt vorhanden!<br> 
                <br> 
                {articles_html_string} <br>
                <br>
                {own_stock_html_string} <br>
                <br>
                an folgende Adresse: <br>
                <br> <strong>
                {self.company}<br>
                {self.first_name} {self.last_name}<br>
                {self.street}<br>
                {self.address_addition + '<br>' if self.address_addition else ""}
                {self.zip_code} {self.city}<br>
                {self.country}<br>
                <br>
                Telefon: <br>
                {self.phone}<br>
                <br>
                <br>
                E-Mail zur Sendungsverfolgung: <br>
                {self.ordernumber}@sk-sporthandel.de <br>      
                """

        return body

    def _get_article_html_string_old_numbersystem(self) -> str:
        """
        Creates the html_string for each article in positionslist
        :return:
        """

        html_string = ""
        for item in self.positions:
            html_string += self._get_clean_article_name(item['articlename']) + "<br>"

            if "Lageritem" in item['article_number']:
                item['article_number'] = item['article_number'].replace("Lageritem_", "")

            if "_" in item['article_number']:
                html_string += item['article_number'].split("_")[1] + "<br>"
            else:
                html_string += item['article_number'] + "<br>"

            if int(item["amount"]) > 1:
                html_string += f"<h2 style='color:red;'>{item['amount']} Stk. </h2> <br>"
            else:
                html_string += f"{item['amount']} Stk. <br>"

            html_string += "<br>"

        return html_string

    def _get_article_html_string_new_numbersystem(self) -> str:
        """
        Creates the html_string for each article in positionslist
        :return:
        """
        # Todo: get article numbers from MongoDB
        html_string = ""
        for item in self.positions:
            html_string += self._get_clean_article_name(item['articlename']) + "<br>"
            html_string += item['article_number'] + "<br>"

            if int(item["amount"]) > 1:
                html_string += f"<h2 style='color:red;'>{item['amount']} Stk. </h2> <br>"
            else:
                html_string += f"{item['amount']} Stk. <br>"

            html_string += "<br>"

        return html_string

    def _get_receiver_email_old_system(self, order_position: dict) -> str:
        """
        Returns the mail-address of the receiver for given article number old system
        :param order_position: position of the order
        :return:
        """
        # return "info@sk-sporthandel.de"

        if "Kwon" in order_position["article_number"]:
            return Config.MAIL_ADDRESS_KWON
        elif "DAX" in order_position["article_number"]:
            return Config.MAIL_ADDRESS_DAX
        elif "Ju" in order_position["article_number"]:
            return Config.MAIL_ADDRESS_JU_SPORTS
        elif "Phoenix" in order_position["article_number"]:
            return Config.MAIL_ADDRESS_PHOENIX
        else:
            return Config.MAIL_ADDRESS_KWON

    def _check_articlenumbers_for_special_handling(self, ) -> None:
        """
        checks the article numbers for special handling (change it)
        :return:
        """

        defined_changes = {
            "Phoenix_J250 - 110120": "Phoenix_J250-120130"
        }

        for position in self.positions:
            if position["article_number"] in defined_changes:
                position["article_number"] = defined_changes[position["article_number"]]
