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

#ifndef __MuQt6__QObjectType__h__
#define __MuQt6__QObjectType__h__
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
class MuQt_QObject;

class QObjectType : public Class
{
  public:

    struct Struct { QObject* object; };
    typedef MuQt_QObject MuQtType;
    typedef QObject QtType;

    //
    //  Constructors
    //

    QObjectType(Context* context, 
           const char* name,
           Class* superClass = 0,
           Class* superClass2 = 0);

    virtual ~QObjectType();

    static bool isInheritable() { return true; }
    static inline ClassInstance* cachedInstance(const MuQtType*);

    //
    //  Class API
    //

    virtual void load();

    MemberFunction* _func[4];
};

// Inheritable object

class MuQt_QObject : public QObject
{
  public:
    virtual ~MuQt_QObject();
    MuQt_QObject(Pointer muobj, const CallEnvironment*, QObject * parent) ;
    virtual bool event(QEvent * e) ;
    virtual bool eventFilter(QObject * watched, QEvent * event) ;
  protected:
    virtual void customEvent(QEvent * event) ;
    virtual void timerEvent(QTimerEvent * event) ;
  public:
    void customEvent_pub(QEvent * event)  { customEvent(event); }
    void customEvent_pub_parent(QEvent * event)  { QObject::customEvent(event); }
    QObject * sender_pub() const { return sender(); }
    QObject * sender_pub_parent() const { return QObject::sender(); }
    int senderSignalIndex_pub() const { return senderSignalIndex(); }
    int senderSignalIndex_pub_parent() const { return QObject::senderSignalIndex(); }
    void timerEvent_pub(QTimerEvent * event)  { timerEvent(event); }
    void timerEvent_pub_parent(QTimerEvent * event)  { QObject::timerEvent(event); }
  public:
    const QObjectType* _baseType;
    ClassInstance* _obj;
    const CallEnvironment* _env;
};

inline ClassInstance* QObjectType::cachedInstance(const QObjectType::MuQtType* obj) { return obj->_obj; }

} // Mu

#endif // __MuQt__QObjectType__h__