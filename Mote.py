import sublime, sublime_plugin

import subprocess
import os, time
import threading
import json
import posixpath
import time
import shutil
from collections import deque

MOTES = {}

def main():
    with open('servers.json') as f:
        MOTES = json.load(f)
    for server in MOTES:
        MOTES[server]['thread'] = MoteSearchThread(server,
            connection_string=MOTES[server]['connection_string'],
            idle_recursive = MOTES[server]['idle_recursive']
            )
    
    root = os.path.join(sublime.packages_path(),'Mote','temp')
    if os.path.exists(root):
        shutil.rmtree(root)

    return MOTES

def show_commands(window):
    commands = []

    for server in MOTES:
        if MOTES[server]['thread'].sftp == None:
            commands.append({
                "caption": "Mote: Connect - %s" % server,
                "command": "mote_view","args":
                {
                    "server": server
                }
            })
        else:
            commands.append({
                "caption": "Mote: View - %s" % server,
                "command": "mote_view","args":
                {
                    "server": server
                }
            })
            commands.append({
                "caption": "Mote: Disconnect - %s" % server,
                "command": "mote_disconnect","args":
                {
                    "server": server
                }
            })
    
    #commands.append({
    #    "caption": "Mote: Status",
    #    "command": "mote_status"
    #})

    def show_quick_panel():
        window.show_quick_panel([ x['caption'] for x in commands ], on_select)
    
    def on_select(picked):
        if picked == -1:
            return
        
        window.run_command(commands[picked]['command'], commands[picked]['args'])
        
        #print commands[picked]


    sublime.set_timeout(show_quick_panel, 10)


# External Commands
class MoteCommand(sublime_plugin.WindowCommand):
    def run(self):
        show_commands(self.window)


# Internal Commands
class MoteViewCommand(sublime_plugin.WindowCommand):
    def run(self, server):
        MOTES[server]['thread'].window = self.window
        if MOTES[server]['thread'].sftp == None:
            MOTES[server]['thread'].start()
        else:
            MOTES[server]['thread'].showfilepanel()


class MoteStatusCommand(sublime_plugin.WindowCommand):
    def run(self):
        for server in MOTES:
            print MOTES[server]
            print MOTES[server]['thread'].is_alive()
            print MOTES[server]['thread'].name
            print MOTES[server]['thread'].sftp
            print MOTES[server]['thread'].results

class MoteDisconnectCommand(sublime_plugin.WindowCommand):
    def run(self, server=''):
        MOTES[server]['thread'].add_command('exit','')


# Listeners

class MoteUploadOnSave(sublime_plugin.EventListener):
    def on_post_save(self, view):
        root = os.path.join(sublime.packages_path(),'Mote','temp')
        relpath = os.path.relpath(view.file_name(),root)
        #print relpath
        if relpath[0:2] != '..':
            server = relpath.split(os.sep)[0]
            server_path = posixpath.join(*relpath.split(os.sep)[1:])
            MOTES[server]['thread'].add_command('save',server_path)

        

class MoteSearchThread(threading.Thread):
    def __init__(self, server, search_path='', connection_string='', idle_recursive=False):
        self.server = server
        self.search_path = search_path
        self.connection_string = connection_string
        self.idle_recursive = idle_recursive
        
        
        self.results = {}
        self.sftp = None

        self.results_lock = threading.Condition()
        self.command_deque = deque()

        self.add_command('ls','', True)

        threading.Thread.__init__(self)

    def connect(self):
        if not self.sftp:
            self.sftp = psftp(self.connection_string)
            self.sftp.next()
        return self
    
    def disconnect(self):
        self.add_command('exit','')
        return self
    
    def add_command(self, command, path, show=False):
        self.results_lock.acquire()
        self.results_lock.notify()
        if show:
            self.show_panel_after = True
        self.command_deque.append((command,path))
        self.results_lock.release()
    
    def get_front_command(self):
        
        if len(self.command_deque) > 0:
            return self.command_deque.pop()
        else:
            return (None,None)
        

    def run(self):
        sublime.set_timeout(lambda:sublime.status_message('Connecting to %s' % self.server),0)
        self.connect()
        while True:
            
            
            
            self.results_lock.acquire()
            if len(self.command_deque) == 0:
                self.results_lock.wait()
            show_panel = self.show_panel_after
            if show_panel == True:
                self.show_panel_after = False
            command, path = self.get_front_command()
            self.results_lock.release()

            #print command, path, show_panel

            if command == 'ls':
                if show_panel == True:
                    sublime.set_timeout(lambda:sublime.status_message('Opening %s' % path),0)
                self.ls(path)
                if show_panel == True:
                    self.showfilepanel()
                    sublime.set_timeout(lambda:sublime.status_message('Finished opening %s' % path),0)
            elif command == 'open':
                sublime.set_timeout(lambda:sublime.status_message('Downloading %s' % path),0)
                self.download(path)
                sublime.set_timeout(lambda:sublime.status_message('Finished downloading %s' % path),0)
            elif command == 'save':
                sublime.set_timeout(lambda:sublime.status_message('Uploading %s' % path),0)
                self.upload(path)
                sublime.set_timeout(lambda:sublime.status_message('Finished uploading %s' % path),0)
            elif command == 'exit':
                break
            else:
                pass
            
            
        sublime.set_timeout(lambda:sublime.status_message('Disconnectin from %s' % self.server),0)
        try:
            self.sftp.send('exit')
        except StopIteration:
            pass
        self.sftp = None
        
        threading.Thread.__init__(self)
    
    def ls(self, search_path = ''):
        fullpath = cleanpath(self.search_path,search_path)

        results = self.cleanls(fullpath, self.sftp.send('ls "%s"' % fullpath))

        if self.idle_recursive:
            subfolders = dict((k,v) for k,v in results.items() if v['type'] == 'folder')
            for recur_folder in subfolders:
                self.add_command('ls',results[recur_folder]['path'])

        #print results
        self.results.update(results)
    
    def download(self, path):
        localpath = os.path.normpath(os.path.join(sublime.packages_path(),'Mote','temp',self.server,path))

        if not os.path.exists(os.path.dirname(localpath)):
            os.makedirs(os.path.dirname(localpath))

        self.sftp.send('get "%s" "%s"' % (path,localpath) )

        sublime.set_timeout(lambda:self.window.open_file(localpath), 0)
        

        pass
    
    def upload(self, path):
        localpath = os.path.normpath(os.path.join(sublime.packages_path(),'Mote','temp',self.server,path))
        self.sftp.send('put "%s" "%s"' % (localpath,path) )
    
    def showfilepanel(self):
        self.keys = sorted(self.results.keys())
        def show_quick_panel():
            self.window.show_quick_panel(self.keys, self.on_select)
        sublime.set_timeout(show_quick_panel, 10)

    def cleanls(self,fullpath, out):
        paths = {}
        for path in out.split('\n')[2:-1]:
            raw_path = path[55:-1].strip()
            if raw_path[0] == '.':
                continue

            named_path = cleanpath(fullpath,raw_path)
            path_key = named_path + ('' if path[0] == '-' else '/..')
            
            #print named_path
            paths[path_key] = {}
            paths[path_key]['path'] = named_path
            paths[path_key]['type'] = 'file' if path[0] == '-' else 'folder'
        #print paths
        return paths

    def on_select(self, picked):
        if picked == -1:
            return
        if not self.results:
            return
        
        key = self.keys[picked]

        #print self.results[key]

        if self.results[key]['type'] == 'folder':
            self.add_command('ls',self.results[key]['path'], True)
        elif self.results[key]['type'] == 'file':
            self.add_command('open',self.results[key]['path'])
            
        else:
            pass


def cleanpath(*args):
    return posixpath.normpath(posixpath.join(*args))

def psftp(connection_string):
    command = ''
    p = subprocess.Popen(r'psftp ' + connection_string, shell=True, bufsize=1024, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)  
    while True:
        command = (yield untilprompt(p,command))
        #print command
        if command == 'exit':
            untilprompt(p,'exit')
            return
        

def untilprompt(proc, strinput = None):
    if strinput:
        proc.stdin.write(strinput+'\n')
        proc.stdin.flush()
    buff = ''
    while proc.poll() == None:
        
        output = proc.stdout.read(1)
        buff += output

        #print buff[-7:-1]
        if buff[-7:-1] == 'psftp>':
            break
    #print buff
    return buff

MOTES = main()