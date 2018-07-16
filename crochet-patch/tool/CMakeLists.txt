set(LLVM_LINK_COMPONENTS
  Support
  )

add_clang_tool(crochet-patch
  CrochetPatch.cpp
  )
target_link_libraries(crochet-patch
  PRIVATE
  crochetPatch
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

install(TARGETS crochet-patch
  RUNTIME DESTINATION bin)
