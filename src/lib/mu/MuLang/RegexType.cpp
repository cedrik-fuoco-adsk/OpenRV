//
// Copyright (c) 2009, Jim Hourihan
// All rights reserved.
//
// SPDX-License-Identifier: Apache-2.0 
// 

#include <MuLang/RegexType.h>
#include <Mu/BaseFunctions.h>
#include <Mu/Function.h>
#include <Mu/Module.h>
#include <Mu/ParameterVariable.h>
#include <Mu/ReferenceType.h>
#include <Mu/SymbolicConstant.h>
#include <Mu/Thread.h>
#include <Mu/Vector.h>
#include <MuLang/DynamicArray.h>
#include <MuLang/DynamicArrayType.h>
#include <MuLang/ExceptionType.h>
#include <MuLang/MuLangContext.h>
#include <MuLang/StringType.h>
#include <ctype.h>
#include <iostream>
#include <sstream>

#if COMPILER == GCC2_96
#include <stdio.h>
#endif

#ifndef REG_BASIC
#define REG_BASIC 0
#endif

#ifndef REG_NOSPEC
#define REG_NOSPEC 0
#endif

//----------------------------------------------------------------------
//
//  "Compiled" functions
//
using namespace std;
using namespace Mu;

Pointer
regex_regex_string(Mu::Thread& NODE_THREAD, Pointer str)
{
    Process *p = NODE_THREAD.process();
    const StringType::String* s = reinterpret_cast<StringType::String*>(str);
    const Class *c = static_cast<MuLangContext*>(p->context())->regexType();
    if (!s) throw NilArgumentException(NODE_THREAD);

    RegexType::Regex *o = new RegexType::Regex(c);
    o->string() = s->c_str();
    o->compile(NODE_THREAD, REG_EXTENDED);
    return Pointer(o);
}

Pointer
regex_regex_string_int(Mu::Thread& NODE_THREAD, 
                       Pointer str,
                       int flags)
{
    Process *p = NODE_THREAD.process();
    const StringType::String* s = reinterpret_cast<StringType::String*>(str);
    const Class *c = static_cast<MuLangContext*>(p->context())->regexType();
    if (!s) throw NilArgumentException(NODE_THREAD);

    RegexType::Regex* o = new RegexType::Regex(c);
    o->string() = s->c_str();
    o->compile(NODE_THREAD, flags);
    return Pointer(o);
}

bool
regex_match_bool_regex_string(Mu::Thread& NODE_THREAD,
                                Pointer reg,
                                Pointer str)
{
    Process *p = NODE_THREAD.process();
    RegexType::Regex* r = reinterpret_cast<RegexType::Regex*>(reg);
    const StringType::String* s = reinterpret_cast<StringType::String*>(str);
    if (!r || !s) throw NilArgumentException(NODE_THREAD);
    return r->matches(NODE_THREAD, s->c_str(), 0);
}

Pointer
regex_smatch_stringBSB_ESB__regex_string(Mu::Thread& NODE_THREAD, 
                                         Pointer reg,
                                         Pointer pstr)
{
    Process *p = NODE_THREAD.process();
    MuLangContext* context = static_cast<MuLangContext*>(p->context());
    RegexType::Regex* r = reinterpret_cast<RegexType::Regex*>(reg);
    const StringType::String* str = reinterpret_cast<StringType::String*>(pstr);

    if (!r || !str) throw NilArgumentException(NODE_THREAD);

    QRegularExpressionMatch matches;
    // TODO_PCRE Remove num param
    if (!r->smatch(NODE_THREAD, str->c_str(),  0, matches, 0)) 
    {
        return  0;
    }

    const StringType* stype = static_cast<const StringType*>(str->type());
    const DynamicArrayType* atype  = 
        static_cast<DynamicArrayType*>(context->arrayType(stype, 1, 0));

    DynamicArray *array = new DynamicArray(atype, 1);
    // capturedTexts() include the implicit capturing group number 0, 
    // capturing the substring matched by the entire pattern
    array->resize(matches.capturedTexts().size());

    for (int i=0; i < matches.capturedTexts().size(); i++)
    {
        StringType::String* s = 0;
        // Access captured text directly
        QString capturedText = matches.capturedTexts().at(i);

        if (!capturedText.isEmpty()) 
        {
            s = stype->allocate(capturedText.toStdString());
        }

        array->element<StringType::String*>(i) = s;
    }

    return Pointer(array);
}

void
print_void_regex(Mu::Thread& NODE_THREAD, Pointer reg)
{
    RegexType::Regex* o = reinterpret_cast<RegexType::Regex*>(reg);

    if (o)
    {
	cout << o->string() << flush;
    }
    else
    {
	cout << "nil" << flush;
    }
}

Pointer
regex_replace_string_regex_string_string(Mu::Thread& NODE_THREAD,
                                         Pointer reg,
                                         Pointer astr,
                                         Pointer bstr)
{
    Process*            p       = NODE_THREAD.process();
    MuLangContext*      context = static_cast<MuLangContext*>(p->context());
    RegexType::Regex*   r       = reinterpret_cast<RegexType::Regex*>(reg);
    const StringType::String* instr   = reinterpret_cast<StringType::String*>(astr);
    const StringType::String* inrepl  = reinterpret_cast<StringType::String*>(bstr);
    const StringType*         stype   = context->stringType();

    if (!r || !instr || !inrepl) throw NilArgumentException(NODE_THREAD);

    String text(instr->c_str());
    String repl(inrepl->c_str());
    String::size_type ic;

    typedef pair<Mu::String,int> ReplPart;
    typedef APIAllocatable::STLVector<ReplPart>::Type ReplParts;
    ReplParts parts;

    while ((ic = repl.find('\\')) != string::npos)
    {
        if (ic < repl.size() - 1)
        {
            char c = repl[ic+1];

            switch (c)
            {
              case '&':
                  parts.push_back(ReplPart(repl.substr(0,ic), 0));
                  break;
              case '0':
              case '1':
              case '2':
              case '3':
              case '4':
              case '5':
              case '6':
              case '7':
              case '8':
              case '9':
                  parts.push_back(ReplPart(repl.substr(0,ic), c-'0'));
                  break;
              case '\\':
                  parts.push_back(ReplPart(repl.substr(0,ic), -1));
                  break;
            }

            repl = repl.substr(ic+2);
        }
    }

    if (repl.size())
    {
        parts.push_back(ReplPart(repl, -2));
    }

    QRegularExpressionMatch matches;
    ostringstream out;

    while (r->smatch(NODE_THREAD, text, 0, matches, 0))
    {
        int b = matches.capturedStart(0);
        int e = matches.capturedEnd(0);

        //  Output everything before the match
        for (int i=0; i < b; i++) out << text[i];

        // Output the replacement string
        for (const auto& part : parts)
        {
            int rl = part.second;
            out << part.first;

            if (rl == -1)  
            {
                out << '\\';
            }
            else if (rl >=  0)
            {
                int bm = matches.capturedStart(rl);
                int em = matches.capturedEnd(rl);

                if (bm <  0 || bm >= text.size() ||
                    em <  0 || em >= text.size()+1)
                {
                    OutOfRangeException exc(NODE_THREAD);
                    exc.message() = "bad replacement index: " + exc.message();
                    throw exc;
                }
                else
                {
                    out << text.substr(bm, em-bm);
                }
            }
        }

        //  Output everything after the match
        text.erase(0, e);
    }

    out << text;

    return Pointer(stype->allocate(out));
}



namespace Mu {
using namespace std;
using namespace Mu;

RegexType::Regex::Regex(const Class *c) 
    : ClassInstance(c)
{
    _flags = convertPcreFlagsToQt(_flags);
}

RegexType::Regex::Regex(const Class *c, Thread& t, const char* s, int flags)
    : ClassInstance(c)
{
    _flags = convertPcreFlagsToQt(_flags);
    if (s) 
    {
        _std_string = s;
        compile(t, flags);
    }
}

RegexType::Regex::~Regex()
{
    //regfree(&_regex);
}

void 
RegexType::freeze()
{
    Class::freeze();
    _isGCAtomic = false;
}

void
RegexType::Regex::throwError(Thread& thread, std::string err)
{
    Process* p = thread.process();
    const MuLangContext* c = static_cast<const MuLangContext*>(p->context());
    
    ExceptionType::Exception *e = 
        new ExceptionType::Exception(c->exceptionType());
    
    e->string() += "Regular exression error: ";
    e->string() += err;
    
    thread.setException(e);
    throw ProgramException(thread, e);
}

// TODO_PCRE Temporary
#define REG_ICASE     0x0001
#define REG_NEWLINE   0x0002
#define REG_NOTBOL    0x0004
#define REG_NOTEOL    0x0008
#define REG_DOTALL    0x0010   /* NOT defined by POSIX. */
#define REG_NOSUB     0x0020
#define REG_UTF8      0x0040   /* NOT defined by POSIX. */

QRegularExpression::PatternOptions RegexType::Regex::convertPcreFlagsToQt(int pcreFlags) 
{
    QRegularExpression::PatternOptions qtFlags = QRegularExpression::NoPatternOption;

    if (pcreFlags & REG_ICASE) {
        qtFlags |= QRegularExpression::CaseInsensitiveOption;
    }
    if (pcreFlags & REG_NEWLINE) {
        qtFlags |= QRegularExpression::DotMatchesEverythingOption;
    }
    if (pcreFlags & REG_NOTBOL) {
        // Qt does not have a direct equivalent for REG_NOTBOL.
        // You might need to adjust your pattern or use a workaround.
        cout << "WARNING: REG_NOTBOL NOT SUPPORTED AS IS IN QT" << endl;
    }
    if (pcreFlags & REG_NOTEOL) {
        // Qt does not have a direct equivalent for REG_NOTEOL.
        // You might need to adjust your pattern or use a workaround.
        cout << "WARNING: REG_NOTEOL NOT SUPPORTED AS IS IN QT" << endl;
    }
    if (pcreFlags & REG_DOTALL) {
        qtFlags |= QRegularExpression::DotMatchesEverythingOption;
    }
    if (pcreFlags & REG_NOSUB) {
        // Qt does not have a direct equivalent for REG_NOSUB.
        // You might need to adjust your pattern or use a workaround.
        cout << "WARNING: REG_NOSUB NOT SUPPORTED AS IS IN QT" << endl;
    }
    if (pcreFlags & REG_UTF8) {
        qtFlags |= QRegularExpression::UseUnicodePropertiesOption;
    }

    return qtFlags;
}

QRegularExpression::MatchOptions RegexType::Regex::convertPcreMatchOptionsToQt(int pcreFlags) {
    QRegularExpression::MatchOptions qtFlags = QRegularExpression::NoMatchOption;

    if (pcreFlags & REG_NOTBOL) {
        qtFlags |= QRegularExpression::AnchoredMatchOption;
    }
    // if (pcreFlags & REG_NOTEMPTY) {
    //     // Qt does not have a direct equivalent for REG_NOTEMPTY.
    //     // You might need to adjust your pattern or use a workaround.
    //     cout << "WARNING: REG_NOTEMPTY NOT SUPPORTED AS IS IN QT" << endl;
    // }
    if (pcreFlags & REG_NOTEOL) {
        // Qt does not have a direct equivalent for REG_NOTEOL.
        // You might need to adjust your pattern or use a workaround.
        cout << "WARNING: REG_NOTEOL NOT SUPPORTED AS IS IN QT" << endl;
    }
    // if (pcreFlags & REG_STARTEND) {
    //     // Qt does not have a direct equivalent for REG_STARTEND.
    //     // You might need to adjust your pattern or use a workaround.
    //     cout << "WARNING: REG_STARTEND NOT SUPPORTED AS IS IN QT" << endl;
    // }
    if (pcreFlags & REG_NOSUB) {
        // Qt does not have a direct equivalent for REG_NOSUB.
        // You might need to adjust your pattern or use a workaround.
        cout << "WARNING: REG_NOSUB NOT SUPPORTED AS IS IN QT" << endl;
    }
    if (pcreFlags & REG_UTF8) {
        // Qt does not have a direct equivalent for REG_UTF8.
        // You might need to adjust your pattern or use a workaround.
        cout << "WARNING: REG_UTF8 NOT SUPPORTED AS IS IN QT" << endl;
    }

    return qtFlags;
}

void
RegexType::Regex::compile(Thread& thread, int flags)
{
    _flags = convertPcreFlagsToQt(flags);
    
    #if defined(_MSC_VER) || defined(PLATFORM_WINDOWS)
        //  "." matches _all_ chars even '\n'
        _flags = convertPcreFlagsToQt(_flags | REG_DOTALL);  
    #endif
    
    QRegularExpression regex(QString::fromStdString(_std_string.c_str()), _flags);
    if (!regex.isValid())
    {
        throwError(thread, regex.errorString().toStdString());
    }
}

bool
RegexType::Regex::matches(Thread& thread, const Mu::String& s, int flags)
{
    QRegularExpression::MatchOptions matchOptions = convertPcreMatchOptionsToQt(flags);
    QRegularExpressionMatch match = _regex.match(s.c_str(), 
                                                 0, 
                                                 QRegularExpression::NormalMatch,
                                                 matchOptions);
    bool matched = match.hasMatch();
    if (!matched)
    {
        throwError(thread, s.c_str());
        return false; // never gets here
    }
    return matched;
}


bool
RegexType::Regex::smatch(Thread& thread, const Mu::String& s, 
                         int flags,
                         QRegularExpressionMatch& matches, size_t num)
{
    //TODO_PCRE Could return the match object and the caller handle it?
    QRegularExpression::MatchOptions matchOpt = convertPcreMatchOptionsToQt(flags);
    matches = _regex.match(QString::fromStdString(s.c_str()),  0, QRegularExpression::NormalMatch, matchOpt);
    bool matched = matches.hasMatch();
    if (!matched)
    {
        throwError(thread, s.c_str());
        return false; // never gets here
    }
    return matched;
}

//----------------------------------------------------------------------

RegexType::RegexType(Context* c, Class *super) : Class(c, "regex", super)
{
}

RegexType::~RegexType() {}

Object*
RegexType::newObject() const
{
    return new Regex(this);
}

void
RegexType::deleteObject(Object *obj) const
{
    delete static_cast<RegexType::Regex*>(obj);
}

void 
RegexType::outputValue(ostream &o, const Value &value, bool full) const
{
    Regex *s = reinterpret_cast<Regex*>(value._Pointer);

    if (s)
    {
        StringType::outputQuotedString(o, s->string());
        o << "r";
    }
    else
    {
	o << "nil";
    }
}

void 
RegexType::outputValueRecursive(ostream &o, const ValuePointer vp, ValueOutputState& state) const
{
    const Regex *s = *reinterpret_cast<const Regex**>(vp);

    if (s)
    {
	StringType::outputQuotedString(o, s->string());
        o << "r";
    }
    else
    {
	o << "nil";
    }
}

//----------------------------------------------------------------------

void
RegexType::load()
{
    USING_MU_FUNCTION_SYMBOLS;

    Symbol* s = scope();
    Context* c = context();
		  
    s->addSymbols( new ReferenceType(c, "regex&", this), 

		   new Function(c, "regex", RegexType::from_string, Cast,
				Return, "regex", 
                                Args, "string", End),

		   new Function(c, "regex", RegexType::construct, Mapped,
				Return, "regex", 
                                Parameters,
                                new ParameterVariable(c, "pattern", "string"),
                                new ParameterVariable(c, "flags", "int"),
                                End),

		   new Function(c, "regex", BaseFunctions::dereference, Cast,
				Return, "regex",
				Args, "regex&", End),

		   new Function(c, "=", BaseFunctions::assign, AsOp,
				Return, "regex&", 
				Args, "regex&", "regex", End),

		   new Function(c, "print", RegexType::print, None,
				Return, "void", 
				Args, "regex", End),

		   EndArguments);

    //
    //  Can't make the array type until the reference type above exists
    //

    MuLangContext* context = (MuLangContext*)globalModule()->context();
    context->arrayType(this, 1, 0);

    addSymbols( new SymbolicConstant(c, "Extended", "int", 
				     Value(int(REG_EXTENDED))),

		new SymbolicConstant(c, "Basic", "int", Value(int(REG_BASIC))),
		new SymbolicConstant(c, "NoSpec", "int", Value(int(REG_NOSPEC))),
		new SymbolicConstant(c, "IgnoreCase", "int", Value(int(REG_ICASE))),
		new SymbolicConstant(c, "NoSub", "int", Value(int(REG_NOSUB))),
		new SymbolicConstant(c, "NotBOL", "int", Value(int(REG_NOTBOL))),
		new SymbolicConstant(c, "NotEOL", "int", Value(int(REG_NOTEOL))),

                new Function(c, "match", RegexType::match, Mapped,
                             Return, "bool",
                             Compiled, regex_match_bool_regex_string,
                             Args, "regex", "string", 
                             End),

                new Function(c, "smatch", RegexType::smatch, 
                             Mapped,
                             Return, "string[]",
                             Compiled, regex_smatch_stringBSB_ESB__regex_string,
                             Args, "regex", "string", 
                             End),

                new Function(c, "replace", RegexType::replace, 
                             Mapped,
                             Return, "string",
                             Compiled, regex_replace_string_regex_string_string,
                             Args, "regex", "string", "string", 
                             End),

#if 0
                new Function(c, "split", RegexType::split, Mapped,
                             Return, "string[]",
                             Args, "regex", "string", 
                             End),
#endif

		EndArguments );

}

NODE_IMPLEMENTATION(RegexType::from_string, Pointer)
{
    NODE_RETURN(regex_regex_string(NODE_THREAD, NODE_ARG(0,Pointer)));
}

NODE_IMPLEMENTATION(RegexType::construct, Pointer)
{
    NODE_RETURN(regex_regex_string_int(NODE_THREAD, 
                                       NODE_ARG(0,Pointer), 
                                       NODE_ARG(1,int)));
}

NODE_IMPLEMENTATION(RegexType::match, bool)
{
    NODE_RETURN(regex_match_bool_regex_string(NODE_THREAD,
                                              NODE_ARG(0,Pointer),
                                              NODE_ARG(1,Pointer)));
}

NODE_IMPLEMENTATION(RegexType::smatch, Pointer)
{
    NODE_RETURN(regex_smatch_stringBSB_ESB__regex_string(NODE_THREAD,
                                                         NODE_ARG(0,Pointer),
                                                         NODE_ARG(1,Pointer)));
}

NODE_IMPLEMENTATION(RegexType::print, void)
{
    print_void_regex(NODE_THREAD, NODE_ARG(0,Pointer));
}

NODE_IMPLEMENTATION(RegexType::replace, Pointer)
{
    NODE_RETURN(regex_replace_string_regex_string_string(NODE_THREAD,
                                                         NODE_ARG(0,Pointer),
                                                         NODE_ARG(1,Pointer),
                                                         NODE_ARG(2,Pointer)));
}


} // namespace Mu

