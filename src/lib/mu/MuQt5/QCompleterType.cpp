//
// Copyright (c) 2009, Jim Hourihan
// All rights reserved.
//
// SPDX-License-Identifier: Apache-2.0
//
#include <MuQt5/qtUtils.h>
#include <MuQt5/QCompleterType.h>
#include <QtGui/QtGui>
#include <QtWidgets/QtWidgets>
#include <QtSvg/QtSvg>
#include <QtNetwork/QtNetwork>
#include <MuQt5/QWidgetType.h>
#include <MuQt5/QActionType.h>
#include <MuQt5/QIconType.h>
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
#include <MuQt5/QAbstractItemModelType.h>
#include <MuQt5/QEventType.h>
#include <MuQt5/QAbstractItemViewType.h>
#include <MuQt5/QModelIndexType.h>
#include <MuQt5/QWidgetType.h>
#include <MuQt5/QTimerEventType.h>
#include <MuQt5/QObjectType.h>

//
//  NOTE: this file was automatically generated by qt2mu.py
//

namespace Mu
{
    using namespace std;

    //----------------------------------------------------------------------
    //  INHERITABLE TYPE IMPLEMENTATION

    // destructor
    MuQt_QCompleter::~MuQt_QCompleter()
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

    MuQt_QCompleter::MuQt_QCompleter(Pointer muobj, const CallEnvironment* ce,
                                     QObject* parent)
        : QCompleter(parent)
    {
        _env = ce;
        _obj = reinterpret_cast<ClassInstance*>(muobj);
        _obj->retainExternal();
        MuLangContext* c = (MuLangContext*)_env->context();
        _baseType = c->findSymbolOfTypeByQualifiedName<QCompleterType>(
            c->internName("qt.QCompleter"));
    }

    MuQt_QCompleter::MuQt_QCompleter(Pointer muobj, const CallEnvironment* ce,
                                     QAbstractItemModel* model, QObject* parent)
        : QCompleter(model, parent)
    {
        _env = ce;
        _obj = reinterpret_cast<ClassInstance*>(muobj);
        _obj->retainExternal();
        MuLangContext* c = (MuLangContext*)_env->context();
        _baseType = c->findSymbolOfTypeByQualifiedName<QCompleterType>(
            c->internName("qt.QCompleter"));
    }

    MuQt_QCompleter::MuQt_QCompleter(Pointer muobj, const CallEnvironment* ce,
                                     const QStringList& list, QObject* parent)
        : QCompleter(list, parent)
    {
        _env = ce;
        _obj = reinterpret_cast<ClassInstance*>(muobj);
        _obj->retainExternal();
        MuLangContext* c = (MuLangContext*)_env->context();
        _baseType = c->findSymbolOfTypeByQualifiedName<QCompleterType>(
            c->internName("qt.QCompleter"));
    }

    QString MuQt_QCompleter::pathFromIndex(const QModelIndex& index) const
    {
        if (!_env)
            return QCompleter::pathFromIndex(index);
        MuLangContext* c = (MuLangContext*)_env->context();
        const MemberFunction* F0 = _baseType->_func[0];
        const MemberFunction* F = _obj->classType()->dynamicLookup(F0);
        if (F != F0)
        {
            Function::ArgumentVector args(2);
            args[0] = Value(Pointer(_obj));
            args[1] =
                Value(makeqtype<QModelIndexType>(c, index, "qt.QModelIndex"));
            Value rval = _env->call(F, args);
            return qstring(rval._Pointer);
        }
        else
        {
            return QCompleter::pathFromIndex(index);
        }
    }

    QStringList MuQt_QCompleter::splitPath(const QString& path) const
    {
        if (!_env)
            return QCompleter::splitPath(path);
        MuLangContext* c = (MuLangContext*)_env->context();
        const MemberFunction* F0 = _baseType->_func[1];
        const MemberFunction* F = _obj->classType()->dynamicLookup(F0);
        if (F != F0)
        {
            Function::ArgumentVector args(2);
            args[0] = Value(Pointer(_obj));
            args[1] = Value(makestring(c, path));
            Value rval = _env->call(F, args);
            return qstringlist(rval._Pointer);
        }
        else
        {
            return QCompleter::splitPath(path);
        }
    }

    bool MuQt_QCompleter::event(QEvent* ev)
    {
        if (!_env)
            return QCompleter::event(ev);
        MuLangContext* c = (MuLangContext*)_env->context();
        const MemberFunction* F0 = _baseType->_func[2];
        const MemberFunction* F = _obj->classType()->dynamicLookup(F0);
        if (F != F0)
        {
            Function::ArgumentVector args(2);
            args[0] = Value(Pointer(_obj));
            args[1] = Value(makeqpointer<QEventType>(c, ev, "qt.QEvent"));
            Value rval = _env->call(F, args);
            return (bool)(rval._bool);
        }
        else
        {
            return QCompleter::event(ev);
        }
    }

    bool MuQt_QCompleter::eventFilter(QObject* o, QEvent* e)
    {
        if (!_env)
            return QCompleter::eventFilter(o, e);
        MuLangContext* c = (MuLangContext*)_env->context();
        const MemberFunction* F0 = _baseType->_func[3];
        const MemberFunction* F = _obj->classType()->dynamicLookup(F0);
        if (F != F0)
        {
            Function::ArgumentVector args(3);
            args[0] = Value(Pointer(_obj));
            args[1] = Value(makeinstance<QObjectType>(c, o, "qt.QObject"));
            args[2] = Value(makeqpointer<QEventType>(c, e, "qt.QEvent"));
            Value rval = _env->call(F, args);
            return (bool)(rval._bool);
        }
        else
        {
            return QCompleter::eventFilter(o, e);
        }
    }

    void MuQt_QCompleter::customEvent(QEvent* event)
    {
        if (!_env)
        {
            QCompleter::customEvent(event);
            return;
        }
        MuLangContext* c = (MuLangContext*)_env->context();
        const MemberFunction* F0 = _baseType->_func[4];
        const MemberFunction* F = _obj->classType()->dynamicLookup(F0);
        if (F != F0)
        {
            Function::ArgumentVector args(2);
            args[0] = Value(Pointer(_obj));
            args[1] = Value(makeqpointer<QEventType>(c, event, "qt.QEvent"));
            Value rval = _env->call(F, args);
        }
        else
        {
            QCompleter::customEvent(event);
        }
    }

    void MuQt_QCompleter::timerEvent(QTimerEvent* event)
    {
        if (!_env)
        {
            QCompleter::timerEvent(event);
            return;
        }
        MuLangContext* c = (MuLangContext*)_env->context();
        const MemberFunction* F0 = _baseType->_func[5];
        const MemberFunction* F = _obj->classType()->dynamicLookup(F0);
        if (F != F0)
        {
            Function::ArgumentVector args(2);
            args[0] = Value(Pointer(_obj));
            args[1] = Value(
                makeqpointer<QTimerEventType>(c, event, "qt.QTimerEvent"));
            Value rval = _env->call(F, args);
        }
        else
        {
            QCompleter::timerEvent(event);
        }
    }

    //----------------------------------------------------------------------
    //  Mu Type CONSTRUCTORS

    QCompleterType::QCompleterType(Context* c, const char* name, Class* super,
                                   Class* super2)
        : Class(c, name, vectorOf2(super, super2))
    {
    }

    QCompleterType::~QCompleterType() {}

    //----------------------------------------------------------------------
    //  PRE-COMPILED FUNCTIONS

    static Pointer QCompleter_QCompleter_QObject(Thread& NODE_THREAD,
                                                 Pointer obj)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        ClassInstance* widget = reinterpret_cast<ClassInstance*>(obj);

        if (!widget)
        {
            return 0;
        }
        else if (QCompleter* w = object<QCompleter>(widget))
        {
            QCompleterType* type =
                c->findSymbolOfTypeByQualifiedName<QCompleterType>(
                    c->internName("qt.QCompleter"), false);
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
        NODE_RETURN(
            QCompleter_QCompleter_QObject(NODE_THREAD, NODE_ARG(0, Pointer)));
    }

    Pointer qt_QCompleter_QCompleter_QCompleter_QCompleter_QObject(
        Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_parent)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QObject* arg1 = object<QObject>(param_parent);
        setobject(param_this,
                  new MuQt_QCompleter(param_this,
                                      NODE_THREAD.process()->callEnv(), arg1));
        return param_this;
    }

    Pointer
    qt_QCompleter_QCompleter_QCompleter_QCompleter_QAbstractItemModel_QObject(
        Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_model,
        Pointer param_parent)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QAbstractItemModel* arg1 = object<QAbstractItemModel>(param_model);
        QObject* arg2 = object<QObject>(param_parent);
        setobject(param_this, new MuQt_QCompleter(
                                  param_this, NODE_THREAD.process()->callEnv(),
                                  arg1, arg2));
        return param_this;
    }

    Pointer
    qt_QCompleter_QCompleter_QCompleter_QCompleter_stringBSB_ESB__QObject(
        Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_list,
        Pointer param_parent)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        const QStringList arg1 = qstringlist(param_list);
        QObject* arg2 = object<QObject>(param_parent);
        setobject(param_this, new MuQt_QCompleter(
                                  param_this, NODE_THREAD.process()->callEnv(),
                                  arg1, arg2));
        return param_this;
    }

    int qt_QCompleter_completionCount_int_QCompleter(Mu::Thread& NODE_THREAD,
                                                     Pointer param_this)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        return arg0->completionCount();
    }

    Pointer qt_QCompleter_completionModel_QAbstractItemModel_QCompleter(
        Mu::Thread& NODE_THREAD, Pointer param_this)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        return makeinstance<QAbstractItemModelType>(c, arg0->completionModel(),
                                                    "qt.QAbstractItemModel");
    }

    Pointer
    qt_QCompleter_currentCompletion_string_QCompleter(Mu::Thread& NODE_THREAD,
                                                      Pointer param_this)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        return makestring(c, arg0->currentCompletion());
    }

    Pointer
    qt_QCompleter_currentIndex_QModelIndex_QCompleter(Mu::Thread& NODE_THREAD,
                                                      Pointer param_this)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        return makeqtype<QModelIndexType>(c, arg0->currentIndex(),
                                          "qt.QModelIndex");
    }

    int qt_QCompleter_currentRow_int_QCompleter(Mu::Thread& NODE_THREAD,
                                                Pointer param_this)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        return arg0->currentRow();
    }

    Pointer
    qt_QCompleter_model_QAbstractItemModel_QCompleter(Mu::Thread& NODE_THREAD,
                                                      Pointer param_this)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        return makeinstance<QAbstractItemModelType>(c, arg0->model(),
                                                    "qt.QAbstractItemModel");
    }

    Pointer qt_QCompleter_pathFromIndex_string_QCompleter_QModelIndex(
        Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_index)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        const QModelIndex arg1 = getqtype<QModelIndexType>(param_index);
        return isMuQtObject(arg0)
                   ? makestring(c, arg0->QCompleter::pathFromIndex(arg1))
                   : makestring(c, arg0->pathFromIndex(arg1));
    }

    Pointer
    qt_QCompleter_popup_QAbstractItemView_QCompleter(Mu::Thread& NODE_THREAD,
                                                     Pointer param_this)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        return makeinstance<QAbstractItemViewType>(c, arg0->popup(),
                                                   "qt.QAbstractItemView");
    }

    bool qt_QCompleter_setCurrentRow_bool_QCompleter_int(
        Mu::Thread& NODE_THREAD, Pointer param_this, int param_row)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        int arg1 = (int)(param_row);
        return arg0->setCurrentRow(arg1);
    }

    void qt_QCompleter_setModel_void_QCompleter_QAbstractItemModel(
        Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_model)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        QAbstractItemModel* arg1 = object<QAbstractItemModel>(param_model);
        arg0->setModel(arg1);
    }

    void qt_QCompleter_setPopup_void_QCompleter_QAbstractItemView(
        Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_popup)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        QAbstractItemView* arg1 = object<QAbstractItemView>(param_popup);
        arg0->setPopup(arg1);
    }

    void qt_QCompleter_setWidget_void_QCompleter_QWidget(
        Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_widget)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        QWidget* arg1 = object<QWidget>(param_widget);
        arg0->setWidget(arg1);
    }

    Pointer qt_QCompleter_splitPath_stringBSB_ESB__QCompleter_string(
        Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_path)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        const QString arg1 = qstring(param_path);
        return isMuQtObject(arg0)
                   ? makestringlist(c, arg0->QCompleter::splitPath(arg1))
                   : makestringlist(c, arg0->splitPath(arg1));
    }

    Pointer qt_QCompleter_widget_QWidget_QCompleter(Mu::Thread& NODE_THREAD,
                                                    Pointer param_this)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        return makeinstance<QWidgetType>(c, arg0->widget(), "qt.QWidget");
    }

    bool qt_QCompleter_event_bool_QCompleter_QEvent(Mu::Thread& NODE_THREAD,
                                                    Pointer param_this,
                                                    Pointer param_ev)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        QEvent* arg1 = getqpointer<QEventType>(param_ev);
        return isMuQtObject(arg0)
                   ? ((MuQt_QCompleter*)arg0)->event_pub_parent(arg1)
                   : ((MuQt_QCompleter*)arg0)->event_pub(arg1);
    }

    bool qt_QCompleter_eventFilter_bool_QCompleter_QObject_QEvent(
        Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_o,
        Pointer param_e)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        QObject* arg1 = object<QObject>(param_o);
        QEvent* arg2 = getqpointer<QEventType>(param_e);
        return isMuQtObject(arg0)
                   ? ((MuQt_QCompleter*)arg0)
                         ->eventFilter_pub_parent(arg1, arg2)
                   : ((MuQt_QCompleter*)arg0)->eventFilter_pub(arg1, arg2);
    }

    void qt_QCompleter_customEvent_void_QCompleter_QEvent(
        Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_event)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        QEvent* arg1 = getqpointer<QEventType>(param_event);
        if (isMuQtObject(arg0))
            ((MuQt_QCompleter*)arg0)->customEvent_pub_parent(arg1);
        else
            ((MuQt_QCompleter*)arg0)->customEvent_pub(arg1);
    }

    void qt_QCompleter_timerEvent_void_QCompleter_QTimerEvent(
        Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_event)
    {
        MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
        QCompleter* arg0 = object<QCompleter>(param_this);
        QTimerEvent* arg1 = getqpointer<QTimerEventType>(param_event);
        if (isMuQtObject(arg0))
            ((MuQt_QCompleter*)arg0)->timerEvent_pub_parent(arg1);
        else
            ((MuQt_QCompleter*)arg0)->timerEvent_pub(arg1);
    }

    static NODE_IMPLEMENTATION(_n_QCompleter0, Pointer)
    {
        NODE_RETURN(qt_QCompleter_QCompleter_QCompleter_QCompleter_QObject(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_QCompleter1, Pointer)
    {
        NODE_RETURN(
            qt_QCompleter_QCompleter_QCompleter_QCompleter_QAbstractItemModel_QObject(
                NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer),
                NODE_ARG(2, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_QCompleter2, Pointer)
    {
        NODE_RETURN(
            qt_QCompleter_QCompleter_QCompleter_QCompleter_stringBSB_ESB__QObject(
                NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer),
                NODE_ARG(2, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_completionCount0, int)
    {
        NODE_RETURN(qt_QCompleter_completionCount_int_QCompleter(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_completionModel0, Pointer)
    {
        NODE_RETURN(qt_QCompleter_completionModel_QAbstractItemModel_QCompleter(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_currentCompletion0, Pointer)
    {
        NODE_RETURN(qt_QCompleter_currentCompletion_string_QCompleter(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_currentIndex0, Pointer)
    {
        NODE_RETURN(qt_QCompleter_currentIndex_QModelIndex_QCompleter(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_currentRow0, int)
    {
        NODE_RETURN(qt_QCompleter_currentRow_int_QCompleter(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_model0, Pointer)
    {
        NODE_RETURN(qt_QCompleter_model_QAbstractItemModel_QCompleter(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_pathFromIndex0, Pointer)
    {
        NODE_RETURN(qt_QCompleter_pathFromIndex_string_QCompleter_QModelIndex(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_popup0, Pointer)
    {
        NODE_RETURN(qt_QCompleter_popup_QAbstractItemView_QCompleter(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_setCurrentRow0, bool)
    {
        NODE_RETURN(qt_QCompleter_setCurrentRow_bool_QCompleter_int(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int)));
    }

    static NODE_IMPLEMENTATION(_n_setModel0, void)
    {
        qt_QCompleter_setModel_void_QCompleter_QAbstractItemModel(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
    }

    static NODE_IMPLEMENTATION(_n_setPopup0, void)
    {
        qt_QCompleter_setPopup_void_QCompleter_QAbstractItemView(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
    }

    static NODE_IMPLEMENTATION(_n_setWidget0, void)
    {
        qt_QCompleter_setWidget_void_QCompleter_QWidget(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
    }

    static NODE_IMPLEMENTATION(_n_splitPath0, Pointer)
    {
        NODE_RETURN(qt_QCompleter_splitPath_stringBSB_ESB__QCompleter_string(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_widget0, Pointer)
    {
        NODE_RETURN(qt_QCompleter_widget_QWidget_QCompleter(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_event0, bool)
    {
        NODE_RETURN(qt_QCompleter_event_bool_QCompleter_QEvent(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_eventFilter0, bool)
    {
        NODE_RETURN(qt_QCompleter_eventFilter_bool_QCompleter_QObject_QEvent(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer),
            NODE_ARG(2, Pointer)));
    }

    static NODE_IMPLEMENTATION(_n_customEvent0, void)
    {
        qt_QCompleter_customEvent_void_QCompleter_QEvent(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
    }

    static NODE_IMPLEMENTATION(_n_timerEvent0, void)
    {
        qt_QCompleter_timerEvent_void_QCompleter_QTimerEvent(
            NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
    }

    void QCompleterType::load()
    {
        USING_MU_FUNCTION_SYMBOLS;
        MuLangContext* c = static_cast<MuLangContext*>(context());
        Module* global = globalModule();

        const string typeName = name();
        const string refTypeName = typeName + "&";
        const string fullTypeName = fullyQualifiedName();
        const string fullRefTypeName = fullTypeName + "&";
        const char* tn = typeName.c_str();
        const char* ftn = fullTypeName.c_str();
        const char* rtn = refTypeName.c_str();
        const char* frtn = fullRefTypeName.c_str();

        scope()->addSymbols(new ReferenceType(c, rtn, this),

                            new Function(c, tn, BaseFunctions::dereference,
                                         Cast, Return, ftn, Args, frtn, End),

                            EndArguments);

        addSymbols(new Function(c, "__allocate", BaseFunctions::classAllocate,
                                None, Return, ftn, End),

                   new Function(c, tn, castFromObject, Cast, Compiled,
                                QCompleter_QCompleter_QObject, Return, ftn,
                                Parameters,
                                new Param(c, "object", "qt.QObject"), End),

                   EndArguments);

        addSymbols(
            // enums
            // member functions
            new Function(c, "QCompleter", _n_QCompleter0, None, Compiled,
                         qt_QCompleter_QCompleter_QCompleter_QCompleter_QObject,
                         Return, "qt.QCompleter", Parameters,
                         new Param(c, "this", "qt.QCompleter"),
                         new Param(c, "parent", "qt.QObject"), End),
            new Function(
                c, "QCompleter", _n_QCompleter1, None, Compiled,
                qt_QCompleter_QCompleter_QCompleter_QCompleter_QAbstractItemModel_QObject,
                Return, "qt.QCompleter", Parameters,
                new Param(c, "this", "qt.QCompleter"),
                new Param(c, "model", "qt.QAbstractItemModel"),
                new Param(c, "parent", "qt.QObject"), End),
            new Function(
                c, "QCompleter", _n_QCompleter2, None, Compiled,
                qt_QCompleter_QCompleter_QCompleter_QCompleter_stringBSB_ESB__QObject,
                Return, "qt.QCompleter", Parameters,
                new Param(c, "this", "qt.QCompleter"),
                new Param(c, "list", "string[]"),
                new Param(c, "parent", "qt.QObject"), End),
            // PROP: caseSensitivity (flags Qt::CaseSensitivity; QCompleter
            // this) PROP: completionColumn (int; QCompleter this)
            new Function(c, "completionCount", _n_completionCount0, None,
                         Compiled, qt_QCompleter_completionCount_int_QCompleter,
                         Return, "int", Parameters,
                         new Param(c, "this", "qt.QCompleter"), End),
            // PROP: completionMode (flags QCompleter::CompletionMode;
            // QCompleter this)
            new Function(
                c, "completionModel", _n_completionModel0, None, Compiled,
                qt_QCompleter_completionModel_QAbstractItemModel_QCompleter,
                Return, "qt.QAbstractItemModel", Parameters,
                new Param(c, "this", "qt.QCompleter"), End),
            // PROP: completionPrefix (string; QCompleter this)
            // PROP: completionRole (int; QCompleter this)
            new Function(c, "currentCompletion", _n_currentCompletion0, None,
                         Compiled,
                         qt_QCompleter_currentCompletion_string_QCompleter,
                         Return, "string", Parameters,
                         new Param(c, "this", "qt.QCompleter"), End),
            new Function(c, "currentIndex", _n_currentIndex0, None, Compiled,
                         qt_QCompleter_currentIndex_QModelIndex_QCompleter,
                         Return, "qt.QModelIndex", Parameters,
                         new Param(c, "this", "qt.QCompleter"), End),
            new Function(c, "currentRow", _n_currentRow0, None, Compiled,
                         qt_QCompleter_currentRow_int_QCompleter, Return, "int",
                         Parameters, new Param(c, "this", "qt.QCompleter"),
                         End),
            // PROP: filterMode (flags Qt::MatchFlags; QCompleter this)
            // PROP: maxVisibleItems (int; QCompleter this)
            new Function(c, "model", _n_model0, None, Compiled,
                         qt_QCompleter_model_QAbstractItemModel_QCompleter,
                         Return, "qt.QAbstractItemModel", Parameters,
                         new Param(c, "this", "qt.QCompleter"), End),
            // PROP: modelSorting (flags QCompleter::ModelSorting; QCompleter
            // this)
            _func[0] = new MemberFunction(
                c, "pathFromIndex", _n_pathFromIndex0, None, Compiled,
                qt_QCompleter_pathFromIndex_string_QCompleter_QModelIndex,
                Return, "string", Parameters,
                new Param(c, "this", "qt.QCompleter"),
                new Param(c, "index", "qt.QModelIndex"), End),
            new Function(c, "popup", _n_popup0, None, Compiled,
                         qt_QCompleter_popup_QAbstractItemView_QCompleter,
                         Return, "qt.QAbstractItemView", Parameters,
                         new Param(c, "this", "qt.QCompleter"), End),
            // PROP: setCaseSensitivity (void; QCompleter this, flags
            // Qt::CaseSensitivity caseSensitivity) PROP: setCompletionColumn
            // (void; QCompleter this, int column) PROP: setCompletionMode
            // (void; QCompleter this, flags QCompleter::CompletionMode mode)
            // PROP: setCompletionRole (void; QCompleter this, int role)
            new Function(c, "setCurrentRow", _n_setCurrentRow0, None, Compiled,
                         qt_QCompleter_setCurrentRow_bool_QCompleter_int,
                         Return, "bool", Parameters,
                         new Param(c, "this", "qt.QCompleter"),
                         new Param(c, "row", "int"), End),
            // PROP: setFilterMode (void; QCompleter this, flags Qt::MatchFlags
            // filterMode) PROP: setMaxVisibleItems (void; QCompleter this, int
            // maxItems)
            new Function(
                c, "setModel", _n_setModel0, None, Compiled,
                qt_QCompleter_setModel_void_QCompleter_QAbstractItemModel,
                Return, "void", Parameters,
                new Param(c, "this", "qt.QCompleter"),
                new Param(c, "model", "qt.QAbstractItemModel"), End),
            // PROP: setModelSorting (void; QCompleter this, flags
            // QCompleter::ModelSorting sorting)
            new Function(
                c, "setPopup", _n_setPopup0, None, Compiled,
                qt_QCompleter_setPopup_void_QCompleter_QAbstractItemView,
                Return, "void", Parameters,
                new Param(c, "this", "qt.QCompleter"),
                new Param(c, "popup", "qt.QAbstractItemView"), End),
            new Function(c, "setWidget", _n_setWidget0, None, Compiled,
                         qt_QCompleter_setWidget_void_QCompleter_QWidget,
                         Return, "void", Parameters,
                         new Param(c, "this", "qt.QCompleter"),
                         new Param(c, "widget", "qt.QWidget"), End),
            _func[1] = new MemberFunction(
                c, "splitPath", _n_splitPath0, None, Compiled,
                qt_QCompleter_splitPath_stringBSB_ESB__QCompleter_string,
                Return, "string[]", Parameters,
                new Param(c, "this", "qt.QCompleter"),
                new Param(c, "path", "string"), End),
            new Function(c, "widget", _n_widget0, None, Compiled,
                         qt_QCompleter_widget_QWidget_QCompleter, Return,
                         "qt.QWidget", Parameters,
                         new Param(c, "this", "qt.QCompleter"), End),
            // PROP: wrapAround (bool; QCompleter this)
            _func[2] = new MemberFunction(
                c, "event", _n_event0, None, Compiled,
                qt_QCompleter_event_bool_QCompleter_QEvent, Return, "bool",
                Parameters, new Param(c, "this", "qt.QCompleter"),
                new Param(c, "ev", "qt.QEvent"), End),
            _func[3] = new MemberFunction(
                c, "eventFilter", _n_eventFilter0, None, Compiled,
                qt_QCompleter_eventFilter_bool_QCompleter_QObject_QEvent,
                Return, "bool", Parameters,
                new Param(c, "this", "qt.QCompleter"),
                new Param(c, "o", "qt.QObject"), new Param(c, "e", "qt.QEvent"),
                End),
            // MISSING: metaObject ("const QMetaObject *"; QCompleter this)
            // MISSING: childEvent (void; QCompleter this, "QChildEvent *"
            // event) // protected MISSING: connectNotify (void; QCompleter
            // this, "const QMetaMethod &" signal) // protected
            _func[4] = new MemberFunction(
                c, "customEvent", _n_customEvent0, None, Compiled,
                qt_QCompleter_customEvent_void_QCompleter_QEvent, Return,
                "void", Parameters, new Param(c, "this", "qt.QCompleter"),
                new Param(c, "event", "qt.QEvent"), End),
            // MISSING: disconnectNotify (void; QCompleter this, "const
            // QMetaMethod &" signal) // protected
            _func[5] = new MemberFunction(
                c, "timerEvent", _n_timerEvent0, None, Compiled,
                qt_QCompleter_timerEvent_void_QCompleter_QTimerEvent, Return,
                "void", Parameters, new Param(c, "this", "qt.QCompleter"),
                new Param(c, "event", "qt.QTimerEvent"), End),
            // static functions
            EndArguments);
        globalScope()->addSymbols(EndArguments);
        scope()->addSymbols(EndArguments);

        const char** propExclusions = 0;

        populate(this, QCompleter::staticMetaObject, propExclusions);
    }

} // namespace Mu
