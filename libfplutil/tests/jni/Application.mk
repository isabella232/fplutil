# Copyright (c) 2014 Google, Inc.
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
APP_PLATFORM:=android-9
APP_ABI:=armeabi-v7a
# Library uses STLPort so verify gnustl compatibility here.
APP_STL:=gnustl_static
APP_MODULES:=FPLUtilTests
# GOOGLETEST_PATH="<relpath to googletest>" required to be passed to ndk-build.
NDK_MODULE_PATH:=$(abspath $(NDK_PROJECT_PATH)/../..):$(NDK_ROOT)/sources/android:$(GOOGLETEST_PATH)