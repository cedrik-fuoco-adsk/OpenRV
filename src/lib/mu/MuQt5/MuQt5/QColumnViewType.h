//
// Copyright (c) 2009, Jim Hourihan
// All rights reserved.
//
// SPDX-License-Identifier: Apache-2.0
//
#ifndef __MuQt5__QColumnViewType__h__
#define __MuQt5__QColumnViewType__h__
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
    class MuQt_QColumnView;

    //
    //  NOTE: file generated by qt2mu.py
    //

    class QColumnViewType : public Class
    {
    public:
        typedef MuQt_QColumnView MuQtType;
        typedef QColumnView QtType;

        //
        //  Constructors
        //

        QColumnViewType(Context* context, const char* name,
                        Class* superClass = 0, Class* superClass2 = 0);

        virtual ~QColumnViewType();

        static bool isInheritable() { return true; }

        static inline ClassInstance* cachedInstance(const MuQtType*);

        //
        //  Class API
        //

        virtual void load();

        MemberFunction* _func[41];
    };

    // Inheritable object

    class MuQt_QColumnView : public QColumnView
    {
    public:
        virtual ~MuQt_QColumnView();
        MuQt_QColumnView(Pointer muobj, const CallEnvironment*,
                         QWidget* parent);
        virtual QModelIndex indexAt(const QPoint& point) const;
        virtual void selectAll();
        virtual void setModel(QAbstractItemModel* model);
        virtual void setRootIndex(const QModelIndex& index);
        virtual void setSelectionModel(QItemSelectionModel* newSelectionModel);
        virtual QSize sizeHint() const;
        virtual QRect visualRect(const QModelIndex& index) const;

    protected:
        virtual QAbstractItemView* createColumn(const QModelIndex& index);
        virtual void currentChanged(const QModelIndex& current,
                                    const QModelIndex& previous);
        virtual int horizontalOffset() const;
        virtual bool isIndexHidden(const QModelIndex& index) const;
        virtual void resizeEvent(QResizeEvent* event);
        virtual void rowsInserted(const QModelIndex& parent, int start,
                                  int end);
        virtual void scrollContentsBy(int dx, int dy);
        virtual void setSelection(const QRect& rect,
                                  QItemSelectionModel::SelectionFlags command);
        virtual int verticalOffset() const;
        virtual QRegion
        visualRegionForSelection(const QItemSelection& selection) const;

    public:
        virtual void keyboardSearch(const QString& search);
        virtual int sizeHintForColumn(int column) const;
        virtual int sizeHintForRow(int row) const;
        virtual QVariant inputMethodQuery(Qt::InputMethodQuery query) const;

    protected:
        virtual bool edit(const QModelIndex& index,
                          QAbstractItemView::EditTrigger trigger,
                          QEvent* event);
        virtual QModelIndexList selectedIndexes() const;
        virtual QItemSelectionModel::SelectionFlags
        selectionCommand(const QModelIndex& index, const QEvent* event) const;
        virtual void startDrag(Qt::DropActions supportedActions);
        virtual void dragEnterEvent(QDragEnterEvent* event);
        virtual void dragLeaveEvent(QDragLeaveEvent* event);
        virtual void dragMoveEvent(QDragMoveEvent* event);
        virtual void dropEvent(QDropEvent* event);
        virtual bool event(QEvent* event_);
        virtual void focusInEvent(QFocusEvent* event);
        virtual bool focusNextPrevChild(bool next);
        virtual void focusOutEvent(QFocusEvent* event);
        virtual void keyPressEvent(QKeyEvent* event);
        virtual void mouseDoubleClickEvent(QMouseEvent* event);
        virtual void mouseMoveEvent(QMouseEvent* event);
        virtual void mousePressEvent(QMouseEvent* event);
        virtual void mouseReleaseEvent(QMouseEvent* event);
        virtual void timerEvent(QTimerEvent* event);
        virtual bool viewportEvent(QEvent* event);
        virtual QSize viewportSizeHint() const;

    public:
        QAbstractItemView* createColumn_pub(const QModelIndex& index)
        {
            return createColumn(index);
        }

        QAbstractItemView* createColumn_pub_parent(const QModelIndex& index)
        {
            return QColumnView::createColumn(index);
        }

        void initializeColumn_pub(QAbstractItemView* column) const
        {
            initializeColumn(column);
        }

        void initializeColumn_pub_parent(QAbstractItemView* column) const
        {
            QColumnView::initializeColumn(column);
        }

        void currentChanged_pub(const QModelIndex& current,
                                const QModelIndex& previous)
        {
            currentChanged(current, previous);
        }

        void currentChanged_pub_parent(const QModelIndex& current,
                                       const QModelIndex& previous)
        {
            QColumnView::currentChanged(current, previous);
        }

        int horizontalOffset_pub() const { return horizontalOffset(); }

        int horizontalOffset_pub_parent() const
        {
            return QColumnView::horizontalOffset();
        }

        bool isIndexHidden_pub(const QModelIndex& index) const
        {
            return isIndexHidden(index);
        }

        bool isIndexHidden_pub_parent(const QModelIndex& index) const
        {
            return QColumnView::isIndexHidden(index);
        }

        void resizeEvent_pub(QResizeEvent* event) { resizeEvent(event); }

        void resizeEvent_pub_parent(QResizeEvent* event)
        {
            QColumnView::resizeEvent(event);
        }

        void rowsInserted_pub(const QModelIndex& parent, int start, int end)
        {
            rowsInserted(parent, start, end);
        }

        void rowsInserted_pub_parent(const QModelIndex& parent, int start,
                                     int end)
        {
            QColumnView::rowsInserted(parent, start, end);
        }

        void scrollContentsBy_pub(int dx, int dy) { scrollContentsBy(dx, dy); }

        void scrollContentsBy_pub_parent(int dx, int dy)
        {
            QColumnView::scrollContentsBy(dx, dy);
        }

        void setSelection_pub(const QRect& rect,
                              QItemSelectionModel::SelectionFlags command)
        {
            setSelection(rect, command);
        }

        void
        setSelection_pub_parent(const QRect& rect,
                                QItemSelectionModel::SelectionFlags command)
        {
            QColumnView::setSelection(rect, command);
        }

        int verticalOffset_pub() const { return verticalOffset(); }

        int verticalOffset_pub_parent() const
        {
            return QColumnView::verticalOffset();
        }

        QRegion
        visualRegionForSelection_pub(const QItemSelection& selection) const
        {
            return visualRegionForSelection(selection);
        }

        QRegion visualRegionForSelection_pub_parent(
            const QItemSelection& selection) const
        {
            return QColumnView::visualRegionForSelection(selection);
        }

        bool edit_pub(const QModelIndex& index,
                      QAbstractItemView::EditTrigger trigger, QEvent* event)
        {
            return edit(index, trigger, event);
        }

        bool edit_pub_parent(const QModelIndex& index,
                             QAbstractItemView::EditTrigger trigger,
                             QEvent* event)
        {
            return QColumnView::edit(index, trigger, event);
        }

        QModelIndexList selectedIndexes_pub() const
        {
            return selectedIndexes();
        }

        QModelIndexList selectedIndexes_pub_parent() const
        {
            return QColumnView::selectedIndexes();
        }

        QItemSelectionModel::SelectionFlags
        selectionCommand_pub(const QModelIndex& index,
                             const QEvent* event) const
        {
            return selectionCommand(index, event);
        }

        QItemSelectionModel::SelectionFlags
        selectionCommand_pub_parent(const QModelIndex& index,
                                    const QEvent* event) const
        {
            return QColumnView::selectionCommand(index, event);
        }

        void startDrag_pub(Qt::DropActions supportedActions)
        {
            startDrag(supportedActions);
        }

        void startDrag_pub_parent(Qt::DropActions supportedActions)
        {
            QColumnView::startDrag(supportedActions);
        }

        void dragEnterEvent_pub(QDragEnterEvent* event)
        {
            dragEnterEvent(event);
        }

        void dragEnterEvent_pub_parent(QDragEnterEvent* event)
        {
            QColumnView::dragEnterEvent(event);
        }

        void dragLeaveEvent_pub(QDragLeaveEvent* event)
        {
            dragLeaveEvent(event);
        }

        void dragLeaveEvent_pub_parent(QDragLeaveEvent* event)
        {
            QColumnView::dragLeaveEvent(event);
        }

        void dragMoveEvent_pub(QDragMoveEvent* event) { dragMoveEvent(event); }

        void dragMoveEvent_pub_parent(QDragMoveEvent* event)
        {
            QColumnView::dragMoveEvent(event);
        }

        void dropEvent_pub(QDropEvent* event) { dropEvent(event); }

        void dropEvent_pub_parent(QDropEvent* event)
        {
            QColumnView::dropEvent(event);
        }

        bool event_pub(QEvent* event_) { return event(event_); }

        bool event_pub_parent(QEvent* event_)
        {
            return QColumnView::event(event_);
        }

        void focusInEvent_pub(QFocusEvent* event) { focusInEvent(event); }

        void focusInEvent_pub_parent(QFocusEvent* event)
        {
            QColumnView::focusInEvent(event);
        }

        bool focusNextPrevChild_pub(bool next)
        {
            return focusNextPrevChild(next);
        }

        bool focusNextPrevChild_pub_parent(bool next)
        {
            return QColumnView::focusNextPrevChild(next);
        }

        void focusOutEvent_pub(QFocusEvent* event) { focusOutEvent(event); }

        void focusOutEvent_pub_parent(QFocusEvent* event)
        {
            QColumnView::focusOutEvent(event);
        }

        void keyPressEvent_pub(QKeyEvent* event) { keyPressEvent(event); }

        void keyPressEvent_pub_parent(QKeyEvent* event)
        {
            QColumnView::keyPressEvent(event);
        }

        void mouseDoubleClickEvent_pub(QMouseEvent* event)
        {
            mouseDoubleClickEvent(event);
        }

        void mouseDoubleClickEvent_pub_parent(QMouseEvent* event)
        {
            QColumnView::mouseDoubleClickEvent(event);
        }

        void mouseMoveEvent_pub(QMouseEvent* event) { mouseMoveEvent(event); }

        void mouseMoveEvent_pub_parent(QMouseEvent* event)
        {
            QColumnView::mouseMoveEvent(event);
        }

        void mousePressEvent_pub(QMouseEvent* event) { mousePressEvent(event); }

        void mousePressEvent_pub_parent(QMouseEvent* event)
        {
            QColumnView::mousePressEvent(event);
        }

        void mouseReleaseEvent_pub(QMouseEvent* event)
        {
            mouseReleaseEvent(event);
        }

        void mouseReleaseEvent_pub_parent(QMouseEvent* event)
        {
            QColumnView::mouseReleaseEvent(event);
        }

        void timerEvent_pub(QTimerEvent* event) { timerEvent(event); }

        void timerEvent_pub_parent(QTimerEvent* event)
        {
            QColumnView::timerEvent(event);
        }

        bool viewportEvent_pub(QEvent* event) { return viewportEvent(event); }

        bool viewportEvent_pub_parent(QEvent* event)
        {
            return QColumnView::viewportEvent(event);
        }

        QSize viewportSizeHint_pub() const { return viewportSizeHint(); }

        QSize viewportSizeHint_pub_parent() const
        {
            return QColumnView::viewportSizeHint();
        }

    public:
        const QColumnViewType* _baseType;
        ClassInstance* _obj;
        const CallEnvironment* _env;
    };

    inline ClassInstance*
    QColumnViewType::cachedInstance(const QColumnViewType::MuQtType* obj)
    {
        return obj->_obj;
    }

} // namespace Mu

#endif // __MuQt__QColumnViewType__h__
