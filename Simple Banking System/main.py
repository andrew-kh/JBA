# Write your code here
import random
import sqlite3

conn = sqlite3.connect('card.s3db')

cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS card (
    id INTEGER,
    number TEXT,
    pin TEXT,
    balance INTEGER DEFAULT 0
);
""")

conn.commit()

welcome_menu = [
    "1. Create an account",
    "2. Log into account",
    "0. Exit",
]

auth_menu = ["1. Balance",
             "2. Add income",
             "3. Do transfer",
             "4. Close account",
             "5. Log out",
             "0. Exit"]

welcome_msg = "\n".join(welcome_menu)

auth_msg = "\n".join(auth_menu)


def luhn_create_checksum(card_number_part):
    luhn_list = [int(i) for i in card_number_part]

    for j in range(len(luhn_list)):
        if j % 2 == 0:
            luhn_list[j] = luhn_list[j] * 2

    luhn_list = [k - 9 if k > 9 else k for k in luhn_list]

    luhn_num = 10 - (sum(luhn_list) % 10)

    if luhn_num == 10:
        luhn_num = 0

    return luhn_num


class Card:
    all_cards = []
    state = 0
    IIN = 400000
    checksum = None
    auth_status = None
    card_number = None
    PIN = None
    balance = None

    def __init__(self):
        self.auth_status = 0
        self.balance = 0
        Card.all_cards.append(self)

    def create_card(self):
        rand_id = str(random.randint(1, 999999999))

        pad_source_card_id = '{:0>9}'
        pad_source_pin = '{:0>4}'

        card_number_part = str(self.IIN) + pad_source_card_id.format(rand_id)

        self.checksum = luhn_create_checksum(card_number_part)

        self.PIN = pad_source_pin.format(str(random.randint(1111, 9999)))

        self.card_number = card_number_part + str(self.checksum)

        cur.execute("SELECT max(id) FROM card;")
        max_id = cur.fetchone()[0]

        row_id = max_id + 1 if max_id is not None else 1

        insert_qry = f'INSERT INTO card VALUES ({row_id}, {self.card_number}, {self.PIN}, {self.balance});'

        cur.execute(insert_qry)

        conn.commit()

        print('Your card has been created')
        print('Your card number:\n' + self.card_number)
        print('Your card PIN:\n' + self.PIN)

    def auth_card(self):
        self.auth_status = 1

    def add_income(self, income):
        if income >= 0:
            self.balance += income

            cur.execute(f"UPDATE card SET balance = {self.balance} WHERE number = {self.card_number};")
            conn.commit()

            print("Income was added!")

    def update_info(self, card_number, card_pin, balance):
        self.card_number = card_number
        self.PIN = card_pin
        self.balance = balance


new_card = Card()

while True:

    if new_card.auth_status == 0:

        usr_input = int(input(welcome_msg))

        if usr_input == 0:
            conn.close()
            break

        elif usr_input == 1:
            new_card.create_card()
        elif usr_input == 2:
            usr_card_id = input('Enter your card number:')

            cur.execute(f"SELECT number, pin, balance FROM card WHERE number = '{usr_card_id}';")

            check_res = cur.fetchall()

            usr_card_id_test, usr_pin_id_test, usr_balance = (0, 0, 0)

            if len(check_res) != 0:
                usr_card_id_test, usr_pin_id_test, usr_balance = check_res[0]

            usr_pin = input('Enter your PIN:')
            if (usr_pin == usr_pin_id_test) & (usr_card_id == usr_card_id_test):
                print('You have successfully logged in!')

                new_card = Card()

                new_card.auth_card()

                new_card.update_info(usr_card_id_test, usr_pin_id_test, usr_balance)

            else:
                print('Wrong card number or PIN!')

    elif new_card.auth_status == 1:
        usr_input = int(input(auth_msg))

        if usr_input == 0:
            conn.close()
            break

        elif usr_input == 1:
            print(new_card.balance)

        elif usr_input == 2:
            print("Enter income:")
            new_card.add_income(int(input()))

        elif usr_input == 3:
            print("Transfer\nEnter card number")
            target_card_num = input()

            luhn_checksum = target_card_num[-1]

            if luhn_checksum == str(luhn_create_checksum(target_card_num[:-1])):

                cur.execute(f"SELECT number FROM card WHERE number = {target_card_num};")

                if len(cur.fetchall()) != 0:

                    if target_card_num == new_card.card_number:
                        print("You can't transfer money to the same account!")
                    else:
                        money_to_transfer = input("Enter how much money you want to transfer:")

                        cur.execute(f"SELECT balance FROM card WHERE number = '{new_card.card_number}'")
                        current_balance = int(cur.fetchall()[0][0])

                        if current_balance >= int(money_to_transfer):
                            new_card.balance -= int(money_to_transfer)

                            cur.execute(f"UPDATE card SET balance = {new_card.balance} WHERE number = '{new_card.card_number}';")
                            conn.commit()

                            cur.execute(f"UPDATE card SET balance =  balance + {money_to_transfer} WHERE number = '{target_card_num}';")
                            conn.commit()

                            print("Success!")
                        else:
                            print("Not enough money!")

                else:
                    print("Such a card does not exist.")

            else:
                print("Probably you made a mistake in the card number. Please try again!")

        elif usr_input == 4:

            print("The account has been closed!")
            cur.execute(f"DELETE FROM card WHERE number = {new_card.card_number}")
            conn.commit()

        elif usr_input == 5:
            new_card.auth_status = 0
