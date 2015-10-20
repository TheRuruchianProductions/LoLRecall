"""Recorder.py: Records spectator data file for a summoner."""
__author__ = 'Ruruche'
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Ruruche"
__email__ = "theruruche@gmail.com"

import requests
import concurrent.futures
import time
from datetime import datetime
import json

api_key = ''
try:
    with open('api_key.txt', 'r') as keyfile:
        api_key = keyfile.read().strip()
        if not api_key.strip():
            print('Please input your riot api key in the api_key.txt file. This key can be found at riot developer page.')
except:
    with open('api_key.txt', 'w') as keyfile:
        keyfile.write('')
    print('Please input your riot api key in the api_key.txt file. This key can be found at riot developer page.')
api_url = 'https://na.api.pvp.net'
base_url = 'http://spectator.na.lol.riotgames.com'
ERROR_CODES = {
    200 : 'success',
    403 : 'forbidden',
    429 : 'rate limit exceeded',
    404 : 'not found',
    401 : 'unauthorized'
}
RESPONSES = {v:k for k,v in ERROR_CODES.items()}
class GameNotAvailableException(Exception):
    def __init__(self, message):
        self.value = message
    def __str__(self):
        return repr(self.value)
        
class SummonerDto:
    def __init__(self, id, name, profileIconId, revisionDate, summonerLevel):
        self.id = id
        self.name = name
        self.profileIconId = profileIconId
        self.revisionDate = revisionDate
        self.summonerLevel = summonerLevel

class Summoner:
    root = lambda region : api_url+'/api/lol/'+region+'/v1.4/summoner/'
    @staticmethod
    def summoner_names(summoners, region='na'):
        url = Summoner.root(region) + 'by-name/'+','.join(summoners)+'?api_key=' + api_key
        resp = requests.get(url)
        if ERROR_CODES[resp.status_code] == 'success':
            return {k:SummonerDto(**v) for (k,v) in resp.json().items() }
        return {}  
        
class CurrentGame:
    @staticmethod
    def current_game(summonerId, platformId='NA1'):
        url = api_url+'/observer-mode/rest/consumer/getSpectatorGameInfo/'+platformId+'/'+str(summonerId)+'?api_key='+api_key
        resp = requests.get(url)
        if ERROR_CODES[resp.status_code] == 'success':
            return resp.json()
        return {}
    @staticmethod
    def current_game_metadata(summonerId, platformId='NA1'):
        game = CurrentGame.current_game(summonerId, platformId)
        if not game:
            raise GameNotAvailableException('Game of summoner ('+str(summonerId)+') in '+str(platformId)+' is not available')
        gid = game['gameId']
        encryption = game["observers"]["encryptionKey"]
        platformId = game["platformId"]
        return {'gameId':gid, 'encryptionKey':encryption, 'platformId':platformId}
    @staticmethod
    def summoner_current_game(summoners, region='na', platformId='NA1'):
        return { summoner:CurrentGame.current_game_metadata( Summoner.summoner_names(summoners, region)[''.join(summoner.split()).lower()].id, platformId )  for summoner in summoners}
class Spectator:
    def ConstructSpectator(summoner, region='na', platformId='NA1'):
        current = CurrentGame.summoner_current_game([summoner], region, platformId)
        return Spectator( platformId, current[summoner]['gameId'], list(current.values())[0])
    def __init__(self, platformId, gameId, currentGame):
        self.platformId = platformId
        self.gameId = gameId
        self.currentGame = currentGame
    def gameMetaData(self):
        return Spectator.getGameMetaData(self.platformId, self.gameId).json()
    def lastChunkInfo(self):
        return Spectator.getLastChunkInfo(self.platformId, self.gameId).json()
    def chunkFrame(self, chunkId):
        return Spectator.getChunkFrame(self.platformId, self.gameId, chunkId)
    def keyFrame(self, keyFrameId):
        return Spectator.getKeyFrame(self.platformId, self.gameId, keyFrameId)
    def spectate(self, keyFrames={}, chunks={}):
        print('Retrieving metadata')
        lastChunkInfo = self.lastChunkInfo()
        metadata = self.gameMetaData()
        keyFrameLastTaken = 0
        gameChunkLastTaken = 0

        print('\nLast chunk >' + str(lastChunkInfo))
        print('\nMetadata >' + str(metadata))
        chunkInterval = metadata['chunkTimeInterval']
        keyFrameInterval = metadata['keyFrameTimeInterval']
        
        sleeptime = min(chunkInterval/1000, keyFrameInterval/1000)
        # while the game has not ended requests for keyframes and chunks 
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # initial get
            for keyFrameId in range(lastChunkInfo['keyFrameId']+1):
                print('getting keyframe ' + str(keyFrameId))
                keyFrames[keyFrameId] = executor.submit( self.keyFrame, keyFrameId) 
                keyFrameLastTaken = keyFrameId
            for chunkId in range( lastChunkInfo['chunkId']+1):
                print('getting chunk ' + str(chunkId))
                chunks[chunkId] = executor.submit( self.chunkFrame, chunkId)
                gameChunkLastTaken = chunkId

            while lastChunkInfo['endGameChunkId']==0 :
                if lastChunkInfo['keyFrameId'] > keyFrameLastTaken:
                    for keyFrameId in range(keyFrameLastTaken +1, lastChunkInfo['keyFrameId']+1):
                        print('getting keyframe ' + str(keyFrameId))
                        keyFrames[keyFrameId] = executor.submit( self.keyFrame, keyFrameId) 
                        keyFrameLastTaken = keyFrameId
                if lastChunkInfo['chunkId'] > gameChunkLastTaken:
                    for chunkId in range( gameChunkLastTaken+1, lastChunkInfo['chunkId']+1):
                        print('getting chunk ' + str(chunkId))
                        chunks[chunkId] = executor.submit( self.chunkFrame, chunkId)
                        gameChunkLastTaken = chunkId
                print('Sleeping for '+ str(sleeptime))
                time.sleep(sleeptime)
                lastChunkInfo = self.lastChunkInfo()
            for keyFrameId in range(keyFrameLastTaken +1, lastChunkInfo['keyFrameId']+1):
                print('getting keyframe ' + str(keyFrameId))
                keyFrames[keyFrameId] = executor.submit( self.keyFrame, keyFrameId) 
                keyFrameLastTaken = keyFrameId
            for chunkId in range( gameChunkLastTaken+1, lastChunkInfo['endGameChunkId']+1):
                print('getting chunk ' + str(chunkId))
                chunks[chunkId] = executor.submit( self.chunkFrame, chunkId)
                gameChunkLastTaken = chunkId
            print('\nGot keyFrames '+ str(keyFrames))
            print('\nGot chunks ' + str(chunks))
            # get results 
            keyFrames   = { k: v.result() for k,v in keyFrames.items()}
            chunks      = { k: v.result() for k,v in chunks.items()}
            keyFrames   = { k: v.content for k,v in keyFrames.items() if v.ok }
            chunks      = { k: v.content for k,v in chunks.items() if v.ok }
        lastChunkInfo = self.lastChunkInfo()
        metadata = self.gameMetaData()
        dir_name = str(self.gameId)+'/'
        keydirectory = 'keyFrames/'+dir_name
        chunksdirectory = 'chunks/'+dir_name
        infodirectory = 'info/'+dir_name
        launchdirectory = 'replay/'+dir_name
        import os 
        print('Writing data to disk')
        if not os.path.isdir(chunksdirectory):
            os.makedirs(chunksdirectory)
        if not os.path.isdir(keydirectory):
            os.makedirs(keydirectory)
        if not os.path.isdir(infodirectory):
            os.makedirs(infodirectory)
        if not os.path.isdir(launchdirectory):
            os.makedirs(launchdirectory)
        for k,v in keyFrames.items():
            with open( keydirectory+str(k), 'wb') as keyfile:
                keyfile.write(v)
        for k,v in chunks.items():
            with open( chunksdirectory+str(k), 'wb') as chunkfile:
                chunkfile.write(v)
        with open(infodirectory+'getLastChunkInfo', 'w') as file:
            file.write(json.dumps(lastChunkInfo))
        with open(infodirectory+'getGameMetaData', 'w') as file:
            file.write(json.dumps(metadata))
        self.currentGame['version'] = str(Spectator.game_version().content.decode())
        with open(infodirectory+'serverdata.txt', 'w') as file:
            file.write(json.dumps(self.currentGame))
        with open(launchdirectory+'replay.bat', 'w') as file:
            file.write('start "" "League of Legends.exe" "8394" "LoLLauncher.exe" "" "spectator localhost:5000 '+str(self.currentGame['encryptionKey'])+' '+str(self.currentGame['gameId'])+' NA1-%RANDOM%%RANDOM%"')
        return self.gameId
    def spectator_call(getInfo):
        def decorated(*args):
            url = base_url +'/observer-mode/rest/consumer/'+str(getInfo(*args))
            return requests.get(url)
        return decorated
    @spectator_call
    def getGameMetaData(platformId, gameId):
        return "getGameMetaData/" + platformId + "/" + str(gameId) + "/0/token"
    @spectator_call
    def getLastChunkInfo(platformId, gameId):
        return "getLastChunkInfo/" + platformId + "/" + str(gameId) + "/0/token"
    @spectator_call
    def getChunkFrame(platformId, gameId, chunkId):
        return "getGameDataChunk/" + platformId + "/" + str(gameId) + "/" + str(chunkId) + "/token" if chunkId else None
    @spectator_call
    def getKeyFrame(platformId, gameId, frameId):
        return "getKeyFrame/" + platformId + "/" + str(gameId) + "/" + str(frameId) + "/token"
    @spectator_call
    def game_version():
        return 'version'
if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    with open('regional_endpoints.txt', 'r') as file:
        entries = [line.split() for line in file.readlines()]
        regional_endpoints = {e[0]: e[2] for e in entries}
        platformIds = {e[0]: e[1] for e in entries}
    with open('spectator_endpoints.txt', 'r') as file:
        entries = [line.split() for line in file.readlines()]
        spectator_endpoints = {e[0] : e[1] for e in entries}
        spectator_ports = {e[0] : e[2] for e in entries}
    parser.add_argument('summoner' , help='Summoner name')
    parser.add_argument('--region', '-r',default='NA', help='The region in which summoner is found (default:NA). \n\tRegions available:\n'+str([i for i in regional_endpoints.items()]))
    parser.add_argument('--spectator', '-s', default='NA', help='The spectator endpoint to record from (default:NA). This usually coincides with the api region.')
    parser.add_argument('--gameID', '-g', help='The game ID. Only needed for recording from non-live streams like op.gg and replay.gg')
    args = parser.parse_args()
    name = args.summoner
    region = args.region
    spectate_endpoint = args.spectator
    gid = args.gameID
    if spectate_endpoint.endswith('.gg'):
        if not gid:
            print ('For non-live recordings please input a game ID of the game you want, this can be found in bat files they give')
            quit()
        print('Warning: you need to find the encryption key from the bat files you download from the site to replay the data')
    try:
        api_url = 'https://'+regional_endpoints[region]
        base_url = 'http://'+spectator_endpoints[spectate_endpoint]
        if not spectate_endpoint.endswith('.gg'):
            spectator = Spectator.ConstructSpectator(name, region, platformIds[region])
        else :
            spectator = Spectator(platformIds[region], gameId, currentGame)
        print('From '+region)
        print('Recording '+str(name)+"'s game")
        print('Finished '+str(spectator.spectate()))
    except GameNotAvailableException as e:
        print(e)