# app/models/timeblock.py

class Timeblock:
    def __init__(self, block_id, start_time, end_time, block_number, previous_block_id=None):
        self.block_id = block_id
        self.start_time = start_time
        self.end_time = end_time
        self.block_number = block_number  # New attribute for block number
        self.previous_block_id = previous_block_id
        self.status = 'future'
        self.predictions = []
        self.community_prediction = 0


    def add_prediction(self, prediction):
        if self.status == 'future':
            self.predictions.append(prediction)
            self.update_community_prediction()

    def update_community_prediction(self):
        if self.predictions:
            self.community_prediction = sum(self.predictions) / len(self.predictions)
        else:
            self.community_prediction = 0

    # Method to convert the object to a dictionary for Firestore, if needed
    def to_firestore_document(self):
        return {
            'block_id': self.block_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'block_number': self.block_number,  # Include block number in Firestore document
            'previous_block_id': self.previous_block_id,
            'status': self.status,
            'predictions': self.predictions,
            'community_prediction': self.community_prediction
        }