//******************************************************************************
// Copyright (c) 2001-2002 Tweak Inc. All rights reserved.
// 
// SPDX-License-Identifier: Apache-2.0
// 
//******************************************************************************

#include <TwkUtil/TwkRegEx.h>
#include <sstream>
#include <algorithm>
#include <stdlib.h>
#include <assert.h>
#include <stdio.h>

using namespace std;

/* AJG - snprintf'isms */
#ifdef _MSC_VER
#define snprintf _snprintf
#endif

namespace TwkUtil {

//******************************************************************************
//******************************************************************************
// REGEX CLASS
//******************************************************************************
//******************************************************************************

//******************************************************************************
// Default constructor. Makes a regular expression that no-one could ever
// match.
RegEx::RegEx()
  : m_pattern( MATCH_NOTHING ),
    m_flags( QRegularExpression::NoPatternOption ),
    m_regexCompStatus( -1 )
{
    init();
}

//******************************************************************************
// Regular constructors...
RegEx::RegEx( const char *pattern, QRegularExpression::PatternOptions flags )
  : m_pattern( pattern ),
    m_flags( flags ),
    m_regexCompStatus( -1 )
{
    init();
}

//******************************************************************************
RegEx::RegEx( const std::string &pattern, QRegularExpression::PatternOptions flags )
  : m_pattern( pattern ),
    m_flags( flags ),
    m_regexCompStatus( -1 )
{
    init();  
}

//******************************************************************************
// Copy constructor
RegEx::RegEx( const RegEx &regex )
  : m_pattern( regex.m_pattern ),
    m_flags( regex.m_flags ),
    m_regexCompStatus( -1 )
{
    init();
}

//******************************************************************************
RegEx::~RegEx()
{

}

//******************************************************************************
// Assignment operator
RegEx &RegEx::operator=( const RegEx &copy )
{
    m_pattern = copy.m_pattern;
    m_flags = copy.m_flags;
    m_regexCompStatus = -1;
    m_preg = QRegularExpression(QString::fromStdString(m_pattern));
    // m_preg.setPatternOptions ?
    init();
    return (*this);
}

//******************************************************************************
void RegEx::init()
{
    try
    {
        m_preg.setPattern(QString::fromStdString(m_pattern));
    }
    catch(const std::exception& e)
    {
        std::string errMsg(e.what());
        std::string fullMsg = "RegEx::init: " + errMsg + ": " + m_pattern;
        TWK_EXC_THROW_WHAT(Exception, fullMsg.c_str());
    }
}

// *****************************************************************************
bool RegEx::matches( const char *fullStr ) const
{
    QRegularExpressionMatch match = m_preg.match(QString::fromUtf8(fullStr));
    return match.hasMatch();
}


//******************************************************************************
const RegEx &RegEx::nothing() 
{
    static RegEx ret( MATCH_NOTHING );
    return ret;
}

//******************************************************************************
const RegEx &RegEx::anything() 
{
    static RegEx ret( MATCH_ANYTHING );
    return ret;
}


//******************************************************************************
//******************************************************************************
// GLOB FUNCTION
//******************************************************************************
//******************************************************************************
string GlobEx::deglobSyntax( const char *pattern )
{
    string gpat( pattern );
    
    int lastFound = 0;
    while( gpat.find( ".", lastFound ) != gpat.npos )
    {
        gpat.replace( gpat.find( ".", lastFound ), 1, "\\." );
        lastFound = gpat.find( ".", lastFound ) + 1;
    }
    while( gpat.find( "?" ) != gpat.npos )
    {
        gpat.replace( gpat.find( "?" ), 1, "." );
    }

    lastFound = 0;
    while( gpat.find( "*", lastFound ) != gpat.npos )
    {
        gpat.replace( gpat.find( "*", lastFound ), 1, ".*" );
        lastFound = gpat.find( "*", lastFound ) + 1;
    }
    
    gpat = "^" + gpat + "$";
    
    return gpat;
}

//******************************************************************************
//******************************************************************************
// MATCH CLASS
//******************************************************************************
//******************************************************************************

//******************************************************************************
// Default constructor
Match::Match()
  : m_regex( &RegEx::nothing() ),
    m_fullStr( "" ),
    m_foundMatch( false )
{
    init();
}

//******************************************************************************
// Regular constructors
Match::Match( const RegEx &regex, const char *fullStr )
  : m_regex( &regex ),
    m_fullStr( fullStr ),
    m_foundMatch( false )
{
    init();
}

//******************************************************************************
Match::Match( const RegEx &regex, const std::string &fullStr )
  : m_regex( &regex ),
    m_fullStr( fullStr ),
    m_foundMatch( false )
{
    init();
}

//******************************************************************************
// Copy constructor
Match::Match( const Match &copy )
  : m_regex( copy.m_regex ),
    m_fullStr( copy.m_fullStr ),
    m_foundMatch( false )
{
    init();
}

//******************************************************************************
Match::~Match()
{

}

//******************************************************************************
// Assignment operator
Match &Match::operator=( const Match &copy )
{
    if (this != &copy)
    {
        m_regex = copy.m_regex;
        m_fullStr = copy.m_fullStr;
        m_foundMatch = false;
        // Directly assign the QRegularExpressionMatch object
        m_pmatch = copy.m_pmatch;
        init();
    }
    return (*this);
}

//******************************************************************************
void Match::init()
{
    m_foundMatch = false;
    
    QRegularExpression regex = m_regex->preg();
    m_pmatch = regex.match(QString::fromStdString(m_fullStr));
    if (m_pmatch.hasMatch())
    {
        m_foundMatch = true;
    }
}


// *****************************************************************************
bool Match::hasSub( const int subNum ) const
{
    assert(subNum >= 0 && subNum < m_regex->subCount());
    assert(m_foundMatch);

    // Check if the capturing group has a match.
    QString str = m_pmatch.captured(subNum);
    return !str.isNull();
}


// *****************************************************************************
int Match::subStartPos( const int subNum ) const
{
    assert(subNum >= 0 && subNum < m_regex->subCount());
    assert(m_foundMatch);

    // get the start position of the subNum-th captured group.
    int startPos = m_pmatch.capturedStart(subNum);
    // TODO_PCRE Check if it should be -1 or 0
    return startPos != -1 ? startPos : -1;
}


// *****************************************************************************
int Match::subEndPos( const int subNum ) const
{
    assert(subNum >= 0 && subNum < m_regex->subCount());
    assert(m_foundMatch);

    // Get the end position of the subNum-th captured group.
    int endPos = m_pmatch.capturedEnd(subNum); 
    // TODO_PCRE Check if it should be -1 or 0
    return endPos != -1 ? endPos : -1;
}


//******************************************************************************
int Match::subLen( const int subNum ) const
{
    assert(subNum >=  0 && subNum < m_regex->subCount());
    assert(m_foundMatch);

    // Get the length of the subNum-th captured group.
    int len = m_pmatch.capturedLength(subNum);
    // TODO_PCRE Check if it should be -1 or 0
    return len != -1 ? len : -1;
}


//******************************************************************************
string Match::subStr( const int subNum ) const
{
    assert(subNum >=  0 && subNum < m_regex->subCount());
    assert(m_foundMatch);

    // Get the captured substring
    QString captured = m_pmatch.captured(subNum);
    return captured.toStdString();
}



} // End namespace TwkUtil;

#ifdef _MSC_VER
#undef snprintf
#endif
