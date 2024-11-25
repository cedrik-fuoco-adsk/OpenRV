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

#ifndef __MuQt6__QAbstractSpinBoxType__h__
#define __MuQt6__QAbstractSpinBoxType__h__
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
class MuQt_QAbstractSpinBox;

class QAbstractSpinBoxType : public Class
{
  public:

    typedef MuQt_QAbstractSpinBox MuQtType;
    typedef QAbstractSpinBox QtType;

    //
    //  Constructors
    //

    QAbstractSpinBoxType(Context* context, 
           const char* name,
           Class* superClass = 0,
           Class* superClass2 = 0);

    virtual ~QAbstractSpinBoxType();

    static bool isInheritable() { return true; }
    static inline ClassInstance* cachedInstance(const MuQtType*);

    //
    //  Class API
    //

    virtual void load();

    MemberFunction* _func[33];
};

// Inheritable object

class MuQt_QAbstractSpinBox : public QAbstractSpinBox
{
  public:
    virtual ~MuQt_QAbstractSpinBox();
    MuQt_QAbstractSpinBox(Pointer muobj, const CallEnvironment*, QWidget * parent) ;
    virtual void stepBy(int steps) ;
    virtual bool event(QEvent * event_) ;
    virtual QVariant inputMethodQuery(Qt::InputMethodQuery query) const;
    virtual QSize minimumSizeHint() const;
    virtual QSize sizeHint() const;
  protected:
    virtual void changeEvent(QEvent * event) ;
    virtual void closeEvent(QCloseEvent * event) ;
    virtual void contextMenuEvent(QContextMenuEvent * event) ;
    virtual void focusInEvent(QFocusEvent * event) ;
    virtual void focusOutEvent(QFocusEvent * event) ;
    virtual void hideEvent(QHideEvent * event) ;
    virtual void keyPressEvent(QKeyEvent * event) ;
    virtual void keyReleaseEvent(QKeyEvent * event) ;
    virtual void mouseMoveEvent(QMouseEvent * event) ;
    virtual void mousePressEvent(QMouseEvent * event) ;
    virtual void mouseReleaseEvent(QMouseEvent * event) ;
    virtual void paintEvent(QPaintEvent * event) ;
    virtual void resizeEvent(QResizeEvent * event) ;
    virtual void showEvent(QShowEvent * event) ;
    virtual void timerEvent(QTimerEvent * event) ;
    virtual void wheelEvent(QWheelEvent * event) ;
  public:
    virtual bool hasHeightForWidth() const;
    virtual int heightForWidth(int w) const;
  protected:
    virtual void dragEnterEvent(QDragEnterEvent * event) ;
    virtual void dragLeaveEvent(QDragLeaveEvent * event) ;
    virtual void dragMoveEvent(QDragMoveEvent * event) ;
    virtual void dropEvent(QDropEvent * event) ;
    virtual bool focusNextPrevChild(bool next) ;
    virtual void leaveEvent(QEvent * event) ;
    virtual void mouseDoubleClickEvent(QMouseEvent * event) ;
    virtual void moveEvent(QMoveEvent * event) ;
    virtual void tabletEvent(QTabletEvent * event) ;
    virtual int metric(QPaintDevice::PaintDeviceMetric m) const;
  public:
    QLineEdit * lineEdit_pub() const { return lineEdit(); }
    QLineEdit * lineEdit_pub_parent() const { return QAbstractSpinBox::lineEdit(); }
    void setLineEdit_pub(QLineEdit * lineEdit)  { setLineEdit(lineEdit); }
    void setLineEdit_pub_parent(QLineEdit * lineEdit)  { QAbstractSpinBox::setLineEdit(lineEdit); }
    void changeEvent_pub(QEvent * event)  { changeEvent(event); }
    void changeEvent_pub_parent(QEvent * event)  { QAbstractSpinBox::changeEvent(event); }
    void closeEvent_pub(QCloseEvent * event)  { closeEvent(event); }
    void closeEvent_pub_parent(QCloseEvent * event)  { QAbstractSpinBox::closeEvent(event); }
    void contextMenuEvent_pub(QContextMenuEvent * event)  { contextMenuEvent(event); }
    void contextMenuEvent_pub_parent(QContextMenuEvent * event)  { QAbstractSpinBox::contextMenuEvent(event); }
    void focusInEvent_pub(QFocusEvent * event)  { focusInEvent(event); }
    void focusInEvent_pub_parent(QFocusEvent * event)  { QAbstractSpinBox::focusInEvent(event); }
    void focusOutEvent_pub(QFocusEvent * event)  { focusOutEvent(event); }
    void focusOutEvent_pub_parent(QFocusEvent * event)  { QAbstractSpinBox::focusOutEvent(event); }
    void hideEvent_pub(QHideEvent * event)  { hideEvent(event); }
    void hideEvent_pub_parent(QHideEvent * event)  { QAbstractSpinBox::hideEvent(event); }
    void keyPressEvent_pub(QKeyEvent * event)  { keyPressEvent(event); }
    void keyPressEvent_pub_parent(QKeyEvent * event)  { QAbstractSpinBox::keyPressEvent(event); }
    void keyReleaseEvent_pub(QKeyEvent * event)  { keyReleaseEvent(event); }
    void keyReleaseEvent_pub_parent(QKeyEvent * event)  { QAbstractSpinBox::keyReleaseEvent(event); }
    void mouseMoveEvent_pub(QMouseEvent * event)  { mouseMoveEvent(event); }
    void mouseMoveEvent_pub_parent(QMouseEvent * event)  { QAbstractSpinBox::mouseMoveEvent(event); }
    void mousePressEvent_pub(QMouseEvent * event)  { mousePressEvent(event); }
    void mousePressEvent_pub_parent(QMouseEvent * event)  { QAbstractSpinBox::mousePressEvent(event); }
    void mouseReleaseEvent_pub(QMouseEvent * event)  { mouseReleaseEvent(event); }
    void mouseReleaseEvent_pub_parent(QMouseEvent * event)  { QAbstractSpinBox::mouseReleaseEvent(event); }
    void paintEvent_pub(QPaintEvent * event)  { paintEvent(event); }
    void paintEvent_pub_parent(QPaintEvent * event)  { QAbstractSpinBox::paintEvent(event); }
    void resizeEvent_pub(QResizeEvent * event)  { resizeEvent(event); }
    void resizeEvent_pub_parent(QResizeEvent * event)  { QAbstractSpinBox::resizeEvent(event); }
    void showEvent_pub(QShowEvent * event)  { showEvent(event); }
    void showEvent_pub_parent(QShowEvent * event)  { QAbstractSpinBox::showEvent(event); }
    void timerEvent_pub(QTimerEvent * event)  { timerEvent(event); }
    void timerEvent_pub_parent(QTimerEvent * event)  { QAbstractSpinBox::timerEvent(event); }
    void wheelEvent_pub(QWheelEvent * event)  { wheelEvent(event); }
    void wheelEvent_pub_parent(QWheelEvent * event)  { QAbstractSpinBox::wheelEvent(event); }
    void dragEnterEvent_pub(QDragEnterEvent * event)  { dragEnterEvent(event); }
    void dragEnterEvent_pub_parent(QDragEnterEvent * event)  { QAbstractSpinBox::dragEnterEvent(event); }
    void dragLeaveEvent_pub(QDragLeaveEvent * event)  { dragLeaveEvent(event); }
    void dragLeaveEvent_pub_parent(QDragLeaveEvent * event)  { QAbstractSpinBox::dragLeaveEvent(event); }
    void dragMoveEvent_pub(QDragMoveEvent * event)  { dragMoveEvent(event); }
    void dragMoveEvent_pub_parent(QDragMoveEvent * event)  { QAbstractSpinBox::dragMoveEvent(event); }
    void dropEvent_pub(QDropEvent * event)  { dropEvent(event); }
    void dropEvent_pub_parent(QDropEvent * event)  { QAbstractSpinBox::dropEvent(event); }
    bool focusNextPrevChild_pub(bool next)  { return focusNextPrevChild(next); }
    bool focusNextPrevChild_pub_parent(bool next)  { return QAbstractSpinBox::focusNextPrevChild(next); }
    void leaveEvent_pub(QEvent * event)  { leaveEvent(event); }
    void leaveEvent_pub_parent(QEvent * event)  { QAbstractSpinBox::leaveEvent(event); }
    void mouseDoubleClickEvent_pub(QMouseEvent * event)  { mouseDoubleClickEvent(event); }
    void mouseDoubleClickEvent_pub_parent(QMouseEvent * event)  { QAbstractSpinBox::mouseDoubleClickEvent(event); }
    void moveEvent_pub(QMoveEvent * event)  { moveEvent(event); }
    void moveEvent_pub_parent(QMoveEvent * event)  { QAbstractSpinBox::moveEvent(event); }
    void tabletEvent_pub(QTabletEvent * event)  { tabletEvent(event); }
    void tabletEvent_pub_parent(QTabletEvent * event)  { QAbstractSpinBox::tabletEvent(event); }
    int metric_pub(QPaintDevice::PaintDeviceMetric m) const { return metric(m); }
    int metric_pub_parent(QPaintDevice::PaintDeviceMetric m) const { return QAbstractSpinBox::metric(m); }
  public:
    const QAbstractSpinBoxType* _baseType;
    ClassInstance* _obj;
    const CallEnvironment* _env;
};

inline ClassInstance* QAbstractSpinBoxType::cachedInstance(const QAbstractSpinBoxType::MuQtType* obj) { return obj->_obj; }

} // Mu

#endif // __MuQt__QAbstractSpinBoxType__h__