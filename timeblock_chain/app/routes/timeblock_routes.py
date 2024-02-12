# app/routes/timeblock_routes.py
import stripe
from flask import Blueprint, request, jsonify, current_app
import traceback

# Set your secret key: remember to change this to your live secret key in production
stripe.api_key = "sk_test_51JVeDoDAsc6s9FznlVl4SNCyqqry5dwBuGp8HxF3vzC20Ag49G1d8HD4r5VRumb5R91TzUcuFSEJaFB3h9I62S6h00RCRPGwuo"


bp = Blueprint('timeblock', __name__, url_prefix='/timeblocks')


# ... (other parts of the file remain unchanged)

@bp.route('/<block_id>/submit_prediction', methods=['POST'])
def submit_prediction(block_id):
    prediction = request.json.get('prediction')

    if prediction is None:
        return jsonify({'error': 'Missing prediction'}), 400

    try:
        current_app.timeblock_service.add_prediction(block_id, prediction)
        return jsonify({'message': 'Prediction added successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'An error occurred while submitting the prediction'}), 500

# app/routes/timeblock_routes.py
# ... other imports ...

@bp.route('/<block_id>/update_community_prediction', methods=['POST'])
def update_community_prediction(block_id):
    try:
        current_app.timeblock_service.update_community_prediction(block_id)
        return jsonify({'message': 'Community prediction updated successfully'}), 200
    except ValueError as e:
        current_app.logger.error(f'ValueError: {str(e)}')
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        # Log the full stack trace, not just the exception message
        current_app.logger.error('Failed to update community prediction: %s\n%s', e, traceback.format_exc())
        return jsonify({'error': 'An error occurred while updating the community prediction'}), 500



@bp.route('/', methods=['GET'])
def get_ordered_timeblocks():
    # Fetch ordered timeblocks
    timeblock_service = current_app.timeblock_service
    ordered_timeblocks = timeblock_service.get_ordered_timeblocks()
    return jsonify(ordered_timeblocks)


@bp.route('/verify_payment', methods=['POST'])
def verify_payment():
    data = request.json
    payment_intent_id = data.get('paymentIntentId')

    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        # Check if the payment was successful
        if payment_intent.status == 'succeeded':
            return jsonify({'result': 'success'}), 200
        else:
            # The payment intent exists but is not succeeded
            return jsonify({'result': 'failure', 'status': payment_intent.status}), 400

    except stripe.error.InvalidRequestError as e:
        # Occurs when a PaymentIntent ID is incorrect or does not exist
        return jsonify({'result': 'failure', 'error': str(e), 'message': 'Invalid PaymentIntent ID or PaymentIntent does not exist.'}), 400
    except stripe.error.StripeError as e:
        # Handle general Stripe errors
        return jsonify({'result': 'failure', 'error': str(e), 'message': 'A Stripe error occurred.'}), 400
    except Exception as e:
        # Handle other unforeseen errors
        return jsonify({'result': 'failure', 'error': str(e), 'message': 'An unknown error occurred.'}), 500


@bp.route('/current_and_future_test', methods=['GET'])
def current_and_future_timeblocks():
    try:
        # Use the service to get current and future timeblocks
        timeblock_service = current_app.timeblock_service
        timeblocks = timeblock_service.get_current_and_future_timeblocks()
        
        # Assuming `get_current_and_future_timeblocks` returns a list of dicts
        return jsonify(timeblocks), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching timeblocks', 'message': str(e)}), 500



@bp.route('/tasks/update_timeblock_status', methods=['GET'])
def update_timeblock_status():
    # Security checks can be done here, e.g., checking for X-Appengine-Cron header
    if 'X-Appengine-Cron' not in request.headers or request.headers['X-Appengine-Cron'] != 'true':
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        current_app.timeblock_service.update_status()
        return jsonify({'message': 'Timeblock statuses updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while updating timeblock statuses', 'message': str(e)}), 500


"""@bp.route('/tasks/move_past_timeblocks', methods=['GET'])
def move_past_timeblocks_route():
    # Security checks can be done here, e.g., checking for X-Appengine-Cron header
    if 'X-Appengine-Cron' not in request.headers or request.headers['X-Appengine-Cron'] != 'true':
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        current_app.timeblock_service.move_past_timeblocks()
        return jsonify({'message': 'Past timeblocks moved successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while moving past timeblocks', 'message': str(e)}), 500
"""
# Add to your timeblock_routes.py

# Add to your timeblock_routes.py

@bp.route('tasks/move_past_timeblocks', methods=['GET'])
def move_past_timeblocks():
    try:
        message = current_app.timeblock_service.move_past_timeblocks()
        if message:
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': 'The operation did not return any message'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add this new route to the existing blueprint

# In timeblock_routes.py
@bp.route('/start_binance_stream', methods=['GET'])
def start_binance_stream():
    try:
        current_app.timeblock_service.start_binance_ws()
        return jsonify({'message': 'Started Binance WebSocket stream'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# In timeblock_routes.py

@bp.route('/start_coinbase_polling', methods=['GET'])
def start_coinbase_polling():
    try:
        current_app.timeblock_service.start_coinbase_polling()
        return jsonify({'message': 'Started Coinbase price polling'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/start_bitcoin_stream', methods=['GET'])
def start_bitcoin_stream():
    try:
        current_app.timeblock_service.start_bitcoin_price_stream()
        return jsonify({'message': 'Started Bitcoin price WebSocket stream'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# This route should be called after a timeblock becomes past
@bp.route('/<block_id>/update_accuracy', methods=['POST'])
def update_accuracy(block_id):
    try:
        accuracy = current_app.timeblock_service.update_overall_accuracy(block_id)
        return jsonify({'message': 'Overall accuracy updated successfully', 'accuracy': accuracy}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': 'An error occurred while updating accuracy'}), 500
