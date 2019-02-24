from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import json
import config

application = app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://" + config.username+":"+config.password+"@"+config.host1+":"+config.port+","+config.host2+":"+config.port+","+config.host3+":"+config.port+"/"+config.database+"?"+config.params

mongo = PyMongo(app)

def encode(obj):
	for key, value in obj.items():
		if isinstance(value, ObjectId):
			obj[key] = str(value)
	return obj

def get_team_players(id):
	teams = mongo.db.teams.find({'team_id':int(id)})
	return [team['players'] for team in teams][0]

def add_player_attributes(player_list):
	for player in player_list:
		player['runs'] = 0
		player['wickets'] = 0
	return player_list

def insert_match(data):
	scorecard_1 = {}
	scorecard_2 = {}
	scorecard_1['players'] = add_player_attributes(get_team_players(data['team_1']['team_id']))
	scorecard_2['players'] = add_player_attributes(get_team_players(data['team_2']['team_id']))
	scorecard_1['team_id'] = data['team_1']['team_id']
	scorecard_2['team_id'] = data['team_2']['team_id']
	scorecard_1['innings'] = []
	scorecard_2['innings'] = []
	scorecard_1['extras'] = 0
	scorecard_2['extras'] = 0
	data['sc_' + str(data['team_1']['team_id'])] = scorecard_1
	data['sc_' + str(data['team_2']['team_id'])] = scorecard_2
	ids = mongo.db.matches.find({},{'match_id':1}).sort('match_id',-1).limit(1)
	if ids.count() > 0:
		new_id = ids[0]['match_id'] + 1
	else:
		new_id = 1
	data['match_id'] = new_id
	matches = mongo.db.matches.insert_one(data)
	return mongo.db.matches.find_one({'match_id':new_id})

def insert_scorecard(data):
	ids = mongo.db.scorecards.find({},{'scorecard_id':1}).sort('scorecard_id',-1).limit(1)
	if ids.count() > 0:
		new_id = ids[0]['scorecard_id'] + 1
	else:
		new_id = 1
	data['scorecard_id'] = new_id
	scorecards = mongo.db.scorecards.insert_one(data)
	return [scorecard['scorecard_id'] for scorecard in mongo.db.scorecards.find({'scorecard_id':new_id},{'scorecard_id':1})][0]

@app.route("/players/<id>", methods=['GET'])
def get_player(id):
	players = mongo.db.player_statistics.find({'player_id':int(id)})
	return jsonify({"response":[encode(player) for player in players]})

@app.route("/players", methods=['GET','POST'])
def get_all_players():
	if 'type' in request.args:
		type = request.args.get('type')
		if type == 'bat':
			players = mongo.db.player_statistics.find().sort('runs', -1).limit(5)
		elif type == 'bowl':
			players = mongo.db.player_statistics.find().sort('wickets', -1).limit(5)
	else:
		players = mongo.db.player_statistics.find()
	return jsonify({"response":[encode(player) for player in players]})

@app.route("/teams/<id>", methods=['GET'])
def get_team(id):
	teams = mongo.db.teams.find({'team_id':int(id)})
	return jsonify({"response":[encode(team) for team in teams]})

@app.route("/teams", methods=['GET'])
def get_all_teams():
	teams = mongo.db.teams.find().sort('points',-1)
	return jsonify({"response":[encode(team) for team in teams]})

@app.route("/matches", methods=['GET','POST'])
def matches():
	if request.method == "POST":
		data = request.get_json()
		return jsonify({"response":{"inserted_match":encode(insert_match(data))}})
	elif request.method == "GET":
		matches = mongo.db.matches.find()
		return jsonify({"response":[encode(match) for match in matches]})
	return ""

@app.route("/matches/<id>", methods=['GET','PUT'])
def get_match(id):
	if request.method == "GET":
		matches = mongo.db.matches.find({'match_id':int(id)})
		return jsonify({"response":[encode(match) for match in matches]})
	elif request.method == "PUT":
		data = request.get_json()
		toss_winner = data['toss_winner_team_id']
		first_innings_bat = data['first_team_id']
		second_innings_bat = data['second_team_id']
		mongo.db.matches.update_one({'match_id':int(id)},{
			"$set":{
			"toss_winner": toss_winner,
			"first_innings": first_innings_bat,
			"second_innings": second_innings_bat
				}
			})
		return "toss result updated"
	return ""

@app.route("/scorecard/<id>", methods=['PUT'])
def update_scorecard(id):
	data = request.get_json()
	ball = {}
	ball['runs_scored'] = data['runs_scored']
	ball['is_wicket'] = data['is_wicket']
	ball['bowler'] = data['bowler_id']
	ball['batsman'] = data['batsman_id']
	ball['type'] = data['type']
	if len(data["extras"]) > 0:
		extras = sum([extra["runs"] for extra in data['extras']])
		mongo.db.matches.update({'match_id':int(id)},
		{"$inc":{
				"sc_"+str(data["batsman_team_id"])+".extras": extras
			}}
		)

	mongo.db.matches.update({'match_id':int(id)},
		{"$push":{
				"sc_"+str(data["batsman_team_id"])+".innings": ball
			}}
		)
	mongo.db.matches.update({'match_id':int(id), "sc_"+str(data["batsman_team_id"])+".players.player_id":data['batsman_id']},
		{"$inc":{
				"sc_"+str(data["batsman_team_id"])+".players.$.runs": data['runs_scored']
			}}
		)

	if data['is_wicket'] == 'Y':
		mongo.db.matches.update({'match_id':int(id), "sc_"+str(data["bowler_team_id"])+".players.player_id":data['bowler_id']},
		{"$inc":{
				"sc_"+str(data["bowler_team_id"])+".players.$.wickets": 1
			}}
		)
	return "scorecard updated"

if __name__ == '__main__':
    app.run(debug=True)