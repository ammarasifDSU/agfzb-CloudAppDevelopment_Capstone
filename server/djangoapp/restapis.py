import requests
import json
import os
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions


# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))
def get_request(url, api_key=False, **kwargs):
    print(kwargs)
    print(f"GET from {url}")
    if api_key:
        # Basic authentication GET
        try:
            response = requests.get(url, headers={'Content-Type': 'application/json'},
                                    params=kwargs, auth=HTTPBasicAuth('apikey', api_key))
        except:
            print("An error occurred while making GET request. ")
    else:
        # No authentication GET
        try:
            response = requests.get(url, headers={'Content-Type': 'application/json'},
                                    params=kwargs)
        except:
            print("An error occurred while making GET request. ")

    # Retrieving the response status code and content
    status_code = response.status_code
    print(f"With status {status_code}")
    print("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
    print(response.text)
    json_data = json.loads(response.text)

    return json_data

# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)


# Create a get_dealers_from_cf method to get dealers from a cloud function
# def get_dealers_from_cf(url, **kwargs):
# - Call get_request() with specified arguments
# - Parse JSON results into a CarDealer object list
def get_dealers_from_cf(url):
    results = []
    json_result = get_request(url)

    # Retrieve the dealer data from the response
    dealers = json_result
    # For each dealer in the response
    for dealer in dealers:
        # Get its data in `doc` object
        dealer_doc = dealer["doc"]
        # Create a CarDealer object with values in `doc` object
        dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                               id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                               short_name=dealer_doc["short_name"],
                               st=dealer_doc["st"], state=dealer_doc["state"], zip=dealer_doc["zip"])
        results.append(dealer_obj)

    return results


# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
# def get_dealer_by_id_from_cf(url, dealerId):
# - Call get_request() with specified arguments
# - Parse JSON results into a DealerView object list

def get_dealer_by_id(url, dealer_id):
    # Call get_request with the dealer_id param
    json_result = get_request(url, dealerId=dealer_id)

    # Create a CarDealer object from response
    dealer = json_result
    dealer_obj = CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"],
                           id=dealer["id"], lat=dealer["lat"], long=dealer["long"],
                           short_name=dealer["short_name"],
                           st=dealer["st"], state=dealer["state"], zip=dealer["zip"])

    return dealer_obj

def post_request(url, json_payload, **kwargs):
    print(f"POST to {url}")
    try:
        response = requests.post(url, params=kwargs, json=json_payload)
    except:
        print("An error occurred while making POST request. ")
    status_code = response.status_code
    print(f"With status {status_code}")

    return response

# Gets all dealers in the specified state from the Cloudant DB with the Cloud Function get-dealerships
def get_dealers_by_state(url, state):
    results = []
    # Call get_request with the state param
    json_result = get_request(url, state=state)
    dealers = json_result["body"]["docs"]
    # For each dealer in the response
    for dealer in dealers:
        # Create a CarDealer object with values in `doc` object
        dealer_obj = CarDealer(address=dealer["address"], city=dealer["city"], full_name=dealer["full_name"],
                               id=dealer["id"], lat=dealer["lat"], long=dealer["long"],
                               short_name=dealer["short_name"],
                               st=dealer["st"], state=dealer["state"], zip=dealer["zip"])
        results.append(dealer_obj)

    return results

def get_dealer_reviews_from_cf(url, dealer_id):
    results = []
    # Perform a GET request with the specified dealer id
    json_result = get_request(url, dealerId=dealer_id)

    if json_result:
        # Get all review data from the response
        reviews = json_result["data"]["docs"]
        # For every review in the response
        for review in reviews:
            # Create a DealerReview object from the data
            # These values must be present
            review_content = review["review"]
            id = review["_id"]
            name = review["name"]
            purchase = review["purchase"]
            dealership = review["dealership"]

            try:
                # These values may be missing
                car_make = review["car_make"]
                car_model = review["car_model"]
                car_year = review["car_year"]
                purchase_date = review["purchase_date"]

                # Creating a review object
                review_obj = DealerReview(dealership=dealership, id=id, name=name, 
                                          purchase=purchase, review=review_content, car_make=car_make, 
                                          car_model=car_model, car_year=car_year, purchase_date=purchase_date
                                          )

            except KeyError:
                print("Something is missing from this review. Using default values.")
                # Creating a review object with some default values
                review_obj = DealerReview(
                    dealership=dealership, id=id, name=name, purchase=purchase, review=review_content)

            # Analysing the sentiment of the review object's review text and saving it to the object attribute "sentiment"
            review_obj.sentiment = analyze_review_sentiments(review_obj.review)
            print(f"sentiment: {review_obj.sentiment}")

            # Saving the review object to the list of results
            results.append(review_obj)

    return results


# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
# def analyze_review_sentiments(text):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative

def analyze_review_sentiments(review_text):
    # Watson NLU configuration
    try:
        if os.environ['env_type'] == 'PRODUCTION':
            url = os.environ['https://api.au-syd.natural-language-understanding.watson.cloud.ibm.com/instances/40e273e8-8fce-459e-93b5-0637c7099efc']
            api_key = os.environ["W9uxhVRYajb7bn69393UjmRp5QEqnZIVu6ay5xzgwYU7"]
    except KeyError:
        url = 'https://api.au-syd.natural-language-understanding.watson.cloud.ibm.com/instances/40e273e8-8fce-459e-93b5-0637c7099efc'
        api_key = 'W9uxhVRYajb7bn69393UjmRp5QEqnZIVu6ay5xzgwYU7'

    version = '2021-08-01'
    authenticator = IAMAuthenticator(api_key)
    nlu = NaturalLanguageUnderstandingV1(
        version=version, authenticator=authenticator)
    nlu.set_service_url(url)

    # get sentiment of the review
    try:
        response = nlu.analyze(text=review_text, features=Features(
            sentiment=SentimentOptions())).get_result()
        print(json.dumps(response))
        # sentiment_score = str(response["sentiment"]["document"]["score"])
        sentiment_label = response["sentiment"]["document"]["label"]
    except:
        print("Review is too short for sentiment analysis. Assigning default sentiment value 'neutral' instead")
        sentiment_label = "neutral"

    # print(sentiment_score)
    print(sentiment_label)

    return sentiment_label

