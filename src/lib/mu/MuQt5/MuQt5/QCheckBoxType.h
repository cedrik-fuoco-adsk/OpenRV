//
// Copyright (c) 2009, Jim Hourihan
// All rights reserved.
//
// SPDX-License-Identifier: Apache-2.0
//
#ifndef __MuQt5__QCheckBoxType__h__
#define __MuQt5__QCheckBoxType__h__
#include <iostream>
#include <Mu/Class.h>
#include <Mu/MuProcess.h>
#include <QtCore/QtCore>
#include <QtGui/QtGui>
#include <QtWidgets/QtWidgets>
#include <QtNetwork/QtNetwork>
#include <QtWebEngine/QtWebEngine>
#include <QtWebEngineWidgets/QtWebEngineWidgets>
#include <QtQml/QtQml>
#include <QtQuick/QtQuick>
#include <QtQuickWidgets/QtQuickWidgets>
#include <QtSvg/QtSvg>
#include <MuQt5/Bridge.h>

namespace Mu
{
    class MuQt_QCheckBox;

    //
    //  NOTE: file generated by qt2mu.py
    //

    class QCheckBoxType : public Class
    {
    public:
        typedef MuQt_QCheckBox MuQtType;
        typedef QCheckBox QtType;

        //
        //  Constructors
        //

        QCheckBoxType(Context* context, const char* name, Class* superClass = 0,
                      Class* superClass2 = 0);

        virtual ~QCheckBoxType();

        static bool isInheritable() { return true; }

        static inline ClassInstance* cachedInstance(const MuQtType*);

        //
        //  Class API
        //

        virtual void load();

        MemberFunction* _func[16];
    };

    // Inheritable object

    class MuQt_QCheckBox : public QCheckBox
    {
    public:
        virtual ~MuQt_QCheckBox();
        MuQt_QCheckBox(Pointer muobj, const CallEnvironment*, QWidget* parent);
        MuQt_QCheckBox(Pointer muobj, const CallEnvironment*,
                       const QString& text, QWidget* parent);
        virtual QSize minimumSizeHint() const;
        virtual QSize sizeHint() const;

    protected:
        virtual void checkStateSet();
        virtual bool event(QEvent* e);
        virtual bool hitButton(const QPoint& pos) const;
        virtual void mouseMoveEvent(QMouseEvent* e);
        virtual void nextCheckState();
        virtual void paintEvent(QPaintEvent* _p14);
        virtual void changeEvent(QEvent* e);
        virtual void focusInEvent(QFocusEvent* e);
        virtual void focusOutEvent(QFocusEvent* e);
        virtual void keyPressEvent(QKeyEvent* e);
        virtual void keyReleaseEvent(QKeyEvent* e);
        virtual void mousePressEvent(QMouseEvent* e);
        virtual void mouseReleaseEvent(QMouseEvent* e);
        virtual void timerEvent(QTimerEvent* e);

    public:
        void checkStateSet_pub() { checkStateSet(); }

        void checkStateSet_pub_parent() { QCheckBox::checkStateSet(); }

        bool event_pub(QEvent* e) { return event(e); }

        bool event_pub_parent(QEvent* e) { return QCheckBox::event(e); }

        bool hitButton_pub(const QPoint& pos) const { return hitButton(pos); }

        bool hitButton_pub_parent(const QPoint& pos) const
        {
            return QCheckBox::hitButton(pos);
        }

        void mouseMoveEvent_pub(QMouseEvent* e) { mouseMoveEvent(e); }

        void mouseMoveEvent_pub_parent(QMouseEvent* e)
        {
            QCheckBox::mouseMoveEvent(e);
        }

        void nextCheckState_pub() { nextCheckState(); }

        void nextCheckState_pub_parent() { QCheckBox::nextCheckState(); }

        void paintEvent_pub(QPaintEvent* _p14) { paintEvent(_p14); }

        void paintEvent_pub_parent(QPaintEvent* _p14)
        {
            QCheckBox::paintEvent(_p14);
        }

        void changeEvent_pub(QEvent* e) { changeEvent(e); }

        void changeEvent_pub_parent(QEvent* e) { QCheckBox::changeEvent(e); }

        void focusInEvent_pub(QFocusEvent* e) { focusInEvent(e); }

        void focusInEvent_pub_parent(QFocusEvent* e)
        {
            QCheckBox::focusInEvent(e);
        }

        void focusOutEvent_pub(QFocusEvent* e) { focusOutEvent(e); }

        void focusOutEvent_pub_parent(QFocusEvent* e)
        {
            QCheckBox::focusOutEvent(e);
        }

        void keyPressEvent_pub(QKeyEvent* e) { keyPressEvent(e); }

        void keyPressEvent_pub_parent(QKeyEvent* e)
        {
            QCheckBox::keyPressEvent(e);
        }

        void keyReleaseEvent_pub(QKeyEvent* e) { keyReleaseEvent(e); }

        void keyReleaseEvent_pub_parent(QKeyEvent* e)
        {
            QCheckBox::keyReleaseEvent(e);
        }

        void mousePressEvent_pub(QMouseEvent* e) { mousePressEvent(e); }

        void mousePressEvent_pub_parent(QMouseEvent* e)
        {
            QCheckBox::mousePressEvent(e);
        }

        void mouseReleaseEvent_pub(QMouseEvent* e) { mouseReleaseEvent(e); }

        void mouseReleaseEvent_pub_parent(QMouseEvent* e)
        {
            QCheckBox::mouseReleaseEvent(e);
        }

        void timerEvent_pub(QTimerEvent* e) { timerEvent(e); }

        void timerEvent_pub_parent(QTimerEvent* e) { QCheckBox::timerEvent(e); }

    public:
        const QCheckBoxType* _baseType;
        ClassInstance* _obj;
        const CallEnvironment* _env;
    };

    inline ClassInstance*
    QCheckBoxType::cachedInstance(const QCheckBoxType::MuQtType* obj)
    {
        return obj->_obj;
    }

} // namespace Mu

#endif // __MuQt__QCheckBoxType__h__
