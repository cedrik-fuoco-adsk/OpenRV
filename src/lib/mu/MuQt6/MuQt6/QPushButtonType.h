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

#ifndef __MuQt6__QPushButtonType__h__
#define __MuQt6__QPushButtonType__h__
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
class MuQt_QPushButton;

class QPushButtonType : public Class
{
  public:

    typedef MuQt_QPushButton MuQtType;
    typedef QPushButton QtType;

    //
    //  Constructors
    //

    QPushButtonType(Context* context, 
           const char* name,
           Class* superClass = 0,
           Class* superClass2 = 0);

    virtual ~QPushButtonType();

    static bool isInheritable() { return true; }
    static inline ClassInstance* cachedInstance(const MuQtType*);

    //
    //  Class API
    //

    virtual void load();

    MemberFunction* _func[16];
};

// Inheritable object

class MuQt_QPushButton : public QPushButton
{
  public:
    virtual ~MuQt_QPushButton();
    MuQt_QPushButton(Pointer muobj, const CallEnvironment*, QWidget * parent) ;
    MuQt_QPushButton(Pointer muobj, const CallEnvironment*, const QString & text, QWidget * parent) ;
    MuQt_QPushButton(Pointer muobj, const CallEnvironment*, const QIcon & icon, const QString & text, QWidget * parent) ;
    virtual QSize minimumSizeHint() const;
    virtual QSize sizeHint() const;
  protected:
    virtual bool event(QEvent * e) ;
    virtual void focusInEvent(QFocusEvent * e) ;
    virtual void focusOutEvent(QFocusEvent * e) ;
    virtual bool hitButton(const QPoint & pos) const;
    virtual void keyPressEvent(QKeyEvent * e) ;
    virtual void mouseMoveEvent(QMouseEvent * e) ;
    virtual void paintEvent(QPaintEvent * _p14) ;
    virtual void checkStateSet() ;
    virtual void nextCheckState() ;
    virtual void changeEvent(QEvent * e) ;
    virtual void keyReleaseEvent(QKeyEvent * e) ;
    virtual void mousePressEvent(QMouseEvent * e) ;
    virtual void mouseReleaseEvent(QMouseEvent * e) ;
    virtual void timerEvent(QTimerEvent * e) ;
  public:
    bool event_pub(QEvent * e)  { return event(e); }
    bool event_pub_parent(QEvent * e)  { return QPushButton::event(e); }
    void focusInEvent_pub(QFocusEvent * e)  { focusInEvent(e); }
    void focusInEvent_pub_parent(QFocusEvent * e)  { QPushButton::focusInEvent(e); }
    void focusOutEvent_pub(QFocusEvent * e)  { focusOutEvent(e); }
    void focusOutEvent_pub_parent(QFocusEvent * e)  { QPushButton::focusOutEvent(e); }
    bool hitButton_pub(const QPoint & pos) const { return hitButton(pos); }
    bool hitButton_pub_parent(const QPoint & pos) const { return QPushButton::hitButton(pos); }
    void keyPressEvent_pub(QKeyEvent * e)  { keyPressEvent(e); }
    void keyPressEvent_pub_parent(QKeyEvent * e)  { QPushButton::keyPressEvent(e); }
    void mouseMoveEvent_pub(QMouseEvent * e)  { mouseMoveEvent(e); }
    void mouseMoveEvent_pub_parent(QMouseEvent * e)  { QPushButton::mouseMoveEvent(e); }
    void paintEvent_pub(QPaintEvent * _p14)  { paintEvent(_p14); }
    void paintEvent_pub_parent(QPaintEvent * _p14)  { QPushButton::paintEvent(_p14); }
    void checkStateSet_pub()  { checkStateSet(); }
    void checkStateSet_pub_parent()  { QPushButton::checkStateSet(); }
    void nextCheckState_pub()  { nextCheckState(); }
    void nextCheckState_pub_parent()  { QPushButton::nextCheckState(); }
    void changeEvent_pub(QEvent * e)  { changeEvent(e); }
    void changeEvent_pub_parent(QEvent * e)  { QPushButton::changeEvent(e); }
    void keyReleaseEvent_pub(QKeyEvent * e)  { keyReleaseEvent(e); }
    void keyReleaseEvent_pub_parent(QKeyEvent * e)  { QPushButton::keyReleaseEvent(e); }
    void mousePressEvent_pub(QMouseEvent * e)  { mousePressEvent(e); }
    void mousePressEvent_pub_parent(QMouseEvent * e)  { QPushButton::mousePressEvent(e); }
    void mouseReleaseEvent_pub(QMouseEvent * e)  { mouseReleaseEvent(e); }
    void mouseReleaseEvent_pub_parent(QMouseEvent * e)  { QPushButton::mouseReleaseEvent(e); }
    void timerEvent_pub(QTimerEvent * e)  { timerEvent(e); }
    void timerEvent_pub_parent(QTimerEvent * e)  { QPushButton::timerEvent(e); }
  public:
    const QPushButtonType* _baseType;
    ClassInstance* _obj;
    const CallEnvironment* _env;
};

inline ClassInstance* QPushButtonType::cachedInstance(const QPushButtonType::MuQtType* obj) { return obj->_obj; }

} // Mu

#endif // __MuQt__QPushButtonType__h__