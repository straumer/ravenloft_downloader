#!/usr/bin/python2

from os.path import expanduser, isdir, isfile, join
import sys
import threading
import urllib2
import argparse
from lxml import etree

#Usage: rldl.py -bgmps /path/to/nwn/directory

description = '''A program to download mandatory and optional files for
Ravenloft POTM, a NWN persistent world.'''
parser = argparse.ArgumentParser(description=description)

parser.add_argument('-p', '--portrait-files', help='Download missing portraits.',
                    action='store_true', dest='portraits')
parser.add_argument('-m', '--music-files', help='Download missing music files.',
                    action='store_true', dest='music')
parser.add_argument('-g', '--gui-files', help='Download missing gui files.',
                    action='store_true', dest='gui')
parser.add_argument('-s', '--sky-files', help='Download missing skybox files.',
                    action='store_true', dest='sky')
parser.add_argument('-b', '--base-files', help='Download missing basefiles.',
                    action='store_true', dest='base')
parser.add_argument('path', help='Path to NWN directory, e.g. ~/games/nwn.')

args = parser.parse_args()
nwn_path = expanduser(args.path)

if(not isdir(nwn_path)):
    sys.exit('Error: Directory in path does not exist.')

#From here on, arguments are all valid.

lock = threading.Lock()

def download_files(local_path, web_path, file_list):
    '''
    Use: download_files(l, w, f)
    Pre: l is a valid local path and w is a valid url. f is a list of
         paths legal from within w and within f except the file name at
         the end of it needn't exist.
    Post: A thread downloads files f from w to path l until none are left in f,
          or spawning program terminates.
    '''

    while(file_list):
        lock.acquire()
        file_path = file_list.pop()
        current_path = join(web_path, file_path)
        print('Downloading... ' + file_path)
        lock.release()
        web_file = urllib2.urlopen(join(web_path, file_path))
        local_file = open(join(local_path, file_path), 'wb')
        local_file.write(web_file.read())
        web_file.close()
        local_file.close()

if __name__ == '__main__':
    
    #Retrieve xml file and read in tree.
    rldl_path = 'http://files.markjohansen.dk/nwn/ravenloft_downloader/'
    pack_list = urllib2.urlopen(join(rldl_path, 'packages.xml'))
    pack_tree = etree.parse(pack_list, etree.XMLParser()).getroot()
    
    #Mark selected packages for inspection.
    pack_selection = []
    arg_list = [args.base, args.gui, args.music, args.portraits, args.sky]
    for i, arg in enumerate(arg_list):
        if(arg):
            pack_selection.append(pack_tree[i])
            #print('Will add ' + pack_tree[i].get('name'))
    
    #Mark files for download.
    file_selection = []
    for pack in pack_selection:
        for elem in pack:
            file_path = elem.get('name').replace('\\', '/')
            if(not isfile(join(nwn_path, file_path))):
                file_selection.append(file_path)

    #Download marked files.
    thread_num = 10
    threads = []
    for t in range(thread_num):
        threads.append(threading.Thread(target=download_files, args=(nwn_path, rldl_path, file_selection)))
    for t in threads:
        t.daemon = True
        t.start()
    for t in threads:
        t.join()

    print('Download finished.')
