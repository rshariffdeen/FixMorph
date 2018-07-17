//===- ASTPatch.h - Structural patching based on ASTDiff ------*- C++ -*- -===//
//
//
//                     The LLVM Compiler Infrastructure
//
// This file is distributed under the University of Illinois Open Source
// License. See LICENSE.TXT for details.
//
//===----------------------------------------------------------------------===//

#ifndef LLVM_CLANG_TOOLING_ASTDIFF_ASTPATCH_H
#define LLVM_CLANG_TOOLING_ASTDIFF_ASTPATCH_H

#include "crochet/ASTDiff.h"
#include "clang/Tooling/Refactoring.h"
#include "llvm/Support/Error.h"

namespace clang {
namespace diff {

enum class patching_error {
  failed_to_build_AST,
  failed_to_apply_replacements,
  failed_to_overwrite_files,
};



class PatchingError : public llvm::ErrorInfo<PatchingError> {
public:
  PatchingError(patching_error Err) : Err(Err) {}
  std::string message() const override;
  void log(raw_ostream &OS) const override { OS << message() << "\n"; }
  patching_error get() const { return Err; }
  static char ID;

private:
  std::error_code convertToErrorCode() const override {
    return llvm::inconvertibleErrorCode();
  }
  patching_error Err;
};

llvm::Error patch(tooling::RefactoringTool &TargetTool, SyntaxTree &Src,
                  SyntaxTree &Dst, std::string ScriptFilePath, const ComparisonOptions &Options,
                  bool Debug = false);

} // end namespace diff
} // end namespace clang

#endif // LLVM_CLANG_TOOLING_ASTDIFF_ASTPATCH_H