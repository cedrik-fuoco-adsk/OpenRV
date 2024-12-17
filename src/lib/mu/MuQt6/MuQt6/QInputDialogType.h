//*****************************************************************************
// Copyright (c) 2024 Autodesk, Inc.
// All rights reserved.
//
// SPDX-License-Identifier: Apache-2.0
//
//*****************************************************************************

// IMPORTANT: This file (not the template) is auto-generated by qt2mu.py script.
//            The prefered way to do a fix is to handrolled it or modify the qt2mu.py script.
//            If it is not possible, manual editing is ok but it could be lost in future generations.

#ifndef __MuQt6__QInputDialogType__h__
#define __MuQt6__QInputDialogType__h__
#include <iostream>
#include <Mu/Class.h>
#include <Mu/MuProcess.h>
#include <QtCore/QtCore>
#include <QtGui/QtGui>
#include <QtWidgets/QtWidgets>
#include <QtNetwork/QtNetwork>
#include <QtWebEngineWidgets/QtWebEngineWidgets>
#include <QtQml/QtQml>
#include <QtQuick/QtQuick>
#include <QtQuickWidgets/QtQuickWidgets>
#include <QtSvg/QtSvg>
#include <QSvgWidget>
#include <MuQt6/Bridge.h>

namespace Mu {
class MuQt_QInputDialog;

class QInputDialogType : public Class
{
  public:

    typedef MuQt_QInputDialog MuQtType;
    typedef QInputDialog QtType;

    //
    //  Constructors
    //

    QInputDialogType(Context* context, 
           const char* name,
           Class* superClass = 0,
           Class* superClass2 = 0);

    virtual ~QInputDialogType();

    static bool isInheritable() { return true; }
    static inline ClassInstance* cachedInstance(const MuQtType*);

    //
    //  Class API
    //

    virtual void load();

    MemberFunction* _func[10];
};

// Inheritable object

class MuQt_QInputDialog : public QInputDialog
{
  public:
    virtual ~MuQt_QInputDialog();
    MuQt_QInputDialog(Pointer muobj, const CallEnvironment*, QWidget * parent, Qt::WindowFlags flags) ;
    virtual void done(int result) ;
    virtual QSize minimumSizeHint() const;
    virtual void setVisible(bool visible) ;
    virtual QSize sizeHint() const;
  protected:
    virtual void closeEvent(QCloseEvent * e) ;
    virtual void contextMenuEvent(QContextMenuEvent * e) ;
    virtual bool eventFilter(QObject * o, QEvent * e) ;
    virtual void keyPressEvent(QKeyEvent * e) ;
    virtual void resizeEvent(QResizeEvent * _p15) ;
    virtual void showEvent(QShowEvent * event) ;
  public:
    void closeEvent_pub(QCloseEvent * e)  { closeEvent(e); }
    void closeEvent_pub_parent(QCloseEvent * e)  { QInputDialog::closeEvent(e); }
    void contextMenuEvent_pub(QContextMenuEvent * e)  { contextMenuEvent(e); }
    void contextMenuEvent_pub_parent(QContextMenuEvent * e)  { QInputDialog::contextMenuEvent(e); }
    bool eventFilter_pub(QObject * o, QEvent * e)  { return eventFilter(o, e); }
    bool eventFilter_pub_parent(QObject * o, QEvent * e)  { return QInputDialog::eventFilter(o, e); }
    void keyPressEvent_pub(QKeyEvent * e)  { keyPressEvent(e); }
    void keyPressEvent_pub_parent(QKeyEvent * e)  { QInputDialog::keyPressEvent(e); }
    void resizeEvent_pub(QResizeEvent * _p15)  { resizeEvent(_p15); }
    void resizeEvent_pub_parent(QResizeEvent * _p15)  { QInputDialog::resizeEvent(_p15); }
    void showEvent_pub(QShowEvent * event)  { showEvent(event); }
    void showEvent_pub_parent(QShowEvent * event)  { QInputDialog::showEvent(event); }
  public:
    const QInputDialogType* _baseType;
    ClassInstance* _obj;
    const CallEnvironment* _env;
};

inline ClassInstance* QInputDialogType::cachedInstance(const QInputDialogType::MuQtType* obj) { return obj->_obj; }

} // Mu

#endif // __MuQt__QInputDialogType__h__