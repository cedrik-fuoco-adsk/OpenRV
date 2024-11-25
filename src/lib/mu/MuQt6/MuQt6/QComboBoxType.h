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

#ifndef __MuQt6__QComboBoxType__h__
#define __MuQt6__QComboBoxType__h__
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
class MuQt_QComboBox;

class QComboBoxType : public Class
{
  public:

    typedef MuQt_QComboBox MuQtType;
    typedef QComboBox QtType;

    //
    //  Constructors
    //

    QComboBoxType(Context* context, 
           const char* name,
           Class* superClass = 0,
           Class* superClass2 = 0);

    virtual ~QComboBoxType();

    static bool isInheritable() { return true; }
    static inline ClassInstance* cachedInstance(const MuQtType*);

    //
    //  Class API
    //

    virtual void load();

    MemberFunction* _func[34];
};

// Inheritable object

class MuQt_QComboBox : public QComboBox
{
  public:
    virtual ~MuQt_QComboBox();
    MuQt_QComboBox(Pointer muobj, const CallEnvironment*, QWidget * parent) ;
    virtual void hidePopup() ;
    virtual void setModel(QAbstractItemModel * model) ;
    virtual void showPopup() ;
    virtual bool event(QEvent * event_) ;
    virtual QVariant inputMethodQuery(Qt::InputMethodQuery query) const;
    virtual QSize minimumSizeHint() const;
    virtual QSize sizeHint() const;
  protected:
    virtual void changeEvent(QEvent * e) ;
    virtual void contextMenuEvent(QContextMenuEvent * e) ;
    virtual void focusInEvent(QFocusEvent * e) ;
    virtual void focusOutEvent(QFocusEvent * e) ;
    virtual void hideEvent(QHideEvent * e) ;
    virtual void keyPressEvent(QKeyEvent * e) ;
    virtual void keyReleaseEvent(QKeyEvent * e) ;
    virtual void mousePressEvent(QMouseEvent * e) ;
    virtual void mouseReleaseEvent(QMouseEvent * e) ;
    virtual void paintEvent(QPaintEvent * e) ;
    virtual void resizeEvent(QResizeEvent * e) ;
    virtual void showEvent(QShowEvent * e) ;
    virtual void wheelEvent(QWheelEvent * e) ;
  public:
    virtual bool hasHeightForWidth() const;
    virtual int heightForWidth(int w) const;
  protected:
    virtual void closeEvent(QCloseEvent * event) ;
    virtual void dragEnterEvent(QDragEnterEvent * event) ;
    virtual void dragLeaveEvent(QDragLeaveEvent * event) ;
    virtual void dragMoveEvent(QDragMoveEvent * event) ;
    virtual void dropEvent(QDropEvent * event) ;
    virtual bool focusNextPrevChild(bool next) ;
    virtual void leaveEvent(QEvent * event) ;
    virtual void mouseDoubleClickEvent(QMouseEvent * event) ;
    virtual void mouseMoveEvent(QMouseEvent * event) ;
    virtual void moveEvent(QMoveEvent * event) ;
    virtual void tabletEvent(QTabletEvent * event) ;
    virtual int metric(QPaintDevice::PaintDeviceMetric m) const;
  public:
    void changeEvent_pub(QEvent * e)  { changeEvent(e); }
    void changeEvent_pub_parent(QEvent * e)  { QComboBox::changeEvent(e); }
    void contextMenuEvent_pub(QContextMenuEvent * e)  { contextMenuEvent(e); }
    void contextMenuEvent_pub_parent(QContextMenuEvent * e)  { QComboBox::contextMenuEvent(e); }
    void focusInEvent_pub(QFocusEvent * e)  { focusInEvent(e); }
    void focusInEvent_pub_parent(QFocusEvent * e)  { QComboBox::focusInEvent(e); }
    void focusOutEvent_pub(QFocusEvent * e)  { focusOutEvent(e); }
    void focusOutEvent_pub_parent(QFocusEvent * e)  { QComboBox::focusOutEvent(e); }
    void hideEvent_pub(QHideEvent * e)  { hideEvent(e); }
    void hideEvent_pub_parent(QHideEvent * e)  { QComboBox::hideEvent(e); }
    void keyPressEvent_pub(QKeyEvent * e)  { keyPressEvent(e); }
    void keyPressEvent_pub_parent(QKeyEvent * e)  { QComboBox::keyPressEvent(e); }
    void keyReleaseEvent_pub(QKeyEvent * e)  { keyReleaseEvent(e); }
    void keyReleaseEvent_pub_parent(QKeyEvent * e)  { QComboBox::keyReleaseEvent(e); }
    void mousePressEvent_pub(QMouseEvent * e)  { mousePressEvent(e); }
    void mousePressEvent_pub_parent(QMouseEvent * e)  { QComboBox::mousePressEvent(e); }
    void mouseReleaseEvent_pub(QMouseEvent * e)  { mouseReleaseEvent(e); }
    void mouseReleaseEvent_pub_parent(QMouseEvent * e)  { QComboBox::mouseReleaseEvent(e); }
    void paintEvent_pub(QPaintEvent * e)  { paintEvent(e); }
    void paintEvent_pub_parent(QPaintEvent * e)  { QComboBox::paintEvent(e); }
    void resizeEvent_pub(QResizeEvent * e)  { resizeEvent(e); }
    void resizeEvent_pub_parent(QResizeEvent * e)  { QComboBox::resizeEvent(e); }
    void showEvent_pub(QShowEvent * e)  { showEvent(e); }
    void showEvent_pub_parent(QShowEvent * e)  { QComboBox::showEvent(e); }
    void wheelEvent_pub(QWheelEvent * e)  { wheelEvent(e); }
    void wheelEvent_pub_parent(QWheelEvent * e)  { QComboBox::wheelEvent(e); }
    void closeEvent_pub(QCloseEvent * event)  { closeEvent(event); }
    void closeEvent_pub_parent(QCloseEvent * event)  { QComboBox::closeEvent(event); }
    void dragEnterEvent_pub(QDragEnterEvent * event)  { dragEnterEvent(event); }
    void dragEnterEvent_pub_parent(QDragEnterEvent * event)  { QComboBox::dragEnterEvent(event); }
    void dragLeaveEvent_pub(QDragLeaveEvent * event)  { dragLeaveEvent(event); }
    void dragLeaveEvent_pub_parent(QDragLeaveEvent * event)  { QComboBox::dragLeaveEvent(event); }
    void dragMoveEvent_pub(QDragMoveEvent * event)  { dragMoveEvent(event); }
    void dragMoveEvent_pub_parent(QDragMoveEvent * event)  { QComboBox::dragMoveEvent(event); }
    void dropEvent_pub(QDropEvent * event)  { dropEvent(event); }
    void dropEvent_pub_parent(QDropEvent * event)  { QComboBox::dropEvent(event); }
    bool focusNextPrevChild_pub(bool next)  { return focusNextPrevChild(next); }
    bool focusNextPrevChild_pub_parent(bool next)  { return QComboBox::focusNextPrevChild(next); }
    void leaveEvent_pub(QEvent * event)  { leaveEvent(event); }
    void leaveEvent_pub_parent(QEvent * event)  { QComboBox::leaveEvent(event); }
    void mouseDoubleClickEvent_pub(QMouseEvent * event)  { mouseDoubleClickEvent(event); }
    void mouseDoubleClickEvent_pub_parent(QMouseEvent * event)  { QComboBox::mouseDoubleClickEvent(event); }
    void mouseMoveEvent_pub(QMouseEvent * event)  { mouseMoveEvent(event); }
    void mouseMoveEvent_pub_parent(QMouseEvent * event)  { QComboBox::mouseMoveEvent(event); }
    void moveEvent_pub(QMoveEvent * event)  { moveEvent(event); }
    void moveEvent_pub_parent(QMoveEvent * event)  { QComboBox::moveEvent(event); }
    void tabletEvent_pub(QTabletEvent * event)  { tabletEvent(event); }
    void tabletEvent_pub_parent(QTabletEvent * event)  { QComboBox::tabletEvent(event); }
    int metric_pub(QPaintDevice::PaintDeviceMetric m) const { return metric(m); }
    int metric_pub_parent(QPaintDevice::PaintDeviceMetric m) const { return QComboBox::metric(m); }
  public:
    const QComboBoxType* _baseType;
    ClassInstance* _obj;
    const CallEnvironment* _env;
};

inline ClassInstance* QComboBoxType::cachedInstance(const QComboBoxType::MuQtType* obj) { return obj->_obj; }

} // Mu

#endif // __MuQt__QComboBoxType__h__