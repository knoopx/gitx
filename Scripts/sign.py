#!/usr/bin/env python
 
# Original work by Rowan James at https://gist.github.com/rowanj/5475988
# This is free and unencumbered software released into the public domain.
# http://unlicense.org

import argparse
import subprocess
import os
import glob
import stat

class CodeSignError(RuntimeError):
    pass

def sign(target, key, verbose=0, deep=False):
    print('Signing ' + os.path.basename(target))
    codesign = ['codesign', '--force', '--verify']
    if verbose:
        for i in range(verbose):
            codesign.append('--verbose')
    codesign = codesign + ['--sign', key]
    ret = subprocess.call(codesign + [target])
    if ret != 0:
        raise CodeSignError

def sign_bins_in_app(path, key, verbose=0):
    subdir = os.path.join(path, 'Contents/MacOS')
    main_bin = None
    for binary in glob.glob(subdir + '/*'):
        if os.access(binary, os.X_OK):
            # Signing must occur in hierarchical order.
            # FIXME: Read the Info.plist instead of guessing the main binary's name.
            if os.path.basename(binary) + '.app' == os.path.basename(path):
                main_bin = binary
            else:
                sign(binary, key, verbose=verbose)
    if main_bin is not None:
        sign(main_bin, key, verbose=verbose)

def sign_apps_in_framework(path, key, verbose=0):
    subdir = os.path.join(path, 'Versions/Current/Resources')
    for app in glob.glob(subdir + '/*.app'):
        sign_bins_in_app(app, key, verbose=verbose)
        sign(app, key, verbose=verbose)

def sign_frameworks_in_app(app_path, key, verbose=0):
    frameworkDir = os.path.join(app_path, 'Contents/Frameworks')
    for framework in glob.glob(frameworkDir + '/*.framework'):
        sign_apps_in_framework(framework, key, verbose)
        sign(framework, key, verbose=verbose)

def sign_resources_in_app(app_path, key, verbose=0):
    executableFlags = stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    resourcesDir = os.path.join(app_path, 'Contents/Resources')
    for filename in os.listdir(resourcesDir):
        filename = os.path.join(resourcesDir, filename)
        if os.path.isfile(filename):
            st = os.stat(filename)
            mode = st.st_mode
            if mode & executableFlags:
                sign(filename, key, verbose)

def sign_everything_in_app(app_path, key, verbose=0):
    sign_frameworks_in_app(app_path, key, verbose=verbose)
    sign_resources_in_app(app_path, key, verbose=verbose)
    sign(app_path, key, verbose=verbose)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sign an app and all frameworks therein')
    parser.add_argument('--app', required=True, help='the app bundle to sign')
    parser.add_argument('--key', help='the key ID to sign with', default='Developer ID Application')
    parser.add_argument('--frameworks','-f', help='sign embedded frameworks', action='store_const',const=True)
    parser.add_argument('--resources','-r', help='sign embedded executable resources', action='store_const',const=True)
    parser.add_argument('--verbose','-v', help='show details of signing process', action='count')

    args = parser.parse_args()
    verbose = args.verbose
    if verbose:
        print('Signing configuration:')
        print('APP = ' + args.app)
        print('ID = ' + args.key)
        print('FRAMEWORKS = %r' % (args.frameworks))
        print('RESOURCES = %r' % (args.resources))
        print('VERBOSE = %r' % (args.verbose))
        
    sign_everything_in_app(args.app, args.key, verbose=verbose)

