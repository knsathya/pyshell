# -*- coding: utf-8 -*-
#
# pyshell & gitshell library
#
# Copyright (C) 2018 Sathya Kuppuswamy
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# @Author  : Sathya Kupppuswamy(sathyaosid@gmail.com)
# @History :
#            @v0.0 - Initial update
# @TODO    :
#
#

import os
import logging
from subprocess import Popen, PIPE
from threading import Thread
from builtins import str
import sys

is_py2 = sys.version[0] == '2'

if is_py2:
    from Queue import Queue, Empty
else:
    from queue import Queue, Empty

GIT_COMMAND_PATH='/usr/bin/git'

class PyShell(object):
    def __init__(self, wd=os.getcwd(), stream_stdout=False, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.wd = wd
        self.stream_stdout = stream_stdout
        self.curr_cmd = None
        self.cmd_out = ''
        self.cmd_err = ''
        self.cmd_ret = 0
        self.dry_run = False

    def dryrun(self, status=False):
        self.dry_run = status

    def _cmd(self, args=[], wd=None, out_log=False, dry_run=False, shell=False):
        output = list()
        error = list()
        wd = wd if wd is not None else self.wd

        self.logger.debug(args)
        self.logger.debug('wd=%s, out_log=%s, dry_run=%s, shell=%s' % (wd, out_log, dry_run, shell))
        self.logger.info("Executing " + ' '.join(list(args)))

        if len(args) < 0:
            return -1, '', 'Argument invalid error'

        if dry_run or self.dry_run:
            return 0, '', ''

        self.curr_cmd = args
        self.wd = wd

        io_q = Queue()
        var_q = Queue()

        def stream_watcher(identifier, stream):
            for line in stream:
                io_q.put((identifier, line))
                var_q.put((identifier, line))

            if not stream.closed:
                stream.close()

        process = Popen(list(args), stdout=PIPE, stderr=PIPE, cwd=wd, shell=shell)

        def printer():
            while True:
                try:
                    # Block for 1 second.
                    item = io_q.get(True, 1)
                except Empty:
                    # No output in either streams for a second. Are we done?
                    if process.poll() is not None:
                        break
                else:
                    identifier, line = item
                    print(identifier + ':', line)
                    if out_log is True:
                        self.logger.info(identifier + ': ' + line)

        def parse_output():
            while True:
                try:
                    # Block for 1 second.
                    item = var_q.get(False)
                except Empty:
                    # No output in either streams for a second. Are we done?
                    if process.poll() is not None:
                        break
                else:
                    identifier, line = item

                    if identifier == "STDERR":
                        error.append(line)
                    elif identifier == "STDOUT":
                        output.append(line)

        if self.stream_stdout is True:
            Thread(target=stream_watcher, name='stdout-watcher', args=('STDOUT', process.stdout)).start()
            Thread(target=stream_watcher, name='stderr-watcher', args=('STDERR', process.stderr)).start()
            Thread(target=printer, name='printer').start()
            parse_output()
        else:
            _output, _error = process.communicate()
            output = [_output]
            error = [_error]

            if len(_output) > 0 and out_log is True:
                self.logger.debug("STDOUT: " + _output)
            if len(_error) > 0 and out_log is True:
                self.logger.error("STDERR: " + _error)
        if is_py2:
            self.cmd_out = ''.join(output)
            self.cmd_err = ''.join(error)
        else:
            self.cmd_out = b" ".join(output)
            self.cmd_err = b" ".join(error)
        self.cmd_ret = process.returncode

        return self.cmd_ret, self.cmd_out, self.cmd_err

    def cmd(self, *args, **kwargs):
        return self._cmd(args=list(args), wd=kwargs.get('wd', self.wd),
                         out_log=kwargs.get('out_log', False),
                         dry_run=kwargs.get('dry_run', False),
                         shell=kwargs.get('shell', False))


fmt_bname = lambda x: x.strip('*').strip() if x is not None and len(x) > 0 else x
fmt_name = lambda x: x.strip() if x is not None and len(x) > 0 else x

class GitShell(PyShell):
    def __init__(self, wd=os.getcwd(), init=False, remote_list=[], fetch_all=False, stream_stdout=False, logger=None):
        super(GitShell, self).__init__(wd=wd, stream_stdout=stream_stdout, logger = logger)
        #self.logger.info('git init=%s, remote_list=%s, fetch_all=%s' % (init, remote_list, fetch_all))
        self.init()
        for remote in remote_list:
            if len(remote) > 0:
                self.add_remote(remote[0], remote[1])
            if fetch_all:
                self.cmd("fetch %s" % remote[0])

    def cmd(self, *args, **kwargs):
        kwargs.pop('shell', None)
        return super(GitShell, self).cmd(GIT_COMMAND_PATH + ' ' + ' '.join(list(args)), shell=True, **kwargs)

    def valid(self,  **kwargs):
        return True if os.path.exists(os.path.join(kwargs.get('wd', self.wd), '.git')) else False

    def _valid_str(self, strlist=[], lencheck=False):
        for entry in strlist:
            if is_py2:
                if entry is None or not isinstance(entry, basestring) or (lencheck and (len(entry) == 0)):
                    return False
            else:
                if entry is None or not isinstance(entry, str) or (lencheck and (len(entry) == 0)):
                    return False

        return True

    def init(self, **kwargs):
        if not self.valid(**kwargs):
            self.cmd('init', '.', **kwargs)

        return True, '', ''

    def valid_branch(self, remote=None, branch='HEAD', **kwargs):
        if branch is None or len(branch) == 0:
            return False

        branch = fmt_bname(branch)

        if remote is not None and len(remote) > 0:
            remote = remote.strip('*').strip()
            branch = remote + '/' + branch
            return (self.cmd("branch -r --list %s" % branch)[1].strip('*').strip() == branch)

        return (fmt_bname(self.cmd("branch --list %s" % branch)[1]) == branch)

    def delete(self, branch, remote=None, force=False):
        branch = fmt_bname(branch)
        remote = fmt_bname(remote)

        # First check whether this is a valid local branch
        if self.valid_branch(branch=branch):
            if self.current_branch() == branch:
                headsha =  self.head_sha()
                self.cmd("checkout %s~1" % headsha)
            if force is True:
                ret = self.cmd("branch -D %s" % branch)
                if ret[0] != 0:
                    return ret
            else:
                ret =  self.cmd("branch -d %s" % branch)
                if ret[0] != 0:
                    return ret

        if self.valid_branch(remote, branch):
            return self.cmd("push %s --delete %s" % (remote, branch))

        return False, '', 'Invalid arguments'


    def checkout(self, remote=None, branch=None):
        branch = branch if remote is None else remote + '/' + branch
        return (self.cmd("checkout %s" % branch)[0] == 0)

    def inprogress(self, **kwargs):
        for pfile in ['MERGE_HEAD', 'REBASE_HEAD', 'rebase-apply']:
            if os.path.exists(os.path.join(kwargs.get('wd', self.wd), '.git', pfile)):
                return True

        if len(self.cmd('rerere diff')[1].strip()) > 0:
            return True

        return False

    def merge(self, lbranch=None, remote=None, rbranch=None, no_ff=False, add_log=False, abort=False, **kwargs):

        options = []
        ret = (0, '', '')

        if no_ff:
            options.append('--no-ff')
        if add_log:
            options.append('--log')

        if abort is True:
            return self.cmd('merge', '--abort', **kwargs)
        else:
            if self.valid_branch(branch=lbranch):
                self.cmd("checkout", lbranch)
            else:
                return -1, '', 'Invalid branch %s' % lbranch

            if not self.valid_branch(remote, rbranch):
                return -1, '', 'Invalid branch %s' % rbranch

            if remote is not None and len(remote) > 0:
                ret = self.cmd('pull', ' '.join(options), rbranch, **kwargs)
            else:
                ret = self.cmd('merge', ' '.join(options), rbranch, **kwargs)

        return ret

    def add_remote(self, name, url, override=False, **kwargs):

        if not self._valid_str([name, url], True):
            return False, '', 'Invalid remote %s' % [name, url]

        name = fmt_name(name)
        url = fmt_name(url)

        old_url = self.cmd('remote', 'get-url', name)[1].strip()

        if override is True or (old_url != url):
            self.cmd('remote', 'remove', name, **kwargs)
            self.cmd('remote', 'add', name, url, **kwargs)

        return True, '', ''

    def push(self, lbranch, remote, rbranch, force=False, use_refs=False, **kwargs):
        if not self._valid_str([lbranch, remote, rbranch], True):
                return False, '', 'Invalid arguments %s' % [lbranch, remote, rbranch]

        # Make sure its not /n terminated.
        lbranch = lbranch.strip()
        remote =  remote.strip()
        rbranch = rbranch.strip()

        if use_refs is True:
            rbranch = 'refs/for/' + rbranch

        if not self.valid_branch(remote, rbranch):
            force = True
        
        if force is True:
            return self.cmd('push','-f', remote, lbranch + ':' + rbranch, ** kwargs)
        else:
            return self.cmd('push', remote, lbranch + ':' + rbranch, **kwargs)

    def current_branch(self, **kwargs):
        cmd_str = "branch | awk -v FS=' ' '/\*/{print $NF}' | sed 's|[()]||g'"
        return self.cmd(cmd_str, shell=True, **kwargs)[1].strip()

    def get_sha(self, commit='HEAD', shalen=12, index="head", **kwargs):

        if index not in ["head", "tail"]:
            index = "head"

        cmd_str = "log %s --oneline --abbrev=%d | %s -1 | cut -d' ' -f1" % (commit, shalen, index)

        ret, out, err = self.cmd(cmd_str, shell=True, **kwargs)
        if ret != 0:
            return None

        return out.strip()

    def base_sha(self, **kwargs):
        return self.get_sha(index="tail", **kwargs)

    def head_sha(self, **kwargs):
        return self.get_sha(**kwargs)
