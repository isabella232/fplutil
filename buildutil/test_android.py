# Copyright 2014 Google Inc. All Rights Reserved.
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the authors be held liable for any damages
# arising from the use of this software.
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
# 1. The origin of this software must not be misrepresented; you must not
# claim that you wrote the original software. If you use this software
# in a product, an acknowledgment in the product documentation would be
# appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
# misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.
#

import argparse
import os
import sys
import unittest
sys.path.append('..')
import buildutil.android as android
import buildutil.common as common
import buildutil.linux as linux


class FileMock(object):

  def __init__(self, string):
    self.string = string

  def close(self):
    pass

  def read(self, nbytes):
    r = self.string[0:nbytes]
    self.string = self.string[nbytes:]
    return r


class RunCommandMock(object):

  def __init__(self, test):
    self.args = None
    self.cwd = None
    self.test = test
    self.stdout = None
    self.stderr = None

  def returns(self, stdout, stderr=None):
    self.stdout = stdout
    self.stderr = stderr

  def expect(self, args, cwd=os.getcwd()):
    self.args = args
    self.cwd = cwd

  def verify(self, args, capture=False, cwd=os.getcwd()):
    self.test.assertEqual(self.cwd, cwd)
    self.test.assertListEqual(self.args, args)
    if capture:
      return (self.stdout, self.stderr)


class AndroidBuildUtilTest(unittest.TestCase):
  """Android-specific unit tests."""

  def test_build_defaults(self):
    d = android.BuildEnvironment.build_defaults()
    # Verify that the android ones are set.
    self.assertIn(android._NDK_HOME, d)
    self.assertIn(android._SDK_HOME, d)
    self.assertIn(android._ANT_PATH, d)
    self.assertIn(android._ANT_FLAGS, d)
    self.assertIn(android._ANT_TARGET, d)
    self.assertIn(android._APK_KEYSTORE, d)
    self.assertIn(android._APK_PASSFILE, d)
    self.assertIn(android._APK_KEYALIAS, d)
    self.assertIn(android._SIGN_APK, d)
    # Verify that a mandatory superclass one gets set.
    self.assertIn(common._PROJECT_DIR, d)
    # Verify that the Linux ones do not get set.
    self.assertNotIn(linux._CMAKE_FLAGS, d)
    self.assertNotIn(linux._CMAKE_PATH, d)

  def test_init(self):
    d = android.BuildEnvironment.build_defaults()
    b = android.BuildEnvironment(d)
    # Verify that the Android ones are set.
    self.assertEqual(b.ndk_home, d[android._NDK_HOME])
    self.assertEqual(b.sdk_home, d[android._SDK_HOME])
    self.assertEqual(b.ant_path, d[android._ANT_PATH])
    self.assertEqual(b.ant_flags, d[android._ANT_FLAGS])
    self.assertEqual(b.ant_target, d[android._ANT_TARGET])
    self.assertEqual(b.apk_keystore, d[android._APK_KEYSTORE])
    self.assertEqual(b.apk_passfile, d[android._APK_PASSFILE])
    self.assertEqual(b.apk_keyalias, d[android._APK_KEYALIAS])
    self.assertEqual(b.sign_apk, d[android._SIGN_APK])
    # Verify that a mandatory superclass one gets set.
    self.assertEqual(b.project_directory, d[common._PROJECT_DIR])
    # Verify that the Linux ones do not get set.
    self.assertNotIn(linux._CMAKE_FLAGS, vars(b))
    self.assertNotIn(linux._CMAKE_PATH, vars(b))

  def test_add_arguments(self):
    p = argparse.ArgumentParser()
    android.BuildEnvironment.add_arguments(p)
    args = ['--' + android._SDK_HOME, 'a',
            '--' + android._NDK_HOME, 'b',
            '--' + android._ANT_PATH, 'c',
            '--' + android._ANT_FLAGS, 'd',
            '--' + android._ANT_TARGET, 'e',
            '--' + android._APK_KEYSTORE, 'f',
            '--' + android._APK_PASSFILE, 'g',
            '--' + android._APK_KEYALIAS, 'h',
            '--' + android._SIGN_APK]
    argobj = p.parse_args(args)
    d = vars(argobj)

    self.assertEqual('a', d[android._SDK_HOME])
    self.assertEqual('b', d[android._NDK_HOME])
    self.assertEqual('c', d[android._ANT_PATH])
    self.assertEqual('d', d[android._ANT_FLAGS])
    self.assertEqual('e', d[android._ANT_TARGET])
    self.assertEqual('f', d[android._APK_KEYSTORE])
    self.assertEqual('g', d[android._APK_PASSFILE])
    self.assertEqual('h', d[android._APK_KEYALIAS])
    self.assertTrue(d[android._SIGN_APK])

    self.assertEqual(os.getcwd(), d[common._PROJECT_DIR])
    # Verify that the Linux ones do not get set.
    self.assertNotIn(linux._CMAKE_FLAGS, d)
    self.assertNotIn(linux._CMAKE_PATH, d)

  def test_construct_android_manifest(self):
    m = android.AndroidManifest(None)
    self.assertEqual(m.min_sdk, 0)
    self.assertEqual(m.target_sdk, 0)
    self.assertIsNone(m.path)

    caught = False
    try:
      android.AndroidManifest('/non existent/bogus_path')
    except common.ConfigurationError:
      caught = True
    finally:
      self.assertTrue(caught)

  def test_manifest_parse_trivial(self):
    f = FileMock('<manifest '
                 'xmlns:android="http://schemas.android.com/apk/res/android">\n'
                 '<uses-sdk android:minSdkVersion="1"/>\n</manifest>')
    m = android.AndroidManifest(None)
    m._parse(f)
    self.assertEqual(m.min_sdk, 1)
    self.assertEqual(m.target_sdk, m.min_sdk)

  def test_manifest_parse_with_target(self):
    f = FileMock(
        '<manifest '
        'xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '<uses-sdk android:minSdkVersion="1" android:targetSdkVersion="2"/>\n'
        '</manifest>')
    m = android.AndroidManifest(None)
    m._parse(f)
    self.assertEqual(m.min_sdk, 1)
    self.assertEqual(m.target_sdk, 2)

  def test_manifest_parse_with_bad_target(self):
    f = FileMock(
        '<manifest '
        'xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '<uses-sdk android:minSdkVersion="1" android:targetSdkVersion="-2"/>\n'
        '</manifest>')
    m = android.AndroidManifest(None)
    m._parse(f)
    self.assertEqual(m.min_sdk, 1)
    # this is an error but we want to catch in processing, not parsing
    self.assertEqual(m.target_sdk, -2)

  def test_manifest_parse_missing_min_version(self):
    f = FileMock('<manifest '
                 'xmlns:android="http://schemas.android.com/apk/res/android">\n'
                 '<uses-sdk/>\n</manifest>')
    m = android.AndroidManifest(None)
    caught = False
    try:
      m._parse(f)
    except common.ConfigurationError:
      caught = True
    finally:
      self.assertTrue(caught)

  def test_manifest_parse_missing_uses_sdk(self):
    f = FileMock('<manifest '
                 'xmlns:android="http://schemas.android.com/apk/res/android">\n'
                 '</manifest>')
    m = android.AndroidManifest(None)
    caught = False
    try:
      m._parse(f)
    except common.ConfigurationError:
      caught = True
    finally:
      self.assertTrue(caught)

  def test_manifest_parse_error(self):
    f = FileMock('<manifest ')
    m = android.AndroidManifest(None)
    caught = False
    try:
      m._parse(f)
    except common.ConfigurationError:
      caught = True
    finally:
      self.assertTrue(caught)

  def test_construct_buildxml(self):
    b = android.BuildXml(None)
    self.assertIsNone(b.path)
    self.assertIsNone(b.project_name)

    caught = False
    try:
      android.BuildXml('/non existent/bogus_path')
    except common.ConfigurationError:
      caught = True
    finally:
      self.assertTrue(caught)

  def test_buildxml_parse_trivial(self):
    f = FileMock('<project name="foo"/>')
    b = android.BuildXml(None)
    b._parse(f)
    self.assertEqual(b.project_name, 'foo')
    self.assertIsNone(b.path)

  def test_buildxml_missing_name(self):
    f = FileMock('<project/>')
    b = android.BuildXml(None)
    caught = False
    try:
      b._parse(f)
    except common.ConfigurationError:
      caught = True
    finally:
      self.assertTrue(caught)

  def test_buildxml_missing_project(self):
    f = FileMock('<not-project name="foo"/>')
    b = android.BuildXml(None)
    caught = False
    try:
      b._parse(f)
    except common.ConfigurationError:
      caught = True
    finally:
      self.assertTrue(caught)

  def test_build_libraries(self):
    d = android.BuildEnvironment.build_defaults()
    b = android.BuildEnvironment(d)
    m = RunCommandMock(self)
    b.run_subprocess = m.verify
    ndk_build = os.path.join(b.ndk_home, 'ndk-build')
    l = 'libfoo'
    lpath = os.path.abspath(os.path.join(b.project_directory, l))
    expect = [ndk_build, '-B', '-j', b.cpu_count, '-C', lpath]
    m.expect(expect)
    b.build_android_libraries([l])
    b.verbose = True
    expect.append('V=1')
    m.expect(expect)
    b.build_android_libraries([l])
    expect.append('NDK_OUT=%s' % lpath)
    m.expect(expect)
    b.build_android_libraries([l], output=l)
    b.make_flags = '-DFOO -DBAR -DBAZ'
    flaglist = ['-DFOO', '-DBAR', '-DBAZ']
    expect += flaglist
    m.expect(expect)
    b.build_android_libraries([l], output=l)
    b.ndk_home = '/dev/null'
    caught = False
    try:
      b.build_android_libraries([l], output=l)
    except common.ToolPathError:
      caught = True
    finally:
      self.assertTrue(caught)

  def test_find_android_sdk(self):
    d = android.BuildEnvironment.build_defaults()
    b = android.BuildEnvironment(d)
    m = RunCommandMock(self)
    b.run_subprocess = m.verify
    expect = ['android', 'list', 'target', '--compact']
    m.expect(expect)
    m.returns('android-3\nandroid-5\nmeaningless\nandroid-10\n')
    got = b._find_best_android_sdk('android', 1, 5)
    self.assertEqual(got, 'android-5')
    got = b._find_best_android_sdk('android', 5, 15)
    self.assertEqual(got, 'android-10')
    got = b._find_best_android_sdk('android', 1, 2)
    self.assertEqual(got, 'android-10')
    caught = False
    try:
      b._find_best_android_sdk('android', 11, 20)
    except common.ConfigurationError:
      caught = True
    finally:
      self.assertTrue(caught)
    m.returns('android-10\nandroid-15\nandroid-7\n')
    got = b._find_best_android_sdk('android', 5, 15)
    self.assertEqual(got, 'android-15')

  # TBD, these are highly dependent high level functions that may need refactor
  # to unit-test well, as they are currently difficult to mock. At the moment
  # the Android examples serve as functional tests for these.
  def test_build_android_apk(self):
    pass

  def test_sign_apk(self):
    pass

if __name__ == '__main__':
  unittest.main()