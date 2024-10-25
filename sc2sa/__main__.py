import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

class SCALABLECAPITAL:
    delimiter = ';'
    quotechar = '\"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_MINIMAL

def str_to_float(string):
    if string == '' or string is None:
        string = '0.0'
    return float(string.replace('.', '').replace(',', '.'))

def convert_data(input_path):
    """
    Scalable Capital Format
    date - Date in YYYY-MM-DD format
    time - Time in HH:MM:SS format
    status - Executed or Pending
    reference - Reference string
    description - Includes name of the shares or service
    assetType - Security or Cash
    type - Type of the transcation: Fee, Buy, Sell Deposit or Distribution (dividend pay)
    isin - ISIN code
    shares - Number of shares
    price - Price per share or unit
    amount - Total amount
    fee - Fee applied to the transaction
    tax - Tax applied to the transaction
    currency - Currency of the transaction
    """

    file_path = Path(input_path)
    logger.info(f"Input file path = {file_path.absolute()}")

    dict_event = {
        'deposit': 'CASH_IN',
        'buy': 'BUY',
        'fee': 'FEE',
        'distribution': 'DIVIDEND',
    }

    converted_data = []
    with open(file_path, encoding='UTF-8') as csv_file:
        transactions =csv.DictReader(csv_file, dialect=SCALABLECAPITAL)
        for row in transactions:

            # If the line is empty, just skip
            if row['date'] == '' or row['date'] is None:
                continue

            # Event
            event = dict_event.get(row['type'].casefold())
            if event is None:
                logger.error(f"Event '{row['type']}' not defined")
                exit(1)

            # Date
            date = f"{row['date']} {row['time']}" #TODO implement some validation here

            # Symbol
            symbol = row['isin']

            # Price
            if event == 'FEE':
                price = 0
            elif event == 'DIVIDEND':
                price = 0
            elif event == 'CASH_IN':
                price = 1
            else:
                price = str_to_float(row['price'])

            # Quantity
            if event == 'CASH_IN':
                quantity = str_to_float(row['amount'])
            elif event == 'FEE':
                quantity = 0
            elif event == 'DIVIDEND':
                quantity = str_to_float(row['amount'])
            else:
                quantity = row['shares']

            if quantity is None:
                logger.error(f"Quantity variable not defined")

            # Currency
            currency = row['currency']

            # FeeTax
            fee = str_to_float(row['fee'])
            tax = str_to_float(row['tax'])
            feetax = fee + tax

            if event == 'FEE': # Override all of the above if it's a FEE event
                feetax = str_to_float(row['amount']) * -1.0

            # Exchange
            exchange = ''

            # FeeCurrency
            feecurrency = 'EUR'

            #DoNotAdjustCash
            donotadjustcash = False

            # Note
            note = f"{row['description']} - {row['status']} - {row['reference']}"

            out_row = [event, date, symbol, price, quantity, currency, feetax, exchange, feecurrency, donotadjustcash, note]
            converted_data.append(out_row)

    return converted_data

def argument_parser():
    parser = argparse.ArgumentParser(description=f"Converts a CSV export file from Scalable capital to \
                                                 the Snowball Analytics CSV format")
    parser.add_argument("filename", help="Input CSV file to be converted")
    parser.add_argument("-d", "--debug", action="store_true", help="Show debuffing log traces")
    parser.add_argument("-o", "--output-file", default="Scalable_capital_transactions_{date}.csv", help="Output file")
    return parser.parse_args()

if __name__ == '__main__':
    args = argument_parser()
    input_path = args.filename

    log_level = "DEBUG"
    logger.remove(0)
    logger.add(sys.stderr, level=log_level)
    logger.info("Starting program...")

    converted_data = convert_data(input_path)
    first_line = "Event,Date,Symbol,Price,Quantity,Currency,FeeTax,Exchange,FeeCurrency,DoNotAdjustCash,Note\n"

    today= datetime.today()
    output_path = Path(args.output_file.format(date=today.strftime("%Y%m%d")))

    with open(output_path, "w", newline='', encoding='utf-8') as output_file:
        output_file.write(first_line)
        csvwriter = csv.writer(output_file, delimiter=',', quotechar='\"', quoting=csv.QUOTE_MINIMAL)
        for row in converted_data:
            csvwriter.writerow(row)
    logger.info(f"Output file written to {output_path.absolute()}")
