#!/usr/bin/env python
'''
Created on Dec 14, 2010

@author: Charlie Meyer <cemeyer2@illinois.edu>
'''
import Queue, getpass, optparse, os
import pysvn, shutil, threading

mp_files = {}
mp_files['mp1'] = ['partners.txt', 'Makefile', 'main.cpp']
mp_files['mp2'] = ['partners.txt', 'image.cpp', 'image.h', 'Makefile', 'scene.cpp', 'scene.h']
mp_files['mp3'] = ['partners.txt', 'mp3extras.cpp']
mp_files['mp4'] = ['partners.txt', 'stack.cpp', 'queue.cpp', 'solidColorPicker.cpp', 'solidColorPicker.h', 'gradientColorPicker.cpp', 'gradientColorPicker.h', 'fills.h', 'fills.cpp']
mp_files['mp5'] = ['partners.txt', 'quadtree.cpp', 'quadtree.h']
mp_files['mp6'] = ['partners.txt', 'kdtilemapper.cpp', 'kdtilemapper.h', 'kdtree.cpp', 'kdtree.h']
mp_files['mp7'] = ['partners.txt', 'dsets.cpp', 'dsets.h', 'maze.cpp', 'maze.h']

thread_count = 10

queue = Queue.Queue()

def main():
        global thread_count
        parser = optparse.OptionParser()
        parser.add_option('-r', '--svnroot',
                          dest='svn_root',
                          metavar='URL',
                          help='sets the Subversion repository location')
        parser.add_option('-m', '--mp',
                          dest='mp',
                          metavar='NAME',
                          help='sets the MP name')
        parser.add_option('-d', '--dest',
                          dest='dest_dir',
                          metavar='DIRECTORY',
                          help='sets destination directory to download to')
        parser.add_option('-u', '--user',
                          dest='svn_user',
                          metavar='NETID',
                          help='sets destination directory to download to')
        parser.add_option('-p', '--password',
                          dest='svn_pass',
                          metavar='PASSWORD',
                          help='sets destination directory to download to')
        parser.add_option('-t', '--threads',
                          dest='threads',
                          metavar='THREAD_COUNT',
                          help='sets the number of simultaneous download threads (default 10)')

        (options, args) = parser.parse_args()

        if not options.svn_root:
                parser.error('Subversion root URL not specified')
        if not options.mp:
                parser.error('MP name not specified')
        if not options.dest_dir:
                parser.error('Download directory not specified')
        if not options.svn_user:
                parser.error('Subversion username not specified')
        
        svn_root = options.svn_root
        mp = options.mp
        dest_dir = options.dest_dir
        svn_user = options.svn_user
        svn_pass = ""
        if options.svn_pass:
            svn_pass = options.svn_pass
        else:
            svn_pass = getpass.getpass("SVN Password: ")
        if options.threads:
            thread_count = int(options.threads)
        roster = get_roster(svn_root, svn_user, svn_pass)
        download(dest_dir, roster, svn_root, mp, svn_user, svn_pass)
        
def get_svn_client(svn_user, svn_pass):
    def notify( event_dict ):
        return
    def ssl_server_trust_prompt( trust_dict ):
        return True, 1000, False
    #helper function to login to svn
    def get_login( realm, user, may_save ):
        return True, svn_user, svn_pass, False
    client = pysvn.Client()
    client.exception_style = 1
    client.set_auth_cache(False)
    client.set_store_passwords(False)
    client.set_interactive(False)
    client.callback_get_login = get_login
    client.callback_ssl_server_trust_prompt = ssl_server_trust_prompt
    client.callback_notify = notify
    return client

def get_roster(svn_root, svn_user, svn_pass):
    client = get_svn_client(svn_user, svn_pass)
    try:
        pathsListing = [result[0].repos_path.replace('/', '')
        for result in client.list(svn_root, recurse=False)]
        netids = filter(lambda x: not x.startswith('_') and len(x) > 0,pathsListing)
        return map(lambda s: str(s), netids)
    except pysvn.ClientError, e:
        # print the whole message
        print("ClientError: "+ str(e.args[0]))
        print("Details: "+str(e.args[1]))
        raise e

def download(dest_dir, roster, svn_root, mp, svn_user, svn_pass):
    if not type(dest_dir) == str or not type(roster) == list or not type(svn_root) == str or not type(mp) == str:
        raise AssertionError("Parameters are of the wrong type")
    if not mp_files.has_key(mp):
        raise AssertionError("Invalid mp specified")
    try:
        os.makedirs(dest_dir)
    except:
        #it already exists, so delete it then create it
        shutil.rmtree(dest_dir)
        os.makedirs(dest_dir)
    for netid in roster:
        queue.put(netid)
    threads = []
    for i in range(0, thread_count):
        client = get_svn_client(svn_user, svn_pass)
        th = SVNDownloader(svn_root, mp, dest_dir, client)
        threads.append(th)
        th.start()
    for thread in threads:
        th.join()

class SVNDownloader( threading.Thread ):
    
    def __init__(self, svn_root, mp, dest_dir, client):
        threading.Thread.__init__(self)
        self.svn_root = svn_root
        self.mp = mp
        self.dest_dir = dest_dir
        self.client = client
        
    def run(self):
        files = mp_files[self.mp]
        while True:
            netid = ""
            try:
                netid = queue.get(True, 2)
            except:
                return
            path = os.path.join(self.dest_dir, netid, self.mp)
            os.makedirs(path)
            for file in files:
                svn_dir = self.svn_root+"/"+netid+"/"+self.mp+"/"+file
                dest_path = os.path.join(path, file)
                try:
                    print "Exporting "+svn_dir+" to "+path
                    self.client.export(svn_dir, dest_path, recurse=False)
                except pysvn.ClientError, e:
                    print("Error exporting "+svn_dir+" to "+path+": "+str(e))

if __name__ == '__main__':
    main()