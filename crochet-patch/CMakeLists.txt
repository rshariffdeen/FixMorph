set(LLVM_LINK_COMPONENTS
  Support
  )

add_clang_library(crochetPatch
  lib/Tooling/ASTMutate.cpp

  LINK_LIBS
  clangAnalysis
  clangAST
  clangBasic
  clangDriver
  clangEdit
  clangFormat
  clangFrontend
  clangLex
  clangParse
  clangRewrite
  clangRewriteFrontend
  clangSerialization
  clangTooling
  clangToolingCore
  clangToolingRefactor


  )


include_directories(
  ${CMAKE_CURRENT_SOURCE_DIR}
  include
  )


add_subdirectory(tool)

