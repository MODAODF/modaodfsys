# coding: utf-8
import os
import uno
import unohelper
from com.sun.star.task import XJob
from com.sun.star.lang import XServiceInfo, XServiceName, XServiceDisplayName

# ~ import json
# ~ import ssl
# ~ from urllib import request
# ~ import urllib
# ~ import pathlib
# ~ import webbrowser
import traceback
# ~ import csv
# ~ import time
from com.sun.star.ui.dialogs.TemplateDescription import FILESAVE_SIMPLE
from qrcodeprint_utils import msgbox, getProjectDataPath, createUnoService
# ~ import base64

from odf import text, table, teletype
from odf.opendocument import load
import odf.element as element

import easymacro as app
import qrcode
import qrcode.image.svg as svg
from com.sun.star.beans import PropertyValue

QR = 'qrcode'
PARA_BREAK = '\n'
PARA_2_BREAK = '\n\n'
PARA_4_BREAK = '\n\n\n\n'
DESK = 'com.sun.star.frame.Desktop'
DISPATCHHELPER = 'com.sun.star.frame.DispatchHelper'
NAME_LABEL = '名稱: '
ADD_LABEL = '網址: '
IMFONTSIZE = 20

class QRcodePrint(unohelper.Base, XJob, XServiceInfo, XServiceName):
    def __init__(self, ctx):
        self._ctx = ctx
        self._name = ''
        self._data = ''
        self._path = ''
        self._writer_run = False
        self._calc_run = False
        self._impress_run = False
        self._type = 'qrcode'
        self._smgr = ctx.getServiceManager()
        self._desktop = self._smgr.createInstanceWithContext(DESK , self._ctx)
        self._frame = self._desktop.getCurrentFrame()
        self.ServiceName = "com.sun.star.task.Job"
        self.ImplementationName = "tw.ossii.QRcodePrint.impl"
        self.SupportedServiceNames = (self.ServiceName, )

    # ~ def _smgr(self):
        # ~ return self._ctx.getServiceManager()

    # ~ def _desktop(self):
        # ~ return self._smgr.createInstanceWithContext(DESK , self._ctx)

    # ~ def _frame(self):
        # ~ return self._desktop.getCurrentFrame()

    def call_dispatch(self, url, args=()):
        # ~ msgbox("call_dispatch")
        # ~ smgr = self._ctx.getServiceManager()
        # ~ desktop = smgr.createInstanceWithContext(DESK , self._ctx)
        # ~ frame = desktop.getCurrentFrame()
        # ~ dispatchHelper = smgr.createInstanceWithContext(DISPATCHHELPER, self._ctx )
        # ~ dispatchHelper.executeDispatch(frame, url, '', 0, args)
        dispatchHelper = self._smgr.createInstanceWithContext(DISPATCHHELPER, self._ctx )
        dispatchHelper.executeDispatch(self._frame, url, '', 0, args)
        return

    ## getHyperlinkList
    #  @param
    def genQRcodePage(self,url):
        # ~ msgbox("getHyperlinkList")
        try:
            # ~ msgbox(url)
            # ~ url = "C:\\Users\\alantom\\Documents\\test_files\\Url2QRCode\\url2qrcode_01.odt"
            # ~ url = "C:\\Users\\alantom\\Documents\\test_files\\Url2QRCode\\url2qrcode_01.ods"
            # ~ url = "C:\\Users\\alantom\\Documents\\test_files\\Url2QRCode\\url2qrcode_01.odp"
            textdoc = load(url)
            doc = app.get_document()

            texts = textdoc.getElementsByType(text.A)
            s = len(texts)
            # ~ msgbox(s)
            # check HYPERLINK
            if s <= 0:
                if doc.type == 'writer' or doc.type == 'impress':
                    return False
            # ~ msgbox(s)
            # ~ data = []
            # ~ index = 0
            # ~ msgbox(doc.type)

            # ~ if doc.type == 'writer':
                # ~ doc.go_end()
                # ~ self.call_dispatch('.uno:InsertPagebreak')
                # ToDo: reset_style

            if doc.type == 'calc':
                doc.insert('_QRcode_')
                doc.activate('_QRcode_')

            if doc.type == 'impress':
                s = int(s/2)

            for i in range(s):
                hyperlinkaddr = texts[i].getAttribute("href")
                if hyperlinkaddr.startswith('http'):
                    hyperlinkname = teletype.extractText(texts[i])
                    # ~ msgbox(hyperlinkname)
                    # ~ msgbox(hyperlinkaddr)
                    # ~ col = []
                    # ~ data.append(col)
                    # ~ data[index].append(hyperlinkname)
                    # ~ data[index].append(hyperlinkaddr)
                    # ~ index = index + 1
                    self._name = hyperlinkname
                    self._data = hyperlinkaddr
                    # ~ self._insert_in_writer(doc)
                    getattr(self, '_insert_in_{}'.format(doc.type))(doc)
                    # ~ app.kill(self._path)

            if doc.type == 'writer':
                if not self._writer_run:
                    return False

            if doc.type == 'impress':
                if not self._impress_run:
                    return False

            if doc.type == 'calc':
                textc = textdoc.getElementsByType(table.TableCell)
                c = len(textc)
                # ~ msgbox(c)
                for i in range(c):
                    formula_text = textc[i].getAttribute("formula")
                    if isinstance(formula_text,str):
                        if formula_text.find('=HYPERLINK') > 0:
                            # ~ msgbox(formula_text)
                            tmp_text = formula_text.replace("\"","").split(";")
                            self._data = tmp_text[0][14:]
                            self._name = tmp_text[1][:-1]
                            # ~ msgbox(self._name)
                            # ~ msgbox(self._data)
                            getattr(self, '_insert_in_{}'.format(doc.type))(doc)
                if self._calc_run:
                    oProp = PropertyValue()
                    oProp.Name = "aExtraHeight"
                    oProp.Value = 0
                    properties = (oProp,)
                    self.call_dispatch('.uno:SetOptimalRowHeight', properties)
                else:
                    doc.remove('_QRcode_')
                    return False
            # ~ return data
            return True
        except:
            oDisp = traceback.format_exc(sys.exc_info()[2])

    def gonext_cell(self, row):
        # ~ msgbox("gonext_cell : " + str(row))
        oProp = PropertyValue()
        oProp.Name = 'ToPoint'
        oProp.Value = str(row+1) + ':1'
        properties = (oProp,)
        self.call_dispatch('.uno:GoToCell', properties)

    def _create_code(self, path=''):
        # ~ msgbox("_create_code")
        if not path:
            path = app.get_temp_file(True)
        if self._type == QR:
            factory = svg.SvgImage
            img = qrcode.make(self._data, border=2, image_factory=factory)
            img.save(path)
        else:
            try:
                path = generate(self._type, self._data, output=path)
            except Exception as e:
                app.error(e)
                return str(e)

        if app.is_created(path):
            self._path = path
            return ''

        return _('Not generated')

    def _insert_in_writer(self, doc):
        # ~ msgbox("_insert_in_writer")
        self._writer_run = True
        doc = app.get_document()
        if not self._data:
            sel = app.get_selection()
            self._data = sel.string
            if not self._data:
                msg = _('Select data')
                self._show_error(msg)
                return

        result = self._create_code()
        if result:
            self._show_error(result)
            return

        # add qrcode on pageEnd
        # ~ doc.go_end()
        # ~ self.call_dispatch('.uno:InsertPagebreak')
        doc.write(NAME_LABEL + self._name)
        doc.write(PARA_BREAK)
        doc.write(ADD_LABEL + self._data)
        doc.write(PARA_BREAK)
        doc.insert_image(self._path)
        doc.write(PARA_2_BREAK)
        return

    def _insert_in_calc(self, doc):
        # ~ msgbox("_insert_in_calc")
        self._calc_run = True
        cell = doc.get_cell()
        if not self._data:
            self._data = cell.value
            if not self._data:
                msg = _('Select data')
                self._show_error(msg)
                return

        result = self._create_code()
        if result:
            self._show_error(result)
            return

        # ~ if not self._ask:
            # ~ cell = cell.offset(1, 0)

        # ~ oProp = PropertyValue()
        # ~ oProp.Name = 'ToPoint'
        # ~ oProp.Value = 'A1'
        # ~ properties = (oProp,)
        # ~ self.call_dispatch('.uno:GoToCell', properties)

        # ~ msgbox(cell.address.Row)

        cell = cell.Next_cell()
        cell.Value(NAME_LABEL + self._name)
        cell = cell.Next_cell()
        # ~ self.gonext_cell(cell.address.Row)

        cell.Value(ADD_LABEL + self._data)
        cell = cell.Next_cell()
        # ~ self.gonext_cell(cell.address.Row)

        cell.Value(PARA_4_BREAK)
        # ~ cell.Height = 2000
        cell.insert_image(self._path)

        self.gonext_cell(cell.address.Row)
        # ~ oProp = PropertyValue()
        # ~ oProp.Name = "RowHeight"
        # ~ oProp.Value = 2000
        # ~ properties = (oProp,)
        # ~ self.call_dispatch('.uno:RowHeight', properties)
        # ~ oProp = PropertyValue()
        # ~ oProp.Name = "aExtraHeight"
        # ~ oProp.Value = 0
        # ~ properties = (oProp,)
        # ~ self.call_dispatch('.uno:SetOptimalRowHeight', properties)

        # ~ cell = cell.Next_cell()
        # ~ self.gonext_cell(cell.address.Row)

        return

    def _insert_in_draw(self, doc):
        self._impress_run = True
        result = self._create_code()
        if result:
            self._show_error(result)
            return

        # ~ smgr = self._ctx.getServiceManager()
        # ~ desktop = smgr.createInstanceWithContext(DESK , self._ctx)
        oDoc = self._desktop.getCurrentComponent()
        numPages = oDoc.getDrawPages().getCount()
        # ~ msgbox(numPages)

        doc.set_currentpage(oDoc.getDrawPages().getByIndex(numPages-1))

        # ~ oProp = PropertyValue()
        # ~ oProp.Name = "WhatLayout"
        # ~ oProp.Value = 1
        # ~ properties = (oProp,)
        # ~ self.call_dispatch('.uno:InsertPage',properties)
        # ~ self.call_dispatch('.')

        self.call_dispatch('.uno:InsertPageQuick')

        doc.insert_text(NAME_LABEL + self._name + "\n" + ADD_LABEL + self._data, IMFONTSIZE)

        doc.insert_image(self._path)
        return

    def _insert_in_impress(self, doc):
        self._insert_in_draw(doc)
        return

    def _show_error(self, error):
        msg = _('Error in: {}\n\n{}').format(self._type, error)
        app.error(error)
        app.errorbox(msg, TITLE)
        return

    # XServiceName method implementations
    def getServiceName(self):
        return self.ImplementationName

    # XServiceInfo method implementations
    def getImplementationName (self):
        return self.ImplementationName

    def supportsService(self, ServiceName):
        return (ServiceName in self.SupportedServiceNames)

    def getSupportedServiceNames (self):
        return self.SupportedServiceNames

    def execute(self, args):
        for prop in args:
            if prop.Name == 'GenQRcodePage':
                # ~ msgbox("QRcodePrintImp genQRcodePage")
                url = prop.Value
                return self.genQRcodePage(url)

g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(QRcodePrint,
                                         "tw.ossii.QRcodePrint.impl",
                                         ("com.sun.star.task.Job",),)
