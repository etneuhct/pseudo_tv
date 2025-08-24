This script automates the creation of a channel catalog via ErsatzTV + Jellyfin.
Using pre-established formats, it finds shows and assigns them to channels. 
Then pushes the information to ErsatzTV.

The idea behind the app is to define frameworks for channels and attach relevant programs 
to them based on the user's library. Therefore, empty blocks are to be expected. 
This results in programs with fixed times, as one would expect on television. 

The process is semi-automated. Format creation is done upstream (here via chatgpt & chatgpt agent).

ErsatzTV is undergoing rapid development, so this program could quickly become obsolete.
Test with: 25.4.0-docker-amd64