# services/timeblock_service.py
# services/timeblock_service.py
from google.cloud import firestore
import stripe
from datetime import datetime, timedelta
import uuid
from ..models.timeblock import Timeblock

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
        # Logic to add a prediction to a timeblock and update the community prediction
        timeblock_ref = self.collection_ref.document(block_id)
        timeblock = timeblock_ref.get().to_dict()

        if not timeblock:
            raise ValueError('Timeblock not found.')

        # Convert prediction to a numerical value (strip commas and dollar sign)
        prediction_value = float(prediction.replace(',', '').replace('$', ''))

        # Add the prediction to the timeblock
        if 'predictions' not in timeblock:
            timeblock['predictions'] = []

        timeblock['predictions'].append(prediction_value)

        # Update the community prediction average
        total = sum(timeblock['predictions'])
        count = len(timeblock['predictions'])
        timeblock['community_prediction'] = total / count if count else prediction_value

        # Commit the changes to Firestore
        timeblock_ref.update(timeblock)
