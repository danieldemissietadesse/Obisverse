# services/timeblock_service.py
# services/timeblock_service.py
from google.cloud import firestore
import stripe
import logging
from datetime import datetime, timedelta
import uuid
from ..models.timeblock import Timeblock
import pytz
import json
from websocket import create_connection
import threading
import requests
import time



class TimeblockService:
    def __init__(self, db):
        self.db = db
        self.collection_ref = self.db.collection('timeblocks')
        self.ensure_future_timeblocks()

    def ensure_future_timeblocks(self):
        # Get the current count of future blocks
        future_blocks_query = self.collection_ref.where(
            'end_time', '>', datetime.now()
        ).stream()

        future_blocks_count = len(list(future_blocks_query))

        # If no future blocks exist, initialize all 2016 blocks
        if future_blocks_count == 0:
            self.create_timeblocks(2016)
        else:
            # Calculate how many new blocks to create to maintain 2016 future blocks
            blocks_to_create = 2016 - future_blocks_count
            if blocks_to_create > 0:
                self.create_timeblocks(blocks_to_create)


    def create_timeblocks(self, blocks_to_create):
        # Try to find the last block to determine the start time and block number for new blocks
        last_block = None
        last_block_query = self.collection_ref.order_by(
            'end_time', direction=firestore.Query.DESCENDING
        ).limit(1).stream()
        
        # Extract the last block if it exists
        last_block_list = list(last_block_query)
        if last_block_list:
            last_block = last_block_list[0].to_dict()

        start_time = last_block['end_time'] if last_block else datetime.now()
        previous_block_id = last_block['block_id'] if last_block else None
        last_block_number = last_block['block_number'] if last_block else 0  # Get the last block number

        # Create the specified number of new timeblocks
        for i in range(blocks_to_create):
            end_time = start_time + timedelta(minutes=10)
            block_id = str(uuid.uuid4())
            block_number = last_block_number + i + 1  # Increment block number for each new block

            timeblock = Timeblock(block_id, start_time, end_time, block_number, previous_block_id)

            # Use the to_firestore_document method to create a dictionary
            timeblock_data = timeblock.to_firestore_document()

            self.collection_ref.document(block_id).set(timeblock_data)

            # Update for the next iteration
            start_time = end_time
            previous_block_id = block_id

    

    def get_ordered_timeblocks(self):
        current_time = datetime.now()
        query = self.collection_ref.order_by('start_time').stream()
        ordered_timeblocks = []

        for doc in query:
            timeblock = doc.to_dict()
            start_time = timeblock['start_time'].replace(tzinfo=None)  # Making timezone-naive
            end_time = timeblock['end_time'].replace(tzinfo=None)    # Making timezone-naive

            # Now compare with the timezone-naive current_time
            if start_time <= current_time < end_time:
                status = 'current'
            elif current_time >= end_time:
                status = 'past'
            else:
                status = 'future'
            timeblock['status'] = status

            ordered_timeblocks.append(timeblock)

        return ordered_timeblocks

    def get_timeblocks(self):
        return self.timeblocks

    def update_status(self):
        # Logic to update the status of each timeblock
        return

    def verify_payment(self, stripe_token):
        try:
            # Verify the Stripe token by making a charge
            stripe.Charge.create(
                amount=200,  # $2 charge
                currency='usd',
                description='Timeblock Prediction Payment',
                source=stripe_token,
            )
            return True
        except stripe.error.StripeError:
            return False

    def add_prediction(self, block_id, prediction):
        timeblock_ref = self.collection_ref.document(block_id)
        timeblock_doc = timeblock_ref.get()

        if not timeblock_doc.exists:
            raise ValueError('Timeblock not found.')

        timeblock_data = timeblock_doc.to_dict()
        prediction_value = float(prediction.replace(',', '').replace('$', ''))

        if 'predictions' not in timeblock_data:
            timeblock_data['predictions'] = []

        timeblock_data['predictions'].append(prediction_value)
        timeblock_ref.update(timeblock_data)

    def update_community_prediction(self, block_id):
        timeblock_ref = self.collection_ref.document(block_id)
        timeblock_doc = timeblock_ref.get()

        if not timeblock_doc.exists:
            raise ValueError('Timeblock not found.')

        timeblock_data = timeblock_doc.to_dict()

        if 'predictions' in timeblock_data and timeblock_data['predictions']:
            # Convert all predictions to floats before summing
            predictions = [float(pred) for pred in timeblock_data['predictions'] if isinstance(pred, (int, float, str)) and str(pred).replace('.','',1).isdigit()]
            total = sum(predictions)
            count = len(predictions)
            if count > 0:
                timeblock_data['community_prediction'] = total / count
                timeblock_ref.update({'community_prediction': timeblock_data['community_prediction']})
            else:
                raise ValueError('No valid predictions to calculate community prediction.')
        else:
            raise ValueError('No predictions to calculate community prediction.')
    # In your TimeblockService class

    def get_current_and_future_timeblocks(self):
        current_time = datetime.now()
        query = self.collection_ref.order_by('start_time').stream()
        timeblocks = []

        for doc in query:
            timeblock = doc.to_dict()
            # Adjusting timezone if necessary
            start_time = timeblock['start_time'].replace(tzinfo=None)
            end_time = timeblock['end_time'].replace(tzinfo=None)

            if start_time <= current_time < end_time or current_time < start_time:
                # Include logic to convert Firestore Timestamp to datetime if necessary
                timeblock['start_time'] = start_time
                timeblock['end_time'] = end_time
                timeblocks.append(timeblock)

        return timeblocks
        
    
    def update_timeblock_statuses(self):
        current_time = datetime.now()
        timeblocks_query = self.collection_ref.stream()

        for doc in timeblocks_query:
            timeblock = doc.to_dict()
            start_time = timeblock['start_time'].replace(tzinfo=None)
            end_time = timeblock['end_time'].replace(tzinfo=None)
            doc_ref = self.collection_ref.document(doc.id)

            if end_time <= current_time:
                # If the block's end time is before the current time, mark it as past
                doc_ref.update({'status': 'past'})
            elif start_time <= current_time < end_time:
                # If the current time falls within the start and end time of the block, mark it as current
                doc_ref.update({'status': 'current'})
            # No need to update future blocks as their status is determined by the absence of 'past' or 'current'

    # Add to the TimeblockService class
    
    # Inside TimeblockService class in timeblock_service.py

    def move_past_timeblocks(self):
        utc_now = datetime.now(pytz.utc)
        pastblocks_ref = self.db.collection('pastblocks')
        bitcoindata_ref = self.db.collection('bitcoindata').document('BTCUSD')

        all_timeblocks = self.collection_ref.stream()
        bitcoindata_doc = bitcoindata_ref.get()
        if not bitcoindata_doc.exists:
            print("Bitcoin data not found.")
            return

        bitcoin_price = bitcoindata_doc.to_dict()['bitcoinPrice']
        batch = self.db.batch()
        moved_count = 0

        for timeblock in all_timeblocks:
            timeblock_dict = timeblock.to_dict()
            timeblock_end_time = timeblock_dict['end_time'].replace(tzinfo=pytz.utc)

            if timeblock_end_time < utc_now and timeblock_dict['status'] != 'past':
                community_prediction = timeblock_dict['community_prediction']
                accuracy = 100 - (abs(community_prediction - bitcoin_price) / bitcoin_price) * 100
                timeblock_dict['status'] = 'past'
                timeblock_dict['overallAccuracy'] = accuracy

                new_pastblock_ref = pastblocks_ref.document(timeblock.id)
                batch.set(new_pastblock_ref, timeblock_dict)
                batch.delete(self.collection_ref.document(timeblock.id))

                moved_count += 1

        batch.commit()
        return f'Moved {moved_count} past timeblocks to the pastblocks collection and updated accuracy'
    # Inside the TimeblockService class

    # Inside the TimeblockService class

    def start_binance_ws(self):
        def run():
            # Binance WebSocket endpoint for live Bitcoin price in the BTCUSDT market
            ws_endpoint = 'wss://stream.binance.com:9443/ws/btcusdt@trade'
            ws = create_connection(ws_endpoint)

            while True:
                response = ws.recv()
                data = json.loads(response)
                # Extract the price from the response and update Firestore
                if data.get('e') == 'trade':  # If the event type is a trade
                    price = data['p']  # 'p' for price
                    # Update Firestore with the latest price
                    self.db.collection('bitcoindata').document('YOUR_DOCUMENT_ID').set({
                        'bitcoinPrice': float(price)
                    }, merge=True)  # Use merge to avoid overwriting other fields
                    print(f"Bitcoin price updated: {price}")

        # Run the WebSocket client in a separate thread
        thread = threading.Thread(target=run)
        thread.daemon = True  # Optional: makes the thread die with the main thread
        thread.start()
    
    # Inside the TimeblockService class's start_coinbase_polling method

    def start_coinbase_polling(self):
        def poll():
            coinbase_url = 'https://api.coinbase.com/v2/prices/BTC-USD/spot'
            while True:
                try:
                    response = requests.get(coinbase_url)
                    response.raise_for_status()  # Raises an error for bad status
                    data = response.json()
                    price = data['data']['amount']
                    print(f"Bitcoin price from Coinbase: {price}")

                    # Update Firestore with the latest price
                    self.db.collection('bitcoindata').document('BTCUSD').set({
                        'bitcoinPrice': float(price),
                        'timestamp': firestore.SERVER_TIMESTAMP
                    }, merge=True)
                except requests.exceptions.HTTPError as e:
                    if response.status_code == 429:
                        # If rate limit is hit, use the Retry-After header or default to 10 seconds
                        wait_time = int(response.headers.get('Retry-After', 10))
                        print(f"Rate limit hit, waiting for {wait_time} seconds.")
                        time.sleep(wait_time)
                    else:
                        print(f"HTTP error occurred: {e}")
                except Exception as e:
                    print(f"Error fetching from Coinbase: {e}")
                time.sleep(1)  # Poll every 1 second

        # Run the poll function in a separate thread
        thread = threading.Thread(target=poll)
        thread.daemon = True
        thread.start()
    
    def start_bitcoin_price_stream(self):
        def run():
            ws_endpoint = 'wss://ws.coincap.io/prices?assets=bitcoin'
            ws = create_connection(ws_endpoint)
            while True:
                response = ws.recv()
                data = json.loads(response)
                bitcoin_price = data.get('bitcoin')
                if bitcoin_price:
                    # Convert price to float and update Firestore
                    self.db.collection('bitcoindata').document('BTCUSD').update({
                        'bitcoinPrice': float(bitcoin_price),
                        'timestamp': firestore.SERVER_TIMESTAMP
                    })
                    print(f"Bitcoin price updated in Firestore: {bitcoin_price}")

        # Start the WebSocket connection in a new thread
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()