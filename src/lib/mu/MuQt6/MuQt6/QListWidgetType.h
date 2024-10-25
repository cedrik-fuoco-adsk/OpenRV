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

#ifndef __MuQt6__QListWidgetType__h__
#define __MuQt6__QListWidgetType__h__
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
class MuQt_QListWidget;

class QListWidgetType : public Class
{
  public:

    typedef MuQt_QListWidget MuQtType;
    typedef QListWidget QtType;

    //
    //  Constructors
    //

    QListWidgetType(Context* context, 
           const char* name,
           Class* superClass = 0,
           Class* superClass2 = 0);

    virtual ~QListWidgetType();

    static bool isInheritable() { return true; }
    static inline ClassInstance* cachedInstance(const MuQtType*);

    //
    //  Class API
    //

    virtual void load();

    MemberFunction* _func[33];
};

// Inheritable object

class MuQt_QListWidget : public QListWidget
{
  public:
    virtual ~MuQt_QListWidget();
    MuQt_QListWidget(Pointer muobj, const CallEnvironment*, QWidget * parent) ;
    virtual void setSelectionModel(QItemSelectionModel * selectionModel) ;
  protected:
    virtual bool dropMimeData(int index, const QMimeData * data, Qt::DropAction action) ;
    virtual QMimeData * mimeData(const QList<QListWidgetItem * > & items) const;
    virtual QStringList mimeTypes() const;
    virtual Qt::DropActions supportedDropActions() const;
    virtual void dropEvent(QDropEvent * event) ;
    virtual bool event(QEvent * e) ;
  public:
    virtual QModelIndex indexAt(const QPoint & p) const;
    virtual void scrollTo(const QModelIndex & index, QAbstractItemView::ScrollHint hint) ;
    virtual void setRootIndex(const QModelIndex & index) ;
    virtual QRect visualRect(const QModelIndex & index) const;
  protected:
    virtual void currentChanged(const QModelIndex & current, const QModelIndex & previous) ;
    virtual void dragLeaveEvent(QDragLeaveEvent * e) ;
    virtual void dragMoveEvent(QDragMoveEvent * e) ;
    virtual int horizontalOffset() const;
    virtual bool isIndexHidden(const QModelIndex & index) const;
    virtual void mouseMoveEvent(QMouseEvent * e) ;
    virtual void mouseReleaseEvent(QMouseEvent * e) ;
    virtual void paintEvent(QPaintEvent * e) ;
    virtual void resizeEvent(QResizeEvent * e) ;
    virtual void rowsAboutToBeRemoved(const QModelIndex & parent, int start, int end) ;
    virtual void rowsInserted(const QModelIndex & parent, int start, int end) ;
    virtual void scrollContentsBy(int dx, int dy) ;
    virtual QModelIndexList selectedIndexes() const;
    virtual void selectionChanged(const QItemSelection & selected, const QItemSelection & deselected) ;
    virtual void setSelection(const QRect & rect, QItemSelectionModel::SelectionFlags command) ;
    virtual void startDrag(Qt::DropActions supportedActions) ;
    virtual void timerEvent(QTimerEvent * e) ;
    virtual void updateGeometries() ;
    virtual int verticalOffset() const;
    virtual QSize viewportSizeHint() const;
    virtual QRegion visualRegionForSelection(const QItemSelection & selection) const;
    virtual void wheelEvent(QWheelEvent * e) ;
  public:
    bool dropMimeData_pub(int index, const QMimeData * data, Qt::DropAction action)  { return dropMimeData(index, data, action); }
    bool dropMimeData_pub_parent(int index, const QMimeData * data, Qt::DropAction action)  { return QListWidget::dropMimeData(index, data, action); }
    QMimeData * mimeData_pub(const QList<QListWidgetItem * > & items) const { return mimeData(items); }
    QMimeData * mimeData_pub_parent(const QList<QListWidgetItem * > & items) const { return QListWidget::mimeData(items); }
    QStringList mimeTypes_pub() const { return mimeTypes(); }
    QStringList mimeTypes_pub_parent() const { return QListWidget::mimeTypes(); }
    Qt::DropActions supportedDropActions_pub() const { return supportedDropActions(); }
    Qt::DropActions supportedDropActions_pub_parent() const { return QListWidget::supportedDropActions(); }
    void dropEvent_pub(QDropEvent * event)  { dropEvent(event); }
    void dropEvent_pub_parent(QDropEvent * event)  { QListWidget::dropEvent(event); }
    bool event_pub(QEvent * e)  { return event(e); }
    bool event_pub_parent(QEvent * e)  { return QListWidget::event(e); }
    void currentChanged_pub(const QModelIndex & current, const QModelIndex & previous)  { currentChanged(current, previous); }
    void currentChanged_pub_parent(const QModelIndex & current, const QModelIndex & previous)  { QListWidget::currentChanged(current, previous); }
    void dragLeaveEvent_pub(QDragLeaveEvent * e)  { dragLeaveEvent(e); }
    void dragLeaveEvent_pub_parent(QDragLeaveEvent * e)  { QListWidget::dragLeaveEvent(e); }
    void dragMoveEvent_pub(QDragMoveEvent * e)  { dragMoveEvent(e); }
    void dragMoveEvent_pub_parent(QDragMoveEvent * e)  { QListWidget::dragMoveEvent(e); }
    int horizontalOffset_pub() const { return horizontalOffset(); }
    int horizontalOffset_pub_parent() const { return QListWidget::horizontalOffset(); }
    bool isIndexHidden_pub(const QModelIndex & index) const { return isIndexHidden(index); }
    bool isIndexHidden_pub_parent(const QModelIndex & index) const { return QListWidget::isIndexHidden(index); }
    void mouseMoveEvent_pub(QMouseEvent * e)  { mouseMoveEvent(e); }
    void mouseMoveEvent_pub_parent(QMouseEvent * e)  { QListWidget::mouseMoveEvent(e); }
    void mouseReleaseEvent_pub(QMouseEvent * e)  { mouseReleaseEvent(e); }
    void mouseReleaseEvent_pub_parent(QMouseEvent * e)  { QListWidget::mouseReleaseEvent(e); }
    void paintEvent_pub(QPaintEvent * e)  { paintEvent(e); }
    void paintEvent_pub_parent(QPaintEvent * e)  { QListWidget::paintEvent(e); }
    void resizeEvent_pub(QResizeEvent * e)  { resizeEvent(e); }
    void resizeEvent_pub_parent(QResizeEvent * e)  { QListWidget::resizeEvent(e); }
    void rowsAboutToBeRemoved_pub(const QModelIndex & parent, int start, int end)  { rowsAboutToBeRemoved(parent, start, end); }
    void rowsAboutToBeRemoved_pub_parent(const QModelIndex & parent, int start, int end)  { QListWidget::rowsAboutToBeRemoved(parent, start, end); }
    void rowsInserted_pub(const QModelIndex & parent, int start, int end)  { rowsInserted(parent, start, end); }
    void rowsInserted_pub_parent(const QModelIndex & parent, int start, int end)  { QListWidget::rowsInserted(parent, start, end); }
    void scrollContentsBy_pub(int dx, int dy)  { scrollContentsBy(dx, dy); }
    void scrollContentsBy_pub_parent(int dx, int dy)  { QListWidget::scrollContentsBy(dx, dy); }
    QModelIndexList selectedIndexes_pub() const { return selectedIndexes(); }
    QModelIndexList selectedIndexes_pub_parent() const { return QListWidget::selectedIndexes(); }
    void selectionChanged_pub(const QItemSelection & selected, const QItemSelection & deselected)  { selectionChanged(selected, deselected); }
    void selectionChanged_pub_parent(const QItemSelection & selected, const QItemSelection & deselected)  { QListWidget::selectionChanged(selected, deselected); }
    void setSelection_pub(const QRect & rect, QItemSelectionModel::SelectionFlags command)  { setSelection(rect, command); }
    void setSelection_pub_parent(const QRect & rect, QItemSelectionModel::SelectionFlags command)  { QListWidget::setSelection(rect, command); }
    void startDrag_pub(Qt::DropActions supportedActions)  { startDrag(supportedActions); }
    void startDrag_pub_parent(Qt::DropActions supportedActions)  { QListWidget::startDrag(supportedActions); }
    void timerEvent_pub(QTimerEvent * e)  { timerEvent(e); }
    void timerEvent_pub_parent(QTimerEvent * e)  { QListWidget::timerEvent(e); }
    void updateGeometries_pub()  { updateGeometries(); }
    void updateGeometries_pub_parent()  { QListWidget::updateGeometries(); }
    int verticalOffset_pub() const { return verticalOffset(); }
    int verticalOffset_pub_parent() const { return QListWidget::verticalOffset(); }
    QSize viewportSizeHint_pub() const { return viewportSizeHint(); }
    QSize viewportSizeHint_pub_parent() const { return QListWidget::viewportSizeHint(); }
    QRegion visualRegionForSelection_pub(const QItemSelection & selection) const { return visualRegionForSelection(selection); }
    QRegion visualRegionForSelection_pub_parent(const QItemSelection & selection) const { return QListWidget::visualRegionForSelection(selection); }
    void wheelEvent_pub(QWheelEvent * e)  { wheelEvent(e); }
    void wheelEvent_pub_parent(QWheelEvent * e)  { QListWidget::wheelEvent(e); }
  public:
    const QListWidgetType* _baseType;
    ClassInstance* _obj;
    const CallEnvironment* _env;
};

inline ClassInstance* QListWidgetType::cachedInstance(const QListWidgetType::MuQtType* obj) { return obj->_obj; }

} // Mu

#endif // __MuQt__QListWidgetType__h__
