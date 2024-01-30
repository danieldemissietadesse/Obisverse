# app/routes/timeblock_routes.py
import stripe
from flask import Blueprint, request, jsonify, current_app


# Set your secret key: remember to change this to your live secret key in production
stripe.api_key = "sk_test_51JVeDoDAsc6s9FznlVl4SNCyqqry5dwBuGp8HxF3vzC20Ag49G1d8HD4r5VRumb5R91TzUcuFSEJaFB3h9I62S6h00RCRPGwuo"


bp = Blueprint('timeblock', __name__, url_prefix='/timeblocks')

@bp.route('/<block_id>/submit_prediction', methods=['POST'])
def submit_prediction(block_id):
    # This route is protected by payment verification
    stripe_token = request.json.get('stripeToken')
    prediction = request.json.get('prediction')

    # Verify the payment
    if not current_app.timeblock_service.verify_payment(stripe_token):
        return jsonify({'error': 'Payment failed'}), 400

    try:
        # Add the prediction to the timeblock
        current_app.timeblock_service.add_prediction(block_id, prediction)
        return jsonify({'message': 'Prediction added successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        # Catch all other exceptions and return a 500 error
        return jsonify({'error': 'An error occurred while submitting the prediction'}), 500


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



# Other routes...
