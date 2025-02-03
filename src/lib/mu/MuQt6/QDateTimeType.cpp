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
#include <MuQt6/QDateTimeType.h>
#include <MuQt6/QActionType.h>
#include <MuQt6/QWidgetType.h>
#include <Mu/Alias.h>
#include <Mu/BaseFunctions.h>
#include <Mu/ClassInstance.h>
#include <Mu/Exception.h>
#include <Mu/Function.h>
#include <Mu/MemberFunction.h>
#include <Mu/MemberVariable.h>
#include <Mu/Node.h>
#include <Mu/ParameterVariable.h>
#include <Mu/ReferenceType.h>
#include <Mu/SymbolicConstant.h>
#include <Mu/Thread.h>
#include <Mu/Value.h>
#include <MuLang/MuLangContext.h>
#include <MuLang/StringType.h>
#include <QtGui/QtGui>
#include <QtWidgets/QtWidgets>
#include <QtSvg/QtSvg>
#include <QSvgWidget>
#include <QtNetwork/QtNetwork>
#include <MuQt6/QTimeType.h>
#include <MuQt6/QDateType.h>
#include <MuQt6/QTimeZoneType.h>

namespace Mu {
using namespace std;

QDateTimeType::Instance::Instance(const Class* c) : ClassInstance(c)
{
}

QDateTimeType::QDateTimeType(Context* c, const char* name, Class* super)
    : Class(c, name, super)
{
}

QDateTimeType::~QDateTimeType()
{
}

static NODE_IMPLEMENTATION(__allocate, Pointer)
{
    QDateTimeType::Instance* i = new QDateTimeType::Instance((Class*)NODE_THIS.type());
    QDateTimeType::registerFinalizer(i);
    NODE_RETURN(i);
}

void 
QDateTimeType::registerFinalizer (void* o)
{
    GC_register_finalizer(o, QDateTimeType::finalizer, 0, 0, 0);
}

void 
QDateTimeType::finalizer (void* obj, void* data)
{
    QDateTimeType::Instance* i = reinterpret_cast<QDateTimeType::Instance*>(obj);
    delete i;
}

//----------------------------------------------------------------------
//  PRE-COMPILED FUNCTIONS

Pointer qt_QDateTime_QDateTime_QDateTime_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    setqtype<QDateTimeType>(param_this,QDateTime());
    return param_this;
}

Pointer qt_QDateTime_QDateTime_QDateTime_QDateTime_QDate_QTime_QTimeZone(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_date, Pointer param_time, Pointer param_timeZone)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDate arg1 = getqtype<QDateType>(param_date);
    QTime arg2 = getqtype<QTimeType>(param_time);
    const QTimeZone  arg3 = getqtype<QTimeZoneType>(param_timeZone);
    setqtype<QDateTimeType>(param_this,QDateTime(arg1, arg2, arg3));
    return param_this;
}

Pointer qt_QDateTime_QDateTime_QDateTime_QDateTime_QDate_QTime(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_date, Pointer param_time)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDate arg1 = getqtype<QDateType>(param_date);
    QTime arg2 = getqtype<QTimeType>(param_time);
    setqtype<QDateTimeType>(param_this,QDateTime(arg1, arg2));
    return param_this;
}

Pointer qt_QDateTime_addDays_QDateTime_QDateTime_int64(Mu::Thread& NODE_THREAD, Pointer param_this, int64 param_ndays)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    qint64 arg1 = (int64)(param_ndays);
    return makeqtype<QDateTimeType>(c,arg0.addDays(arg1),"qt.QDateTime");
}

Pointer qt_QDateTime_addDuration_QDateTime_QDateTime_int(Mu::Thread& NODE_THREAD, Pointer param_this, int param_msecs)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    std::chrono::milliseconds arg1 = (std::chrono::milliseconds)(param_msecs);
    return makeqtype<QDateTimeType>(c,arg0.addDuration(arg1),"qt.QDateTime");
}

Pointer qt_QDateTime_addMSecs_QDateTime_QDateTime_int64(Mu::Thread& NODE_THREAD, Pointer param_this, int64 param_msecs)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    qint64 arg1 = (int64)(param_msecs);
    return makeqtype<QDateTimeType>(c,arg0.addMSecs(arg1),"qt.QDateTime");
}

Pointer qt_QDateTime_addMonths_QDateTime_QDateTime_int(Mu::Thread& NODE_THREAD, Pointer param_this, int param_nmonths)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    int arg1 = (int)(param_nmonths);
    return makeqtype<QDateTimeType>(c,arg0.addMonths(arg1),"qt.QDateTime");
}

Pointer qt_QDateTime_addSecs_QDateTime_QDateTime_int64(Mu::Thread& NODE_THREAD, Pointer param_this, int64 param_s)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    qint64 arg1 = (int64)(param_s);
    return makeqtype<QDateTimeType>(c,arg0.addSecs(arg1),"qt.QDateTime");
}

Pointer qt_QDateTime_addYears_QDateTime_QDateTime_int(Mu::Thread& NODE_THREAD, Pointer param_this, int param_nyears)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    int arg1 = (int)(param_nyears);
    return makeqtype<QDateTimeType>(c,arg0.addYears(arg1),"qt.QDateTime");
}

Pointer qt_QDateTime_date_QDate_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return makeqtype<QDateType>(c,arg0.date(),"qt.QDate");
}

int64 qt_QDateTime_daysTo_int64_QDateTime_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_other)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    const QDateTime  arg1 = getqtype<QDateTimeType>(param_other);
    return arg0.daysTo(arg1);
}

bool qt_QDateTime_isDaylightTime_bool_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return arg0.isDaylightTime();
}

bool qt_QDateTime_isNull_bool_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return arg0.isNull();
}

bool qt_QDateTime_isValid_bool_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return arg0.isValid();
}

int64 qt_QDateTime_msecsTo_int64_QDateTime_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_other)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    const QDateTime  arg1 = getqtype<QDateTimeType>(param_other);
    return arg0.msecsTo(arg1);
}

int qt_QDateTime_offsetFromUtc_int_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return arg0.offsetFromUtc();
}

int64 qt_QDateTime_secsTo_int64_QDateTime_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_other)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    const QDateTime  arg1 = getqtype<QDateTimeType>(param_other);
    return arg0.secsTo(arg1);
}

void qt_QDateTime_setDate_void_QDateTime_QDate(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_date)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    QDate arg1 = getqtype<QDateType>(param_date);
    arg0.setDate(arg1);
    setqtype<QDateTimeType>(param_this,arg0);
}

void qt_QDateTime_setMSecsSinceEpoch_void_QDateTime_int64(Mu::Thread& NODE_THREAD, Pointer param_this, int64 param_msecs)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    qint64 arg1 = (int64)(param_msecs);
    arg0.setMSecsSinceEpoch(arg1);
    setqtype<QDateTimeType>(param_this,arg0);
}

void qt_QDateTime_setSecsSinceEpoch_void_QDateTime_int64(Mu::Thread& NODE_THREAD, Pointer param_this, int64 param_secs)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    qint64 arg1 = (int64)(param_secs);
    arg0.setSecsSinceEpoch(arg1);
    setqtype<QDateTimeType>(param_this,arg0);
}

void qt_QDateTime_setTime_void_QDateTime_QTime(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_time)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    QTime arg1 = getqtype<QTimeType>(param_time);
    arg0.setTime(arg1);
    setqtype<QDateTimeType>(param_this,arg0);
}

void qt_QDateTime_setTimeZone_void_QDateTime_QTimeZone(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_toZone)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    const QTimeZone  arg1 = getqtype<QTimeZoneType>(param_toZone);
    arg0.setTimeZone(arg1);
    setqtype<QDateTimeType>(param_this,arg0);
}

void qt_QDateTime_swap_void_QDateTime_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_other)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    QDateTime  arg1 = getqtype<QDateTimeType>(param_other);
    arg0.swap(arg1);
    setqtype<QDateTimeType>(param_this,arg0);
}

Pointer qt_QDateTime_time_QTime_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return makeqtype<QTimeType>(c,arg0.time(),"qt.QTime");
}

Pointer qt_QDateTime_timeRepresentation_QTimeZone_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return makeqtype<QTimeZoneType>(c,arg0.timeRepresentation(),"qt.QTimeZone");
}

int qt_QDateTime_timeSpec_int_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return int(arg0.timeSpec());
}

Pointer qt_QDateTime_timeZone_QTimeZone_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return makeqtype<QTimeZoneType>(c,arg0.timeZone(),"qt.QTimeZone");
}

Pointer qt_QDateTime_timeZoneAbbreviation_string_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return makestring(c,arg0.timeZoneAbbreviation());
}

Pointer qt_QDateTime_toLocalTime_QDateTime_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return makeqtype<QDateTimeType>(c,arg0.toLocalTime(),"qt.QDateTime");
}

int64 qt_QDateTime_toMSecsSinceEpoch_int64_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return arg0.toMSecsSinceEpoch();
}

Pointer qt_QDateTime_toOffsetFromUtc_QDateTime_QDateTime_int(Mu::Thread& NODE_THREAD, Pointer param_this, int param_offsetSeconds)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    int arg1 = (int)(param_offsetSeconds);
    return makeqtype<QDateTimeType>(c,arg0.toOffsetFromUtc(arg1),"qt.QDateTime");
}

int64 qt_QDateTime_toSecsSinceEpoch_int64_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return arg0.toSecsSinceEpoch();
}

Pointer qt_QDateTime_toString_string_QDateTime_int(Mu::Thread& NODE_THREAD, Pointer param_this, int param_format)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    Qt::DateFormat arg1 = (Qt::DateFormat)(param_format);
    return makestring(c,arg0.toString(arg1));
}

Pointer qt_QDateTime_toTimeZone_QDateTime_QDateTime_QTimeZone(Mu::Thread& NODE_THREAD, Pointer param_this, Pointer param_timeZone)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    const QTimeZone  arg1 = getqtype<QTimeZoneType>(param_timeZone);
    return makeqtype<QDateTimeType>(c,arg0.toTimeZone(arg1),"qt.QDateTime");
}

Pointer qt_QDateTime_toUTC_QDateTime_QDateTime(Mu::Thread& NODE_THREAD, Pointer param_this)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    return makeqtype<QDateTimeType>(c,arg0.toUTC(),"qt.QDateTime");
}

Pointer qt_QDateTime_operatorPlus_EQ__QDateTime_QDateTime_int(Mu::Thread& NODE_THREAD, Pointer param_this, int param_duration)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    std::chrono::milliseconds arg1 = (std::chrono::milliseconds)(param_duration);
    return makeqtype<QDateTimeType>(c,arg0.operator+=(arg1),"qt.QDateTime");
}

Pointer qt_QDateTime_operatorMinus_EQ__QDateTime_QDateTime_int(Mu::Thread& NODE_THREAD, Pointer param_this, int param_duration)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    QDateTime arg0 = getqtype<QDateTimeType>(param_this);
    std::chrono::milliseconds arg1 = (std::chrono::milliseconds)(param_duration);
    return makeqtype<QDateTimeType>(c,arg0.operator-=(arg1),"qt.QDateTime");
}

Pointer qt_QDateTime_currentDateTime_QDateTime_QTimeZone(Mu::Thread& NODE_THREAD, Pointer param_zone)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    const QTimeZone  arg0 = getqtype<QTimeZoneType>(param_zone);
    return makeqtype<QDateTimeType>(c,QDateTime::currentDateTime(arg0),"qt.QDateTime");
}

Pointer qt_QDateTime_currentDateTime_QDateTime(Mu::Thread& NODE_THREAD)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    return makeqtype<QDateTimeType>(c,QDateTime::currentDateTime(),"qt.QDateTime");
}

Pointer qt_QDateTime_currentDateTimeUtc_QDateTime(Mu::Thread& NODE_THREAD)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    return makeqtype<QDateTimeType>(c,QDateTime::currentDateTimeUtc(),"qt.QDateTime");
}

int64 qt_QDateTime_currentMSecsSinceEpoch_int64(Mu::Thread& NODE_THREAD)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    return QDateTime::currentMSecsSinceEpoch();
}

int64 qt_QDateTime_currentSecsSinceEpoch_int64(Mu::Thread& NODE_THREAD)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    return QDateTime::currentSecsSinceEpoch();
}

Pointer qt_QDateTime_fromMSecsSinceEpoch_QDateTime_int64_QTimeZone(Mu::Thread& NODE_THREAD, int64 param_msecs, Pointer param_timeZone)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    qint64 arg0 = (int64)(param_msecs);
    const QTimeZone  arg1 = getqtype<QTimeZoneType>(param_timeZone);
    return makeqtype<QDateTimeType>(c,QDateTime::fromMSecsSinceEpoch(arg0, arg1),"qt.QDateTime");
}

Pointer qt_QDateTime_fromMSecsSinceEpoch_QDateTime_int64(Mu::Thread& NODE_THREAD, int64 param_msecs)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    qint64 arg0 = (int64)(param_msecs);
    return makeqtype<QDateTimeType>(c,QDateTime::fromMSecsSinceEpoch(arg0),"qt.QDateTime");
}

Pointer qt_QDateTime_fromSecsSinceEpoch_QDateTime_int64_QTimeZone(Mu::Thread& NODE_THREAD, int64 param_secs, Pointer param_timeZone)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    qint64 arg0 = (int64)(param_secs);
    const QTimeZone  arg1 = getqtype<QTimeZoneType>(param_timeZone);
    return makeqtype<QDateTimeType>(c,QDateTime::fromSecsSinceEpoch(arg0, arg1),"qt.QDateTime");
}

Pointer qt_QDateTime_fromSecsSinceEpoch_QDateTime_int64(Mu::Thread& NODE_THREAD, int64 param_secs)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    qint64 arg0 = (int64)(param_secs);
    return makeqtype<QDateTimeType>(c,QDateTime::fromSecsSinceEpoch(arg0),"qt.QDateTime");
}

Pointer qt_QDateTime_fromString_QDateTime_string_int(Mu::Thread& NODE_THREAD, Pointer param_string, int param_format)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    const QString  arg0 = qstring(param_string);
    Qt::DateFormat arg1 = (Qt::DateFormat)(param_format);
    return makeqtype<QDateTimeType>(c,QDateTime::fromString(arg0, arg1),"qt.QDateTime");
}


static NODE_IMPLEMENTATION(_n_QDateTime0, Pointer)
{
    NODE_RETURN(qt_QDateTime_QDateTime_QDateTime_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_QDateTime1, Pointer)
{
    NODE_RETURN(qt_QDateTime_QDateTime_QDateTime_QDateTime_QDate_QTime_QTimeZone(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer), NODE_ARG(2, Pointer), NODE_ARG(3, Pointer)));
}

static NODE_IMPLEMENTATION(_n_QDateTime2, Pointer)
{
    NODE_RETURN(qt_QDateTime_QDateTime_QDateTime_QDateTime_QDate_QTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer), NODE_ARG(2, Pointer)));
}

static NODE_IMPLEMENTATION(_n_addDays0, Pointer)
{
    NODE_RETURN(qt_QDateTime_addDays_QDateTime_QDateTime_int64(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int64)));
}

static NODE_IMPLEMENTATION(_n_addDuration0, Pointer)
{
    NODE_RETURN(qt_QDateTime_addDuration_QDateTime_QDateTime_int(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int)));
}

static NODE_IMPLEMENTATION(_n_addMSecs0, Pointer)
{
    NODE_RETURN(qt_QDateTime_addMSecs_QDateTime_QDateTime_int64(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int64)));
}

static NODE_IMPLEMENTATION(_n_addMonths0, Pointer)
{
    NODE_RETURN(qt_QDateTime_addMonths_QDateTime_QDateTime_int(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int)));
}

static NODE_IMPLEMENTATION(_n_addSecs0, Pointer)
{
    NODE_RETURN(qt_QDateTime_addSecs_QDateTime_QDateTime_int64(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int64)));
}

static NODE_IMPLEMENTATION(_n_addYears0, Pointer)
{
    NODE_RETURN(qt_QDateTime_addYears_QDateTime_QDateTime_int(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int)));
}

static NODE_IMPLEMENTATION(_n_date0, Pointer)
{
    NODE_RETURN(qt_QDateTime_date_QDate_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_daysTo0, int64)
{
    NODE_RETURN(qt_QDateTime_daysTo_int64_QDateTime_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer)));
}

static NODE_IMPLEMENTATION(_n_isDaylightTime0, bool)
{
    NODE_RETURN(qt_QDateTime_isDaylightTime_bool_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_isNull0, bool)
{
    NODE_RETURN(qt_QDateTime_isNull_bool_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_isValid0, bool)
{
    NODE_RETURN(qt_QDateTime_isValid_bool_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_msecsTo0, int64)
{
    NODE_RETURN(qt_QDateTime_msecsTo_int64_QDateTime_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer)));
}

static NODE_IMPLEMENTATION(_n_offsetFromUtc0, int)
{
    NODE_RETURN(qt_QDateTime_offsetFromUtc_int_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_secsTo0, int64)
{
    NODE_RETURN(qt_QDateTime_secsTo_int64_QDateTime_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer)));
}

static NODE_IMPLEMENTATION(_n_setDate0, void)
{
    qt_QDateTime_setDate_void_QDateTime_QDate(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
}

static NODE_IMPLEMENTATION(_n_setMSecsSinceEpoch0, void)
{
    qt_QDateTime_setMSecsSinceEpoch_void_QDateTime_int64(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int64));
}

static NODE_IMPLEMENTATION(_n_setSecsSinceEpoch0, void)
{
    qt_QDateTime_setSecsSinceEpoch_void_QDateTime_int64(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int64));
}

static NODE_IMPLEMENTATION(_n_setTime0, void)
{
    qt_QDateTime_setTime_void_QDateTime_QTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
}

static NODE_IMPLEMENTATION(_n_setTimeZone0, void)
{
    qt_QDateTime_setTimeZone_void_QDateTime_QTimeZone(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
}

static NODE_IMPLEMENTATION(_n_swap0, void)
{
    qt_QDateTime_swap_void_QDateTime_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer));
}

static NODE_IMPLEMENTATION(_n_time0, Pointer)
{
    NODE_RETURN(qt_QDateTime_time_QTime_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_timeRepresentation0, Pointer)
{
    NODE_RETURN(qt_QDateTime_timeRepresentation_QTimeZone_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_timeSpec0, int)
{
    NODE_RETURN(qt_QDateTime_timeSpec_int_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_timeZone0, Pointer)
{
    NODE_RETURN(qt_QDateTime_timeZone_QTimeZone_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_timeZoneAbbreviation0, Pointer)
{
    NODE_RETURN(qt_QDateTime_timeZoneAbbreviation_string_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_toLocalTime0, Pointer)
{
    NODE_RETURN(qt_QDateTime_toLocalTime_QDateTime_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_toMSecsSinceEpoch0, int64)
{
    NODE_RETURN(qt_QDateTime_toMSecsSinceEpoch_int64_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_toOffsetFromUtc0, Pointer)
{
    NODE_RETURN(qt_QDateTime_toOffsetFromUtc_QDateTime_QDateTime_int(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int)));
}

static NODE_IMPLEMENTATION(_n_toSecsSinceEpoch0, int64)
{
    NODE_RETURN(qt_QDateTime_toSecsSinceEpoch_int64_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_toString1, Pointer)
{
    NODE_RETURN(qt_QDateTime_toString_string_QDateTime_int(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int)));
}

static NODE_IMPLEMENTATION(_n_toTimeZone0, Pointer)
{
    NODE_RETURN(qt_QDateTime_toTimeZone_QDateTime_QDateTime_QTimeZone(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, Pointer)));
}

static NODE_IMPLEMENTATION(_n_toUTC0, Pointer)
{
    NODE_RETURN(qt_QDateTime_toUTC_QDateTime_QDateTime(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_operatorPlus_EQ_0, Pointer)
{
    NODE_RETURN(qt_QDateTime_operatorPlus_EQ__QDateTime_QDateTime_int(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int)));
}

static NODE_IMPLEMENTATION(_n_operatorMinus_EQ_0, Pointer)
{
    NODE_RETURN(qt_QDateTime_operatorMinus_EQ__QDateTime_QDateTime_int(NODE_THREAD, NONNIL_NODE_ARG(0, Pointer), NODE_ARG(1, int)));
}

static NODE_IMPLEMENTATION(_n_currentDateTime0, Pointer)
{
    NODE_RETURN(qt_QDateTime_currentDateTime_QDateTime_QTimeZone(NODE_THREAD, NODE_ARG(0, Pointer)));
}

static NODE_IMPLEMENTATION(_n_currentDateTime1, Pointer)
{
    NODE_RETURN(qt_QDateTime_currentDateTime_QDateTime(NODE_THREAD));
}

static NODE_IMPLEMENTATION(_n_currentDateTimeUtc0, Pointer)
{
    NODE_RETURN(qt_QDateTime_currentDateTimeUtc_QDateTime(NODE_THREAD));
}

static NODE_IMPLEMENTATION(_n_currentMSecsSinceEpoch0, int64)
{
    NODE_RETURN(qt_QDateTime_currentMSecsSinceEpoch_int64(NODE_THREAD));
}

static NODE_IMPLEMENTATION(_n_currentSecsSinceEpoch0, int64)
{
    NODE_RETURN(qt_QDateTime_currentSecsSinceEpoch_int64(NODE_THREAD));
}

static NODE_IMPLEMENTATION(_n_fromMSecsSinceEpoch0, Pointer)
{
    NODE_RETURN(qt_QDateTime_fromMSecsSinceEpoch_QDateTime_int64_QTimeZone(NODE_THREAD, NODE_ARG(0, int64), NODE_ARG(1, Pointer)));
}

static NODE_IMPLEMENTATION(_n_fromMSecsSinceEpoch1, Pointer)
{
    NODE_RETURN(qt_QDateTime_fromMSecsSinceEpoch_QDateTime_int64(NODE_THREAD, NODE_ARG(0, int64)));
}

static NODE_IMPLEMENTATION(_n_fromSecsSinceEpoch0, Pointer)
{
    NODE_RETURN(qt_QDateTime_fromSecsSinceEpoch_QDateTime_int64_QTimeZone(NODE_THREAD, NODE_ARG(0, int64), NODE_ARG(1, Pointer)));
}

static NODE_IMPLEMENTATION(_n_fromSecsSinceEpoch1, Pointer)
{
    NODE_RETURN(qt_QDateTime_fromSecsSinceEpoch_QDateTime_int64(NODE_THREAD, NODE_ARG(0, int64)));
}

static NODE_IMPLEMENTATION(_n_fromString0, Pointer)
{
    NODE_RETURN(qt_QDateTime_fromString_QDateTime_string_int(NODE_THREAD, NODE_ARG(0, Pointer), NODE_ARG(1, int)));
}


//
// Copyright (C) 2024  Autodesk, Inc. All Rights Reserved. 
// 
// SPDX-License-Identifier: Apache-2.0 
//

Pointer qt_QDateTime_fromString_QDateTime_string_string(Mu::Thread& NODE_THREAD, Pointer param_string, Pointer param_format)
{
    MuLangContext* c = static_cast<MuLangContext*>(NODE_THREAD.context());
    const QString  arg0 = qstring(param_string);
    const QString  arg1 = qstring(param_format);

    QStringList parts = arg1.split(" ");
    QDate date = QDate::fromString(parts[0], "yyyy-MM-dd");
    QTime time = QTime::fromString(parts[1], "hh:mm:ss");

    QDateTime dt(date, time);
    return makeqtype<QDateTimeType>(c,dt,"qt.QDateTime");
}

static NODE_IMPLEMENTATION(_n_fromString1, Pointer)
{
    NODE_RETURN(qt_QDateTime_fromString_QDateTime_string_string(NODE_THREAD, NODE_ARG(0, Pointer), NODE_ARG(1, Pointer)));
}

void
QDateTimeType::load()
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
    
    addSymbols(new Function(c, "__allocate", __allocate, None,
                            Return, ftn,
                            End),

               EndArguments );

addSymbols(
    new Alias(c, "YearRange", "int"),
      new SymbolicConstant(c, "First", "int", Value(int(QDateTime::YearRange::First))),
      new SymbolicConstant(c, "Last", "int", Value(int(QDateTime::YearRange::Last))),
    EndArguments);

addSymbols(
    // enums
    // member functions
    new Function(c, "QDateTime", _n_QDateTime0, None, Compiled, qt_QDateTime_QDateTime_QDateTime_QDateTime, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    new Function(c, "QDateTime", _n_QDateTime1, None, Compiled, qt_QDateTime_QDateTime_QDateTime_QDateTime_QDate_QTime_QTimeZone, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "date", "qt.QDate"), new Param(c, "time", "qt.QTime"), new Param(c, "timeZone", "qt.QTimeZone"), End),
    new Function(c, "QDateTime", _n_QDateTime2, None, Compiled, qt_QDateTime_QDateTime_QDateTime_QDateTime_QDate_QTime, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "date", "qt.QDate"), new Param(c, "time", "qt.QTime"), End),
    // MISSING: QDateTime (QDateTime; QDateTime this, QDateTime other)
    // MISSING: QDateTime (QDateTime; QDateTime this, "QDateTime & &" other)
    new Function(c, "addDays", _n_addDays0, None, Compiled, qt_QDateTime_addDays_QDateTime_QDateTime_int64, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "ndays", "int64"), End),
    new Function(c, "addDuration", _n_addDuration0, None, Compiled, qt_QDateTime_addDuration_QDateTime_QDateTime_int, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "msecs", "int"), End),
    new Function(c, "addMSecs", _n_addMSecs0, None, Compiled, qt_QDateTime_addMSecs_QDateTime_QDateTime_int64, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "msecs", "int64"), End),
    new Function(c, "addMonths", _n_addMonths0, None, Compiled, qt_QDateTime_addMonths_QDateTime_QDateTime_int, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "nmonths", "int"), End),
    new Function(c, "addSecs", _n_addSecs0, None, Compiled, qt_QDateTime_addSecs_QDateTime_QDateTime_int64, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "s", "int64"), End),
    new Function(c, "addYears", _n_addYears0, None, Compiled, qt_QDateTime_addYears_QDateTime_QDateTime_int, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "nyears", "int"), End),
    new Function(c, "date", _n_date0, None, Compiled, qt_QDateTime_date_QDate_QDateTime, Return, "qt.QDate", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    new Function(c, "daysTo", _n_daysTo0, None, Compiled, qt_QDateTime_daysTo_int64_QDateTime_QDateTime, Return, "int64", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "other", "qt.QDateTime"), End),
    new Function(c, "isDaylightTime", _n_isDaylightTime0, None, Compiled, qt_QDateTime_isDaylightTime_bool_QDateTime, Return, "bool", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    new Function(c, "isNull", _n_isNull0, None, Compiled, qt_QDateTime_isNull_bool_QDateTime, Return, "bool", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    new Function(c, "isValid", _n_isValid0, None, Compiled, qt_QDateTime_isValid_bool_QDateTime, Return, "bool", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    new Function(c, "msecsTo", _n_msecsTo0, None, Compiled, qt_QDateTime_msecsTo_int64_QDateTime_QDateTime, Return, "int64", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "other", "qt.QDateTime"), End),
    new Function(c, "offsetFromUtc", _n_offsetFromUtc0, None, Compiled, qt_QDateTime_offsetFromUtc_int_QDateTime, Return, "int", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    new Function(c, "secsTo", _n_secsTo0, None, Compiled, qt_QDateTime_secsTo_int64_QDateTime_QDateTime, Return, "int64", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "other", "qt.QDateTime"), End),
    new Function(c, "setDate", _n_setDate0, None, Compiled, qt_QDateTime_setDate_void_QDateTime_QDate, Return, "void", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "date", "qt.QDate"), End),
    new Function(c, "setMSecsSinceEpoch", _n_setMSecsSinceEpoch0, None, Compiled, qt_QDateTime_setMSecsSinceEpoch_void_QDateTime_int64, Return, "void", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "msecs", "int64"), End),
    new Function(c, "setSecsSinceEpoch", _n_setSecsSinceEpoch0, None, Compiled, qt_QDateTime_setSecsSinceEpoch_void_QDateTime_int64, Return, "void", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "secs", "int64"), End),
    new Function(c, "setTime", _n_setTime0, None, Compiled, qt_QDateTime_setTime_void_QDateTime_QTime, Return, "void", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "time", "qt.QTime"), End),
    new Function(c, "setTimeZone", _n_setTimeZone0, None, Compiled, qt_QDateTime_setTimeZone_void_QDateTime_QTimeZone, Return, "void", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "toZone", "qt.QTimeZone"), End),
    new Function(c, "swap", _n_swap0, None, Compiled, qt_QDateTime_swap_void_QDateTime_QDateTime, Return, "void", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "other", "qt.QDateTime"), End),
    new Function(c, "time", _n_time0, None, Compiled, qt_QDateTime_time_QTime_QDateTime, Return, "qt.QTime", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    new Function(c, "timeRepresentation", _n_timeRepresentation0, None, Compiled, qt_QDateTime_timeRepresentation_QTimeZone_QDateTime, Return, "qt.QTimeZone", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    new Function(c, "timeSpec", _n_timeSpec0, None, Compiled, qt_QDateTime_timeSpec_int_QDateTime, Return, "int", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    new Function(c, "timeZone", _n_timeZone0, None, Compiled, qt_QDateTime_timeZone_QTimeZone_QDateTime, Return, "qt.QTimeZone", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    new Function(c, "timeZoneAbbreviation", _n_timeZoneAbbreviation0, None, Compiled, qt_QDateTime_timeZoneAbbreviation_string_QDateTime, Return, "string", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    // MISSING: toCFDate ("CFDateRef"; QDateTime this)
    new Function(c, "toLocalTime", _n_toLocalTime0, None, Compiled, qt_QDateTime_toLocalTime_QDateTime_QDateTime, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    new Function(c, "toMSecsSinceEpoch", _n_toMSecsSinceEpoch0, None, Compiled, qt_QDateTime_toMSecsSinceEpoch_int64_QDateTime, Return, "int64", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    // MISSING: toNSDate ("NSDate *"; QDateTime this)
    new Function(c, "toOffsetFromUtc", _n_toOffsetFromUtc0, None, Compiled, qt_QDateTime_toOffsetFromUtc_QDateTime_QDateTime_int, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "offsetSeconds", "int"), End),
    new Function(c, "toSecsSinceEpoch", _n_toSecsSinceEpoch0, None, Compiled, qt_QDateTime_toSecsSinceEpoch_int64_QDateTime, Return, "int64", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    // MISSING: toString (string; QDateTime this, string format, "QCalendar" cal)
    new Function(c, "toString", _n_toString1, None, Compiled, qt_QDateTime_toString_string_QDateTime_int, Return, "string", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "format", "int", Value((int)Qt::TextDate)), End),
    // MISSING: toString (string; QDateTime this, "QStringView" format, "QCalendar" cal)
    new Function(c, "toTimeZone", _n_toTimeZone0, None, Compiled, qt_QDateTime_toTimeZone_QDateTime_QDateTime_QTimeZone, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "timeZone", "qt.QTimeZone"), End),
    new Function(c, "toUTC", _n_toUTC0, None, Compiled, qt_QDateTime_toUTC_QDateTime_QDateTime, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), End),
    // static functions
    new Function(c, "currentDateTime", _n_currentDateTime0, None, Compiled, qt_QDateTime_currentDateTime_QDateTime_QTimeZone, Return, "qt.QDateTime", Parameters, new Param(c, "zone", "qt.QTimeZone"), End),
    new Function(c, "currentDateTime", _n_currentDateTime1, None, Compiled, qt_QDateTime_currentDateTime_QDateTime, Return, "qt.QDateTime", End),
    new Function(c, "currentDateTimeUtc", _n_currentDateTimeUtc0, None, Compiled, qt_QDateTime_currentDateTimeUtc_QDateTime, Return, "qt.QDateTime", End),
    new Function(c, "currentMSecsSinceEpoch", _n_currentMSecsSinceEpoch0, None, Compiled, qt_QDateTime_currentMSecsSinceEpoch_int64, Return, "int64", End),
    new Function(c, "currentSecsSinceEpoch", _n_currentSecsSinceEpoch0, None, Compiled, qt_QDateTime_currentSecsSinceEpoch_int64, Return, "int64", End),
    // MISSING: fromCFDate (QDateTime; "CFDateRef" date)
    new Function(c, "fromMSecsSinceEpoch", _n_fromMSecsSinceEpoch0, None, Compiled, qt_QDateTime_fromMSecsSinceEpoch_QDateTime_int64_QTimeZone, Return, "qt.QDateTime", Parameters, new Param(c, "msecs", "int64"), new Param(c, "timeZone", "qt.QTimeZone"), End),
    new Function(c, "fromMSecsSinceEpoch", _n_fromMSecsSinceEpoch1, None, Compiled, qt_QDateTime_fromMSecsSinceEpoch_QDateTime_int64, Return, "qt.QDateTime", Parameters, new Param(c, "msecs", "int64"), End),
    // MISSING: fromNSDate (QDateTime; "const NSDate *" date)
    new Function(c, "fromSecsSinceEpoch", _n_fromSecsSinceEpoch0, None, Compiled, qt_QDateTime_fromSecsSinceEpoch_QDateTime_int64_QTimeZone, Return, "qt.QDateTime", Parameters, new Param(c, "secs", "int64"), new Param(c, "timeZone", "qt.QTimeZone"), End),
    new Function(c, "fromSecsSinceEpoch", _n_fromSecsSinceEpoch1, None, Compiled, qt_QDateTime_fromSecsSinceEpoch_QDateTime_int64, Return, "qt.QDateTime", Parameters, new Param(c, "secs", "int64"), End),
    new Function(c, "fromString", _n_fromString0, None, Compiled, qt_QDateTime_fromString_QDateTime_string_int, Return, "qt.QDateTime", Parameters, new Param(c, "string", "string"), new Param(c, "format", "int", Value((int)Qt::TextDate)), End),
    // MISSING: fromString (QDateTime; "QStringView" string, flags Qt::DateFormat format)
    // MISSING: fromString (QDateTime; "QStringView" string, "QStringView" format, "QCalendar" cal)
    // MISSING: fromString (QDateTime; string string, "QStringView" format, "QCalendar" cal)
    // MISSING: fromString (QDateTime; string string, string format, "QCalendar" cal)
    EndArguments);
globalScope()->addSymbols(
    new Function(c, "+=", _n_operatorPlus_EQ_0, Op, Compiled, qt_QDateTime_operatorPlus_EQ__QDateTime_QDateTime_int, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "duration", "int"), End),
    new Function(c, "-=", _n_operatorMinus_EQ_0, Op, Compiled, qt_QDateTime_operatorMinus_EQ__QDateTime_QDateTime_int, Return, "qt.QDateTime", Parameters, new Param(c, "this", "qt.QDateTime"), new Param(c, "duration", "int"), End),
    // MISSING: = (QDateTime; QDateTime this, QDateTime other)
    EndArguments);
scope()->addSymbols(
    EndArguments);

//
// Copyright (C) 2024  Autodesk, Inc. All Rights Reserved. 
// 
// SPDX-License-Identifier: Apache-2.0 
//

addSymbol( new Function(c, "fromString", _n_fromString1, None, 
                        Compiled, qt_QDateTime_fromString_QDateTime_string_string, 
                        Return, "qt.QDateTime", 
                        Parameters, 
                        new Param(c, "string", "string"), new Param(c, "format", "string"), 
                        End)
        );
}

} // Mu
