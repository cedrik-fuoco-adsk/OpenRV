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

#ifndef __MuQt6__QTcpServerType__h__
#define __MuQt6__QTcpServerType__h__
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
class MuQt_QTcpServer;

class QTcpServerType : public Class
{
  public:

    typedef MuQt_QTcpServer MuQtType;
    typedef QTcpServer QtType;

    //
    //  Constructors
    //

    QTcpServerType(Context* context, 
           const char* name,
           Class* superClass = 0,
           Class* superClass2 = 0);

    virtual ~QTcpServerType();

    static bool isInheritable() { return true; }
    static inline ClassInstance* cachedInstance(const MuQtType*);

    //
    //  Class API
    //

    virtual void load();

    MemberFunction* _func[6];
};

// Inheritable object

class MuQt_QTcpServer : public QTcpServer
{
  public:
    virtual ~MuQt_QTcpServer();
    MuQt_QTcpServer(Pointer muobj, const CallEnvironment*, QObject * parent) ;
    virtual bool hasPendingConnections() const;
    virtual QTcpSocket * nextPendingConnection() ;
    virtual bool event(QEvent * e) ;
    virtual bool eventFilter(QObject * watched, QEvent * event) ;
  protected:
    virtual void customEvent(QEvent * event) ;
    virtual void timerEvent(QTimerEvent * event) ;
  public:
    void addPendingConnection_pub(QTcpSocket * socket)  { addPendingConnection(socket); }
    void addPendingConnection_pub_parent(QTcpSocket * socket)  { QTcpServer::addPendingConnection(socket); }
    void customEvent_pub(QEvent * event)  { customEvent(event); }
    void customEvent_pub_parent(QEvent * event)  { QTcpServer::customEvent(event); }
    void timerEvent_pub(QTimerEvent * event)  { timerEvent(event); }
    void timerEvent_pub_parent(QTimerEvent * event)  { QTcpServer::timerEvent(event); }
  public:
    const QTcpServerType* _baseType;
    ClassInstance* _obj;
    const CallEnvironment* _env;
};

inline ClassInstance* QTcpServerType::cachedInstance(const QTcpServerType::MuQtType* obj) { return obj->_obj; }

} // Mu

#endif // __MuQt__QTcpServerType__h__