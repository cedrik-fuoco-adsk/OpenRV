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

#ifndef __MuQt6__QProcessType__h__
#define __MuQt6__QProcessType__h__
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
class MuQt_QProcess;

class QProcessType : public Class
{
  public:

    typedef MuQt_QProcess MuQtType;
    typedef QProcess QtType;

    //
    //  Constructors
    //

    QProcessType(Context* context, 
           const char* name,
           Class* superClass = 0,
           Class* superClass2 = 0);

    virtual ~QProcessType();

    static bool isInheritable() { return true; }
    static inline ClassInstance* cachedInstance(const MuQtType*);

    //
    //  Class API
    //

    virtual void load();

    MemberFunction* _func[14];
};

// Inheritable object

class MuQt_QProcess : public QProcess
{
  public:
    virtual ~MuQt_QProcess();
    MuQt_QProcess(Pointer muobj, const CallEnvironment*, QObject * parent) ;
    virtual qint64 bytesToWrite() const;
    virtual void close() ;
    virtual bool isSequential() const;
    virtual bool open(QIODeviceBase::OpenMode mode) ;
    virtual bool waitForBytesWritten(int msecs) ;
    virtual bool waitForReadyRead(int msecs) ;
    virtual bool atEnd() const;
    virtual qint64 bytesAvailable() const;
    virtual bool canReadLine() const;
    virtual qint64 pos() const;
    virtual bool reset() ;
    virtual bool seek(qint64 pos) ;
    virtual qint64 size() const;
  protected:
    virtual qint64 skipData(qint64 maxSize) ;
  public:
    void setProcessState_pub(QProcess::ProcessState state)  { setProcessState(state); }
    void setProcessState_pub_parent(QProcess::ProcessState state)  { QProcess::setProcessState(state); }
    qint64 skipData_pub(qint64 maxSize)  { return skipData(maxSize); }
    qint64 skipData_pub_parent(qint64 maxSize)  { return QProcess::skipData(maxSize); }
  public:
    const QProcessType* _baseType;
    ClassInstance* _obj;
    const CallEnvironment* _env;
};

inline ClassInstance* QProcessType::cachedInstance(const QProcessType::MuQtType* obj) { return obj->_obj; }

} // Mu

#endif // __MuQt__QProcessType__h__