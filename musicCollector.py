# This Python file uses the following encoding: utf-8

import fbconsole
import urllib, urllib2
import json
import re
import unicodedata

def strip_accents(s): # Credit to oefe on stackoverflow.com
  if not s: return False
  return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
 
def buildArtistList(members,prior):
  final = []
  for i in members:
    priorlen = len(final)
    newartists = []
    for artist in fbconsole.get('/%s/music' %(i))['data']: 
      newartists.append(artist['name'])
    for artist in newartists:
      if artist not in (final + prior):
        final.append(artist)
    if len(final) - priorlen == 1:
      print 'Got artists of %s - %s new artist added' %((fbconsole.get('/%s' %(i)))['name'],len(final) - priorlen)
    else:
      print 'Got artists of %s - %s new artists added' %((fbconsole.get('/%s' %(i)))['name'],len(final) - priorlen)
  return final

def readPriorFile(filename):
  priorlist = filename.read().splitlines()
  if len(priorlist) == 1:
    print "Loaded the name of %s artist already downloaded" %len(priorlist)
  else:
    print "Loaded the names of %s artists already downloaded" %len(priorlist)
  return priorlist
  
def writePriorFile(outfile,priorlist,currlist):
  outtext = ""
  for i in sorted(priorlist + currlist):
    outtext += "%s\n" %(i)
  outfile.write(outtext)
  return

def lastfmAutocorrect(artist):
  urlfile = urllib2.urlopen("http://ws.audioscrobbler.com/2.0/?method=artist.getcorrection&artist=%s&api_key=391b912ffaff32d1a99c9187708191cd&format=json" %(re.sub(" ","%20",artist)))
  try:
    if json.loads(urlfile.read())["error"] == 6: 
      print "Invalid artist name '%s' removed" %artist
      return False
  except:
    True
  try:
    correction = json.loads(urlfile.read())["corrections"]["correction"]["artist"]["name"]
    print "Arist name '%s' corrected to '%s'" %(artist,correction)
    return correction
  except:
    return artist

def discographyTorrentSearch(artist):
  if not artist: return False
  torrentfiles = []
  urlfile = urllib2.urlopen("http://isohunt.com/js/json.php?ihq=%s&rows=1&sort=seeds" %(re.sub(" ","%20",artist) + "%%20discography"))
  try:
    if not re.search("%s(?i)" %artist, urlfile.read()["items"]["list"][0]["title"]):
      raise
    torrentfiles.append(json.loads(urlfile.read())["items"]["list"][0]["enclosure_url"])
    print "Found discography torrent for artist '%s'" %artist
  except:
    print "Discography for artist '%s' not found, trying albums" %artist
    torrentfiles = albumTorrentSearch(artist)
  return torrentfiles

def albumTorrentSearch(artist):
  torrentfiles = []
  albums = getLastfmAlbums(artist)
  if not albums: return torrentfiles
  for album in albums:
    urlfile = urllib2.urlopen("http://isohunt.com/js/json.php?ihq=%s&rows=1&sort=seeds" %(re.sub(" ","%20",artist) + "%%20" + re.sub(" ","%20",album)))
    try:
      if not re.search("%s(?i)" %artist, urlfile.read()["items"]["list"][0]["title"]):
        raise
      torrentfiles.append(json.loads(urlfile.read())["items"]["list"][0]["enclosure_url"])
      print "    Found album torrent for '%s - %s'" %(artist,album)
    except:
      True
  return torrentfiles

def getLastfmAlbums(artist):
  albums = []
  urlfile = urllib2.urlopen("http://ws.audioscrobbler.com/2.0/?method=artist.gettopalbums&artist=%s&api_key=391b912ffaff32d1a99c9187708191cd&limit=10&autocorrect=1&format=json" %re.sub(" ","%20",artist))
  
  try:
    jsondata = json.loads(urlfile.read())["topalbums"]["album"]
  except:
    print "  No albums found for artist '%s' on last.fm" %artist
    return False
  
  maxplaycount = 0
  for album in jsondata:
    if int(album["playcount"]) > maxplaycount: maxplaycount = int(album["playcount"])
    
  for album in jsondata:
    if int(album["playcount"]) > int(maxplaycount)/10:
      albums.append(album["name"]) 
  
  if len(albums) == 1:
    print "  Found %s album for %s on last.fm" %(len(albums),re.sub("%20"," ",artist))
  else:
    print "  Found %s albums for %s on last.fm" %(len(albums),re.sub("%20"," ",artist))
  return albums

def getTorrentFiles(files,dest):
  for link in files:
    print "Downloading %s" %link
    urllib.urlretrieve(link, "%s%s" %(dest, re.sub("\+"," ",re.sub("%25\+"," ",link[link.rfind("/")+1:])))) 

def getFBID():
  grouplist = []
  for group in fbconsole.get('/me/groups')["data"]:
    grouplist.append((group["name"],group["id"]))
  print "Please choose the Facebook group you wish to get music from:\n"
  for i in range(len(grouplist)):
    print str(i + 1) + " - " + grouplist[i][0]
  print "\nEnter the number of the group: "

  ID = grouplist[int(raw_input()) - 1][1]
  return ID

def main():
  from config import *
  fbconsole.AUTH_SCOPE = ['user_groups','user_likes','friends_likes']
  fbconsole.APP_ID = FB_API_ID 
  fbconsole.authenticate() # Logs in to Facebook, opening a webpage requesting permissions from the user.
  FB_GROUP_ID = getFBID() 
  
  
  
  print "\n(Stage 1/6) - Loading list of artists already downloaded\n"
  priorfile = open("prior.txt", "r+")
  prior = readPriorFile(priorfile)
  priorfile.close()
  
  print "\n(Stage 2/6) - Getting list of Facebook users\n"
  members = [user['id'] for user in fbconsole.get('/%s/members' %(FB_GROUP_ID))['data']]
  print "Successfully retrieved list of Facebook users"
  
  if len(members) == 1:
    print "\n(Stage 3/6) - Getting list of artists liked by %s Facebook user\n" %len(members)
  else:
    print "\n(Stage 3/6) - Getting list of artists liked by %s Facebook users\n" %len(members)
  newartists = buildArtistList(members,prior)
  torrentfiles = []
  
  if len(newartists) == 1:
    print "\n(Stage 4/6) - Getting links of torrent files for %s artist\n" %len(newartists)
  else:
    print "\n(Stage 4/6) - Getting links of torrent files for %s artists\n" %len(newartists)
  for artist in newartists:
    try:
      for torrent in discographyTorrentSearch(strip_accents(lastfmAutocorrect(artist))):
        torrentfiles.append(torrent)
    except TypeError:
      True
  
  if len(torrentfiles) == 1: 
    print "\n(Stage 5/6) - Downloading %s torrent file\n" %len(torrentfiles)
  else:
    print "\n(Stage 5/6) - Downloading %s torrent files\n" %len(torrentfiles)
  getTorrentFiles(torrentfiles,torrentpath)
  
  if len(torrentfiles) > 0:
    print "The downloaded torrent files were placed in %s" %torrentpath
  
  print "\n(Stage 6/6) - Saving list of artists already downloaded\n"
  priorfile = open("prior.txt", "w")
  writePriorFile(priorfile,prior,newartists)
  
if __name__ == "__main__":
  main()