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

#ifndef __MuQt5__$TType__h__
#define __MuQt5__$TType__h__
#include <iostream>
#include <Mu/Class.h>
#include <Mu/ClassInstance.h>
#include <QtCore/QtCore>
#include <QtGui/QtGui>
#include <QtWidgets/QtWidgets>

namespace Mu {

//
//  NOTE: file generated by qt2mu.py
//

class $TType : public Class
{
  public:
    //
    //  Types
    //

    typedef $T ValueType;

    class Instance : public ClassInstance
    {
      public:
        //
        //  Probably need some kind of finalizer for classes that are
        //  references (e.g. QIcon)
        //
        Instance(const Class*);
        $T value;
    };

    //
    //  Constructors
    //

    $TType(Context* context, const char* name, Class* superClass = 0);
    virtual ~$TType();

    //
    //  Class API
    //

    virtual void load();

    //
    //  Finalizer
    //

    static void registerFinalizer (void*);
    static void finalizer (void*, void*);
};

} // Mu

#endif // __MuQt5__$TType__h__
