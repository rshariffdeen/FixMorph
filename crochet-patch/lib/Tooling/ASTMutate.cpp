#include "crochet-patch/Tooling/ASTMutate.h"
#include "clang/Basic/FileManager.h"
#include "clang/Basic/Diagnostic.h"
#include "clang/Basic/SourceManager.h"
#include "clang/Lex/Lexer.h"
#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/ASTContext.h"
#include "clang/AST/PrettyPrinter.h"
#include "clang/AST/RecordLayout.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Rewrite/Frontend/Rewriters.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "llvm/IR/Module.h"
#include "llvm/Support/Path.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Support/Timer.h"

#include <sys/types.h>
#include <sys/stat.h>
#include <stdio.h>
#include <iostream>
#include <string>

#define VISIT(func) \
  bool func { VisitRange(element->getSourceRange()); return true; }

using namespace clang;

namespace {
  class ASTMutator : public ASTConsumer,
                     public RecursiveASTVisitor<ASTMutator> {
    typedef RecursiveASTVisitor<ASTMutator> base;

  public:
    ASTMutator(raw_ostream *Out = NULL,
               ACTION Action = NUMBER,
               unsigned int Line = 0, unsigned int Column = 0, unsigned int Offset = 0,
               StringRef Query = (StringRef)"", StringRef Value = (StringRef)"")
      : Out(Out ? *Out : llvm::outs()),
        Action(Action), Line(Line), Offset(Offset),
        Query(Query), Value(Value), Column(Column) {}

    virtual void HandleTranslationUnit(ASTContext &Context) {
      TranslationUnitDecl *D = Context.getTranslationUnitDecl();
      // Setup
     
      mainFileID=Context.getSourceManager().getMainFileID();
      Rewrite.setSourceMgr(Context.getSourceManager(),
                           Context.getLangOpts());
      // Run Recursive AST Visitor
      TraverseDecl(D);
      if (modified)      
        OutputRewritten(Context);
      
    };
    
    Rewriter Rewrite;


    bool SelectRange(SourceRange r)
    {
      //llvm::outs() << "1" << "\n";
      FullSourceLoc loc = FullSourceLoc(r.getEnd(), Rewrite.getSourceMgr());
      //llvm::outs() << "2" << "\n";
     // loc.dump();
      //llvm::outs() << "3" << "\n";
      return (loc.getFileID() == mainFileID);
    }

  

    void DeleteNode(Stmt *s)
    {

      SourceManager &SM = Rewrite.getSourceMgr();
      PresumedLoc PLoc = SM.getPresumedLoc(s->getSourceRange().getBegin());   
      unsigned line_number = PLoc.getLine();
      unsigned column_number = PLoc.getColumn();

      if(line_number == Line && column_number == Column) {     

        // Out << "Start of Operation" << "\n";

        std::string search_type = Query.substr(0, Query.find(":"));
        std::string search_value = Query.substr(Query.find(":") + 2, Query.find("(") - Query.find(":") - 2);
        std::string node_type = s->getStmtClassName();
        std::string node_value = Rewrite.getRewrittenText(s->getSourceRange());

        // Out << search_type << "\n";
        // Out << node_type << "\n";

        if (search_value == node_value && search_type == node_type){
        
          // Out << "Query Type: " << query_type << "\n";DeclRefExpr
          // Out << "Query Value: " << query_value << "\n";

          // Out << "Node Type: " << node_type << "\n";
          // Out << "Node Value: " << node_value << "\n";

          SourceRange r = expandRange(s->getSourceRange());
          Rewrite.ReplaceText(r, "");
          modified = true;
     

        }
                
         // Out << "End of Operation" << "\n";
      }

    }

    bool replaceSubString(std::string& str, const std::string& from, const std::string& to) {
      size_t start_pos = str.find(from);
      if(start_pos == std::string::npos)
          return false;
      str.replace(start_pos, from.length(), to);
      return true;
    }

    void UpdateNode(Stmt *s)
    {
      
      SourceManager &SM = Rewrite.getSourceMgr();
      PresumedLoc PLoc = SM.getPresumedLoc(s->getSourceRange().getBegin());   
      unsigned line_number = PLoc.getLine();
      unsigned column_number = PLoc.getColumn();
     

      if(line_number == Line && column_number == Column) {

        bool complete = false;
        // Out << "Start of Operation" << "\n";

        StringRef search_type = Query.substr(0, Query.find(":"));
        std::string node_type = s->getStmtClassName();

       
        if ((node_type =="DeclStmt" && search_type == "VarDecl"  )|| search_type == node_type){
         
          std::string query_search = Query.substr(Query.find(":") + 2); 
          std::string node_value = Rewrite.getRewrittenText(s->getSourceRange());

          // Out << "Node Type: " << node_type << "\n";
          // Out << "Node Value: " << node_value << "\n";               

          // Out << "Query Search: " << query_search << "\n";
          // Out << "Query Replace: " << query_replace << "\n";
          

          if (node_value.find(query_search) != std::string::npos){
            complete = true;  
            modified = true;                  
            SourceRange r = expandRange(s->getSourceRange());
            replaceSubString(node_value, query_search, Value);
            Rewrite.ReplaceText(r,node_value);

          }

        }
            
                
         // Out << "End of Operation" << "\n";
      }

    }

    void InsertBefore(Stmt *s, std::string insert_value){
      SourceManager &SM = Rewrite.getSourceMgr();
      SourceRange r = expandRange(s->getSourceRange()); 
      PresumedLoc InsertLoc = SM.getPresumedLoc(r.getBegin()); 
      Rewrite.InsertTextBefore(r.getBegin(), insert_value);
      llvm::errs() << "InsertLoc: " << InsertLoc.getLine() << ":" << InsertLoc.getColumn() << "\n";
    }

    void InsertAfter(Stmt *s, std::string insert_value){
      SourceManager &SM = Rewrite.getSourceMgr();
      SourceRange r = expandRange(s->getSourceRange()); 
      PresumedLoc InsertLoc = SM.getPresumedLoc(r.getBegin()); 
      Rewrite.InsertTextAfter(r.getEnd(), insert_value);
      llvm::errs() << "InsertLoc: " << InsertLoc.getLine() << ":" << InsertLoc.getColumn() << "\n";
    }

    void InsertChild(Stmt *s, std::string insert_value){
      SourceManager &SM = Rewrite.getSourceMgr();
     
      if (Offset == 0){
       SourceRange r = expandRange(s->getSourceRange()); 
       PresumedLoc InsertLoc = SM.getPresumedLoc(r.getBegin()); 
       Rewrite.InsertTextAfter(r.getBegin(), insert_value);
       llvm::errs() << "InsertLoc: " << InsertLoc.getLine() << ":" << InsertLoc.getColumn() << "\n";

      } else {
        
        unsigned int iteration = 0;        
        for (Stmt::child_iterator i = s->child_begin(), e = s->child_end(); i != e; ++i) {    
              Stmt *currStmt = *i;         
              if (iteration == Offset){  
                Out << "getting offset\n" ;             
                SourceRange r = expandRange(currStmt->getSourceRange()); 
                PresumedLoc InsertLoc = SM.getPresumedLoc(r.getBegin()); 
                Rewrite.InsertTextBefore(r.getBegin(), insert_value);
                llvm::errs() << "InsertLoc: " << InsertLoc.getLine() << ":" << InsertLoc.getColumn() << "\n";               
                break;
              }

              iteration++;            
              
        }
      }

      
    }

    std::string getInsertValue( std::string insert_node_type){
      std::string insert_value;
      if (insert_node_type == "IfStmt"){
            insert_value = "if (true) {} ";
          } else if (insert_node_type == "DeclStmt"){
            insert_value = "\n";
          } else if (insert_node_type == "CompoundStmt"){
            insert_value = "{ }";
          } else if (insert_node_type == "CallExpr"){
            insert_value = "( )";
          } else if (insert_node_type == "ReturnStmt"){
            insert_value = "return \n";
          } else {
            insert_value = Value.substr(Value.find(":"));
          }

      return insert_value;    
    }

    void InsertNode(Stmt *s)
    {

      SourceManager &SM = Rewrite.getSourceMgr();
      PresumedLoc PLoc = SM.getPresumedLoc(s->getSourceRange().getBegin());   
      unsigned line_number = PLoc.getLine();
      unsigned column_number = PLoc.getColumn();

      std::string search_node_type = Query;
      std::string insert_node_type = Value.substr(0, Value.find(":"));   
      std::string node_type = s->getStmtClassName();

      if(line_number == Line && column_number == Column) {
        // Out<< Line << "\n"; 
        // Out<< Column << "\n";
        // Out<< "Lcation match" << "\n"; 
        if (search_node_type == node_type || node_type == typeMap[search_node_type]){
          // Out<< "node type match" << "\n"; 
          if (search_node_type == "BinaryOperator") {
             if (Offset == 0){
                InsertBefore(s, getInsertValue(insert_node_type)); 
             } else{
                InsertAfter(s, getInsertValue(insert_node_type));
             }

          } else if (search_node_type == "UnaryOperator"){

                InsertAfter(s, getInsertValue(insert_node_type));

          } else if (search_node_type == "CompoundStmt"){

                InsertChild(s, getInsertValue(insert_node_type));                    

          } else if (search_node_type == "DeclStmt"){

                InsertChild(s, getInsertValue(insert_node_type));

          } else if (search_node_type == "CallExpr"){

               if (Offset == 0){
                  InsertBefore(s, getInsertValue(insert_node_type)); 
               } else{
                  InsertChild(s, getInsertValue(insert_node_type));
               }
                
          } else if (search_node_type == "IfStmt"){

               if (Offset == 0){
                  InsertBefore(s, getInsertValue(insert_node_type)); 
               } else if (insert_node_type == "CompoundStmt"){

                  InsertAfter(s, getInsertValue(insert_node_type));

               } else{
                  InsertChild(s, getInsertValue(insert_node_type));

               }
                
          } 


        }

      }

    }

   

   

    // This function adapted from clang/lib/ARCMigrate/Transforms.cpp
    SourceLocation findCorrectEndLocation(SourceLocation loc) {
      SourceManager &SM = Rewrite.getSourceMgr();
      if (loc.isMacroID()) {
        if (!Lexer::isAtEndOfMacroExpansion(loc, SM,
                                            Rewrite.getLangOpts(), &loc))
          return SourceLocation();
      }
      loc = Lexer::getLocForEndOfToken(loc, /*Offset=*/0, SM,
                                       Rewrite.getLangOpts());

      // Break down the source location.
      std::pair<FileID, unsigned> locInfo = SM.getDecomposedLoc(loc);

      // Try to load the file buffer.
      bool invalidTemp = false;
      StringRef file = SM.getBufferData(locInfo.first, &invalidTemp);
      if (invalidTemp)
        return SourceLocation();

      const char *tokenBegin = file.data() + locInfo.second;

      // Lex from the start of the given location.
      Lexer lexer(SM.getLocForStartOfFile(locInfo.first),
                  Rewrite.getLangOpts(),
                  file.begin(), tokenBegin, file.end());
      Token tok;
      lexer.LexFromRawLexer(tok);
      if (tok.isNot(tok::semi) && tok.isNot(tok::comma))
        return SourceLocation();

      return tok.getLocation();
    }

    SourceRange expandRange(SourceRange r){
      // If the range is a full statement, and is followed by a
      // semi-colon then expand the range to include the semicolon.
      SourceLocation b = r.getBegin();
      SourceLocation e = findCorrectEndLocation(r.getEnd());
      if (e.isInvalid()) e = r.getEnd();
      return SourceRange(b,e);
    }

    bool VisitStmt(Stmt *s){      

      switch (s->getStmtClass()){        
      case Stmt::NoStmtClass:
        break;
      default:   
            
        SourceRange r = expandRange(s->getSourceRange());
        SourceManager &SM = Rewrite.getSourceMgr(); 
        PresumedLoc SLoc = SM.getPresumedLoc(s->getSourceRange().getBegin());   
        PresumedLoc ELoc = SM.getPresumedLoc(s->getSourceRange().getEnd());
        Out << s->getStmtClassName() << "\n";
        Out << SLoc.getLine() << ":" << SLoc.getColumn() << "-" << ELoc.getLine() << ":" << ELoc.getColumn() << "\n";        
        if(SelectRange(r)){        

          switch(Action){        
          case DELETE:    DeleteNode(s);   break;
          case INSERT:    InsertNode(s);   break;
          case UPDATE:    UpdateNode(s);   break;        
          
          }
          
        }
      }
      return true;
    }

    //// from AST/EvaluatedExprVisitor.h
    // VISIT(VisitDeclRefExpr(DeclRefExpr *element));
    // VISIT(VisitOffsetOfExpr(OffsetOfExpr *element));
    // VISIT(VisitUnaryExprOrTypeTraitExpr(UnaryExprOrTypeTraitExpr *element));
    // VISIT(VisitExpressionTraitExpr(ExpressionTraitExpr *element));
    // VISIT(VisitBlockExpr(BlockExpr *element));
    // VISIT(VisitCXXUuidofExpr(CXXUuidofExpr *element));
    // VISIT(VisitCXXNoexceptExpr(CXXNoexceptExpr *element));
    // VISIT(VisitMemberExpr(MemberExpr *element));
    // VISIT(VisitChooseExpr(ChooseExpr *element));
    // VISIT(VisitDesignatedInitExpr(DesignatedInitExpr *element));
    // VISIT(VisitCXXTypeidExpr(CXXTypeidExpr *element));
    // VISIT(VisitStmt(Stmt *element));

    //// from Analysis/Visitors/CFGRecStmtDeclVisitor.h
    // VISIT(VisitDeclRefExpr(DeclRefExpr *element)); // <- duplicate above
    // VISIT(VisitDeclStmt(DeclStmt *element));
    // VISIT(VisitDecl(Decl *element)); // <- throws assertion error
    // VISIT(VisitCXXRecordDecl(CXXRecordDecl *element));
    // VISIT(VisitChildren(Stmt *element));
    // VISIT(VisitStmt(Stmt *element)); // <- duplicate above
    // VISIT(VisitCompoundStmt(CompoundStmt *element));
    // VISIT(VisitConditionVariableInit(Stmt *element));

    void OutputRewritten(ASTContext &Context) {
      // output rewritten source code or ID count
      switch(Action){      
      case LISTER:
      case GET:
        break;
      default:
        const RewriteBuffer *RewriteBuf = 
          Rewrite.getRewriteBufferFor(Context.getSourceManager().getMainFileID());
        Out << "/* Start Crochet Output */\n";  
        Out << std::string(RewriteBuf->begin(), RewriteBuf->end());
        Out << "/* End Crochet Output */\n";  
      }
    }
    
  private:
    raw_ostream &Out;
    ACTION Action;
    bool firstStmt = true, modified=false;
    unsigned int Line, Column, Offset;
    StringRef Query;
    StringRef Value;
    FileID mainFileID;    
    std::map<std::string, std::string> typeMap = {{"VarDecl", "DeclStmt"}};
    std::string crochetComment = "/* Code modified by Crochet */\n";
    
  };
}


ASTConsumer *clang::CreateASTRemover(unsigned int Line, unsigned int Column, StringRef SearchQuery){
  return new ASTMutator(0, DELETE, Line, Column, -1, SearchQuery);
}

ASTConsumer *clang::CreateASTUpdater(unsigned int Line, unsigned int Column, StringRef SearchQuery, StringRef ReplaceQuery){
  return new ASTMutator(0, UPDATE, Line, Column, -1, SearchQuery, ReplaceQuery);
}


ASTConsumer *clang::CreateASTInserter(unsigned int Line, unsigned int Column, StringRef SearchQuery, StringRef InsertQuery, unsigned int Offset){
  return new ASTMutator(0, INSERT, Line, Column, Offset, SearchQuery, InsertQuery);
}


ASTConsumer *clang::CreateASTMover(unsigned int Line, unsigned int Column, StringRef SearchQuery, StringRef MoveQuery){
  return new ASTMutator(0, MOVE, Line, Column, -1, SearchQuery, MoveQuery);
}
