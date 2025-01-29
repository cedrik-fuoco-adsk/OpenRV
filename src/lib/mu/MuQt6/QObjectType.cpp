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

#include <MuQt6/qtUtils.h>
#include <MuQt6/QObjectType.h>
#include <QtGui/QtGui>
#include <QtWidgets/QtWidgets>
#include <QtSvg/QtSvg>
#include <QSvgWidget>
#include <QtNetwork/QtNetwork>
#include <MuQt6/QWidgetType.h>
#include <MuQt6/QActionType.h>
#include <MuQt6/QIconType.h>
#include <Mu/BaseFunctions.h>
#include <Mu/Thread.h>
#include <Mu/Alias.h>
#include <Mu/SymbolicConstant.h>
#include <Mu/ClassInstance.h>
#include <Mu/Function.h>
#include <Mu/MemberFunction.h>
#include <Mu/MemberVariable.h>
#include <Mu/Node.h>
#include <Mu/Exception.h>
#include <Mu/ParameterVariable.h>
#include <Mu/ReferenceType.h>
#include <Mu/Value.h>
#include <MuLang/MuLangContext.h>
#include <MuLang/StringType.h>
//
// Copyright (C) 2023  Autodesk, Inc. All Rights Reserved. 
// 
// SPDX-License-Identifier: Apache-2.0 
//
#include <MuQt6/QVariantType.h>
#include <MuQt6/QTimerEventType.h>
#include <MuQt6/QEventType.h>

namespace Mu {
using namespace std;

//----------------------------------------------------------------------
//  INHERITABLE TYPE IMPLEMENTATION

// destructor
MuQt_QObject::~MuQt_QObject()
{
    if (_obj)
    {
        *_obj->data<Pointer>() = Pointer(0);
        _obj->releaseExternal();
    }
    _obj = 0;
    _env = 0;
    _baseType = 0;
}

MuQt_QObject::MuQt_QObject(Pointer muobj, const CallEnvironment* ce, QObject * parent) 
 : QObject(parent)
{
    _env = ce;
    _obj = reinterpret_cast<ClassInstance*>(muobj);
    _obj->retainExternal();
    MuLangContext* c = (MuLangContext*)_env->context();
    _baseType = c->findSymbolOfTypeByQualifiedName<QObjectType>(c->internName("qt.QObject"));
}

bool MuQt_QObject::event(QEvent * e) 
{
    if (!_env) return QObject::event(e);
    MuLangContext* c = (MuLangContext*)_env->context();
    const MemberFunction* F0 = _baseType->_func[0];
    const MemberFunction* F = _obj->classType()->dynamicLookup(F0);
    if (F != F0) 
    {
        Function::ArgumentVector args(2);
        args[0] = Value(Pointer(_obj));
        args[1] = Value(makeqpointer<QEventType>(c,e,"qt.QEvent"));
        Value rval = _env->call(F, args);
        return (bool)(rval._bool);
    }
    else
    {
        return QObject::event(e);
    }
}

bool MuQt_QObject::eventFilter(QObject * watched, QEvent * event) 
{
    if (!_env) return QObject::eventFilter(watched, event);
    MuLangContext* c = (MuLangContext*)_env->context();
    const MemberFunction* F0 = _baseType->_func[1];
    const MemberFunction* F = _obj->classType()->dynamicLookup(F0);
    if (F != F0) 
    {
        Function::ArgumentVector args(3);
        args[0] = Value(Pointer(_obj));
        args[1] = Value(makeinstance<QObjectType>(c,watched,"qt.QObject"));
        args[2] = Value(makeqpointer<QEventType>(c,event,"qt.QEvent"));
        Value rval = _env->call(F, args);
        return (bool)(rval._bool);
    }
    else
    {
        return QObject::eventFilter(watched, event);
    }
}

void MuQt_QObject::customEvent(QEvent * event) 
{
    if (!_env) { QObject::customEvent(event); return; }
    MuLangContext* c = (MuLangContext*)_env->context();
    const MemberFunction* F0 = _baseType->_func[2];
    const MemberFunction* F = _obj->classType()->dynamicLookup(F0);
    if (F != F0) 
    {
        Function::ArgumentVector args(2);
        args[0] = Value(Pointer(_obj));
        args[1] = Value(makeqpointer<QEventType>(c,event,"qt.QEvent"));
        Value rval = _env->call(F, args);
    }
    else
    {
        QObject::customEvent(event);
    }
}

void MuQt_QObject::timerEvent(QTimerEvent * event) 
{
    if (!_env) { QObject::timerEvent(event); return; }
    MuLangContext* c = (MuLangContext*)_env->context();
    const MemberFunction* F0 = _baseType->_func[3];
    const MemberFunction* F = _obj->classType()->dynamicLookup(F0);
    if (F != F0) 
    {
        Function::ArgumentVector args(2);
        args[0] = Value(Pointer(_obj));
        args[1] = Value(makeqpointer<QTimerEventType>(c,event,"qt.QTimerEvent"));
        Value rval = _env->call(F, args);
    }
    else
    {
        QObject::timerEvent(event);
    }
}



//----------------------------------------------------------------------
//  Mu Type CONSTRUCTORS

QObjectType::QObjectType(Context* c, const char* name, Class* super, Class* super2)
: Class(c, name, vectorOf2(super, super2))
{
}

QObjectType::~QObjectType()
{
}

//----------------------------------------------------------------------
//  PRE-COMPILED FUNCTIONS

static Pointer
QObject_QObject_QObject(Thread& NODE_THREAD, Pointer obj)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    ClassInstance* widget = reinterpret_cast<ClassInstance*>(obj);

    if (!widget)
    {
        return 0;
    }
    else if (QObject* w = object<QObject>(widget))
    {
        QObjectType* type = 
            c->findSymbolOfTypeByQualifiedName<QObjectType>(c->internName("qt.QObject"), false);
        ClassInstance* o = ClassInstance::allocate(type);
        setobject(o, w);
        return o;
    }
    else
    {
        throw BadCastException();
    }
}

static NODE_IMPLEMENTATION(castFromObject, Pointer)
{
    NODE_RETURN( QObject_QObject_QObject(NODE_THREAD, NODE_ARG(0, Pointer)) );
}

Pointer qt_QObject_QObject_QObject_QObject_QObject(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_parent)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject * arg1 = object<QObject>(param_parent);
    setobject(param_this, new MuQt_QObject(param_this, NODE_THREAD.process()->callEnv(), arg1));
    return param_this;
}

bool qt_QObject_blockSignals_bool_QObject_bool(Mu::Thread& NODE_THREAD, Pointer param_this, bool param_block)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    bool arg1 = (bool)(param_block);
    return arg0->blockSignals(arg1);
}

void qt_QObject_dumpObjectInfo_void_QObject(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    arg0->dumpObjectInfo();
}

void qt_QObject_dumpObjectTree_void_QObject(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    arg0->dumpObjectTree();
}

bool qt_QObject_event_bool_QObject_QEvent(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_e)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    QEvent * arg1 = getqpointer<QEventType>(param_e);
    return isMuQtObject(arg0) ? arg0->QObject::event(arg1) : arg0->event(arg1);
}

bool qt_QObject_eventFilter_bool_QObject_QObject_QEvent(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_watched, Pointer param_event)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    QObject * arg1 = object<QObject>(param_watched);
    QEvent * arg2 = getqpointer<QEventType>(param_event);
    return isMuQtObject(arg0) ? arg0->QObject::eventFilter(arg1, arg2) : arg0->eventFilter(arg1, arg2);
}

void qt_QObject_installEventFilter_void_QObject_QObject(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_filterObj)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    QObject * arg1 = object<QObject>(param_filterObj);
    arg0->installEventFilter(arg1);
}

bool qt_QObject_isQuickItemType_bool_QObject(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    return arg0->isQuickItemType();
}

bool qt_QObject_isWidgetType_bool_QObject(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    return arg0->isWidgetType();
}

bool qt_QObject_isWindowType_bool_QObject(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    return arg0->isWindowType();
}

void qt_QObject_killTimer_void_QObject_int(Mu::Thread& NODE_THREAD, Pointer param_this, int param_id)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    int arg1 = (int)(param_id);
    arg0->killTimer(arg1);
}

Pointer qt_QObject_parent_QObject_QObject(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    return makeinstance<QObjectType>(c, arg0->parent(), "qt.QObject");
}

void qt_QObject_removeEventFilter_void_QObject_QObject(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_obj)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    QObject * arg1 = object<QObject>(param_obj);
    arg0->removeEventFilter(arg1);
}

void qt_QObject_setObjectName_void_QObject_string(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_name)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    const QString  arg1 = qstring(param_name);
    arg0->setObjectName(arg1);
}

void qt_QObject_setParent_void_QObject_QObject(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_parent)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    QObject * arg1 = object<QObject>(param_parent);
    arg0->setParent(arg1);
}

bool qt_QObject_signalsBlocked_bool_QObject(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    return arg0->signalsBlocked();
}

int qt_QObject_startTimer_int_QObject_int_int(Mu::Thread& NODE_THREAD, Pointer param_this, int param_interval, int param_timerType)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    int arg1 = (int)(param_interval);
    Qt::TimerType arg2 = (Qt::TimerType)(param_timerType);
    return arg0->startTimer(arg1, arg2);
}

void qt_QObject_customEvent_void_QObject_QEvent(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_event)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    QEvent * arg1 = getqpointer<QEventType>(param_event);
    if (isMuQtObject(arg0)) ((MuQt_QObject*)arg0)->customEvent_pub_parent(arg1);
    else ((MuQt_QObject*)arg0)->customEvent_pub(arg1);
}

Pointer qt_QObject_sender_QObject_QObject(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    return makeinstance<QObjectType>(c, ((MuQt_QObject*)arg0)->sender_pub(), "qt.QObject");
}

int qt_QObject_senderSignalIndex_int_QObject(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    return ((MuQt_QObject*)arg0)->senderSignalIndex_pub();
}

void qt_QObject_timerEvent_void_QObject_QTimerEvent(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_event)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QObject* arg0 = object<QObject>(param_this);
    QTimerEvent * arg1 = getqpointer<QTimerEventType>(param_event);
    if (isMuQtObject(arg0)) ((MuQt_QObject*)arg0)->timerEvent_pub_parent(arg1);
    else ((MuQt_QObject*)arg0)->timerEvent_pub(arg1);
}

Pointer qt_QObject_tr_string_QObject_string_string_int(Mu::Thread& NODE_THREAD, Pointer sourceText, Pointer disambiguation, int n)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QString arg0 = qstring(sourceText);
    QString arg1 = qstring(disambiguation);
    int arg2 = n;
    return makestring(c, QObject::tr(arg0.toStdString().c_str(), arg1.toStdString().c_str(),arg2));
}


static NODE_IMPLEMENTATION(_n_QObject0, Pointer)
{
    NODE_RETURN(qt_QObject_QObject_QObject_QObject_QObject(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer)));
}

static NODE_IMPLEMENTATION(_n_blockSignals0, bool)
{
    NODE_RETURN(qt_QObject_blockSignals_bool_QObject_bool(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, bool)));
}

static NODE_IMPLEMENTATION(_n_dumpObjectInfo0, void)
{
    qt_QObject_dumpObjectInfo_void_QObject(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer));
}

static NODE_IMPLEMENTATION(_n_dumpObjectTree0, void)
{
    qt_QObject_dumpObjectTree_void_QObject(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer));
}

static NODE_IMPLEMENTATION(_n_event0, bool)
{
    NODE_RETURN(qt_QObject_event_bool_QObject_QEvent(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer)));
}

static NODE_IMPLEMENTATION(_n_eventFilter0, bool)
{
    NODE_RETURN(qt_QObject_eventFilter_bool_QObject_QObject_QEvent(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer), NODE_ARG(2, Pointer)));
}

static NODE_IMPLEMENTATION(_n_installEventFilter0, void)
{
    qt_QObject_installEventFilter_void_QObject_QObject(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
}

static NODE_IMPLEMENTATION(_n_isQuickItemType0, bool)
{
    NODE_RETURN(qt_QObject_isQuickItemType_bool_QObject(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_isWidgetType0, bool)
{
    NODE_RETURN(qt_QObject_isWidgetType_bool_QObject(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_isWindowType0, bool)
{
    NODE_RETURN(qt_QObject_isWindowType_bool_QObject(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_killTimer0, void)
{
    qt_QObject_killTimer_void_QObject_int(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int));
}

static NODE_IMPLEMENTATION(_n_parent0, Pointer)
{
    NODE_RETURN(qt_QObject_parent_QObject_QObject(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_removeEventFilter0, void)
{
    qt_QObject_removeEventFilter_void_QObject_QObject(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
}

static NODE_IMPLEMENTATION(_n_setObjectName0, void)
{
    qt_QObject_setObjectName_void_QObject_string(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
}

static NODE_IMPLEMENTATION(_n_setParent0, void)
{
    qt_QObject_setParent_void_QObject_QObject(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
}

static NODE_IMPLEMENTATION(_n_signalsBlocked0, bool)
{
    NODE_RETURN(qt_QObject_signalsBlocked_bool_QObject(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_startTimer0, int)
{
    NODE_RETURN(qt_QObject_startTimer_int_QObject_int_int(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int), NODE_ARG(2, int)));
}

static NODE_IMPLEMENTATION(_n_customEvent0, void)
{
    qt_QObject_customEvent_void_QObject_QEvent(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
}

static NODE_IMPLEMENTATION(_n_sender0, Pointer)
{
    NODE_RETURN(qt_QObject_sender_QObject_QObject(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_senderSignalIndex0, int)
{
    NODE_RETURN(qt_QObject_senderSignalIndex_int_QObject(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_timerEvent0, void)
{
    qt_QObject_timerEvent_void_QObject_QTimerEvent(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
}

static NODE_IMPLEMENTATION(_n_tr0, Pointer)
{
    NODE_RETURN(qt_QObject_tr_string_QObject_string_string_int(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer),NODE_ARG(2, int)));
}

//
// Copyright (C) 2023  Autodesk, Inc. All Rights Reserved. 
// 
// SPDX-License-Identifier: Apache-2.0 
//

static Pointer
findChild_Object_string(Thread& NODE_THREAD, Pointer obj, Pointer p)
{
    ClassInstance* self = reinterpret_cast<ClassInstance*>(obj);
    StringType::String* name = reinterpret_cast<StringType::String*>(p);
    QObject* o = object<QObject>(self);
    ClassInstance* rval = ClassInstance::allocate(self->classType());
    setobject(rval, o->findChild<QObject*>(name->c_str()));
    return rval;
}

static NODE_IMPLEMENTATION(findChild, Pointer)
{
    NODE_RETURN( findChild_Object_string(NODE_THREAD,
                                         NODE_ARG(0, Pointer),
                                         NODE_ARG(1, Pointer)) );
}

#include <MuQt6/QVariantType.h>
#include <MuQt6/QTimerEventType.h>
#include <MuQt6/QEventType.h>
#include <MuQt6/QVariantType.h>

static bool
setProperty_bool_Object_string_qt_QVariant(Thread& NODE_THREAD,
                                           Pointer obj,
                                           Pointer n,
                                           Pointer v)
{
    ClassInstance* self = reinterpret_cast<ClassInstance*>(obj);
    StringType::String* name = reinterpret_cast<StringType::String*>(n);
    const QVariant  value = getqtype<QVariantType>(v);
    QObject* o = object<QObject>(self);
    return o->setProperty(name->c_str(), value);
}

static NODE_IMPLEMENTATION(setProperty, bool)
{
    NODE_RETURN( setProperty_bool_Object_string_qt_QVariant(NODE_THREAD,
                                                            NODE_ARG(0, Pointer),
                                                            NODE_ARG(1, Pointer),
                                                            NODE_ARG(2, Pointer)) );
}

void
QObjectType::load()
{
    USING_MU_FUNCTION_SYMBOLS;
    MuLangContext* c = static_cast<MuLangContext*>(context());
    Module* global = globalModule();
    
    const string typeName        = name();
    const string refTypeName     = typeName + "&";
    const string fullTypeName    = fullyQualifiedName();
    const string fullRefTypeName = fullTypeName + "&";
    const char*  tn              = typeName.c_str();
    const char*  ftn             = fullTypeName.c_str();
    const char*  rtn             = refTypeName.c_str();
    const char*  frtn            = fullRefTypeName.c_str();

    scope()->addSymbols(new ReferenceType(c, rtn, this),

                        new Function(c, tn, BaseFunctions::dereference, Cast,
                                     Return, ftn,
                                     Args, frtn, End),

                        EndArguments);
    
    addSymbols(new Function(c, "__allocate", BaseFunctions::classAllocate, None,
                            Return, ftn,
                            End),

   new MemberVariable(c, "native", "qt.NativeObject"),

               new Function(c, tn, castFromObject, Cast,
                            Compiled, QObject_QObject_QObject,
                            Return, ftn,
                            Parameters,
                            new Param(c, "object", "qt.QObject"),
                            End),

               EndArguments );

addSymbols(
    // enums
    // member functions
    new Function(c, "QObject", _n_QObject0, None, Compiled, qt_QObject_QObject_QObject_QObject_QObject, Return, "qt.QObject", Parameters, new Param(c, "this", "qt.QObject"), new Param(c, "parent", "qt.QObject"), End),
    // MISSING: bindableObjectName ("QBindable<QString>"; QObject this)
    new Function(c, "blockSignals", _n_blockSignals0, None, Compiled, qt_QObject_blockSignals_bool_QObject_bool, Return, "bool", Parameters, new Param(c, "this", "qt.QObject"), new Param(c, "block", "bool"), End),
    // MISSING: children ("const QObjectList &"; QObject this)
    // MISSING: connect (flags QMetaObject::Connection; QObject this, QObject sender, "const char *" signal, "const char *" method, flags Qt::ConnectionType type)
    new Function(c, "dumpObjectInfo", _n_dumpObjectInfo0, None, Compiled, qt_QObject_dumpObjectInfo_void_QObject, Return, "void", Parameters, new Param(c, "this", "qt.QObject"), End),
    new Function(c, "dumpObjectTree", _n_dumpObjectTree0, None, Compiled, qt_QObject_dumpObjectTree_void_QObject, Return, "void", Parameters, new Param(c, "this", "qt.QObject"), End),
    // MISSING: dynamicPropertyNames ("QList<QByteArray>"; QObject this)
    _func[0] = new MemberFunction(c, "event", _n_event0, None, Compiled, qt_QObject_event_bool_QObject_QEvent, Return, "bool", Parameters, new Param(c, "this", "qt.QObject"), new Param(c, "e", "qt.QEvent"), End),
    _func[1] = new MemberFunction(c, "eventFilter", _n_eventFilter0, None, Compiled, qt_QObject_eventFilter_bool_QObject_QObject_QEvent, Return, "bool", Parameters, new Param(c, "this", "qt.QObject"), new Param(c, "watched", "qt.QObject"), new Param(c, "event", "qt.QEvent"), End),
    // MISSING: findChild ("T"; QObject this, string name, flags Qt::FindChildOptions options)
    // MISSING: findChildren ("QList<T>"; QObject this, string name, flags Qt::FindChildOptions options)
    // MISSING: findChildren ("QList<T>"; QObject this, flags Qt::FindChildOptions options)
    // MISSING: findChildren ("QList<T>"; QObject this, QRegularExpression re, flags Qt::FindChildOptions options)
    // MISSING: inherits (bool; QObject this, "const char *" className)
    new Function(c, "installEventFilter", _n_installEventFilter0, None, Compiled, qt_QObject_installEventFilter_void_QObject_QObject, Return, "void", Parameters, new Param(c, "this", "qt.QObject"), new Param(c, "filterObj", "qt.QObject"), End),
    new Function(c, "isQuickItemType", _n_isQuickItemType0, None, Compiled, qt_QObject_isQuickItemType_bool_QObject, Return, "bool", Parameters, new Param(c, "this", "qt.QObject"), End),
    new Function(c, "isWidgetType", _n_isWidgetType0, None, Compiled, qt_QObject_isWidgetType_bool_QObject, Return, "bool", Parameters, new Param(c, "this", "qt.QObject"), End),
    new Function(c, "isWindowType", _n_isWindowType0, None, Compiled, qt_QObject_isWindowType_bool_QObject, Return, "bool", Parameters, new Param(c, "this", "qt.QObject"), End),
    new Function(c, "killTimer", _n_killTimer0, None, Compiled, qt_QObject_killTimer_void_QObject_int, Return, "void", Parameters, new Param(c, "this", "qt.QObject"), new Param(c, "id", "int"), End),
    // MISSING: metaObject ("const QMetaObject *"; QObject this)
    // MISSING: moveToThread (void; QObject this, "QThread *" targetThread)
    // PROP: objectName (string; QObject this)
    new Function(c, "parent", _n_parent0, None, Compiled, qt_QObject_parent_QObject_QObject, Return, "qt.QObject", Parameters, new Param(c, "this", "qt.QObject"), End),
    // MISSING: property (QVariant; QObject this, "const char *" name)
    new Function(c, "removeEventFilter", _n_removeEventFilter0, None, Compiled, qt_QObject_removeEventFilter_void_QObject_QObject, Return, "void", Parameters, new Param(c, "this", "qt.QObject"), new Param(c, "obj", "qt.QObject"), End),
    new Function(c, "setObjectName", _n_setObjectName0, None, Compiled, qt_QObject_setObjectName_void_QObject_string, Return, "void", Parameters, new Param(c, "this", "qt.QObject"), new Param(c, "name", "string"), End),
    // MISSING: setObjectName (void; QObject this, "QAnyStringView" name)
    new Function(c, "setParent", _n_setParent0, None, Compiled, qt_QObject_setParent_void_QObject_QObject, Return, "void", Parameters, new Param(c, "this", "qt.QObject"), new Param(c, "parent", "qt.QObject"), End),
    // MISSING: setProperty (bool; QObject this, "const char *" name, QVariant value)
    new Function(c, "signalsBlocked", _n_signalsBlocked0, None, Compiled, qt_QObject_signalsBlocked_bool_QObject, Return, "bool", Parameters, new Param(c, "this", "qt.QObject"), End),
    new Function(c, "startTimer", _n_startTimer0, None, Compiled, qt_QObject_startTimer_int_QObject_int_int, Return, "int", Parameters, new Param(c, "this", "qt.QObject"), new Param(c, "interval", "int"), new Param(c, "timerType", "int", Value((int)Qt::CoarseTimer)), End),
    // MISSING: startTimer (int; QObject this, flags std::chrono::milliseconds time, flags Qt::TimerType timerType)
    // MISSING: thread ("QThread *"; QObject this)
    // MISSING: childEvent (void; QObject this, "QChildEvent *" event) // protected
    // MISSING: connectNotify (void; QObject this, "const QMetaMethod &" signal) // protected
    _func[2] = new MemberFunction(c, "customEvent", _n_customEvent0, None, Compiled, qt_QObject_customEvent_void_QObject_QEvent, Return, "void", Parameters, new Param(c, "this", "qt.QObject"), new Param(c, "event", "qt.QEvent"), End),
    // MISSING: disconnectNotify (void; QObject this, "const QMetaMethod &" signal) // protected
    // MISSING: isSignalConnected (bool; QObject this, "const QMetaMethod &" signal) // protected
    // MISSING: receivers (int; QObject this, "const char *" signal) // protected
    new Function(c, "sender", _n_sender0, None, Compiled, qt_QObject_sender_QObject_QObject, Return, "qt.QObject", Parameters, new Param(c, "this", "qt.QObject"), End),
    new Function(c, "senderSignalIndex", _n_senderSignalIndex0, None, Compiled, qt_QObject_senderSignalIndex_int_QObject, Return, "int", Parameters, new Param(c, "this", "qt.QObject"), End),
    _func[3] = new MemberFunction(c, "timerEvent", _n_timerEvent0, None, Compiled, qt_QObject_timerEvent_void_QObject_QTimerEvent, Return, "void", Parameters, new Param(c, "this", "qt.QObject"), new Param(c, "event", "qt.QTimerEvent"), End),
    // static functions
    // MISSING: connect (flags QMetaObject::Connection; QObject sender, "const char *" signal, QObject receiver, "const char *" method, flags Qt::ConnectionType type)
    // MISSING: connect (flags QMetaObject::Connection; QObject sender, "const QMetaMethod &" signal, QObject receiver, "const QMetaMethod &" method, flags Qt::ConnectionType type)
    // MISSING: connect (flags QMetaObject::Connection; QObject sender, "PointerToMemberFunction" signal, QObject receiver, "PointerToMemberFunction" method, flags Qt::ConnectionType type)
    // MISSING: connect (flags QMetaObject::Connection; QObject sender, "PointerToMemberFunction" signal, "Functor" functor)
    // MISSING: connect (flags QMetaObject::Connection; QObject sender, "PointerToMemberFunction" signal, QObject context, "Functor" functor, flags Qt::ConnectionType type)
    new Function(c, "tr", _n_tr0, None, Compiled, qt_QObject_tr_string_QObject_string_string_int, Return, "string", Parameters, new Param(c, "sourceText", "string"), new Param(c, "disambiguation", "string", Value(nullptr)), new Param(c, "n", "int", Value((int)-1)), End),
    EndArguments);
globalScope()->addSymbols(
    EndArguments);
scope()->addSymbols(
    EndArguments);

//
// Copyright (C) 2023  Autodesk, Inc. All Rights Reserved. 
// 
// SPDX-License-Identifier: Apache-2.0 
//

addSymbols( new Function(c, "findChild", findChild, None,
                         Return, ftn,
                         Parameters,
                         new Param(c, "this", ftn),
                         new Param(c, "name", "string"),
                         End),

            new Function(c, "setProperty", setProperty, None,
                         Return, "bool",
                         Parameters,
                         new Param(c, "this", ftn),
                         new Param(c, "name", "string"),
                         new Param(c, "value", "qt.QVariant"),
                         End),

            EndArguments);

    const char** propExclusions = 0;

    populate(this, QObject::staticMetaObject, propExclusions);
}

} // Mu
