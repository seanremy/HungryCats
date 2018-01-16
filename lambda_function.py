# based on https://github.com/ModusCreateOrg/alexa-skill-demo/blob/master/lambda_function.py#L1
import datetime
import boto3

def lambda_handler(event, context):
	if (event['session']['application']['applicationId'] !=
		"amzn1.ask.skill.e8ca8a82-52c5-480c-a998-739bd2230f0a"):
		raise ValueError("Invalid Application ID")
	
	if event["request"]["type"] == "LaunchRequest":
		return on_launch(event["request"], event["session"])
	elif event["request"]["type"] == "IntentRequest":
		return on_intent(event["request"], event["session"])
	elif event["request"]["type"] == "SessionEndedRequest":
		return on_session_ended(event["request"], event["session"])

def on_launch(launch_request, session):
	return get_welcome_response()

def on_intent(intent_request, session):
	intent = intent_request["intent"]
	intent_name = intent_request["intent"]["name"]

	if intent_name == "GetHunger":
		return get_hunger()
	elif intent_name == "FeedCats":
		return feed_cats()
	elif intent_name == "AMAZON.HelpIntent":
		return get_welcome_response()
	elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
		return handle_session_end_request()
	else:
		raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
	print "Ending session."

def handle_session_end_request():
	card_title = "HungryCats - Thanks"
	speech_output = "Bye!"
	should_end_session = True

	return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_welcome_response():
	session_attributes = {}
	card_title = "Hungry Cats - Welcome"
	speech_output = "Welcome to the Alexa Hungry Cats skill. " \
					"You can ask me when the cats need to be fed, " \
					"or tell me that you've fed the cats."
	reprompt_text = "Please ask me about the cats."
	should_end_session = False
	return build_response(session_attributes, build_speechlet_response(
		card_title, speech_output, reprompt_text, should_end_session))

def dt_list():
	# gets the current datetime as the appropriate list format
	now = datetime.datetime.utcnow()
	return [(now.hour-5)%24,now.minute] # convert from UTC to eastern time

def hunger_comp(now_m, last_m):
	# returns true if the cats are hungry
	ft1 = 420 	# breakfast time
	ft2 = 1110	# dinner time

	if now_m < last_m:
		return now_m >= ft1
	else:
		return (last_m < ft1 and now_m >= ft1) or (last_m < ft2 and now_m >= ft2)

def get_hunger():
	session_attributes = {}
	card_title = "Hungry Cats - Hunger Level"
	reprompt_text = ""
	should_end_session = False

	dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
	table = dynamodb.Table('WhenWereTheCatsFed')
	response = table.scan()

	now = dt_list()
	last = [int(el) for el in response['Items'][0]['date_time'].split(',')]

	now_m = now[0]*60 + now[1]
	last_m = last[0]*60 + last[1]

	if(hunger_comp(now_m, last_m)):
		speech_output = "The cats are hungry."
	else:
		speech_output = "The cats have been fed."

	return build_response(session_attributes, build_speechlet_response(
		card_title, speech_output, reprompt_text, should_end_session))

def feed_cats():
	session_attributes = {}
	card_title = "Hungry Cats - Feed Cats"
	reprompt_text = ""
	should_end_session = True

	dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
	table = dynamodb.Table('WhenWereTheCatsFed')
	response = table.scan()

	now = ','.join([str(el) for el in dt_list()])
	response = table.update_item(
		Key={'Id': 1},
		UpdateExpression='SET date_time = :val1',
		ExpressionAttributeValues={':val1': now},
		ReturnValues="UPDATED_NEW"
	)
	speech_output = "Thank you for feeding the cats."

	return build_response(session_attributes, build_speechlet_response(
		card_title, speech_output, reprompt_text, should_end_session))

def build_speechlet_response(title, output, reprompt_text, should_end_session):
	return {
		"outputSpeech": {
			"type": "PlainText",
			"text": output
		},
		"card": {
			"type": "Simple",
			"title": title,
			"content": output
		},
		"reprompt": {
			"outputSpeech": {
				"type": "PlainText",
				"text": reprompt_text
			}
		},
		"shouldEndSession": should_end_session
	}

def build_response(session_attributes, speechlet_response):
	return {
		"version": "1.0",
		"sessionAttributes": session_attributes,
		"response": speechlet_response
	}