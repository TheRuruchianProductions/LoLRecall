"""ReplayServer.py: Replays data files captured by Recorder.py."""
__author__ = 'Ruruche'
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Ruruche"
__email__ = "theruruche@gmail.com"

from flask import Flask, jsonify
import requests
import os
import json
app = Flask(__name__)
keyFrameCounter = [1]
@app.route('/observer-mode/rest/consumer/getGameMetaData/<platformId>/<int:gameId>/<random>/token', methods=['GET'])
def getGameMetaData(platformId, gameId, random):
    print('\nGame metadata requested for game '+str(gameId))
    content = ""
    with open('info/'+str(gameId)+'/getGameMetaData', encoding='utf-8') as file:
        content = file.read()
    return content
@app.route('/observer-mode/rest/consumer/getLastChunkInfo/<platformId>/<int:gameId>/<random>/token', methods=['GET'])
def getLastChunkInfo(platformId, gameId, random):
    print('\nChunk info requested for game '+str(gameId))
    content = ""
    with open('info/'+str(gameId)+'/getLastChunkInfo', encoding='utf-8') as file:
        content = file.read()
        jcontent = json.loads(content)
        keyFrameId = jcontent['keyFrameId']
        keyFrameId = min(keyFrameCounter[0], keyFrameId)
        
        jcontent['keyFrameId'] = keyFrameId
        content = json.dumps(jcontent)
    return content
@app.route('/observer-mode/rest/consumer/getGameDataChunk/<platformId>/<int:gameId>/<int:chunkId>/token', methods=['GET'])
def getGameDataChunk(platformId, gameId, chunkId):
    print('\nGame data chunk '+str(chunkId)+' for game '+str(gameId)+' requested')
    content = ""
    with open('chunks/'+str(gameId)+'/'+str(chunkId), 'rb') as file:
        content = file.read()
    return content
@app.route('/observer-mode/rest/consumer/getKeyFrame/<platformId>/<int:gameId>/<int:frameId>/token', methods=['GET'])
def getKeyFrame(platformId, gameId, frameId):
    print('\n*******\nKey frame '+str(frameId)+' for game '+str(gameId)+' requested')
    content = ""
    keyFrameCounter[0] += 1
    with open('keyFrames/'+str(gameId)+'/'+str(frameId), 'rb') as file:
        content = file.read()
    return content    
@app.route('/observer-mode/rest/consumer/version', methods=['GET'])
def getVersion():
    print('\nVersion requested')
    return requests.get('http://spectator.na.lol.riotgames.com/observer-mode/rest/consumer/version').content
    
    
if __name__ == '__main__':
    app.run(debug=True)