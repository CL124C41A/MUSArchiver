#!/usr/bin/env python3

'''
MUSArchiver (MUSic Archiver)

 - extracts toc and tracks from an audio cd for storage purposes
 - applies the metadata from the toc to track and album names
 - it's written to be read, understood and modified
 - converts the tracks to a playable wav format
 - fails gracefully and resumes nicely

by Claudio Venanzi, 2020
'''

import os, sys, shutil

#==============================================================================

class Album:

    def __init__(self):

        # initialize instance variables

        self.title     = 'unknown'
        self.performer = 'unknown'
        self.tracks    = []

        # split the toc into the header and track sections, look at
        # the generated disk.toc file to understand its structure

        with open('disk.toc', 'r') as file:
            meta, *tracks = file.read().split('// Track ')

        # extract title and performer informations (if present) from the header

        for line in meta.splitlines():
            if 'TITLE'     in line: self.title     = line.split('"')[1]
            if 'PERFORMER' in line: self.performer = line.split('"')[1]

        # instance a Track object for each track in the toc
        # and add it to the album's track list

        for track in tracks: self.tracks.append(Track(track))

    def __str__(self):
        return ' - '.join([self.performer, self.title])

#==============================================================================

class Track:

    def __init__(self, track):

        # separate the ordinal number of the track
        # from the rest of the track text

        ordinal, *lines = track.splitlines()

        # initialize the instance variable; the ordinal is adjusted
        # to a two character string for numbers less than 10

        self.ordinal = ('0' if int(ordinal) < 10 else '') + ordinal
        self.title = 'unknown'

        # extract title informations (if present) from the text

        for line in lines:
            if 'TITLE' in line: self.title = line.split('"')[1]

    def __str__(self):
        return ' '.join([self.ordinal, self.title])

#==============================================================================

# check for system utilities availability
# the utilities and relative options are hardwired into the code for simplicity

for utility in ['cdrdao', 'toc2cue', 'bchunk', 'sox']:
    if not shutil.which(utility):
        sys.exit(utility + ' not found')

# setup the working directory and enter it

os.mkdir('wip') if not os.path.exists('wip') else ()
os.chdir('wip')

# extract the disk data only if a toc file is not present
# if a toc file is found, the bin file is considered good

# extraction failure will cause the program to exit,
# restart the program to make another attempt

if not os.path.exists('disk.toc'):
    if os.system('cdrdao read-cd --read-raw --datafile disk.bin disk.toc'):
        sys.exit('extraction failed')

# convert the raw data from the bin file to track files (one per track)

os.system('toc2cue disk.toc disk.cue')
os.system('bchunk disk.bin disk.cue ""')

# create an instance of Album; its initialization code
# will extract all the relevant metadata from the toc file

album = Album()

# for each track in the album's track list, convert the relative cdr file
# to wav and rename it accordingly to the stored toc data; then remove
# the starting cdr -- it's not useful anymore

for track in album.tracks:
    cdr = track.ordinal + '.cdr'
    os.system('sox ' + cdr + ' "' + str(track) + '.wav"')
    os.remove(cdr)

# go up one level in the filesystem and rename the work directory
# with the album's title and artist stored in the toc

os.chdir(os.pardir)
os.rename('wip', str(album))
