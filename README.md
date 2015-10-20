# SummonerRecall

<h3> This is a python script to record spectator information from LoL. </h3>
<h4> This is written under GPLv3. Spread the joy. </h4>

Requirements :
Python 3.4
<br> https://www.python.org/downloads/

Dependencies:
<ol>
<li> Open command line
<ol>
<li> window + r 
<li> type cmd
<li> press enter
</ol>
<li> Type
<ol>
<li> pip install requests
<li> pip install flask
<li> close the window
</ol>
<li> Download LoLRecall
<ol>
<li> On the right there is a button Download ZIP; click it
<li> Unzip it and go into the folder
<li> shift+rightclick
<li> select open command line window here
</ol>
<li> Type 
<ol>
<li> python Recorder.py (This will create the api_key.txt for you)
</ol>
<li> Get API key from Riot 
<ol>
<li> Login to <b>https://developer.riotgames.com/ </b>
<li> copy the key to api_key.txt generated in the previous step
</ol>
<li> Record
<ol>
<li> start a game
<li> type : python Recorder.py <b>[summoner name]</b> (Type the actual summoner name without the [])
<li> a replay.bat will be generated in the replay directory under the folder named with the gameID
</ol>
<li> Replay
<ol>
<li> type : python ReplayServer.py
<li> copy the replay.bat you want
<li> go to League of Legends director: ...\Riot Games\League of Legends\RADS\solutions\lol_game_client_sln\releases\<b>[some numbers]</b>\deploy
<li> paste the replay.bat here
<li> double click the replay.bat
<li> Enjoy!
</ol>
</ol>
<h5>
Pending development:
<ul>
<li> Summoner tracker
<li> Easier replays
</ul>
</h5>
