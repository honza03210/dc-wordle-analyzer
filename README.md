# dc-wordle-analyzer

A script analyzing a picture sent by the Wordle Discord app - who played and whether he solved it successfully.

This project showcases some simple image processing algorithms (flood fill, bounding box computation, erosion, opening, color analysis, shape analysis) all written from the ground up. 

The Wordle Discord app sends only a message "Player1... PlayerN are (were) plaing Wordle" together with an image of their profile pictures and their playthroughs. However, the ordering is inconsistent and alt text is really unhelpful ("X (un)finished games of Wordle").

This script takes the png sent by the app and prints names of the players in the png together with solved / not solved. To match the profile pictures (pfps) with users, the script needs the players pfps in advance in the "players" directory named as username.png (or many other image formats). This could be automatically downloaded with a discord bot (e.g. download the pfps of all users in a wordle channel). The output could then be used to give access to a premium channel to people who have successfully solved todays wordle.


The basic pipeline
1. split the image into sections corresponding to individual players 
2. identify pfp vs playthrough section
3. check for a successful solve
4. analyze pfp colours and match it to a known player
