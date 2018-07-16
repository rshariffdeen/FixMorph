set(LLVM_LINK_COMPONENTS
  ${LLVM_TARGETS_TO_BUILD}
  Option
  Support
  )

add_clang_executable(crochet-diff
  CrochetDiff.cpp
  )

target_link_libraries(crochet-diff
  PRIVATE
  clangAST
  clangBasic
  clangDriver
  clangFrontend
  clangRewrite
  clangRewriteFrontend
  clangStaticAnalyzerFrontend
  clangTooling
  clangToolingASTDiff
  clangToolingCore
  )

install(TARGETS crochet-diff
  RUNTIME DESTINATION bin)
