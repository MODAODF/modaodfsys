#!/usr/bin/env python3

# == Rapid Develop Macros in LibreOffice ==

# ~ This file is part of ZAZ.

# ~ ZAZ is free software: you can redistribute it and/or modify
# ~ it under the terms of the GNU General Public License as published by
# ~ the Free Software Foundation, either version 3 of the License, or
# ~ (at your option) any later version.

# ~ ZAZ is distributed in the hope that it will be useful,
# ~ but WITHOUT ANY WARRANTY; without even the implied warranty of
# ~ MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# ~ GNU General Public License for more details.

# ~ You should have received a copy of the GNU General Public License
# ~ along with ZAZ.  If not, see <https://www.gnu.org/licenses/>.

import base64
import csv
import ctypes
import datetime
import errno
import gettext
import getpass
import hashlib
import json
import logging
import os
import platform
import re
import shlex
import shutil
import socket
import subprocess
import ssl
import sys
import tempfile
import threading
import time
import traceback
import zipfile

from functools import wraps
from pathlib import Path, PurePath
from pprint import pprint
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from string import Template
from subprocess import PIPE

import smtplib
from smtplib import SMTPException, SMTPAuthenticationError
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
import mailbox

import uno
import unohelper
from com.sun.star.util import Time, Date, DateTime
from com.sun.star.beans import PropertyValue, NamedValue
from com.sun.star.awt import MessageBoxButtons as MSG_BUTTONS
from com.sun.star.awt.MessageBoxResults import YES
from com.sun.star.awt.PosSize import POSSIZE, SIZE
from com.sun.star.awt import Size, Point
from com.sun.star.awt import Rectangle
from com.sun.star.awt import KeyEvent
from com.sun.star.awt.KeyFunction import QUIT
from com.sun.star.datatransfer import XTransferable, DataFlavor
from com.sun.star.table.CellContentType import EMPTY, VALUE, TEXT, FORMULA

from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER

from com.sun.star.script import ScriptEventDescriptor
from com.sun.star.lang import XEventListener
from com.sun.star.awt import XActionListener
from com.sun.star.awt import XMouseListener
from com.sun.star.awt import XMouseMotionListener
from com.sun.star.util import XModifyListener
from com.sun.star.awt import XTopWindowListener
from com.sun.star.awt import XWindowListener
from com.sun.star.awt import XMenuListener
from com.sun.star.awt import XKeyListener
from com.sun.star.awt import XItemListener
from com.sun.star.awt import XFocusListener
from com.sun.star.awt import XTabListener
from com.sun.star.awt.grid import XGridDataListener
from com.sun.star.awt.grid import XGridSelectionListener


try:
    from fernet import Fernet, InvalidToken
except ImportError:
    pass


ID_EXTENSION = ''

DIR = {
    'images': 'images',
    'locales': 'locales',
}

KEY = {
    'enter': 1280,
}

SEPARATION = 5

MSG_LANG = {
    'es': {
        'OK': 'Aceptar',
        'Cancel': 'Cancelar',
        'Select file': 'Seleccionar archivo',
        'Incorrect user or password': 'Nombre de usuario o contraseña inválidos',
        'Allow less secure apps in GMail': 'Activa: Permitir aplicaciones menos segura en GMail',
    }
}

OS = platform.system()
USER = getpass.getuser()
PC = platform.node()
DESKTOP = os.environ.get('DESKTOP_SESSION', '')
INFO_DEBUG = '{}\n\n{}\n\n{}'.format(sys.version, platform.platform(), '\n'.join(sys.path))

IS_WIN = OS == 'Windows'
LOG_NAME = 'ZAZ'
CLIPBOARD_FORMAT_TEXT = 'text/plain;charset=utf-16'

PYTHON = 'python'
if IS_WIN:
    PYTHON = 'python.exe'
CALC = 'calc'
WRITER = 'writer'

OBJ_CELL = 'ScCellObj'
OBJ_RANGE = 'ScCellRangeObj'
OBJ_RANGES = 'ScCellRangesObj'
OBJ_TYPE_RANGES = (OBJ_CELL, OBJ_RANGE, OBJ_RANGES)

TEXT_RANGE = 'SwXTextRange'
TEXT_RANGES = 'SwXTextRanges'
TEXT_TYPE_RANGES = (TEXT_RANGE, TEXT_RANGES)

TYPE_DOC = {
    'calc': 'com.sun.star.sheet.SpreadsheetDocument',
    'writer': 'com.sun.star.text.TextDocument',
    'impress': 'com.sun.star.presentation.PresentationDocument',
    'draw': 'com.sun.star.drawing.DrawingDocument',
    'base': 'com.sun.star.sdb.DocumentDataSource',
    'math': 'com.sun.star.formula.FormulaProperties',
    'basic': 'com.sun.star.script.BasicIDE',
    'main': 'com.sun.star.frame.StartModule',
}

NODE_MENUBAR = 'private:resource/menubar/menubar'
MENUS_MAIN = {
    'file': '.uno:PickList',
    'tools': '.uno:ToolsMenu',
    'help': '.uno:HelpMenu',
}
MENUS_CALC = {
    'file': '.uno:PickList',
    'edit': '.uno:EditMenu',
    'view': '.uno:ViewMenu',
    'insert': '.uno:InsertMenu',
    'format': '.uno:FormatMenu',
    'styles': '.uno:FormatStylesMenu',
    'sheet': '.uno:SheetMenu',
    'data': '.uno:DataMenu',
    'tools': '.uno:ToolsMenu',
    'windows': '.uno:WindowList',
    'help': '.uno:HelpMenu',
}
MENUS_WRITER = {
    'file': '.uno:PickList',
    'edit': '.uno:EditMenu',
    'view': '.uno:ViewMenu',
    'insert': '.uno:InsertMenu',
    'format': '.uno:FormatMenu',
    'styles': '.uno:FormatStylesMenu',
    'sheet': '.uno:TableMenu',
    'data': '.uno:FormatFormMenu',
    'tools': '.uno:ToolsMenu',
    'windows': '.uno:WindowList',
    'help': '.uno:HelpMenu',
}
MENUS_APP = {
    'main': MENUS_MAIN,
    'calc': MENUS_CALC,
    'writer': MENUS_WRITER,
}

EXT = {
    'pdf': 'pdf',
}

FILE_NAME_DEBUG = 'debug.odt'
FILE_NAME_CONFIG = 'zaz-{}.json'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_DATE = '%d/%m/%Y %H:%M:%S'
logging.addLevelName(logging.ERROR, '\033[1;41mERROR\033[1;0m')
logging.addLevelName(logging.DEBUG, '\x1b[33mDEBUG\033[1;0m')
logging.addLevelName(logging.INFO, '\x1b[32mINFO\033[1;0m')
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=LOG_DATE)
log = logging.getLogger(__name__)


_start = 0
_stop_thread = {}
TIMEOUT = 10
SECONDS_DAY = 60 * 60 * 24


CTX = uno.getComponentContext()
SM = CTX.getServiceManager()


def create_instance(name, with_context=False):
    if with_context:
        instance = SM.createInstanceWithContext(name, CTX)
    else:
        instance = SM.createInstance(name)
    return instance


def get_app_config(node_name, key=''):
    name = 'com.sun.star.configuration.ConfigurationProvider'
    service = 'com.sun.star.configuration.ConfigurationAccess'
    cp = create_instance(name, True)
    node = PropertyValue(Name='nodepath', Value=node_name)
    try:
        ca = cp.createInstanceWithArguments(service, (node,))
        if ca and not key:
            return ca
        if ca and ca.hasByName(key):
            return ca.getPropertyValue(key)
    except Exception as e:
        error(e)
        return ''


# ~ FILTER_PDF = '/org.openoffice.Office.Common/Filter/PDF/Export/'
LANGUAGE = get_app_config('org.openoffice.Setup/L10N/', 'ooLocale')
LANG = LANGUAGE.split('-')[0]
NAME = TITLE = get_app_config('org.openoffice.Setup/Product', 'ooName')
VERSION = get_app_config('org.openoffice.Setup/Product','ooSetupVersion')

nd = '/org.openoffice.Office.Calc/Calculate/Other/Date'
d = get_app_config(nd, 'DD')
m = get_app_config(nd, 'MM')
y = get_app_config(nd, 'YY')
DATE_OFFSET = datetime.date(y, m, d).toordinal()


def mri(obj):
    m = create_instance('mytools.Mri')
    if m is None:
        msg = 'Extension MRI not found'
        error(msg)
        return

    m.inspect(obj)
    return


def inspect(obj):
    zaz = create_instance('net.elmau.zaz.inspect')
    zaz.inspect(obj)
    return


def catch_exception(f):
    @wraps(f)
    def func(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            name = f.__name__
            if IS_WIN:
                debug(traceback.format_exc())
            log.error(name, exc_info=True)
    return func


class LogWin(object):

    def __init__(self, doc):
        self.doc = doc

    def write(self, info):
        text = self.doc.Text
        cursor = text.createTextCursor()
        cursor.gotoEnd(False)
        text.insertString(cursor, str(info) + '\n\n', 0)
        return


def info(data):
    log.info(data)
    return


def debug(*info):
    if IS_WIN:
        doc = get_document(FILE_NAME_DEBUG)
        if doc is None:
            return
        doc = LogWin(doc.obj)
        doc.write(str(info))
        return

    data = [str(d) for d in info]
    log.debug('\t'.join(data))
    return


def error(info):
    log.error(info)
    return


def save_log(path, data):
    with open(path, 'a') as out:
        out.write('{} -{}- '.format(str(now())[:19], LOG_NAME))
        pprint(data, stream=out)
    return


def run_in_thread(fn):
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw)
        t.start()
        return t
    return run


def now(only_time=False):
    now = datetime.datetime.now()
    if only_time:
        return now.time()
    return now


def today():
    return datetime.date.today()


def get_date(year, month, day, hour=-1, minute=-1, second=-1):
    if hour > -1 or minute > -1 or second > -1:
        h = hour
        m = minute
        s = second
        if h == -1:
            h = 0
        if m == -1:
            m = 0
        if s == -1:
            s = 0
        d = datetime.datetime(year, month, day, h, m, s)
    else:
        d = datetime.date(year, month, day)
    return d


def get_config(key='', default=None, prefix='config'):
    path_json = FILE_NAME_CONFIG.format(prefix)
    values = None
    path = join(get_config_path('UserConfig'), path_json)
    if not exists_path(path):
        return default

    with open(path, 'r', encoding='utf-8') as fh:
        data = fh.read()
        values = json.loads(data)

    if key:
        return values.get(key, default)

    return values


def set_config(key, value, prefix='config'):
    path_json = FILE_NAME_CONFIG.format(prefix)
    path = join(get_config_path('UserConfig'), path_json)
    values = get_config(default={}, prefix=prefix)
    values[key] = value
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(values, fh, ensure_ascii=False, sort_keys=True, indent=4)
    return True


def sleep(seconds):
    time.sleep(seconds)
    return


def _(msg):
    L = LANGUAGE.split('-')[0]
    if L == 'en':
        return msg

    if not L in MSG_LANG:
        return msg

    return MSG_LANG[L][msg]


def msgbox(message, title=TITLE, buttons=MSG_BUTTONS.BUTTONS_OK, type_msg='infobox'):
    """ Create message box
        type_msg: infobox, warningbox, errorbox, querybox, messbox
        http://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1awt_1_1XMessageBoxFactory.html
    """
    toolkit = create_instance('com.sun.star.awt.Toolkit')
    parent = toolkit.getDesktopWindow()
    mb = toolkit.createMessageBox(parent, type_msg, buttons, title, str(message))
    return mb.execute()


def question(message, title=TITLE):
    res = msgbox(message, title, MSG_BUTTONS.BUTTONS_YES_NO, 'querybox')
    return res == YES


def warning(message, title=TITLE):
    return msgbox(message, title, type_msg='warningbox')


def errorbox(message, title=TITLE):
    return msgbox(message, title, type_msg='errorbox')


def get_desktop():
    return create_instance('com.sun.star.frame.Desktop', True)


def get_dispatch():
    return create_instance('com.sun.star.frame.DispatchHelper')


def call_dispatch(url, args=()):
    frame = get_document().frame
    dispatch = get_dispatch()
    dispatch.executeDispatch(frame, url, '', 0, args)
    return


def get_temp_file(only_name=False):
    delete = True
    if IS_WIN:
        delete = False
    tmp = tempfile.NamedTemporaryFile(delete=delete)
    if only_name:
        tmp = tmp.name
    return tmp

def _path_url(path):
    if path.startswith('file://'):
        return path
    return uno.systemPathToFileUrl(path)


def _path_system(path):
    if path.startswith('file://'):
        return os.path.abspath(uno.fileUrlToSystemPath(path))
    return path


def exists_app(name):
    try:
        dn = subprocess.DEVNULL
        subprocess.Popen([name, ''], stdout=dn, stderr=dn).terminate()
    except OSError as e:
        if e.errno == errno.ENOENT:
            return False
    return True


def exists_path(path):
    return Path(path).exists()


def get_type_doc(obj):
    for k, v in TYPE_DOC.items():
        if obj.supportsService(v):
            return k
    return ''


def dict_to_property(values, uno_any=False):
    ps = tuple([PropertyValue(Name=n, Value=v) for n, v in values.items()])
    if uno_any:
        ps = uno.Any('[]com.sun.star.beans.PropertyValue', ps)
    return ps


def property_to_dict(values):
    d = {i.Name: i.Value for i in values}
    return d


def set_properties(model, properties):
    if 'X' in properties:
        properties['PositionX'] = properties.pop('X')
    if 'Y' in properties:
        properties['PositionY'] = properties.pop('Y')
    keys = tuple(properties.keys())
    values = tuple(properties.values())
    model.setPropertyValues(keys, values)
    return


def array_to_dict(values):
    d = {r[0]: r[1] for r in values}
    return d


# ~ Custom classes
class ObjectBase(object):

    def __init__(self, obj):
        self._obj = obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __getitem__(self, index):
        return self.obj[index]

    def __getattr__(self, name):
        a = None
        if name == 'obj':
            a = super().__getattr__(name)
        else:
            if hasattr(self.obj, name):
                a = getattr(self.obj, name)
        return a

    @property
    def obj(self):
        return self._obj
    @obj.setter
    def obj(self, value):
        self._obj = value


class LOObjectBase(object):

    def __init__(self, obj):
        self.__dict__['_obj'] = obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return True

    def __setattr__(self, name, value):
        print('BASE__setattr__', name)
        if name == '_obj':
            super().__setattr__(name, value)
        else:
            self.obj.setPropertyValue(name, value)

    # ~ def _try_for_method(self, name):
        # ~ a = None
        # ~ m = 'get{}'.format(name)
        # ~ if hasattr(self.obj, m):
            # ~ a = getattr(self.obj, m)()
        # ~ else:
            # ~ a = getattr(self.obj, name)
        # ~ return a

    def __getattr__(self, name):
        print('BASE__getattr__', name)
        if name == 'obj':
            a = super().__getattr__(name)
        else:
            a = self.obj.getPropertyValue(name)
            # ~ Bug
            if a is None:
                msg = 'Error get: {} - {}'.format(self.obj.ImplementationName, name)
                error(msg)
                raise Exception(msg)
        return a

    @property
    def obj(self):
        return self._obj


class LODocument(object):

    def __init__(self, obj):
        self._obj = obj
        self._init_values()

    def _init_values(self):
        self._type_doc = get_type_doc(self.obj)
        self._cc = self.obj.getCurrentController()
        return

    @property
    def obj(self):
        return self._obj

    @property
    def title(self):
        return self.obj.getTitle()
    @title.setter
    def title(self, value):
        self.obj.setTitle(value)

    @property
    def uid(self):
        return self.obj.RuntimeUID

    @property
    def type(self):
        return self._type_doc

    @property
    def frame(self):
        return self._cc.getFrame()

    @property
    def is_saved(self):
        return self.obj.hasLocation()

    @property
    def is_modified(self):
        return self.obj.isModified()

    @property
    def is_read_only(self):
        return self.obj.isReadOnly()

    @property
    def path(self):
        return _path_system(self.obj.getURL())

    @property
    def statusbar(self):
        return self._cc.getStatusIndicator()

    @property
    def visible(self):
        w = self._cc.getFrame().getContainerWindow()
        return w.isVisible()
    @visible.setter
    def visible(self, value):
        w = self._cc.getFrame().getContainerWindow()
        w.setVisible(value)

    @property
    def zoom(self):
        return self._cc.ZoomValue
    @zoom.setter
    def zoom(self, value):
        self._cc.ZoomValue = value

    @property
    def table_auto_formats(self):
        taf = create_instance('com.sun.star.sheet.TableAutoFormats')
        return taf.ElementNames

    def create_instance(self, name):
        obj = self.obj.createInstance(name)
        return obj

    def save(self, path='', **kwargs):
        # ~ opt = _properties(kwargs)
        opt = dict_to_property(kwargs)
        if path:
            self._obj.storeAsURL(_path_url(path), opt)
        else:
            self._obj.store()
        return True

    def close(self):
        self.obj.close(True)
        return

    def focus(self):
        w = self._cc.getFrame().getComponentWindow()
        w.setFocus()
        return

    def paste(self):
        sc = create_instance('com.sun.star.datatransfer.clipboard.SystemClipboard')
        transferable = sc.getContents()
        self._cc.insertTransferable(transferable)
        return self.obj.getCurrentSelection()

    def to_pdf(self, path, **kwargs):
        path_pdf = path
        if path:
            if is_dir(path):
                _, _, n, _ = get_info_path(self.path)
                path_pdf = join(path, '{}.{}'.format(n, EXT['pdf']))
        else:
            path_pdf = replace_ext(self.path, EXT['pdf'])

        filter_name = '{}_pdf_Export'.format(self.type)
        filter_data = dict_to_property(kwargs, True)
        args = {
            'FilterName': filter_name,
            'FilterData': filter_data,
        }
        args = dict_to_property(args)
        try:
            self.obj.storeToURL(_path_url(path_pdf), args)
        except Exception as e:
            error(e)
            path_pdf = ''

        return path_pdf


class FormControlBase(object):
    EVENTS = {
        'action': 'actionPerformed',
        'click': 'mousePressed',
    }
    TYPES = {
        'actionPerformed': 'XActionListener',
        'mousePressed': 'XMouseListener',
    }

    def __init__(self, obj):
        self._obj = obj
        self._index = -1
        self._rules = {}

    @property
    def obj(self):
        return self._obj

    @property
    def name(self):
        return self.obj.Name

    @property
    def form(self):
        return self.obj.getParent()

    @property
    def index(self):
        return self._index
    @index.setter
    def index(self, value):
        self._index = value

    @property
    def events(self):
        return self.form.getScriptEvents(self.index)

    def remove_event(self, name=''):
        for ev in self.events:
            if name and \
                ev.EventMethod == self.EVENTS[name] and \
                ev.ListenerType == self.TYPES[ev.EventMethod]:
                self.form.revokeScriptEvent(self.index,
                    ev.ListenerType, ev.EventMethod, ev.AddListenerParam)
                break
            else:
                self.form.revokeScriptEvent(self.index,
                    ev.ListenerType, ev.EventMethod, ev.AddListenerParam)
        return

    def add_event(self, name, macro):
        if not 'name' in macro:
            macro['name'] = '{}_{}'.format(self.name, name)

        event = ScriptEventDescriptor()
        event.AddListenerParam = ''
        event.EventMethod = self.EVENTS[name]
        event.ListenerType = self.TYPES[event.EventMethod]
        event.ScriptCode = _get_url_script(macro)
        event.ScriptType = 'Script'

        for ev in self.events:
            if ev.EventMethod == event.EventMethod and \
                ev.ListenerType == event.ListenerType:
                self.form.revokeScriptEvent(self.index,
                    event.ListenerType, event.EventMethod, event.AddListenerParam)
                break

        self.form.registerScriptEvent(self.index, event)
        return


class FormButton(FormControlBase):

    def __init__(self, obj):
        super().__init__(obj)



class LOForm(ObjectBase):

    def __init__(self, obj):
        super().__init__(obj)
        self._init_controls()

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._controls[index]
        else:
            return getattr(self, index)

    def _get_type_control(self, name):
        types = {
            # ~ 'stardiv.Toolkit.UnoFixedTextControl': 'label',
            'com.sun.star.form.OButtonModel': 'formbutton',
            # ~ 'stardiv.Toolkit.UnoEditControl': 'text',
            # ~ 'stardiv.Toolkit.UnoRoadmapControl': 'roadmap',
            # ~ 'stardiv.Toolkit.UnoFixedHyperlinkControl': 'link',
            # ~ 'stardiv.Toolkit.UnoListBoxControl': 'listbox',
        }
        return types[name]

    def _init_controls(self):
        self._controls = []
        for i, c in enumerate(self.obj.ControlModels):
            tipo = self._get_type_control(c.ImplementationName)
            control = get_custom_class(tipo, c)
            control.index = i
            self._controls.append(control)
            setattr(self, c.Name, control)

    @property
    def name(self):
        return self._obj.getName()
    @name.setter
    def name(self, value):
        self._obj.setName(value)


class LOForms(ObjectBase):

    def __init__(self, obj, doc):
        self._doc = doc
        super().__init__(obj)

    def __getitem__(self, index):
        form = super().__getitem__(index)
        return LOForm(form)

    @property
    def doc(self):
        return self._doc

    @property
    def count(self):
        return self.obj.getCount()

    @property
    def names(self):
        return self.obj.getElementNames()

    def exists(self, name):
        return name in self.names

    def insert(self, name):
        form = self.doc.create_instance('com.sun.star.form.component.Form')
        self.obj.insertByName(name, form)
        return self[name]

    def remove(self, index):
        if isinstance(index, int):
            self.obj.removeByIndex(index)
        else:
            self.obj.removeByName(index)
        return


class LOCellStyle(LOObjectBase):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def name(self):
        return self.obj.Name

    def apply(self, properties):
        set_properties(self.obj, properties)
        return


class LOCellStyles(object):

    def __init__(self, obj):
        self._obj = obj

    def __len__(self):
        return len(self.obj)

    def __getitem__(self, index):
        return LOCellStyle(self.obj[index])

    def __setitem__(self, key, value):
         self.obj[key] = value

    def __delitem__(self, key):
        if not isinstance(key, str):
            key = key.Name
        del self.obj[key]

    def __contains__(self, item):
        return item in self.obj

    @property
    def obj(self):
        return self._obj

    @property
    def names(self):
        return self.obj.ElementNames

    def apply(self, style, properties):
        set_properties(style, properties)
        return


class LOImage(object):
    TYPES = {
        'image/png': 'png',
        'image/jpeg': 'jpg',
    }

    def __init__(self, obj):
        self._obj = obj

    @property
    def obj(self):
        return self._obj

    @property
    def address(self):
        return self.obj.Anchor.AbsoluteName

    @property
    def name(self):
        return self.obj.Name

    @property
    def mimetype(self):
        return self.obj.Bitmap.MimeType

    @property
    def url(self):
        return _path_system(self.obj.URL)
    @url.setter
    def url(self, value):
        self.obj.URL = _path_url(value)

    @property
    def path(self):
        return _path_system(self.obj.GraphicURL)
    @path.setter
    def path(self, value):
        self.obj.GraphicURL = _path_url(value)

    @property
    def visible(self):
        return self.obj.Visible
    @visible.setter
    def visible(self, value):
        self_obj.Visible = value

    def save(self, path):
        if is_dir(path):
            p = path
            n = self.name
        else:
            p, fn, n, e = get_info_path(path)
        ext = self.TYPES[self.mimetype]
        path = join(p, '{}.{}'.format(n, ext))
        size = len(self.obj.Bitmap.DIB)
        data = self.obj.GraphicStream.readBytes((), size)
        data = data[-1].value
        save_file(path, 'wb', data)
        return path


class LOCalc(LODocument):

    def __init__(self, obj):
        super().__init__(obj)
        self._sheets = obj.getSheets()

    def __getitem__(self, index):
        if isinstance(index, str):
            code_name = [s.Name for s in self._sheets if s.CodeName == index]
            if code_name:
                index = code_name[0]
        return LOCalcSheet(self._sheets[index], self)

    def __setitem__(self, key, value):
        self._sheets[key] = value

    def __contains__(self, item):
        return item in self.obj.Sheets

    @property
    def headers(self):
        return self._cc.ColumnRowHeaders
    @headers.setter
    def headers(self, value):
        self._cc.ColumnRowHeaders = value

    @property
    def tabs(self):
        return self._cc.SheetTabs
    @tabs.setter
    def tabs(self, value):
        self._cc.SheetTabs = value

    @property
    def active(self):
        return LOCalcSheet(self._cc.getActiveSheet(), self)

    def activate(self, sheet):
        obj = sheet
        if isinstance(sheet, LOCalcSheet):
            obj = sheet.obj
        elif isinstance(sheet, str):
            obj = self[sheet].obj
        self._cc.setActiveSheet(obj)
        return

    @property
    def selection(self):
        sel = self.obj.getCurrentSelection()
        if sel.ImplementationName in OBJ_TYPE_RANGES:
            sel = LOCellRange(sel, self)
        return sel

    @property
    def sheets(self):
        return LOCalcSheets(self._sheets, self)

    @property
    def names(self):
        return self.sheets.names

    @property
    def cell_style(self):
        obj = self.obj.getStyleFamilies()['CellStyles']
        return LOCellStyles(obj)

    def create(self):
        return self.obj.createInstance('com.sun.star.sheet.Spreadsheet')

    def insert(self, name, pos=-1):
        # ~ sheet = obj.createInstance('com.sun.star.sheet.Spreadsheet')
        # ~ obj.Sheets['New'] = sheet
        index = pos
        if pos < 0:
            index = self._sheets.Count + pos + 1
        if isinstance(name, str):
            self._sheets.insertNewByName(name, index)
        else:
            for n in name:
                self._sheets.insertNewByName(n, index)
            name = n
        return LOCalcSheet(self._sheets[name], self)

    def move(self, name, pos=-1):
        return self.sheets.move(name, pos)

    def remove(self, name):
        return self.sheets.remove(name)

    def copy(self, source='', target='', pos=-1):
        index = pos
        if pos < 0:
            index = self._sheets.Count + pos + 1

        names = source
        if not names:
            names = self.names
        elif isinstance(source, str):
            names = (source,)

        new_names = target
        if not target:
            new_names = [n + '_2' for n in names]
        elif isinstance(target, str):
            new_names = (target,)

        for i, ns in enumerate(names):
            self.sheets.copy(ns, new_names[i], index + i)

        return LOCalcSheet(self._sheets[index], self)

    def copy_from(self, doc, source='', target='', pos=-1):
        index = pos
        if pos < 0:
            index = self._sheets.Count + pos + 1

        names = source
        if not names:
            names = doc.names
        elif isinstance(source, str):
            names = (source,)

        new_names = target
        if not target:
            new_names = names
        elif isinstance(target, str):
            new_names = (target,)

        for i, n in enumerate(names):
            self._sheets.importSheet(doc.obj, n, index + i)
            self.sheets[index + i].name = new_names[i]

        # ~ doc.getCurrentController().setActiveSheet(sheet)
        # ~ For controls in sheet
        # ~ doc.getCurrentController().setFormDesignMode(False)

        return LOCalcSheet(self._sheets[index], self)

    def sort(self, reverse=False):
        names = sorted(self.names, reverse=reverse)
        for i, n in enumerate(names):
            self.sheets.move(n, i)
        return

    def get_cell(self, index=None):
        """
            index is str 'A1'
            index is tuple (row, col)
        """
        if index is None:
            cell = self.selection.first
        else:
            cell = LOCellRange(self.active[index].obj, self)
        return cell

    def select(self, rango):
        r = rango
        if hasattr(rango, 'obj'):
            r = rango.obj
        elif isinstance(rango, str):
            r = self.get_cell(rango).obj
        self._cc.select(r)
        return

    def create_cell_style(self, name=''):
        obj = self.create_instance('com.sun.star.style.CellStyle')
        if name:
            self.cell_style[name] = obj
        return LOCellStyle(obj)

    def clear_undo(self):
        self.obj.getUndoManager().clear()
        return

    def filter_by_color(self, cell=None):
        if cell is None:
            cell = self.selection.first
        cr = cell.current_region
        col = cell.column - cr.column
        rangos = cell.get_column(col).visible
        for r in rangos:
            for row in range(r.rows):
                c = r[row, 0]
                if c.back_color != cell.back_color:
                    c.rows_visible = False
        return


class LOCalcSheets(object):

    def __init__(self, obj, doc):
        self._obj = obj
        self._doc = doc

    def __getitem__(self, index):
        return LOCalcSheet(self.obj[index], self.doc)

    @property
    def obj(self):
        return self._obj

    @property
    def doc(self):
        return self._doc

    @property
    def count(self):
        return self.obj.Count

    @property
    def names(self):
        return self.obj.ElementNames

    def copy(self, name, new_name, pos):
        self.obj.copyByName(name, new_name, pos)
        return

    def move(self, name, pos):
        index = pos
        if pos < 0:
            index = self.count + pos + 1
        sheet = self.obj[name]
        self.obj.moveByName(sheet.Name, index)
        return

    def remove(self, name):
        sheet = self.obj[name]
        self.obj.removeByName(sheet.Name)
        return


class LOCalcSheet(object):

    def __init__(self, obj, doc):
        self._obj = obj
        self._doc = doc
        self._init_values()

    def __getitem__(self, index):
        return LOCellRange(self.obj[index], self.doc)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def _init_values(self):
        self._events = None
        self._dp = self.obj.getDrawPage()
        self._images = {i.Name: LOImage(i) for i in self._dp}

    @property
    def obj(self):
        return self._obj

    @property
    def doc(self):
        return self._doc

    @property
    def images(self):
        return self._images

    @property
    def name(self):
        return self._obj.Name
    @name.setter
    def name(self, value):
        self._obj.Name = value

    @property
    def code_name(self):
        return self._obj.CodeName
    @code_name.setter
    def code_name(self, value):
        self._obj.CodeName = value

    @property
    def color(self):
        return self._obj.TabColor
    @color.setter
    def color(self, value):
        self._obj.TabColor = get_color(value)

    @property
    def active(self):
        return self.doc.selection.first

    def activate(self):
        self.doc.activate(self.obj)
        return

    @property
    def visible(self):
        return self.obj.IsVisible
    @visible.setter
    def visible(self, value):
        self.obj.IsVisible = value

    @property
    def is_protected(self):
        return self._obj.isProtected()

    @property
    def password(self):
        return ''
    @visible.setter
    def password(self, value):
        self.obj.protect(value)

    def unprotect(self, value):
        try:
            self.obj.unprotect(value)
            return True
        except:
            pass
        return False

    def get_cursor(self, cell):
        return self.obj.createCursorByRange(cell)

    def exists_chart(self, name):
        return name in self.obj.Charts.ElementNames

    @property
    def forms(self):
        return LOForms(self._dp.getForms(), self.doc)

    @property
    def events(self):
        return self._events
    @events.setter
    def events(self, controllers):
        self._events = controllers
        self._connect_listeners()

    def _connect_listeners(self):
        if self.events is None:
            return

        listeners = {
            'addModifyListener': EventsModify,
        }
        for key, value in listeners.items():
            getattr(self.obj, key)(listeners[key](self.events))
            print('add_listener')
        return


class LOWriter(LODocument):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def obj(self):
        return self._obj

    @property
    def string(self):
        return self._obj.getText().String

    @property
    def text(self):
        return self._obj.getText()

    @property
    def cursor(self):
        return self.text.createTextCursor()

    @property
    def paragraphs(self):
        return [LOTextRange(p) for p in self.text]

    @property
    def selection(self):
        sel = self.obj.getCurrentSelection()
        if sel.ImplementationName == TEXT_RANGES:
            return LOTextRange(sel[0])
        elif sel.ImplementationName == TEXT_RANGE:
            return LOTextRange(sel)
        return sel

    def write(self, data, cursor=None):
        cursor = cursor or self.selection.cursor.getEnd()
        if data.startswith('\n'):
            c = data.split('\n')
            for i in range(len(c)-1):
                self.text.insertControlCharacter(cursor, PARAGRAPH_BREAK, False)
        else:
            self.text.insertString(cursor, data, False)
        return

    def insert_table(self, data, cursor=None):
        cursor = cursor or self.selection.cursor.getEnd()
        table = self.obj.createInstance('com.sun.star.text.TextTable')
        rows = len(data)
        cols = len(data[0])
        table.initialize(rows, cols)
        self.insert_content(cursor, table)
        table.DataArray = data
        return WriterTable(table)

    def create_chart(self, tipo, cursor=None):
        cursor = cursor or self.selection.cursor.getEnd()
        chart = LOChart(None, tipo)
        chart.cursor = cursor
        chart.doc = self
        return chart

    def insert_content(self, cursor, data, replace=False):
        self.text.insertTextContent(cursor, data, replace)
        return

    # ~ f = doc.createInstance('com.sun.star.text.TextFrame')
    # ~ f.setSize(Size(10000, 500))

    def insert_image(self, path, **kwargs):
        cursor = kwargs.get('cursor', self.selection.cursor.getEnd())
        w = kwargs.get('width', 2000)
        h = kwargs.get('Height', 2000)
        image = self.create_instance('com.sun.star.text.GraphicObject')
        image.GraphicURL = _path_url(path)
        image.AnchorType = AS_CHARACTER
        image.Width = w
        image.Height = h
        self.insert_content(cursor, image)
        return

    def go_start(self):
        cursor = self._cc.getViewCursor()
        cursor.gotoStart(False)
        return cursor

    def go_end(self):
        cursor = self._cc.getViewCursor()
        cursor.gotoEnd(False)
        return cursor

    def select(self, text):
        self._cc.select(text)
        return

    def search(self, options):
        descriptor = self.obj.createSearchDescriptor()
        descriptor.setSearchString(options.get('Search', ''))
        descriptor.SearchCaseSensitive = options.get('CaseSensitive', False)
        descriptor.SearchWords = options.get('Words', False)
        if 'Attributes' in options:
            attr = dict_to_property(options['Attributes'])
            descriptor.setSearchAttributes(attr)
        if hasattr(descriptor, 'SearchRegularExpression'):
            descriptor.SearchRegularExpression = options.get('RegularExpression', False)
        if hasattr(descriptor, 'SearchType') and 'Type' in options:
            descriptor.SearchType = options['Type']

        if options.get('First', False):
            found = self.obj.findFirst(descriptor)
        else:
            found = self.obj.findAll(descriptor)

        return found

    def replace(self, options):
        descriptor = self.obj.createReplaceDescriptor()
        descriptor.setSearchString(options['Search'])
        descriptor.setReplaceString(options['Replace'])
        descriptor.SearchCaseSensitive = options.get('CaseSensitive', False)
        descriptor.SearchWords = options.get('Words', False)
        if 'Attributes' in options:
            attr = dict_to_property(options['Attributes'])
            descriptor.setSearchAttributes(attr)
        if hasattr(descriptor, 'SearchRegularExpression'):
            descriptor.SearchRegularExpression = options.get('RegularExpression', False)
        if hasattr(descriptor, 'SearchType') and 'Type' in options:
            descriptor.SearchType = options['Type']
        found = self.obj.replaceAll(descriptor)
        return found


class LOTextRange(object):

    def __init__(self, obj):
        self._obj = obj
        self._is_paragraph = self.obj.ImplementationName == 'SwXParagraph'
        self._is_table = self.obj.ImplementationName == 'SwXTextTable'

    @property
    def obj(self):
        return self._obj

    @property
    def is_paragraph(self):
        return self._is_paragraph

    @property
    def is_table(self):
        return self._is_table

    @property
    def string(self):
        return self.obj.String

    @property
    def text(self):
        return self.obj.getText()

    @property
    def cursor(self):
        return self.text.createTextCursorByRange(self.obj)


class LOBase(object):
    TYPES = {
        str: 'setString',
        int: 'setInt',
        float: 'setFloat',
        bool: 'setBoolean',
        Date: 'setDate',
        Time: 'setTime',
        DateTime: 'setTimestamp',
    }
    # ~ setArray
    # ~ setBinaryStream
    # ~ setBlob
    # ~ setByte
    # ~ setBytes
    # ~ setCharacterStream
    # ~ setClob
    # ~ setNull
    # ~ setObject
    # ~ setObjectNull
    # ~ setObjectWithInfo
    # ~ setPropertyValue
    # ~ setRef
    def __init__(self, name, path='', **kwargs):
        self._name = name
        self._path = path
        self._dbc = create_instance('com.sun.star.sdb.DatabaseContext')
        if path:
            path_url = _path_url(path)
            db = self._dbc.createInstance()
            db.URL = 'sdbc:embedded:firebird'
            db.DatabaseDocument.storeAsURL(path_url, ())
            if not self.exists:
                self._dbc.registerDatabaseLocation(name, path_url)
        else:
            if name.startswith('odbc:'):
                self._con = self._odbc(name, kwargs)
            else:
                db = self._dbc.getByName(name)
                self.path = _path_system(self._dbc.getDatabaseLocation(name))
                self._con = db.getConnection('', '')

        if self._con is None:
            msg = 'Not connected to: {}'.format(name)
        else:
            msg = 'Connected to: {}'.format(name)
        debug(msg)

    def _odbc(self, name, kwargs):
        dm = create_instance('com.sun.star.sdbc.DriverManager')
        args = dict_to_property(kwargs)
        try:
            con = dm.getConnectionWithInfo('sdbc:{}'.format(name), args)
            return con
        except Exception as e:
            error(str(e))
            return None

    @property
    def obj(self):
        return self._obj

    @property
    def name(self):
        return self._name

    @property
    def connection(self):
        return self._con

    @property
    def path(self):
        return self._path
    @path.setter
    def path(self, value):
        self._path = value

    @property
    def exists(self):
        return self._dbc.hasRegisteredDatabase(self.name)

    @classmethod
    def register(self, path, name):
        if not self._dbc.hasRegisteredDatabase(name):
            self._dbc.registerDatabaseLocation(name, _path_url(path))
        return

    def revoke(self, name):
        self._dbc.revokeDatabaseLocation(name)
        return True

    def save(self):
        # ~ self._db.connection.commit()
        # ~ self._db.connection.getTables().refresh()
        # ~ oDisp.executeDispatch(oFrame,".uno:DBRefreshTables", "", 0, Array())
        self._obj.DatabaseDocument.store()
        self.refresh()
        return

    def close(self):
        self._con.close()
        return

    def refresh(self):
        self._con.getTables().refresh()
        return

    def get_tables(self):
        tables = self._con.getTables()
        tables = [tables.getByIndex(i) for i in range(tables.Count)]
        return tables

    def cursor(self, sql, params):
        cursor = self._con.prepareStatement(sql)
        for i, v in enumerate(params, 1):
            if not type(v) in self.TYPES:
                error('Type not support')
                debug((i, type(v), v, self.TYPES[type(v)]))
            getattr(cursor, self.TYPES[type(v)])(i, v)
        return cursor

    def execute(self, sql, params):
        debug(sql)
        if params:
            cursor = self.cursor(sql, params)
            cursor.execute()
        else:
            cursor = self._con.createStatement()
            cursor.execute(sql)
            # ~ resulset = cursor.executeQuery(sql)
            # ~ rows = cursor.executeUpdate(sql)
        self.save()
        return cursor


class LODrawImpress(LODocument):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def draw_page(self):
        return self._cc.getCurrentPage()

    def insert_text(self, text, fontsize):
        # ~ msgbox('insert_text : '+ text)
        otextshape = self.draw_page.getByIndex(0) # TitleText
        if otextshape.supportsService("com.sun.star.presentation.TitleTextShape"):
            otextshape.setString(text)
            otextshape.ParaAdjust = 0 # LEFT
            otextshape.CharHeight = fontsize
            otextshape.CharHeightAsian = fontsize
        return

    def set_currentpage(self, page):
        # ~ msgbox('set_currentpage')
        self._cc.setCurrentPage(page)
        return

    def insert_image(self, path, **kwargs):
        w = kwargs.get('width', 9000)
        h = kwargs.get('Height', 9000)
        x = kwargs.get('X', 2000)
        y = kwargs.get('Y', 7000)

        image = self.create_instance('com.sun.star.drawing.GraphicObjectShape')
        image.GraphicURL = _path_url(path)
        image.Size = Size(w, h)
        image.Position = Point(x, y)
        self.draw_page.add(image)
        return


class LOImpress(LODrawImpress):

    def __init__(self, obj):
        super().__init__(obj)


class LODraw(LODrawImpress):

    def __init__(self, obj):
        super().__init__(obj)


class LOMath(LODocument):

    def __init__(self, obj):
        super().__init__(obj)


class LOBasicIde(LODocument):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def selection(self):
        sel = self._cc.getSelection()
        return sel


class LOCellRange(object):

    def __init__(self, obj, doc):
        self._obj = obj
        self._doc = doc
        self._init_values()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __getitem__(self, index):
        return LOCellRange(self.obj[index], self.doc)

    def __contains__(self, item):
        return item.in_range(self)

    def _init_values(self):
        self._type_obj = self.obj.ImplementationName
        self._type_content = EMPTY

        if self._type_obj == OBJ_CELL:
            self._type_content = self.obj.getType()
        return

    @property
    def obj(self):
        return self._obj

    @property
    def doc(self):
        return self._doc

    @property
    def type(self):
        return self._type_obj

    @property
    def type_content(self):
        return self._type_content

    @property
    def first(self):
        if self.type == OBJ_RANGES:
            obj = LOCellRange(self.obj[0][0,0], self.doc)
        else:
            obj = LOCellRange(self.obj[0,0], self.doc)
        return obj

    @property
    def value(self):
        v = None
        if self._type_content == VALUE:
            v = self.obj.getValue()
        elif self._type_content == TEXT:
            v = self.obj.getString()
        elif self._type_content == FORMULA:
            v = self.obj.getFormula()
        return v
    @value.setter
    def value(self, data):
        if isinstance(data, str):
            if data.startswith('='):
                self.obj.setFormula(data)
            else:
                self.obj.setString(data)
        elif isinstance(data, (int, float, bool)):
            self.obj.setValue(data)
        elif isinstance(data, datetime.datetime):
            d = data.toordinal()
            t = (data - datetime.datetime.fromordinal(d)).seconds / SECONDS_DAY
            self.obj.setValue(d - DATE_OFFSET + t)
        elif isinstance(data, datetime.date):
            d = data.toordinal()
            self.obj.setValue(d - DATE_OFFSET)
        elif isinstance(data, datetime.time):
            d = (data.hour * 3600 + data.minute * 60 + data.second) / SECONDS_DAY
            self.obj.setValue(d)

    def Value(self, data):
        if isinstance(data, str):
            if data.startswith('='):
                self.obj.setFormula(data)
            else:
                self.obj.setString(data)
        elif isinstance(data, (int, float, bool)):
            self.obj.setValue(data)
        elif isinstance(data, datetime.datetime):
            d = data.toordinal()
            t = (data - datetime.datetime.fromordinal(d)).seconds / SECONDS_DAY
            self.obj.setValue(d - DATE_OFFSET + t)
        elif isinstance(data, datetime.date):
            d = data.toordinal()
            self.obj.setValue(d - DATE_OFFSET)
        elif isinstance(data, datetime.time):
            d = (data.hour * 3600 + data.minute * 60 + data.second) / SECONDS_DAY
            self.obj.setValue(d)

    @property
    def data(self):
        return self.obj.getDataArray()
    @data.setter
    def data(self, values):
        self.obj.setDataArray(values)

    @property
    def formula(self):
        return self.obj.getFormulaArray()
    @formula.setter
    def formula(self, values):
        self.obj.setFormulaArray(values)

    @property
    def column(self):
        a = self.address
        if hasattr(a, 'Column'):
            c = a.Column
        else:
            c = a.StartColumn
        return c

    @property
    def row(self):
        a = self.address
        if hasattr(a, 'Row'):
            c = a.Row
        else:
            c = a.StartRow
        return c

    @property
    def columns(self):
        return self._obj.Columns.Count

    @property
    def rows(self):
        return self._obj.Rows.Count

    def to_size(self, rows, cols):
        cursor = self.sheet.get_cursor(self.obj[0,0])
        cursor.collapseToSize(cols, rows)
        return LOCellRange(self.sheet[cursor.AbsoluteName].obj, self.doc)

    def copy_from(self, rango, formula=False):
        data = rango
        if isinstance(rango, LOCellRange):
            if formula:
                data = rango.formula
            else:
                data = rango.data
        rows = len(data)
        cols = len(data[0])
        if formula:
            self.to_size(rows, cols).formula = data
        else:
            self.to_size(rows, cols).data = data
        return

    def copy_to(self, cell, formula=False):
        rango = cell.to_size(self.rows, self.columns)
        if formula:
            rango.formula = self.data
        else:
            rango.data = self.data
        return

    def copy(self, source):
        self.sheet.obj.copyRange(self.address, source.range_address)
        return

    def offset(self, row=1, col=0):
        ra = self.obj.getRangeAddress()
        col = ra.EndColumn + col
        row = ra.EndRow + row
        return LOCellRange(self.sheet[row, col].obj, self.doc)

    @property
    def next_cell(self):
        a = self.current_region.address
        if hasattr(a, 'StartColumn'):
            col = a.StartColumn
        else:
            col = a.Column
        if hasattr(a, 'EndRow'):
            row = a.EndRow + 1
        else:
            row = a.Row + 1

        return LOCellRange(self.sheet[row, col].obj, self.doc)

    def Next_cell(self):
        a = self.current_region.address
        if hasattr(a, 'StartColumn'):
            col = a.StartColumn
        else:
            col = a.Column
        if hasattr(a, 'EndRow'):
            row = a.EndRow + 1
        else:
            row = a.Row + 1

        return LOCellRange(self.sheet[row, col].obj, self.doc)

    @property
    def sheet(self):
        return LOCalcSheet(self.obj.Spreadsheet, self.doc)

    @property
    def charts(self):
        return self.obj.Spreadsheet.Charts

    @property
    def ps(self):
        ps = Rectangle()
        s = self.obj.Size
        p = self.obj.Position
        ps.X = p.X
        ps.Y = p.Y
        ps.Width = s.Width
        ps.Height = s.Height
        return ps

    @property
    def draw_page(self):
        return self.sheet.obj.getDrawPage()

    @property
    def name(self):
        return self.obj.AbsoluteName

    @property
    def address(self):
        if self._type_obj == OBJ_CELL:
            a = self.obj.getCellAddress()
        elif self._type_obj == OBJ_RANGE:
            a = self.obj.getRangeAddress()
        else:
            a = self.obj.getRangeAddressesAsString()
        return a

    @property
    def range_address(self):
        return self.obj.getRangeAddress()

    @property
    def current_region(self):
        cursor = self.sheet.get_cursor(self.obj[0,0])
        cursor.collapseToCurrentRegion()
        return LOCellRange(self.sheet[cursor.AbsoluteName].obj, self.doc)

    @property
    def visible(self):
        cursor = self.sheet.get_cursor(self.obj)
        rangos = [LOCellRange(self.sheet[r.AbsoluteName].obj, self.doc)
            for r in cursor.queryVisibleCells()]
        return tuple(rangos)

    @property
    def empty(self):
        cursor = self.sheet.get_cursor(self.obj)
        rangos = [LOCellRange(self.sheet[r.AbsoluteName].obj, self.doc)
            for r in cursor.queryEmptyCells()]
        return tuple(rangos)

    @property
    def back_color(self):
        return self._obj.CellBackColor
    @back_color.setter
    def back_color(self, value):
        self._obj.CellBackColor = get_color(value)

    @property
    def cell_style(self):
        return self.obj.CellStyle
    @cell_style.setter
    def cell_style(self, value):
        self.obj.CellStyle = value

    @property
    def auto_format(self):
        return self.obj.CellStyle
    @auto_format.setter
    def auto_format(self, value):
        self.obj.autoFormat(value)

    def insert_image(self, path, **kwargs):
        s = self.obj.Size
        # ~ w = kwargs.get('width', s.Width)
        # ~ h = kwargs.get('Height', s.Height)
        w = kwargs.get('width', 2000)
        h = kwargs.get('Height', 2000)
        img = self.doc.create_instance('com.sun.star.drawing.GraphicObjectShape')
        img.GraphicURL = _path_url(path)
        self.draw_page.add(img)
        img.Anchor = self.obj
        img.setSize(Size(w, h))
        return

    def insert_shape(self, tipo, **kwargs):
        s = self.obj.Size
        w = kwargs.get('width', s.Width)
        h = kwargs.get('Height', s.Height)
        img = self.doc.create_instance('com.sun.star.drawing.{}Shape'.format(tipo))
        set_properties(img, kwargs)
        self.draw_page.add(img)
        img.Anchor = self.obj
        img.setSize(Size(w, h))
        return

    def select(self):
        self.doc._cc.select(self.obj)
        return

    def in_range(self, rango):
        if isinstance(rango, LOCellRange):
            address = rango.address
        else:
            address = rango.getRangeAddress()
        cursor = self.sheet.get_cursor(self.obj)
        result = cursor.queryIntersection(address)
        return bool(result.Count)

    def fill(self, source=1):
        self.obj.fillAuto(0, source)
        return

    def clear(self, what=31):
        # ~ http://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1sheet_1_1CellFlags.html
        self.obj.clearContents(what)
        return

    @property
    def rows_visible(self):
        return self._obj.getRows().IsVisible
    @rows_visible.setter
    def rows_visible(self, value):
        self._obj.getRows().IsVisible = value

    @property
    def columns_visible(self):
        return self._obj.getColumns().IsVisible
    @columns_visible.setter
    def columns_visible(self, value):
        self._obj.getColumns().IsVisible = value

    def get_column(self, index=0, first=False):
        ca = self.address
        ra = self.current_region.address
        if hasattr(ca, 'Column'):
            col = ca.Column
        else:
            col = ca.StartColumn + index
        start = 1
        if first:
            start = 0
        if hasattr(ra, 'Row'):
            row_start = ra.Row + start
            row_end = ra.Row + 1
        else:
            row_start = ra.StartRow + start
            row_end = ra.EndRow + 1
        return LOCellRange(self.sheet[row_start:row_end, col:col+1].obj, self.doc)

    def import_csv(self, path, **kwargs):
        data = import_csv(path, **kwargs)
        self.copy_from(data)
        return

    def export_csv(self, path, **kwargs):
        data = self.current_region.data
        export_csv(path, data, **kwargs)
        return

    def create_chart(self, tipo):
        chart = LOChart(None, tipo)
        chart.cell = self
        return chart

    def search(self, options):
        descriptor = self.obj.Spreadsheet.createSearchDescriptor()
        descriptor.setSearchString(options.get('Search', ''))
        descriptor.SearchCaseSensitive = options.get('CaseSensitive', False)
        descriptor.SearchWords = options.get('Words', False)
        if hasattr(descriptor, 'SearchRegularExpression'):
            descriptor.SearchRegularExpression = options.get('RegularExpression', False)
        if hasattr(descriptor, 'SearchType') and 'Type' in options:
            descriptor.SearchType = options['Type']

        if options.get('First', False):
            found = self.obj.findFirst(descriptor)
        else:
            found = self.obj.findAll(descriptor)

        return found

    def replace(self, options):
        descriptor = self.obj.Spreadsheet.createReplaceDescriptor()
        descriptor.setSearchString(options['Search'])
        descriptor.setReplaceString(options['Replace'])
        descriptor.SearchCaseSensitive = options.get('CaseSensitive', False)
        descriptor.SearchWords = options.get('Words', False)
        if hasattr(descriptor, 'SearchRegularExpression'):
            descriptor.SearchRegularExpression = options.get('RegularExpression', False)
        if hasattr(descriptor, 'SearchType') and 'Type' in options:
            descriptor.SearchType = options['Type']
        found = self.obj.replaceAll(descriptor)
        return found


class EventsListenerBase(unohelper.Base, XEventListener):

    def __init__(self, controller, name, window=None):
        self._controller = controller
        self._name = name
        self._window = window

    @property
    def name(self):
        return self._name

    def disposing(self, event):
        self._controller = None
        if not self._window is None:
            self._window.setMenuBar(None)


class EventsButton(EventsListenerBase, XActionListener):

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def actionPerformed(self, event):
        event_name = '{}_action'.format(self._name)
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return


class EventsMouse(EventsListenerBase, XMouseListener, XMouseMotionListener):

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def mousePressed(self, event):
        event_name = '{}_click'.format(self._name)
        if event.ClickCount == 2:
            event_name = '{}_double_click'.format(self._name)
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return

    def mouseReleased(self, event):
        pass

    def mouseEntered(self, event):
        pass

    def mouseExited(self, event):
        pass

    # ~ XMouseMotionListener
    def mouseMoved(self, event):
        pass

    def mouseDragged(self, event):
        pass


class EventsMouseLink(EventsMouse):

    def mouseEntered(self, event):
        obj = event.Source.Model
        obj.TextColor = get_color('blue')
        return

    def mouseExited(self, event):
        obj = event.Source.Model
        obj.TextColor = 0
        return


class EventsMouseGrid(EventsMouse):
    selected = False

    def mousePressed(self, event):
        super().mousePressed(event)
        # ~ obj = event.Source
        # ~ col = obj.getColumnAtPoint(event.X, event.Y)
        # ~ row = obj.getRowAtPoint(event.X, event.Y)
        # ~ print(col, row)
        # ~ if col == -1 and row == -1:
            # ~ if self.selected:
                # ~ obj.deselectAllRows()
            # ~ else:
                # ~ obj.selectAllRows()
            # ~ self.selected = not self.selected
        return

    def mouseReleased(self, event):
        # ~ obj = event.Source
        # ~ col = obj.getColumnAtPoint(event.X, event.Y)
        # ~ row = obj.getRowAtPoint(event.X, event.Y)
        # ~ if row == -1 and col > -1:
            # ~ gdm = obj.Model.GridDataModel
            # ~ for i in range(gdm.RowCount):
                # ~ gdm.updateRowHeading(i, i + 1)
        return


class EventsModify(EventsListenerBase, XModifyListener):

    def __init__(self, controller):
        super().__init__(controller)

    def modified(self, event):
        event_name = '{}_modified'.format(event.Source.Name)
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return


class EventsItem(EventsListenerBase, XItemListener):

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def disposing(self, event):
        pass

    def itemStateChanged(self, event):
        event_name = '{}_item_changed'.format(self.name)
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return


class EventsItemRoadmap(EventsItem):

    def itemStateChanged(self, event):
        dialog = event.Source.Context.Model
        dialog.Step = event.ItemId + 1
        return


class EventsFocus(EventsListenerBase, XFocusListener):

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def focusGained(self, event):
        service = event.Source.Model.ImplementationName
        if service == 'stardiv.Toolkit.UnoControlListBoxModel':
            return
        obj = event.Source.Model
        obj.BackgroundColor = COLOR_ON_FOCUS

    def focusLost(self, event):
        obj = event.Source.Model
        obj.BackgroundColor = -1


class EventsKey(EventsListenerBase, XKeyListener):
    """
        event.KeyChar
        event.KeyCode
        event.KeyFunc
        event.Modifiers
    """

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def keyPressed(self, event):
        pass

    def keyReleased(self, event):
        event_name = '{}_key_released'.format(self._name)
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return


class EventsTab(EventsListenerBase, XTabListener):

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def activated(self, id):
        event_name = '{}_activated'.format(self.name)
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(id)
        return


class EventsGrid(EventsListenerBase, XGridDataListener, XGridSelectionListener):

    def __init__(self, controller, name):
        super().__init__(controller, name)

    def dataChanged(self, event):
        event_name = '{}_data_changed'.format(self.name)
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return

    def rowHeadingChanged(self, event):
        pass

    def rowsInserted(self, event):
        pass

    def rowsRemoved(self, evemt):
        pass

    def selectionChanged(self, event):
        event_name = '{}_selection_changed'.format(self.name)
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return


class EventsKeyWindow(EventsListenerBase, XKeyListener):
    """
        event.KeyChar
        event.KeyCode
        event.KeyFunc
        event.Modifiers
    """

    def __init__(self, cls):
        super().__init__(cls.events, cls.name)
        self._cls = cls

    def keyPressed(self, event):
        pass

    def keyReleased(self, event):
        event_name = '{}_key_released'.format(self._cls.name)
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        else:
            if event.KeyFunc == QUIT and hasattr(self._cls, 'close'):
                self._cls.close()
        return


class EventsWindow(EventsListenerBase, XTopWindowListener, XWindowListener):

    def __init__(self, cls):
        self._cls = cls
        super().__init__(cls.events, cls.name, cls._window)

    def windowOpened(self, event):
        event_name = '{}_opened'.format(self._name)
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return

    def windowActivated(self, event):
        control_name = '{}_activated'.format(event.Source.Model.Name)
        if hasattr(self._controller, control_name):
            getattr(self._controller, control_name)(event)
        return

    def windowDeactivated(self, event):
        control_name = '{}_deactivated'.format(event.Source.Model.Name)
        if hasattr(self._controller, control_name):
            getattr(self._controller, control_name)(event)
        return

    def windowMinimized(self, event):
        pass

    def windowNormalized(self, event):
        pass

    def windowClosing(self, event):
        if self._window:
            control_name = 'window_closing'
        else:
            control_name = '{}_closing'.format(event.Source.Model.Name)

        if hasattr(self._controller, control_name):
            getattr(self._controller, control_name)(event)
        # ~ else:
            # ~ if not self._modal and not self._block:
                # ~ event.Source.Visible = False
        return

    def windowClosed(self, event):
        control_name = '{}_closed'.format(event.Source.Model.Name)
        if hasattr(self._controller, control_name):
            getattr(self._controller, control_name)(event)
        return

    # ~ XWindowListener
    def windowResized(self, event):
        sb = self._cls._subcont
        sb.setPosSize(0, 0, event.Width, event.Height, SIZE)
        event_name = '{}_resized'.format(self._name)
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return

    def windowMoved(self, event):
        pass

    def windowShown(self, event):
        pass

    def windowHidden(self, event):
        pass


class EventsMenu(EventsListenerBase, XMenuListener):

    def __init__(self, controller):
        super().__init__(controller, '')

    def itemHighlighted(self, event):
        pass

    def itemSelected(self, event):
        name = event.Source.getCommand(event.MenuId)
        if name.startswith('menu'):
            event_name = '{}_selected'.format(name)
        else:
            event_name = 'menu_{}_selected'.format(name)
        if hasattr(self._controller, event_name):
            getattr(self._controller, event_name)(event)
        return

    def itemActivated(self, event):
        return

    def itemDeactivated(self, event):
        return


class UnoBaseObject(object):

    def __init__(self, obj):
        self._obj = obj
        self._model = self.obj.Model
        self._rules = {}

    @property
    def obj(self):
        return self._obj

    @property
    def model(self):
        return self._model

    @property
    def name(self):
        return self.model.Name

    @property
    def parent(self):
        ps = self.obj.getContext().PosSize
        return self.obj.getContext()

    def _get_possize(self, name):
        ps = self.obj.getPosSize()
        return getattr(ps, name)

    def _set_possize(self, name, value):
        ps = self.obj.getPosSize()
        setattr(ps, name, value)
        self.obj.setPosSize(ps.X, ps.Y, ps.Width, ps.Height, POSSIZE)
        return

    @property
    def x(self):
        if hasattr(self.model, 'PositionX'):
            return self.model.PositionX
        return self._get_possize('X')
    @x.setter
    def x(self, value):
        if hasattr(self.model, 'PositionX'):
            self.model.PositionX = value
        else:
            self._set_possize('X', value)

    @property
    def y(self):
        if hasattr(self.model, 'PositionY'):
            return self.model.PositionY
        return self._get_possize('Y')
    @y.setter
    def y(self, value):
        if hasattr(self.model, 'PositionY'):
            self.model.PositionY = value
        else:
            self._set_possize('Y', value)

    @property
    def width(self):
        return self._model.Width
    @width.setter
    def width(self, value):
        if hasattr(self.model, 'Width'):
            self.model.Width = value
        elif hasattr(self.obj, 'PosSize'):
            self._set_possize('Width', value)

    @property
    def height(self):
        if hasattr(self.model, 'Height'):
            return self.model.Height
        ps = self.obj.getPosSize()
        return ps.Height
    @height.setter
    def height(self, value):
        if hasattr(self.model, 'Height'):
            self.model.Height = value
        elif hasattr(self.obj, 'PosSize'):
            self._set_possize('Height', value)

    @property
    def tag(self):
        return self.model.Tag
    @tag.setter
    def tag(self, value):
        self.model.Tag = value

    @property
    def visible(self):
        return self.obj.Visible
    @visible.setter
    def visible(self, value):
        self.obj.setVisible(value)

    @property
    def enabled(self):
        return self.model.Enabled
    @enabled.setter
    def enabled(self, value):
        self.model.Enabled = value

    @property
    def step(self):
        return self.model.Step
    @step.setter
    def step(self, value):
        self.model.Step = value

    @property
    def back_color(self):
        return self.model.BackgroundColor
    @back_color.setter
    def back_color(self, value):
        self.model.BackgroundColor = value

    @property
    def rules(self):
        return self._rules
    @rules.setter
    def rules(self, value):
        self._rules = value

    def set_focus(self):
        self.obj.setFocus()
        return

    def center(self, horizontal=True, vertical=False):
        p = self.parent.Model
        w = p.Width
        h = p.Height
        if horizontal:
            x = w / 2 - self.width / 2
            self.x = x
        if vertical:
            y = h / 2 - self.height / 2
            self.y = y
        return

    def move(self, origin, x=0, y=5):
        if x:
            self.x = origin.x + origin.width + x
        else:
            self.x = origin.x
        if y:
            self.y = origin.y + origin.height + y
        else:
            self.y = origin.y
        return

    def possize(self, origin):
        self.x = origin.x
        self.y = origin.y
        self.width = origin.width
        self.height = origin.height
        return


class UnoLabel(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'label'

    @property
    def value(self):
        return self.model.Label
    @value.setter
    def value(self, value):
        self.model.Label = value


class UnoLabelLink(UnoLabel):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'link'


class UnoButton(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'button'

    @property
    def value(self):
        return self.model.Label
    @value.setter
    def value(self, value):
        self.model.Label = value


class UnoText(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'text'

    @property
    def value(self):
        return self.model.Text
    @value.setter
    def value(self, value):
        self.model.Text = value

    def validate(self):

        return


class UnoListBox(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)

    @property
    def type(self):
        return 'listbox'

    @property
    def value(self):
        return self.obj.getSelectedItem()

    @property
    def count(self):
        return len(self.data)

    @property
    def data(self):
        return self.model.StringItemList
    @data.setter
    def data(self, values):
        self.model.StringItemList = list(sorted(values))
        return

    def unselect(self):
        self.obj.selectItem(self.value, False)
        return

    def select(self, pos=0):
        if isinstance(pos, str):
            self.obj.selectItem(pos, True)
        else:
            self.obj.selectItemPos(pos, True)
        return

    def clear(self):
        self.model.removeAllItems()
        return

    def _set_image_url(self, image):
        if exists_path(image):
            return _path_url(image)

        if not ID_EXTENSION:
            return ''

        path = get_path_extension(ID_EXTENSION)
        path = join(path, DIR['images'], image)
        return _path_url(path)

    def insert(self, value, path='', pos=-1, show=True):
        if pos < 0:
            pos = self.count
        if path:
            self.model.insertItem(pos, value, self._set_image_url(path))
        else:
            self.model.insertItemText(pos, value)
        if show:
            self.select(pos)
        return


class UnoGrid(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)
        self._gdm = self._model.GridDataModel
        # ~ self._data = []
        self._columns = {}
        # ~ self._format_columns = ()

    def __getitem__(self, index):
        value = self._gdm.getCellData(index[0], index[1])
        return value

    @property
    def type(self):
        return 'grid'

    def _format_cols(self):
        rows = tuple(tuple(
            self._format_columns[i].format(r) for i, r in enumerate(row)) for row in self._data
        )
        return rows

    # ~ @property
    # ~ def format_columns(self):
        # ~ return self._format_columns
    # ~ @format_columns.setter
    # ~ def format_columns(self, value):
        # ~ self._format_columns = value

    @property
    def value(self):
        return self[self.column, self.row]

    @property
    def data(self):
        return self._data
    @data.setter
    def data(self, values):
        # ~ self._data = values
        self.clear()
        headings = tuple(range(1, len(values) + 1))
        self._gdm.addRows(headings, values)
        # ~ rows = range(grid_dm.RowCount)
        # ~ colors = [COLORS['GRAY'] if r % 2 else COLORS['WHITE'] for r in rows]
        # ~ grid.Model.RowBackgroundColors = tuple(colors)
        return

    @property
    def row(self):
        return self.obj.CurrentRow

    @property
    def rows(self):
        return self._gdm.RowCount

    @property
    def column(self):
        return self.obj.CurrentColumn

    @property
    def columns(self):
        return self._gdm.ColumnCount

    def set_cell_tooltip(self, col, row, value):
        self._gdm.updateCellToolTip(col, row, value)
        return

    def get_cell_tooltip(self, col, row):
        value = self._gdm.getCellToolTip(col, row)
        return value

    def _validate_column(self, data):
        row = []
        for i, d in enumerate(data):
            if i in self._columns:
                if 'image' in self._columns[i]:
                    row.append(self._columns[i]['image'])
            else:
                row.append(d)
        return tuple(row)

    def clear(self):
        self._gdm.removeAllRows()
        return

    def add_row(self, data):
        # ~ self._data.append(data)
        data = self._validate_column(data)
        self._gdm.addRow(self.rows + 1, data)
        return

    def remove_row(self, row):
        self._gdm.removeRow(row)
        # ~ del self._data[row]
        self.update_row_heading()
        return

    def update_row_heading(self):
        for i in range(self.rows):
            self._gdm.updateRowHeading(i, i + 1)
        return

    def sort(self, column, asc=True):
        self._gdm.sortByColumn(column, asc)
        self.update_row_heading()
        return

    def set_column_image(self, column, path):
        gp = create_instance('com.sun.star.graphic.GraphicProvider')
        data = dict_to_property({'URL': _path_url(path)})
        image = gp.queryGraphic(data)
        if not column in self._columns:
            self._columns[column] = {}
        self._columns[column]['image'] = image
        return


class UnoRoadmap(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)
        self._options = ()

    @property
    def options(self):
        return self._options
    @options.setter
    def options(self, values):
        self._options = values
        for i, v in enumerate(values):
            opt = self.model.createInstance()
            opt.ID = i
            opt.Label = v
            self.model.insertByIndex(i, opt)
        return

    @property
    def enabled(self):
        return True
    @enabled.setter
    def enabled(self, value):
        for m in self.model:
            m.Enabled = value
        return

    def set_enabled(self, index, value):
        self.model.getByIndex(index).Enabled = value
        return


class UnoTree(UnoBaseObject):

    def __init__(self, obj, ):
        super().__init__(obj)
        self._tdm = None
        self._data = []

    @property
    def selection(self):
        return self.obj.Selection

    @property
    def root(self):
        if self._tdm is None:
            return ''
        return self._tdm.Root.DisplayValue

    @root.setter
    def root(self, value):
        self._add_data_model(value)

    def _add_data_model(self, name):
        tdm = create_instance('com.sun.star.awt.tree.MutableTreeDataModel')
        root = tdm.createNode(name, True)
        root.DataValue = 0
        tdm.setRoot(root)
        self.model.DataModel = tdm
        self._tdm = self.model.DataModel
        self._add_data()
        return

    @property
    def data(self):
        return self._data
    @data.setter
    def data(self, values):
        self._data = list(values)
        self._add_data()

    def _add_data(self):
        if not self.data:
            return

        parents = {}
        for node in self.data:
            parent = parents.get(node[1], self._tdm.Root)
            child = self._tdm.createNode(node[2], False)
            child.DataValue = node[0]
            parent.appendChild(child)
            parents[node[0]] = child
        self.obj.expandNode(self._tdm.Root)
        return


class UnoTab(UnoBaseObject):

    def __init__(self, obj):
        super().__init__(obj)
        self._events = None

    def __getitem__(self, index):
        return self.get_sheet(index)

    @property
    def current(self):
        return self.obj.getActiveTabID()
    @property
    def active(self):
        return self.current

    def get_sheet(self, id):
        if isinstance(id, int):
            sheet = self.obj.Controls[id-1]
        else:
            sheet = self.obj.getControl(id.lower())
        return sheet

    @property
    def sheets(self):
        return self._sheets
    @sheets.setter
    def sheets(self, values):
        i = len(self.obj.Controls)
        for title in values:
            i += 1
            sheet = self.model.createInstance('com.sun.star.awt.UnoPageModel')
            sheet.Title = title
            self.model.insertByName('sheet{}'.format(i), sheet)
        return

    def insert(self, title):
        id = len(self.obj.Controls) + 1
        sheet = self.model.createInstance('com.sun.star.awt.UnoPageModel')
        sheet.Title = title
        self.model.insertByName('sheet{}'.format(id), sheet)
        return id

    def remove(self, id):
        sheet = self.get_sheet(id)
        for control in sheet.getControls():
            sheet.Model.removeByName(control.Model.Name)
            sheet.removeControl(control)
        # ~ self._model.removeByName('page_{}'.format(ID))

        self.obj.removeTab(id)
        return

    def activate(self, id):
        self.obj.activateTab(id)
        return

    @property
    def events(self):
        return self._events
    @events.setter
    def events(self, controllers):
        self._events = controllers

    def _special_properties(self, tipo, properties):
        columns = properties.pop('Columns', ())
        if tipo == 'grid':
            properties['ColumnModel'] = _set_column_model(columns)
            if not 'Width' in properties:
                properties['Width'] = self.width
            if not 'Height' in properties:
                properties['Height'] = self.height
        elif tipo == 'button' and 'ImageURL' in properties:
            properties['ImageURL'] = self._set_image_url(properties['ImageURL'])
        elif tipo == 'roadmap':
            if not 'Height' in properties:
                properties['Height'] = self.height
            if 'Title' in properties:
                properties['Text'] = properties.pop('Title')
        elif tipo == 'pages':
            if not 'Width' in properties:
                properties['Width'] = self.width
            if not 'Height' in properties:
                properties['Height'] = self.height

        return properties

    def add_control(self, id, properties):
        tipo = properties.pop('Type').lower()
        root = properties.pop('Root', '')
        sheets = properties.pop('Sheets', ())
        properties = self._special_properties(tipo, properties)

        sheet = self.get_sheet(id)
        sheet_model = sheet.getModel()
        model = sheet_model.createInstance(get_control_model(tipo))
        set_properties(model, properties)
        name = properties['Name']
        sheet_model.insertByName(name, model)

        control = sheet.getControl(name)
        add_listeners(self.events, control, name)
        control = get_custom_class(tipo, control)

        if tipo == 'tree' and root:
            control.root = root
        elif tipo == 'pages' and sheets:
            control.sheets = sheets

        setattr(self, name, control)
        return


def get_custom_class(tipo, obj):
    classes = {
        'label': UnoLabel,
        'button': UnoButton,
        'text': UnoText,
        'listbox': UnoListBox,
        'grid': UnoGrid,
        'link': UnoLabelLink,
        'roadmap': UnoRoadmap,
        'tree': UnoTree,
        'tab': UnoTab,
        # ~ 'image': UnoImage,
        # ~ 'radio': UnoRadio,
        # ~ 'groupbox': UnoGroupBox,
        'formbutton': FormButton,
    }
    return classes[tipo](obj)


def get_control_model(control):
    services = {
        'label': 'com.sun.star.awt.UnoControlFixedTextModel',
        'link': 'com.sun.star.awt.UnoControlFixedHyperlinkModel',
        'text': 'com.sun.star.awt.UnoControlEditModel',
        'listbox': 'com.sun.star.awt.UnoControlListBoxModel',
        'button': 'com.sun.star.awt.UnoControlButtonModel',
        'roadmap': 'com.sun.star.awt.UnoControlRoadmapModel',
        'grid': 'com.sun.star.awt.grid.UnoControlGridModel',
        'tree': 'com.sun.star.awt.tree.TreeControlModel',
        'groupbox': 'com.sun.star.awt.UnoControlGroupBoxModel',
        'image': 'com.sun.star.awt.UnoControlImageControlModel',
        'radio': 'com.sun.star.awt.UnoControlRadioButtonModel',
        'tab': 'com.sun.star.awt.UnoMultiPageModel',
    }
    return services[control]


def add_listeners(events, control, name=''):
    listeners = {
        'addActionListener': EventsButton,
        'addMouseListener': EventsMouse,
        'addItemListener': EventsItem,
        'addFocusListener': EventsFocus,
        'addKeyListener': EventsKey,
        'addTabListener': EventsTab,
    }
    if hasattr(control, 'obj'):
        control = contro.obj
    # ~ debug(control.ImplementationName)
    is_grid = control.ImplementationName == 'stardiv.Toolkit.GridControl'
    is_link = control.ImplementationName == 'stardiv.Toolkit.UnoFixedHyperlinkControl'
    is_roadmap = control.ImplementationName == 'stardiv.Toolkit.UnoRoadmapControl'

    for key, value in listeners.items():
        if hasattr(control, key):
            if is_grid and key == 'addMouseListener':
                control.addMouseListener(EventsMouseGrid(events, name))
                continue
            if is_link and key == 'addMouseListener':
                control.addMouseListener(EventsMouseLink(events, name))
                continue
            if is_roadmap and key == 'addItemListener':
                control.addItemListener(EventsItemRoadmap(events, name))
                continue

            getattr(control, key)(listeners[key](events, name))

    if is_grid:
        controllers = EventsGrid(events, name)
        control.addSelectionListener(controllers)
        control.Model.GridDataModel.addGridDataListener(controllers)
    return


class WriterTable(ObjectBase):

    def __init__(self, obj):
        super().__init__(obj)

    def __getitem__(self, key):
        obj = super().__getitem__(key)
        return WriterTableRange(obj, key, self.name)

    @property
    def name(self):
        return self.obj.Name
    @name.setter
    def name(self, value):
        self.obj.Name = value


class WriterTableRange(ObjectBase):

    def __init__(self, obj, index, table_name):
        self._index = index
        self._table_name = table_name
        super().__init__(obj)
        self._is_cell = hasattr(self.obj, 'CellName')

    def __getitem__(self, key):
        obj = super().__getitem__(key)
        return WriterTableRange(obj, key, self._table_name)

    @property
    def value(self):
        return self.obj.String
    @value.setter
    def value(self, value):
        self.obj.String = value

    @property
    def data(self):
        return self.obj.getDataArray()
    @data.setter
    def data(self, values):
        if isinstance(values, list):
            values = tuple(values)
        self.obj.setDataArray(values)

    @property
    def rows(self):
        return len(self.data)

    @property
    def columns(self):
        return len(self.data[0])

    @property
    def name(self):
        if self._is_cell:
            name = '{}.{}'.format(self._table_name, self.obj.CellName)
        elif isinstance(self._index, str):
            name = '{}.{}'.format(self._table_name, self._index)
        else:
            c1 = self.obj[0,0].CellName
            c2 = self.obj[self.rows-1,self.columns-1].CellName
            name = '{}.{}:{}'.format(self._table_name, c1, c2)
        return name

    def get_cell(self, *index):
        return self[index]

    def get_column(self, index=0, start=1):
        return self[start:self.rows,index:index+1]

    def get_series(self):
        class Serie():
            pass
        series = []
        for i in range(self.columns):
            serie = Serie()
            serie.label = self.get_cell(0,i).name
            serie.data = self.get_column(i).data
            serie.values = self.get_column(i).name
            series.append(serie)
        return series


class ChartFormat(object):

    def __call__(self, obj):
        for k, v in self.__dict__.items():
            if hasattr(obj, k):
                setattr(obj, k, v)


class LOChart(object):
    BASE = 'com.sun.star.chart.{}Diagram'

    def __init__(self, obj, tipo=''):
        self._obj = obj
        self._type = tipo
        self._name = ''
        self._table = None
        self._data = ()
        self._data_series = ()
        self._cell = None
        self._cursor = None
        self._doc = None
        self._title = ChartFormat()
        self._subtitle = ChartFormat()
        self._legend = ChartFormat()
        self._xaxistitle = ChartFormat()
        self._yaxistitle = ChartFormat()
        self._xaxis = ChartFormat()
        self._yaxis = ChartFormat()
        self._xmaingrid = ChartFormat()
        self._ymaingrid = ChartFormat()
        self._xhelpgrid = ChartFormat()
        self._yhelpgrid = ChartFormat()
        self._area = ChartFormat()
        self._wall = ChartFormat()
        self._dim3d = False
        self._series = ()
        self._labels = ()
        return

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.insert()

    @property
    def obj(self):
        return self._obj
    @obj.setter
    def obj(self, value):
        self._obj = value

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, value):
        self._name = value

    @property
    def type(self):
        return self._type
    @type.setter
    def type(self, value):
        self._type = value

    @property
    def table(self):
        return self._table
    @table.setter
    def table(self, value):
        self._table = value

    @property
    def data(self):
        return self._data
    @data.setter
    def data(self, value):
        self._data = value

    @property
    def cell(self):
        return self._cell
    @cell.setter
    def cell(self, value):
        self._cell = value
        self.doc = value.doc

    @property
    def cursor(self):
        return self._cursor
    @cursor.setter
    def cursor(self, value):
        self._cursor = value

    @property
    def doc(self):
        return self._doc
    @doc.setter
    def doc(self, value):
        self._doc = value

    @property
    def width(self):
        return self._width
    @width.setter
    def width(self, value):
        self._width = value

    @property
    def height(self):
        return self._height
    @height.setter
    def height(self, value):
        self._height = value

    @property
    def title(self):
        return self._title

    @property
    def subtitle(self):
        return self._subtitle

    @property
    def legend(self):
        return self._legend

    @property
    def xaxistitle(self):
        return self._xaxistitle

    @property
    def yaxistitle(self):
        return self._yaxistitle

    @property
    def xaxis(self):
        return self._xaxis

    @property
    def yaxis(self):
        return self._yaxis

    @property
    def xmaingrid(self):
        return self._xmaingrid

    @property
    def ymaingrid(self):
        return self._ymaingrid

    @property
    def xhelpgrid(self):
        return self._xhelpgrid

    @property
    def yhelpgrid(self):
        return self._yhelpgrid

    @property
    def area(self):
        return self._area

    @property
    def wall(self):
        return self._wall

    @property
    def dim3d(self):
        return self._dim3d
    @dim3d.setter
    def dim3d(self, value):
        self._dim3d = value

    @property
    def series(self):
        return self._series
    @series.setter
    def series(self, value):
        self._series = value

    @property
    def data_series(self):
        return self._series
    @data_series.setter
    def data_series(self, value):
        self._data_series = value

    @property
    def labels(self):
        return self._labels
    @labels.setter
    def labels(self, value):
        self._labels = value

    def _add_series_writer(self, chart):
        dp = self.doc.create_instance('com.sun.star.chart2.data.DataProvider')
        chart.attachDataProvider(dp)
        chart_type = chart.getFirstDiagram().getCoordinateSystems()[0].getChartTypes()[0]
        self._data_series = self.table[self.data].get_series()
        series = [self._create_serie(dp, s) for s in self._data_series[1:]]
        chart_type.setDataSeries(tuple(series))
        chart_data = chart.getData()
        chart_data.ComplexRowDescriptions = self._data_series[0].data
        return

    def _get_series(self):
        rango = self._data_series
        class Serie():
            pass
        series = []
        for i in range(0, rango.columns, 2):
            serie = Serie()
            serie.label = rango[0, i+1].name
            serie.xvalues = rango.get_column(i).name
            serie.values = rango.get_column(i+1).name
            series.append(serie)
        return series

    def _add_series_calc(self, chart):
        dp = self.doc.create_instance('com.sun.star.chart2.data.DataProvider')
        chart.attachDataProvider(dp)
        chart_type = chart.getFirstDiagram().getCoordinateSystems()[0].getChartTypes()[0]
        series = self._get_series()
        series = [self._create_serie(dp, s) for s in series]
        chart_type.setDataSeries(tuple(series))
        return

    def _create_serie(self, dp, data):
        serie = create_instance('com.sun.star.chart2.DataSeries')
        rango = data.values
        is_x = hasattr(data, 'xvalues')
        if is_x:
            xrango = data.xvalues
        rango_label = data.label

        lds = create_instance('com.sun.star.chart2.data.LabeledDataSequence')
        values = self._create_data(dp, rango, 'values-y')
        lds.setValues(values)
        if data.label:
            label = self._create_data(dp, rango_label, '')
            lds.setLabel(label)

        xlds = ()
        if is_x:
            xlds = create_instance('com.sun.star.chart2.data.LabeledDataSequence')
            values = self._create_data(dp, xrango, 'values-x')
            xlds.setValues(values)

        if is_x:
            serie.setData((lds, xlds))
        else:
            serie.setData((lds,))

        return serie

    def _create_data(self, dp, rango, role):
        data = dp.createDataSequenceByRangeRepresentation(rango)
        if not data is None:
            data.Role = role
        return data

    def _from_calc(self):
        ps = self.cell.ps
        ps.Width = self.width
        ps.Height = self.height
        charts = self.cell.charts
        data = ()
        if self.data:
            data = (self.data.address,)
        charts.addNewByName(self.name, ps, data, True, True)
        self.obj = charts.getByName(self.name)
        chart = self.obj.getEmbeddedObject()
        chart.setDiagram(chart.createInstance(self.BASE.format(self.type)))
        if not self.data:
            self._add_series_calc(chart)
        return chart

    def _from_writer(self):
        obj = self.doc.create_instance('com.sun.star.text.TextEmbeddedObject')
        obj.setPropertyValue('CLSID', '12DCAE26-281F-416F-a234-c3086127382e')
        obj.Name = self.name
        obj.setSize(Size(self.width, self.height))
        self.doc.insert_content(self.cursor, obj)
        self.obj = obj
        chart = obj.getEmbeddedObject()
        tipo = self.type
        if self.type == 'Column':
            tipo = 'Bar'
            chart.Diagram.Vertical = True
        chart.setDiagram(chart.createInstance(self.BASE.format(tipo)))
        chart.DataSourceLabelsInFirstColumn = True
        if isinstance(self.data, str):
            self._add_series_writer(chart)
        else:
            chart_data = chart.getData()
            labels = [r[0] for r in self.data]
            data = [(r[1],) for r in self.data]
            chart_data.setData(data)
            chart_data.RowDescriptions = labels

        # ~ Bug
        if tipo == 'Pie':
            chart.setDiagram(chart.createInstance(self.BASE.format('Bar')))
            chart.setDiagram(chart.createInstance(self.BASE.format('Pie')))

        return chart

    def insert(self):
        if not self.cell is None:
            chart = self._from_calc()
        elif not self.cursor is None:
            chart = self._from_writer()

        diagram = chart.Diagram

        if self.type == 'Bar':
            diagram.Vertical = True

        if hasattr(self.title, 'String'):
            chart.HasMainTitle = True
            self.title(chart.Title)

        if hasattr(self.subtitle, 'String'):
            chart.HasSubTitle = True
            self.subtitle(chart.SubTitle)

        if self.legend.__dict__:
            chart.HasLegend = True
            self.legend(chart.Legend)

        if self.xaxistitle.__dict__:
            diagram.HasXAxisTitle = True
            self.xaxistitle(diagram.XAxisTitle)

        if self.yaxistitle.__dict__:
            diagram.HasYAxisTitle = True
            self.yaxistitle(diagram.YAxisTitle)

        if self.dim3d:
            diagram.Dim3D = True

        if self.series:
            data_series = chart.getFirstDiagram(
                ).getCoordinateSystems(
                )[0].getChartTypes()[0].DataSeries
            for i, serie in enumerate(data_series):
                for k, v in self.series[i].items():
                    if hasattr(serie, k):
                        setattr(serie, k, v)
        return self


def _set_column_model(columns):
    #~ https://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1awt_1_1grid_1_1XGridColumn.html
    column_model = create_instance('com.sun.star.awt.grid.DefaultGridColumnModel', True)
    for column in columns:
        grid_column = create_instance('com.sun.star.awt.grid.GridColumn', True)
        for k, v in column.items():
            setattr(grid_column, k, v)
        column_model.addColumn(grid_column)
    return column_model


def _set_image_url(image, id_extension=''):
    if exists_path(image):
        return _path_url(image)

    if not id_extension:
        return ''

    path = get_path_extension(id_extension)
    path = join(path, DIR['images'], image)
    return _path_url(path)


class LODialog(object):

    def __init__(self, **properties):
        self._obj = self._create(properties)
        self._init_values()

    def _init_values(self):
        self._model = self._obj.Model
        self._init_controls()
        self._events = None
        self._color_on_focus = -1
        self._id_extension = ''
        self._images = 'images'
        return

    def _create(self, properties):
        path = properties.pop('Path', '')
        if path:
            dp = create_instance('com.sun.star.awt.DialogProvider', True)
            return dp.createDialog(_path_url(path))

        if 'Location' in properties:
            location = properties.get('Location', 'application')
            library = properties.get('Library', 'Standard')
            if location == 'user':
                location = 'application'
            dp = create_instance('com.sun.star.awt.DialogProvider', True)
            path = 'vnd.sun.star.script:{}.{}?location={}'.format(
                library, properties['Name'], location)
            if location == 'document':
                uid = get_document().uid
                path = 'vnd.sun.star.tdoc:/{}/Dialogs/{}/{}.xml'.format(
                    uid, library, properties['Name'])
            return dp.createDialog(path)

        dlg = create_instance('com.sun.star.awt.UnoControlDialog', True)
        model = create_instance('com.sun.star.awt.UnoControlDialogModel', True)
        toolkit = create_instance('com.sun.star.awt.Toolkit', True)
        set_properties(model, properties)
        dlg.setModel(model)
        dlg.setVisible(False)
        dlg.createPeer(toolkit, None)

        return dlg

    def _get_type_control(self, name):
        types = {
            'stardiv.Toolkit.UnoFixedTextControl': 'label',
            'stardiv.Toolkit.UnoFixedHyperlinkControl': 'link',
            'stardiv.Toolkit.UnoEditControl': 'text',
            'stardiv.Toolkit.UnoButtonControl': 'button',
            'stardiv.Toolkit.UnoListBoxControl': 'listbox',
            'stardiv.Toolkit.UnoRoadmapControl': 'roadmap',
            'stardiv.Toolkit.UnoMultiPageControl': 'pages',
        }
        return types[name]

    def _init_controls(self):
        for control in self.obj.getControls():
            tipo = self._get_type_control(control.ImplementationName)
            name = control.Model.Name
            control = get_custom_class(tipo, control)
            setattr(self, name, control)
        return

    @property
    def obj(self):
        return self._obj

    @property
    def model(self):
        return self._model

    @property
    def id_extension(self):
        return self._id_extension
    @id_extension.setter
    def id_extension(self, value):
        global ID_EXTENSION
        ID_EXTENSION = value
        self._id_extension = value

    @property
    def images(self):
        return self._images
    @images.setter
    def images(self, value):
        self._images = value

    @property
    def height(self):
        return self.model.Height
    @height.setter
    def height(self, value):
        self.model.Height = value

    @property
    def width(self):
        return self.model.Width
    @width.setter
    def width(self, value):
        self.model.Width = value

    @property
    def color_on_focus(self):
        return self._color_on_focus
    @color_on_focus.setter
    def color_on_focus(self, value):
        global COLOR_ON_FOCUS
        COLOR_ON_FOCUS = get_color(value)
        self._color_on_focus = COLOR_ON_FOCUS

    @property
    def step(self):
        return self.model.Step
    @step.setter
    def step(self, value):
        self.model.Step = value

    @property
    def events(self):
        return self._events
    @events.setter
    def events(self, controllers):
        self._events = controllers
        self._connect_listeners()

    def _connect_listeners(self):
        for control in self.obj.getControls():
            add_listeners(self._events, control, control.Model.Name)
        return

    def open(self):
        return self.obj.execute()

    def close(self, value=0):
        return self.obj.endDialog(value)

    def _get_control_model(self, control):
        services = {
            'label': 'com.sun.star.awt.UnoControlFixedTextModel',
            'link': 'com.sun.star.awt.UnoControlFixedHyperlinkModel',
            'text': 'com.sun.star.awt.UnoControlEditModel',
            'listbox': 'com.sun.star.awt.UnoControlListBoxModel',
            'button': 'com.sun.star.awt.UnoControlButtonModel',
            'roadmap': 'com.sun.star.awt.UnoControlRoadmapModel',
            'grid': 'com.sun.star.awt.grid.UnoControlGridModel',
            'tree': 'com.sun.star.awt.tree.TreeControlModel',
            'groupbox': 'com.sun.star.awt.UnoControlGroupBoxModel',
            'image': 'com.sun.star.awt.UnoControlImageControlModel',
            'radio': 'com.sun.star.awt.UnoControlRadioButtonModel',
            'pages': 'com.sun.star.awt.UnoMultiPageModel',
        }
        return services[control]

    def _set_column_model(self, columns):
        #~ https://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1awt_1_1grid_1_1XGridColumn.html
        column_model = create_instance('com.sun.star.awt.grid.DefaultGridColumnModel', True)
        for column in columns:
            grid_column = create_instance('com.sun.star.awt.grid.GridColumn', True)
            for k, v in column.items():
                setattr(grid_column, k, v)
            column_model.addColumn(grid_column)
        return column_model

    def _set_image_url(self, image):
        if exists_path(image):
            return _path_url(image)

        if not self.id_extension:
            return ''

        path = get_path_extension(self.id_extension)
        path = join(path, self.images, image)
        return _path_url(path)

    def _special_properties(self, tipo, properties):
        columns = properties.pop('Columns', ())
        if tipo == 'grid':
            properties['ColumnModel'] = self._set_column_model(columns)
        elif tipo == 'button' and 'ImageURL' in properties:
            properties['ImageURL'] = self._set_image_url(properties['ImageURL'])
        elif tipo == 'roadmap':
            if not 'Height' in properties:
                properties['Height'] = self.height
            if 'Title' in properties:
                properties['Text'] = properties.pop('Title')
        elif tipo == 'tab':
            if not 'Width' in properties:
                properties['Width'] = self.width
            if not 'Height' in properties:
                properties['Height'] = self.height

        return properties

    def add_control(self, properties):
        tipo = properties.pop('Type').lower()
        root = properties.pop('Root', '')
        sheets = properties.pop('Sheets', ())

        properties = self._special_properties(tipo, properties)
        model = self.model.createInstance(self._get_control_model(tipo))
        set_properties(model, properties)
        name = properties['Name']
        self.model.insertByName(name, model)
        control = self.obj.getControl(name)
        add_listeners(self.events, control, name)
        control = get_custom_class(tipo, control)

        if tipo == 'tree' and root:
            control.root = root
        elif tipo == 'pages' and sheets:
            control.sheets = sheets
            control.events = self.events

        setattr(self, name, control)
        return

    def center(self, control, x=0, y=0):
        w = self.width
        h = self.height

        if isinstance(control, tuple):
            wt = SEPARATION * -1
            for c in control:
                wt += c.width + SEPARATION
            x = w / 2 - wt / 2
            for c in control:
                c.x = x
                x = c.x + c.width + SEPARATION
            return

        if x < 0:
            x = w + x - control.width
        elif x == 0:
            x = w / 2 - control.width / 2
        if y < 0:
            y = h + y - control.height
        elif y == 0:
            y = h / 2 - control.height / 2
        control.x = x
        control.y = y
        return


class LOWindow(object):
    EMPTY = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE dlg:window PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "dialog.dtd">
<dlg:window xmlns:dlg="http://openoffice.org/2000/dialog" xmlns:script="http://openoffice.org/2000/script" dlg:id="empty" dlg:left="0" dlg:top="0" dlg:width="0" dlg:height="0" dlg:closeable="true" dlg:moveable="true" dlg:withtitlebar="false"/>"""

    def __init__(self, **kwargs):
        self._events = None
        self._menu = None
        self._container = None
        self._id_extension = ''
        self._obj = self._create(kwargs)

    @property
    def id_extension(self):
        return self._id_extension
    @id_extension.setter
    def id_extension(self, value):
        global ID_EXTENSION
        ID_EXTENSION = value
        self._id_extension = value

    def _create(self, properties):
        ps = (
            properties.get('X', 0),
            properties.get('Y', 0),
            properties.get('Width', 500),
            properties.get('Height', 500),
        )
        self._title = properties.get('Title', TITLE)
        self._create_frame(ps)
        self._create_container(ps)
        self._create_subcontainer(ps)
        # ~ self._create_splitter(ps)
        return

    def _create_frame(self, ps):
        service = 'com.sun.star.frame.TaskCreator'
        tc = create_instance(service, True)
        self._frame = tc.createInstanceWithArguments((
            NamedValue('FrameName', 'EasyMacroWin'),
            NamedValue('PosSize', Rectangle(*ps)),
            ))
        self._window = self._frame.getContainerWindow()
        self._toolkit = self._window.getToolkit()
        desktop = get_desktop()
        self._frame.setCreator(desktop)
        desktop.getFrames().append(self._frame)
        self._frame.Title = self._title
        return

    def _create_container(self, ps):
        # ~ toolkit = self._window.getToolkit()
        service = 'com.sun.star.awt.UnoControlContainer'
        self._container = create_instance(service, True)
        service = 'com.sun.star.awt.UnoControlContainerModel'
        model = create_instance(service, True)
        model.BackgroundColor = get_color(225, 225, 225)
        self._container.setModel(model)
        self._container.createPeer(self._toolkit, self._window)
        self._container.setPosSize(*ps, POSSIZE)
        self._frame.setComponent(self._container, None)
        return

    def _create_subcontainer(self, ps):
        service = 'com.sun.star.awt.ContainerWindowProvider'
        cwp = create_instance(service, True)
        with get_temp_file() as f:
            f.write(self.EMPTY)
            f.flush()
            subcont = cwp.createContainerWindow(
                _path_url(f.name), '', self._container.getPeer(), None)

        # ~ service = 'com.sun.star.awt.UnoControlDialog'
        # ~ subcont2 = create_instance(service, True)
        # ~ service = 'com.sun.star.awt.UnoControlDialogModel'
        # ~ model = create_instance(service, True)
        # ~ service = 'com.sun.star.awt.UnoControlContainer'
        # ~ context = create_instance(service, True)
        # ~ subcont2.setModel(model)
        # ~ subcont2.setContext(context)
        # ~ subcont2.createPeer(self._toolkit, self._container.getPeer())

        subcont.setPosSize(0, 0, 500, 500, POSSIZE)
        subcont.setVisible(True)
        self._container.addControl('subcont', subcont)
        self._subcont = subcont
        return

    def _get_base_control(self, tipo):
        services = {
            'label': 'com.sun.star.awt.UnoControlFixedText',
            'button': 'com.sun.star.awt.UnoControlButton',
            'text': 'com.sun.star.awt.UnoControlEdit',
            'listbox': 'com.sun.star.awt.UnoControlListBox',
            'link': 'com.sun.star.awt.UnoControlFixedHyperlink',
            'roadmap': 'com.sun.star.awt.UnoControlRoadmap',
            'image': 'com.sun.star.awt.UnoControlImageControl',
            'groupbox': 'com.sun.star.awt.UnoControlGroupBox',
            'radio': 'com.sun.star.awt.UnoControlRadioButton',
            'tree': 'com.sun.star.awt.tree.TreeControl',
            'grid': 'com.sun.star.awt.grid.UnoControlGrid',
            'tab': 'com.sun.star.awt.tab.UnoControlTabPage',
        }
        return services[tipo]

    def _special_properties(self, tipo, properties):
        columns = properties.pop('Columns', ())
        if tipo == 'grid':
            properties['ColumnModel'] = self._set_column_model(columns)
        elif tipo == 'button' and 'ImageURL' in properties:
            properties['ImageURL'] = _set_image_url(
                properties['ImageURL'], self.id_extension)
        elif tipo == 'roadmap':
            if not 'Height' in properties:
                properties['Height'] = self.height
            if 'Title' in properties:
                properties['Text'] = properties.pop('Title')
        elif tipo == 'tab':
            if not 'Width' in properties:
                properties['Width'] = self.width - 20
            if not 'Height' in properties:
                properties['Height'] = self.height - 20

        return properties

    def add_control(self, properties):
        tipo = properties.pop('Type').lower()
        root = properties.pop('Root', '')
        sheets = properties.pop('Sheets', ())

        properties = self._special_properties(tipo, properties)
        model = self._subcont.Model.createInstance(get_control_model(tipo))
        set_properties(model, properties)
        name = properties['Name']
        self._subcont.Model.insertByName(name, model)
        control = self._subcont.getControl(name)
        add_listeners(self.events, control, name)
        control = get_custom_class(tipo, control)

        if tipo == 'tree' and root:
            control.root = root
        elif tipo == 'tab' and sheets:
            control.sheets = sheets
            control.events = self.events

        setattr(self, name, control)
        return

    def _create_popupmenu(self, menus):
        menu = create_instance('com.sun.star.awt.PopupMenu', True)
        for i, m in enumerate(menus):
            label = m['label']
            cmd = m.get('event', '')
            if not cmd:
                cmd = label.lower().replace(' ', '_')
            if label == '-':
                menu.insertSeparator(i)
            else:
                menu.insertItem(i, label, m.get('style', 0), i)
                menu.setCommand(i, cmd)
                # ~ menu.setItemImage(i, path?, True)
        menu.addMenuListener(EventsMenu(self.events))
        return menu

    def _create_menu(self, menus):
        #~ https://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1awt_1_1XMenu.html
        #~ nItemId  specifies the ID of the menu item to be inserted.
        #~ aText    specifies the label of the menu item.
        #~ nItemStyle   0 = Standard, CHECKABLE = 1, RADIOCHECK = 2, AUTOCHECK = 4
        #~ nItemPos specifies the position where the menu item will be inserted.
        self._menu = create_instance('com.sun.star.awt.MenuBar', True)
        for i, m in enumerate(menus):
            self._menu.insertItem(i, m['label'], m.get('style', 0), i)
            cmd = m['label'].lower().replace(' ', '_')
            self._menu.setCommand(i, cmd)
            submenu = self._create_popupmenu(m['submenu'])
            self._menu.setPopupMenu(i, submenu)

        self._window.setMenuBar(self._menu)
        return

    def add_menu(self, menus):
        self._create_menu(menus)
        return

    def _add_listeners(self, control=None):
        if self.events is None:
            return
        controller = EventsWindow(self)
        self._window.addTopWindowListener(controller)
        self._window.addWindowListener(controller)
        self._container.addKeyListener(EventsKeyWindow(self))
        return

    @property
    def name(self):
        return self._title.lower().replace(' ', '_')

    @property
    def events(self):
        return self._events
    @events.setter
    def events(self, value):
        self._events = value
        self._add_listeners()

    @property
    def width(self):
        return self._container.Size.Width

    @property
    def height(self):
        return self._container.Size.Height

    def open(self):
        self._window.setVisible(True)
        return

    def close(self):
        self._window.setMenuBar(None)
        self._window.dispose()
        self._frame.close(True)
        return


# ~ Python >= 3.7
# ~ def __getattr__(name):


def _get_class_doc(obj):
    classes = {
        'calc': LOCalc,
        'writer': LOWriter,
        'base': LOBase,
        'impress': LOImpress,
        'draw': LODraw,
        'math': LOMath,
        'basic': LOBasicIde,
    }
    type_doc = get_type_doc(obj)
    return classes[type_doc](obj)


# ~ Export ok
def get_document(title=''):
    doc = None
    desktop = get_desktop()
    if not title:
        doc = _get_class_doc(desktop.getCurrentComponent())
        return doc

    for d in desktop.getComponents():
        if hasattr(d, 'Title') and d.Title == title:
            doc = d
            break

    if doc is None:
        return

    return _get_class_doc(doc)


def get_documents(custom=True):
    docs = []
    desktop = get_desktop()
    for doc in desktop.getComponents():
        if custom:
            docs.append(_get_class_doc(doc))
        else:
            docs.append(doc)
    return docs


def get_selection():
    return get_document().selection


def get_cell(*args):
    if args:
        index = args
        if len(index) == 1:
            index = args[0]
        cell = get_document().get_cell(index)
    else:
        cell = get_selection().first
    return cell


def active_cell():
    return get_cell()


def create_dialog(properties):
    return LODialog(**properties)


def create_window(kwargs):
    return LOWindow(**kwargs)


# ~ Export ok
def get_config_path(name='Work'):
    """
        Return de path name in config
        http://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1util_1_1XPathSettings.html
    """
    path = create_instance('com.sun.star.util.PathSettings')
    return _path_system(getattr(path, name))


def get_path_python():
    path = get_config_path('Module')
    return join(path, PYTHON)


# ~ Export ok
def get_file(init_dir='', multiple=False, filters=()):
    """
        init_folder: folder default open
        multiple: True for multiple selected
        filters: Example
        (
            ('XML', '*.xml'),
            ('TXT', '*.txt'),
        )
    """
    if not init_dir:
        init_dir = get_config_path()
    init_dir = _path_url(init_dir)
    file_picker = create_instance('com.sun.star.ui.dialogs.FilePicker')
    file_picker.setTitle(_('Select file'))
    file_picker.setDisplayDirectory(init_dir)
    file_picker.setMultiSelectionMode(multiple)

    path = ''
    if filters:
        file_picker.setCurrentFilter(filters[0][0])
        for f in filters:
            file_picker.appendFilter(f[0], f[1])

    if file_picker.execute():
        path = _path_system(file_picker.getSelectedFiles()[0])
        if multiple:
            path = [_path_system(f) for f in file_picker.getSelectedFiles()]

    return path


# ~ Export ok
def get_path(init_dir='', filters=()):
    """
        Options: http://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1ui_1_1dialogs_1_1TemplateDescription.html
        filters: Example
        (
            ('XML', '*.xml'),
            ('TXT', '*.txt'),
        )
    """
    if not init_dir:
        init_dir = get_config_path()
    init_dir = _path_url(init_dir)
    file_picker = create_instance('com.sun.star.ui.dialogs.FilePicker')
    file_picker.setTitle(_('Select file'))
    file_picker.setDisplayDirectory(init_dir)
    file_picker.initialize((2,))
    if filters:
        file_picker.setCurrentFilter(filters[0][0])
        for f in filters:
            file_picker.appendFilter(f[0], f[1])

    path = ''
    if file_picker.execute():
        path =  _path_system(file_picker.getSelectedFiles()[0])
    return path


# ~ Export ok
def get_dir(init_dir=''):
    folder_picker = create_instance('com.sun.star.ui.dialogs.FolderPicker')
    if not init_dir:
        init_dir = get_config_path()
    init_dir = _path_url(init_dir)
    folder_picker.setDisplayDirectory(init_dir)

    path = ''
    if folder_picker.execute():
        path = _path_system(folder_picker.getDirectory())
    return path


# ~ Export ok
def get_info_path(path):
    path, filename = os.path.split(path)
    name, extension = os.path.splitext(filename)
    return (path, filename, name, extension)


# ~ Export ok
def read_file(path, mode='r', array=False):
    data = ''
    with open(path, mode) as f:
        if array:
            data = tuple(f.read().splitlines())
        else:
            data = f.read()
    return data


# ~ Export ok
def save_file(path, mode='w', data=None):
    with open(path, mode) as f:
        f.write(data)
    return


# ~ Export ok
def to_json(path, data):
    with open(path, 'w') as f:
        f.write(json.dumps(data, indent=4, sort_keys=True))
    return


# ~ Export ok
def from_json(path):
    with open(path) as f:
        data = json.loads(f.read())
    return data


# ~ Export ok
def json_dumps(data):
    return json.dumps(data, indent=4, sort_keys=True)


# ~ Export ok
def json_loads(data):
    return json.loads(data)


def get_path_extension(id):
    path = ''
    pip = CTX.getValueByName('/singletons/com.sun.star.deployment.PackageInformationProvider')
    try:
        path = _path_system(pip.getPackageLocation(id))
    except Exception as e:
        error(e)
    return path


def get_home():
    return Path.home()


# ~ Export ok
def inputbox(message, default='', title=TITLE, echochar=''):

    class ControllersInput(object):

        def __init__(self, dlg):
            self.d = dlg

        def cmd_ok_action(self, event):
            self.d.close(1)
            return

    args = {
        'Title': title,
        'Width': 200,
        'Height': 80,
    }
    dlg = LODialog(**args)
    dlg.events = ControllersInput(dlg)

    args = {
        'Type': 'Label',
        'Name': 'lbl_msg',
        'Label': message,
        'Width': 140,
        'Height': 50,
        'X': 5,
        'Y': 5,
        'MultiLine': True,
        'Border': 1,
    }
    dlg.add_control(args)

    args = {
        'Type': 'Text',
        'Name': 'txt_value',
        'Text': default,
        'Width': 190,
        'Height': 15,
    }
    if echochar:
        args['EchoChar'] = ord(echochar[0])
    dlg.add_control(args)
    dlg.txt_value.move(dlg.lbl_msg)

    args = {
        'Type': 'button',
        'Name': 'cmd_ok',
        'Label': _('OK'),
        'Width': 40,
        'Height': 15,
        'DefaultButton': True,
        'PushButtonType': 1,
    }
    dlg.add_control(args)
    dlg.cmd_ok.move(dlg.lbl_msg, 10, 0)

    args = {
        'Type': 'button',
        'Name': 'cmd_cancel',
        'Label': _('Cancel'),
        'Width': 40,
        'Height': 15,
        'PushButtonType': 2,
    }
    dlg.add_control(args)
    dlg.cmd_cancel.move(dlg.cmd_ok)

    if dlg.open():
        return dlg.txt_value.value

    return ''


# ~ Export ok
def new_doc(type_doc=CALC, **kwargs):
    path = 'private:factory/s{}'.format(type_doc)
    opt = dict_to_property(kwargs)
    doc = get_desktop().loadComponentFromURL(path, '_default', 0, opt)
    return _get_class_doc(doc)


# ~ Export ok
def new_db(path, name=''):
    p, fn, n, e = get_info_path(path)
    if not name:
        name = n
    return LOBase(name, path)


# ~ Todo
def exists_db(name):
    dbc = create_instance('com.sun.star.sdb.DatabaseContext')
    return dbc.hasRegisteredDatabase(name)


# ~ Todo
def register_db(name, path):
    dbc = create_instance('com.sun.star.sdb.DatabaseContext')
    dbc.registerDatabaseLocation(name, _path_url(path))
    return


# ~ Todo
def get_db(name):
    return LOBase(name)


# ~ Export ok
def open_doc(path, **kwargs):
    """ Open document in path
        Usually options:
            Hidden: True or False
            AsTemplate: True or False
            ReadOnly: True or False
            Password: super_secret
            MacroExecutionMode: 4 = Activate macros
            Preview: True or False

        http://api.libreoffice.org/docs/idl/ref/interfacecom_1_1sun_1_1star_1_1frame_1_1XComponentLoader.html
        http://api.libreoffice.org/docs/idl/ref/servicecom_1_1sun_1_1star_1_1document_1_1MediaDescriptor.html
    """
    path = _path_url(path)
    opt = dict_to_property(kwargs)
    doc = get_desktop().loadComponentFromURL(path, '_default', 0, opt)
    if doc is None:
        return

    return _get_class_doc(doc)


# ~ Export ok
def open_file(path):
    if IS_WIN:
        os.startfile(path)
    else:
        pid = subprocess.Popen(['xdg-open', path]).pid
    return


# ~ Export ok
def join(*paths):
    return os.path.join(*paths)


# ~ Export ok
def is_dir(path):
    return Path(path).is_dir()


# ~ Export ok
def is_file(path):
    return Path(path).is_file()


# ~ Export ok
def get_file_size(path):
    return Path(path).stat().st_size


# ~ Export ok
def is_created(path):
    return is_file(path) and bool(get_file_size(path))


# ~ Export ok
def replace_ext(path, extension):
    path, _, name, _ = get_info_path(path)
    return '{}/{}.{}'.format(path, name, extension)


# ~ Export ok
def zip_content(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
    return names


def popen(command, stdin=None):
    try:
        proc = subprocess.Popen(shlex.split(command), shell=IS_WIN,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in proc.stdout:
            yield line.decode().rstrip()
    except Exception as e:
        error(e)
        yield (e.errno, e.strerror)


def url_open(url, options={}, verify=True, json=False):
    data = ''
    err = ''
    req = Request(url)
    try:
        if verify:
            response = urlopen(req)
        else:
            context = ssl._create_unverified_context()
            response = urlopen(req, context=context)
    except HTTPError as e:
        error(e)
        err = str(e)
    except URLError as e:
        error(e.reason)
        err = str(e.reason)
    else:
        if json:
            data = json_loads(response.read())
        else:
            data = response.read()

    return data, err


def run(command, wait=False):
    try:
        if wait:
            result = subprocess.check_output(command, shell=True)
        else:
            p = subprocess.Popen(shlex.split(command), stdin=None,
                stdout=None, stderr=None, close_fds=True)
            result, er = p.communicate()
    except subprocess.CalledProcessError as e:
        msg = ("run [ERROR]: output = %s, error code = %s\n"
            % (e.output, e.returncode))
        error(msg)
        return False

    if result is None:
        return True

    return result.decode()


def _zippwd(source, target, pwd):
    if IS_WIN:
        return False
    if not exists_app('zip'):
        return False

    cmd = 'zip'
    opt = '-j '
    args = "{} --password {} ".format(cmd, pwd)

    if isinstance(source, (tuple, list)):
        if not target:
            return False
        args += opt + target + ' ' + ' '.join(source)
    else:
        if is_file(source) and not target:
            target = replace_ext(source, 'zip')
        elif is_dir(source) and not target:
            target = join(PurePath(source).parent,
                '{}.zip'.format(PurePath(source).name))
            opt = '-r '
        args += opt + target + ' ' + source

    result = run(args, True)
    if not result:
        return False

    return is_created(target)


# ~ Export ok
def zip(source, target='', mode='w', pwd=''):
    if pwd:
        return _zippwd(source, target, pwd)

    if isinstance(source, (tuple, list)):
        if not target:
            return False

        with zipfile.ZipFile(target, mode, compression=zipfile.ZIP_DEFLATED) as z:
            for path in source:
                _, name, _, _ = get_info_path(path)
                z.write(path, name)

        return is_created(target)

    if is_file(source):
        if not target:
            target = replace_ext(source, 'zip')
        z = zipfile.ZipFile(target, mode, compression=zipfile.ZIP_DEFLATED)
        _, name, _, _ = get_info_path(source)
        z.write(source, name)
        z.close()
        return is_created(target)

    if not target:
        target = join(
            PurePath(source).parent,
            '{}.zip'.format(PurePath(source).name))
    z = zipfile.ZipFile(target, mode, compression=zipfile.ZIP_DEFLATED)
    root_len = len(os.path.abspath(source))
    for root, dirs, files in os.walk(source):
        relative = os.path.abspath(root)[root_len:]
        for f in files:
            fullpath = join(root, f)
            file_name = join(relative, f)
            z.write(fullpath, file_name)
    z.close()

    return is_created(target)


# ~ Export ok
def unzip(source, path='', members=None, pwd=None):
    if not path:
        path, _, _, _ = get_info_path(source)
    with zipfile.ZipFile(source) as z:
        if not pwd is None:
            pwd = pwd.encode()
        if isinstance(members, str):
            members = (members,)
        z.extractall(path, members=members, pwd=pwd)
    return True


# ~ Export ok
def merge_zip(target, zips):
    try:
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as t:
            for path in zips:
                with zipfile.ZipFile(path, compression=zipfile.ZIP_DEFLATED) as s:
                    for name in s.namelist():
                        t.writestr(name, s.open(name).read())
    except Exception as e:
        error(e)
        return False

    return True


# ~ Export ok
def kill(path):
    p = Path(path)
    try:
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(path)
    except OSError as e:
        log.error(e)
    return


def get_size_screen():
    if IS_WIN:
        user32 = ctypes.windll.user32
        res = '{}x{}'.format(user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
    else:
        args = 'xrandr | grep "*" | cut -d " " -f4'
        res = run(args, True)
    return res.strip()


def get_clipboard():
    df = None
    text = ''
    sc = create_instance('com.sun.star.datatransfer.clipboard.SystemClipboard')
    transferable = sc.getContents()
    data = transferable.getTransferDataFlavors()
    for df in data:
        if df.MimeType == CLIPBOARD_FORMAT_TEXT:
            break
    if df:
        text = transferable.getTransferData(df)
    return text


class TextTransferable(unohelper.Base, XTransferable):
    """Keep clipboard data and provide them."""

    def __init__(self, text):
        df = DataFlavor()
        df.MimeType = CLIPBOARD_FORMAT_TEXT
        df.HumanPresentableName = "encoded text utf-16"
        self.flavors = [df]
        self.data = [text]

    def getTransferData(self, flavor):
        if not flavor:
            return
        for i, f in enumerate(self.flavors):
            if flavor.MimeType == f.MimeType:
                return self.data[i]
        return

    def getTransferDataFlavors(self):
        return tuple(self.flavors)

    def isDataFlavorSupported(self, flavor):
        if not flavor:
            return False
        mtype = flavor.MimeType
        for f in self.flavors:
            if mtype == f.MimeType:
                return True
        return False


# ~ Export ok
def set_clipboard(value):
    ts = TextTransferable(value)
    sc = create_instance('com.sun.star.datatransfer.clipboard.SystemClipboard')
    sc.setContents(ts, None)
    return


# ~ Export ok
def copy():
    call_dispatch('.uno:Copy')
    return


# ~ Export ok
def get_epoch():
    n = now()
    return int(time.mktime(n.timetuple()))


# ~ Export ok
def file_copy(source, target='', name=''):
    p, f, n, e = get_info_path(source)
    if target:
        p = target
    if name:
        e = ''
        n = name
    path_new = join(p, '{}{}'.format(n, e))
    shutil.copy(source, path_new)
    return path_new


def get_path_content(path, filters=''):
    paths = []
    if filters in ('*', '*.*'):
        filters = ''
    for folder, _, files in os.walk(path):
        if filters:
            pattern = re.compile(r'\.(?:{})$'.format(filters), re.IGNORECASE)
            paths += [join(folder, f) for f in files if pattern.search(f)]
        else:
            paths += files
    return paths


def _get_menu(type_doc, name_menu):
    instance = 'com.sun.star.ui.ModuleUIConfigurationManagerSupplier'
    service = TYPE_DOC[type_doc]
    manager = create_instance(instance, True)
    ui = manager.getUIConfigurationManager(service)
    menus = ui.getSettings(NODE_MENUBAR, True)
    command = MENUS_APP[type_doc][name_menu]
    for menu in menus:
        data = property_to_dict(menu)
        if data.get('CommandURL', '') == command:
            idc = data.get('ItemDescriptorContainer', None)
            return ui, menus, idc
    return None, None, None


def _get_index_menu(menu, command):
    for i, m in enumerate(menu):
        data = property_to_dict(m)
        cmd = data.get('CommandURL', '')
        if cmd == command:
            return i
        # ~ submenu = data.get('ItemDescriptorContainer', None)
        # ~ if not submenu is None:
            # ~ get_index_menu(submenu, command, count + 1)
    return 0


def _store_menu(ui, menus, menu, index, data=(), remove=False):
    if remove:
        uno.invoke(menu, 'removeByIndex', (index,))
    else:
        properties = dict_to_property(data, True)
        uno.invoke(menu, 'insertByIndex', (index + 1, properties))
    ui.replaceSettings(NODE_MENUBAR, menus)
    ui.store()
    return


def insert_menu(type_doc, name_menu, **kwargs):
    ui, menus, menu = _get_menu(type_doc, name_menu.lower())
    if menu is None:
        return 0

    label = kwargs.get('Label', '-')
    separator = False
    if label == '-':
        separator = True
    command = kwargs.get('CommandURL', '')
    index = kwargs.get('Index', 0)
    if not index:
        index = _get_index_menu(menu, kwargs['After'])
    if separator:
        data = {'Type': 1}
        _store_menu(ui, menus, menu, index, data)
        return index + 1

    index_menu = _get_index_menu(menu, command)
    if index_menu:
        msg = 'Exists: %s' % command
        debug(msg)
        return 0

    sub_menu = kwargs.get('Submenu', ())
    idc = None
    if sub_menu:
        idc = ui.createSettings()

    data = {
        'CommandURL': command,
        'Label': label,
        'Style': 0,
        'Type': 0,
        'ItemDescriptorContainer': idc
    }
    _store_menu(ui, menus, menu, index, data)
    if sub_menu:
        _add_sub_menus(ui, menus, idc, sub_menu)
    return True


def _add_sub_menus(ui, menus, menu, sub_menu):
    for i, sm in enumerate(sub_menu):
        submenu = sm.pop('Submenu', ())
        sm['Type'] = 0
        if submenu:
            idc = ui.createSettings()
            sm['ItemDescriptorContainer'] = idc
        if sm['Label'] == '-':
            sm = {'Type': 1}
        _store_menu(ui, menus, menu, i - 1, sm)
        if submenu:
            _add_sub_menus(ui, menus, idc, submenu)
    return


def remove_menu(type_doc, name_menu, command):
    ui, menus, menu = _get_menu(type_doc, name_menu.lower())
    if menu is None:
        return False

    index = _get_index_menu(menu, command)
    if not index:
        debug('Not exists: %s' % command)
        return False

    _store_menu(ui, menus, menu, index, remove=True)
    return True


def _get_app_submenus(menus, count=0):
    for i, menu in enumerate(menus):
        data = property_to_dict(menu)
        cmd = data.get('CommandURL', '')
        msg = '  ' * count + '├─' + cmd
        debug(msg)
        submenu = data.get('ItemDescriptorContainer', None)
        if not submenu is None:
            _get_app_submenus(submenu, count + 1)
    return


def get_app_menus(name_app, index=-1):
    instance = 'com.sun.star.ui.ModuleUIConfigurationManagerSupplier'
    service = TYPE_DOC[name_app]
    manager = create_instance(instance, True)
    ui = manager.getUIConfigurationManager(service)
    menus = ui.getSettings(NODE_MENUBAR, True)
    if index == -1:
        for menu in menus:
            data = property_to_dict(menu)
            debug(data.get('CommandURL', ''))
    else:
        menus = property_to_dict(menus[index])['ItemDescriptorContainer']
        _get_app_submenus(menus)
    return menus


# ~ Export ok
def start():
    global _start
    _start = now()
    log.info(_start)
    return


# ~ Export ok
def end():
    global _start
    e = now()
    return str(e - _start).split('.')[0]


# ~ Export ok
# ~ https://en.wikipedia.org/wiki/Web_colors
def get_color(*value):
    if len(value) == 1 and isinstance(value[0], int):
        return value[0]
    if len(value) == 1 and isinstance(value[0], tuple):
        value = value[0]

    COLORS = {
        'aliceblue': 15792383,
        'antiquewhite': 16444375,
        'aqua': 65535,
        'aquamarine': 8388564,
        'azure': 15794175,
        'beige': 16119260,
        'bisque': 16770244,
        'black': 0,
        'blanchedalmond': 16772045,
        'blue': 255,
        'blueviolet': 9055202,
        'brown': 10824234,
        'burlywood': 14596231,
        'cadetblue': 6266528,
        'chartreuse': 8388352,
        'chocolate': 13789470,
        'coral': 16744272,
        'cornflowerblue': 6591981,
        'cornsilk': 16775388,
        'crimson': 14423100,
        'cyan': 65535,
        'darkblue': 139,
        'darkcyan': 35723,
        'darkgoldenrod': 12092939,
        'darkgray': 11119017,
        'darkgreen': 25600,
        'darkgrey': 11119017,
        'darkkhaki': 12433259,
        'darkmagenta': 9109643,
        'darkolivegreen': 5597999,
        'darkorange': 16747520,
        'darkorchid': 10040012,
        'darkred': 9109504,
        'darksalmon': 15308410,
        'darkseagreen': 9419919,
        'darkslateblue': 4734347,
        'darkslategray': 3100495,
        'darkslategrey': 3100495,
        'darkturquoise': 52945,
        'darkviolet': 9699539,
        'deeppink': 16716947,
        'deepskyblue': 49151,
        'dimgray': 6908265,
        'dimgrey': 6908265,
        'dodgerblue': 2003199,
        'firebrick': 11674146,
        'floralwhite': 16775920,
        'forestgreen': 2263842,
        'fuchsia': 16711935,
        'gainsboro': 14474460,
        'ghostwhite': 16316671,
        'gold': 16766720,
        'goldenrod': 14329120,
        'gray': 8421504,
        'grey': 8421504,
        'green': 32768,
        'greenyellow': 11403055,
        'honeydew': 15794160,
        'hotpink': 16738740,
        'indianred': 13458524,
        'indigo': 4915330,
        'ivory': 16777200,
        'khaki': 15787660,
        'lavender': 15132410,
        'lavenderblush': 16773365,
        'lawngreen': 8190976,
        'lemonchiffon': 16775885,
        'lightblue': 11393254,
        'lightcoral': 15761536,
        'lightcyan': 14745599,
        'lightgoldenrodyellow': 16448210,
        'lightgray': 13882323,
        'lightgreen': 9498256,
        'lightgrey': 13882323,
        'lightpink': 16758465,
        'lightsalmon': 16752762,
        'lightseagreen': 2142890,
        'lightskyblue': 8900346,
        'lightslategray': 7833753,
        'lightslategrey': 7833753,
        'lightsteelblue': 11584734,
        'lightyellow': 16777184,
        'lime': 65280,
        'limegreen': 3329330,
        'linen': 16445670,
        'magenta': 16711935,
        'maroon': 8388608,
        'mediumaquamarine': 6737322,
        'mediumblue': 205,
        'mediumorchid': 12211667,
        'mediumpurple': 9662683,
        'mediumseagreen': 3978097,
        'mediumslateblue': 8087790,
        'mediumspringgreen': 64154,
        'mediumturquoise': 4772300,
        'mediumvioletred': 13047173,
        'midnightblue': 1644912,
        'mintcream': 16121850,
        'mistyrose': 16770273,
        'moccasin': 16770229,
        'navajowhite': 16768685,
        'navy': 128,
        'oldlace': 16643558,
        'olive': 8421376,
        'olivedrab': 7048739,
        'orange': 16753920,
        'orangered': 16729344,
        'orchid': 14315734,
        'palegoldenrod': 15657130,
        'palegreen': 10025880,
        'paleturquoise': 11529966,
        'palevioletred': 14381203,
        'papayawhip': 16773077,
        'peachpuff': 16767673,
        'peru': 13468991,
        'pink': 16761035,
        'plum': 14524637,
        'powderblue': 11591910,
        'purple': 8388736,
        'red': 16711680,
        'rosybrown': 12357519,
        'royalblue': 4286945,
        'saddlebrown': 9127187,
        'salmon': 16416882,
        'sandybrown': 16032864,
        'seagreen': 3050327,
        'seashell': 16774638,
        'sienna': 10506797,
        'silver': 12632256,
        'skyblue': 8900331,
        'slateblue': 6970061,
        'slategray': 7372944,
        'slategrey': 7372944,
        'snow': 16775930,
        'springgreen': 65407,
        'steelblue': 4620980,
        'tan': 13808780,
        'teal': 32896,
        'thistle': 14204888,
        'tomato': 16737095,
        'turquoise': 4251856,
        'violet': 15631086,
        'wheat': 16113331,
        'white': 16777215,
        'whitesmoke': 16119285,
        'yellow': 16776960,
        'yellowgreen': 10145074,
    }

    if len(value) == 3:
        color = (value[0] << 16) + (value[1] << 8) + value[2]
    else:
        value = value[0]
        if value[0] == '#':
            r, g, b = bytes.fromhex(value[1:])
            color = (r << 16) + (g << 8) + b
        else:
            color = COLORS.get(value.lower(), -1)
    return color


COLOR_ON_FOCUS = get_color('LightYellow')


# ~ Export ok
def render(template, data):
    s = Template(template)
    return s.safe_substitute(**data)


def _to_date(value):
    new_value = value
    if isinstance(value, Time):
        new_value = datetime.time(value.Hours, value.Minutes, value.Seconds)
    elif isinstance(value, Date):
        new_value = datetime.date(value.Year, value.Month, value.Day)
    elif isinstance(value, DateTime):
        new_value = datetime.datetime(
            value.Year, value.Month, value.Day,
            value.Hours, value.Minutes, value.Seconds)
    return new_value


def date_to_struct(value):
    # ~ print(type(value))
    if isinstance(value, datetime.datetime):
        d = DateTime()
        d.Seconds = value.second
        d.Minutes = value.minute
        d.Hours = value.hour
        d.Day = value.day
        d.Month = value.month
        d.Year = value.year
    elif isinstance(value, datetime.date):
        d = Date()
        d.Day = value.day
        d.Month = value.month
        d.Year = value.year
    return d


# ~ Export ok
def format(template, data):
    """
        https://pyformat.info/
    """
    if isinstance(data, (str, int, float)):
        # ~ print(template.format(data))
        return template.format(data)

    if isinstance(data, (Time, Date, DateTime)):
        return template.format(_to_date(data))

    if isinstance(data, tuple) and isinstance(data[0], tuple):
        data = {r[0]: _to_date(r[1]) for r in data}
        return template.format(**data)

    data = [_to_date(v) for v in data]
    result = template.format(*data)
    return result


def _get_url_script(macro):
    macro['language'] = macro.get('language', 'Python')
    macro['location'] = macro.get('location', 'user')
    data = macro.copy()
    if data['language'] == 'Python':
        data['module'] = '.py$'
    elif data['language'] == 'Basic':
        data['module'] = '.{}.'.format(macro['module'])
        if macro['location'] == 'user':
            data['location'] = 'application'
    else:
        data['module'] = '.'

    url = 'vnd.sun.star.script:{library}{module}{name}?language={language}&location={location}'
    path = url.format(**data)
    return path


def _call_macro(macro):
    #~ https://wiki.openoffice.org/wiki/Documentation/DevGuide/Scripting/Scripting_Framework_URI_Specification
    name = 'com.sun.star.script.provider.MasterScriptProviderFactory'
    factory = create_instance(name, False)

    macro['language'] = macro.get('language', 'Python')
    macro['location'] = macro.get('location', 'user')
    data = macro.copy()
    if data['language'] == 'Python':
        data['module'] = '.py$'
    elif data['language'] == 'Basic':
        data['module'] = '.{}.'.format(macro['module'])
        if macro['location'] == 'user':
            data['location'] = 'application'
    else:
        data['module'] = '.'

    args = macro.get('args', ())
    url = 'vnd.sun.star.script:{library}{module}{name}?language={language}&location={location}'
    path = url.format(**data)

    script = factory.createScriptProvider('').getScript(path)
    return script.invoke(args, None, None)[0]


# ~ Export ok
def call_macro(macro):
    in_thread = macro.pop('thread')
    if in_thread:
        t = threading.Thread(target=_call_macro, args=(macro,))
        t.start()
        return

    return _call_macro(macro)


class TimerThread(threading.Thread):

    def __init__(self, event, seconds, macro):
        threading.Thread.__init__(self)
        self.stopped = event
        self.seconds = seconds
        self.macro = macro

    def run(self):
        info('Timer started... {}'.format(self.macro['name']))
        while not self.stopped.wait(self.seconds):
            _call_macro(self.macro)
        info('Timer stopped... {}'.format(self.macro['name']))
        return


# ~ Export ok
def timer(name, seconds, macro):
    global _stop_thread
    _stop_thread[name] = threading.Event()
    thread = TimerThread(_stop_thread[name], seconds, macro)
    thread.start()
    return


# ~ Export ok
def stop_timer(name):
    global _stop_thread
    _stop_thread[name].set()
    del _stop_thread[name]
    return


def _get_key(password):
    digest = hashlib.sha256(password.encode()).digest()
    key = base64.urlsafe_b64encode(digest)
    return key


# ~ Export ok
def encrypt(data, password):
    f = Fernet(_get_key(password))
    token = f.encrypt(data).decode()
    return token


# ~ Export ok
def decrypt(token, password):
    data = ''
    f = Fernet(_get_key(password))
    try:
        data = f.decrypt(token.encode()).decode()
    except InvalidToken as e:
        error('Invalid Token')
    return data


class SmtpServer(object):

    def __init__(self, config):
        self._server = None
        self._error = ''
        self._sender = ''
        self._is_connect = self._login(config)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def is_connect(self):
        return self._is_connect

    @property
    def error(self):
        return self._error

    def _login(self, config):
        name = config['server']
        port = config['port']
        is_ssl = config['ssl']
        self._sender = config['user']
        hosts = ('gmail' in name or 'outlook' in name)
        try:
            if is_ssl and hosts:
                self._server = smtplib.SMTP(name, port, timeout=TIMEOUT)
                self._server.ehlo()
                self._server.starttls()
                self._server.ehlo()
            elif is_ssl:
                self._server = smtplib.SMTP_SSL(name, port, timeout=TIMEOUT)
                self._server.ehlo()
            else:
                self._server = smtplib.SMTP(name, port, timeout=TIMEOUT)

            self._server.login(self._sender, config['pass'])
            msg = 'Connect to: {}'.format(name)
            debug(msg)
            return True
        except smtplib.SMTPAuthenticationError as e:
            if '535' in str(e):
                self._error = _('Incorrect user or password')
                return False
            if '534' in str(e) and 'gmail' in name:
                self._error = _('Allow less secure apps in GMail')
                return False
        except smtplib.SMTPException as e:
            self._error = str(e)
            return False
        except Exception as e:
            self._error = str(e)
            return False
        return False

    def _body(self, msg):
        body = msg.replace('\\n', '<BR>')
        return body

    def send(self, message):
        file_name = 'attachment; filename={}'
        email = MIMEMultipart()
        email['From'] = self._sender
        email['To'] = message['to']
        email['Cc'] = message.get('cc', '')
        email['Subject'] = message['subject']
        email['Date'] = formatdate(localtime=True)
        if message.get('confirm', False):
            email['Disposition-Notification-To'] = email['From']
        email.attach(MIMEText(self._body(message['body']), 'html'))

        for path in message.get('files', ()):
            _, fn, _, _ = get_info_path(path)
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(read_file(path, 'rb'))
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', file_name.format(fn))
            email.attach(part)

        receivers = (
            email['To'].split(',') +
            email['CC'].split(',') +
            message.get('bcc', '').split(','))
        try:
            self._server.sendmail(self._sender, receivers, email.as_string())
            msg = 'Email sent...'
            debug(msg)
            if message.get('path', ''):
                self.save_message(email, message['path'])
            return True
        except Exception as e:
            self._error = str(e)
            return False
        return False

    def save_message(self, email, path):
        mbox = mailbox.mbox(path, create=True)
        mbox.lock()
        try:
            msg = mailbox.mboxMessage(email)
            mbox.add(msg)
            mbox.flush()
        finally:
            mbox.unlock()
        return

    def close(self):
        try:
            self._server.quit()
            msg = 'Close connection...'
            debug(msg)
        except:
            pass
        return


def _send_email(server, messages):
    with SmtpServer(server) as server:
        if server.is_connect:
            for msg in messages:
                server.send(msg)
        else:
            error(server.error)
    return server.error


def send_email(server, message):
    messages = message
    if isinstance(message, dict):
        messages = (message,)
    t = threading.Thread(target=_send_email, args=(server, messages))
    t.start()
    return


def server_smtp_test(config):
    with SmtpServer(config) as server:
        if server.error:
            error(server.error)
    return server.error


def import_csv(path, **kwargs):
    """
        See https://docs.python.org/3.5/library/csv.html#csv.reader
    """
    with open(path) as f:
        rows = tuple(csv.reader(f, **kwargs))
    return rows


def export_csv(path, data, **kwargs):
    with open(path, 'w') as f:
        writer = csv.writer(f, **kwargs)
        writer.writerows(data)
    return


def install_locales(path, domain='base', dir_locales=DIR['locales']):
    p, *_ = get_info_path(path)
    path_locales = join(p, dir_locales)
    try:
        lang = gettext.translation(domain, path_locales, languages=[LANG])
        lang.install()
        _ = lang.gettext
    except Exception as e:
        from gettext import gettext as _
        error(e)
    return _


class LIBOServer(object):
    HOST = 'localhost'
    PORT = '8100'
    ARG = 'socket,host={},port={};urp;StarOffice.ComponentContext'.format(HOST, PORT)
    CMD = ['soffice',
        '-env:SingleAppInstance=false',
        '-env:UserInstallation=file:///tmp/LIBO_Process8100',
        '--headless', '--norestore', '--invisible',
        '--accept={}'.format(ARG)]

    def __init__(self):
        self._server = None
        self._ctx = None
        self._sm = None
        self._start_server()
        self._init_values()

    def _init_values(self):
        global CTX
        global SM

        if not self.is_running:
            return

        ctx = uno.getComponentContext()
        service = 'com.sun.star.bridge.UnoUrlResolver'
        resolver = ctx.ServiceManager.createInstanceWithContext(service, ctx)
        self._ctx = resolver.resolve('uno:{}'.format(self.ARG))
        self._sm = self._ctx.getServiceManager()
        CTX = self._ctx
        SM = self._sm
        return

    @property
    def is_running(self):
        try:
            s = socket.create_connection((self.HOST, self.PORT), 5.0)
            s.close()
            debug('LibreOffice is running...')
            return True
        except ConnectionRefusedError:
            return False

    def _start_server(self):
        if self.is_running:
            return

        for i in range(3):
            self._server = subprocess.Popen(self.CMD,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(3)
            if self.is_running:
                break
        return

    def stop(self):
        if self._server is None:
            print('Search pgrep soffice')
        else:
            self._server.terminate()
        debug('LibreOffice is stop...')
        return

    def create_instance(self, name, with_context=True):
        if with_context:
            instance = self._sm.createInstanceWithContext(name, self._ctx)
        else:
            instance = self._sm.createInstance(name)
        return instance


# ~ controls = {
    # ~ 'CheckBox': 'com.sun.star.awt.UnoControlCheckBoxModel',
    # ~ 'ComboBox': 'com.sun.star.awt.UnoControlComboBoxModel',
    # ~ 'CurrencyField': 'com.sun.star.awt.UnoControlCurrencyFieldModel',
    # ~ 'DateField': 'com.sun.star.awt.UnoControlDateFieldModel',
    # ~ 'FileControl': 'com.sun.star.awt.UnoControlFileControlModel',
    # ~ 'FormattedField': 'com.sun.star.awt.UnoControlFormattedFieldModel',
    # ~ 'GroupBox': 'com.sun.star.awt.UnoControlGroupBoxModel',
    # ~ 'ImageControl': 'com.sun.star.awt.UnoControlImageControlModel',
    # ~ 'NumericField': 'com.sun.star.awt.UnoControlNumericFieldModel',
    # ~ 'PatternField': 'com.sun.star.awt.UnoControlPatternFieldModel',
    # ~ 'ProgressBar': 'com.sun.star.awt.UnoControlProgressBarModel',
    # ~ 'ScrollBar': 'com.sun.star.awt.UnoControlScrollBarModel',
    # ~ 'SimpleAnimation': 'com.sun.star.awt.UnoControlSimpleAnimationModel',
    # ~ 'SpinButton': 'com.sun.star.awt.UnoControlSpinButtonModel',
    # ~ 'Throbber': 'com.sun.star.awt.UnoControlThrobberModel',
    # ~ 'TimeField': 'com.sun.star.awt.UnoControlTimeFieldModel',
# ~ }
