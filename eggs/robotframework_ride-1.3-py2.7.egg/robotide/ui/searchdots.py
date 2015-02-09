#  Copyright 2008-2012 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import wx


class DottedSearch(object):
    """Class that can be used to make Search dots...

    parent - the UI component that the timer should be bound to

    callback - function that will receive timer events in UI thread
               argument to callback is string containing dots '.', '..'. '...' etc.

    """

    def __init__(self, parent, callback):
        self._timer = wx.Timer(parent)
        self._dots = 0
        self._callback = callback
        parent.Bind(wx.EVT_TIMER, self._timer_event)

    def _timer_event(self, event):
        self._dots = (self._dots + 1) % 5
        self._callback('.'*self._dots)

    def start(self):
        self._timer.Start(500)

    def stop(self):
        self._timer.Stop()
