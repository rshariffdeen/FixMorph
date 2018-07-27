//===- ASTDiff.cpp - AST differencing implementation-----------*- C++ -*- -===//
//
//                     The LLVM Compiler Infrastructure
//
// This file is distributed under the University of Illinois Open Source
// License. See LICENSE.TXT for details.
//
//===----------------------------------------------------------------------===//
//
// This file contains definitons for the AST differencing interface.
//
//===----------------------------------------------------------------------===//

#include "crochet/ASTDiff.h"

#include "clang/AST/LexicallyOrderedRecursiveASTVisitor.h"
#include "clang/Lex/Lexer.h"
#include "llvm/ADT/PriorityQueue.h"
#include "llvm/Support/MD5.h"

#include <limits>
#include <memory>
#include <unordered_set>

using namespace llvm;
using namespace clang;

namespace clang {
namespace diff {

bool ComparisonOptions::isMatchingAllowed(NodeRef N1, NodeRef N2) const {
  return (N1.isMacro() && N2.isMacro()) || N1.getType().isSame(N2.getType());
}
void printChangeKind(raw_ostream &OS, ChangeKind Kind) {
  switch (Kind) {
  case NoChange:
    break;
  case Delete:
    OS << "Delete";
    break;
  case Update:
    OS << "Update";
    break;
  case Insert:
    OS << "Insert";
    break;
  case Move:
    OS << "Move";
    break;
  case UpdateMove:
    OS << "Update and Move";
    break;
  }
}

namespace {
struct NodeChange {
  ChangeKind Change = NoChange;
  int Shift = 0;
  NodeChange() = default;
  NodeChange(ChangeKind Change, int Shift) : Change(Change), Shift(Shift) {}
};
} // end anonymous namespace

class ASTDiff::Impl {
private:
  std::unique_ptr<NodeId[]> SrcToDst, DstToSrc;

public:
  SyntaxTree::Impl &T1, &T2;
  std::map<NodeId, NodeChange> ChangesT1, ChangesT2;

  Impl(SyntaxTree::Impl &T1, SyntaxTree::Impl &T2,
       const ComparisonOptions &Options);

  /// Matches nodes one-by-one based on their similarity.
  void computeMapping();

  // Compute Change for each node based on similarity.
  void computeChangeKinds();

  const Node *getMapped(NodeRef N) const;

  ChangeKind getNodeChange(NodeRef N) const;

  void dumpChanges(raw_ostream &OS, bool DumpMatches) const;

private:
  // Adds a mapping between two nodes.
  void link(NodeRef N1, NodeRef N2);

  // Returns the mapped node, or null.
  const Node *getDst(NodeRef N1) const;
  const Node *getSrc(NodeRef N2) const;

  // Returns true if the two subtrees are identical.
  bool identical(NodeRef N1, NodeRef N2) const;

  // Returns false if the nodes must not be mached.
  bool isMatchingPossible(NodeRef N1, NodeRef N2) const;

  // Returns true if the nodes' parents are matched.
  bool haveSameParents(NodeRef N1, NodeRef N2) const;

  // Uses an optimal albeit slow algorithm to compute a mapping between two
  // subtrees, but only if both have fewer nodes than MaxSize.
  void addOptimalMapping(NodeRef N1, NodeRef N2);

  // Computes the ratio of common descendants between the two nodes.
  // Descendants are only considered to be equal when they are mapped.
  double getJaccardSimilarity(NodeRef N1, NodeRef N2) const;

  double getNodeSimilarity(NodeRef N1, NodeRef N2) const;

  // Returns the node that has the highest degree of similarity.
  const Node *findCandidate(NodeRef N1) const;

  const Node *findCandidateFromChildren(NodeRef N1, NodeRef P2) const;

  // Returns a mapping of identical subtrees.
  void matchTopDown();

  // Tries to match any yet unmapped nodes, in a bottom-up fashion.
  void matchBottomUp();

  // Matches nodes, whose parents are matched.
  void matchChildren();

  int findNewPosition(NodeRef N) const;

  const ComparisonOptions &Options;

  friend class ZhangShashaMatcher;
};

namespace {
struct NodeList {
  SyntaxTree::Impl &Tree;
  std::vector<NodeId> Ids;
  NodeList(SyntaxTree::Impl &Tree) : Tree(Tree) {}
  void push_back(NodeId Id) { Ids.push_back(Id); }
  NodeRefIterator begin() const { return {&Tree, &*Ids.begin()}; }
  NodeRefIterator end() const { return {&Tree, &*Ids.end()}; }
  NodeRef operator[](size_t Index) { return *(begin() + Index); }
  size_t size() { return Ids.size(); }
  void sort() { std::sort(Ids.begin(), Ids.end()); }
};
} // end anonymous namespace

using HashType = std::array<uint8_t, 16>;

/// Represents the AST of a TranslationUnit.
class SyntaxTree::Impl {
public:
  Impl(SyntaxTree *Parent, ASTUnit &AST);
  /// Constructs a tree from an AST node.
  Impl(SyntaxTree *Parent, Decl *N, ASTUnit &AST);
  Impl(SyntaxTree *Parent, Stmt *N, ASTUnit &AST);
  template <class T>
  Impl(SyntaxTree *Parent,
       typename std::enable_if<std::is_base_of<Stmt, T>::value, T>::type *Node,
       ASTUnit &AST)
      : Impl(Parent, dyn_cast<Stmt>(Node), AST) {}
  template <class T>
  Impl(SyntaxTree *Parent,
       typename std::enable_if<std::is_base_of<Decl, T>::value, T>::type *Node,
       ASTUnit &AST)
      : Impl(Parent, dyn_cast<Decl>(Node), AST) {}

  SyntaxTree *Parent;
  ASTUnit &AST;
  PrintingPolicy TypePP;
  /// Nodes in preorder.
  std::vector<Node> Nodes;
  NodeList Leaves;
  std::vector<int> PreorderToPostorderId;
  NodeList NodesBfs;
  NodeList NodesPostorder;
  std::map<NodeId, SourceRange> TemplateArgumentLocations;

  int getSize() const { return Nodes.size(); }
  NodeRef getRoot() const { return getNode(getRootId()); }
  NodeId getRootId() const { return 0; }
  PreorderIterator begin() const { return &getRoot(); }
  PreorderIterator end() const { return begin() + getSize(); }
  PostorderIterator postorder_begin() const { return NodesPostorder.begin(); }
  PostorderIterator postorder_end() const { return NodesPostorder.end(); }
  llvm::iterator_range<PostorderIterator> postorder() const {
    return {postorder_begin(), postorder_end()};
  }

  NodeRef getNode(NodeId Id) const { return Nodes[Id]; }
  Node &getMutableNode(NodeRef N) { return Nodes[N.getId()]; }
  Node &getMutableNode(NodeId Id) { return getMutableNode(getNode(Id)); }

private:
  void initTree();
  void setLeftMostDescendants();
};

NodeRef NodeRefIterator::operator*() const { return Tree->getNode(*IdPointer); }

NodeRefIterator &NodeRefIterator::operator++() { return ++IdPointer, *this; }
NodeRefIterator &NodeRefIterator::operator+(int Offset) {
  return IdPointer += Offset, *this;
}
NodeRefIterator::difference_type NodeRefIterator::
operator-(const NodeRefIterator &Other) const {
  assert(Tree == Other.Tree &&
         "Cannot subtract two iterators of different trees.");
  return IdPointer - Other.IdPointer;
}

bool NodeRefIterator::operator!=(const NodeRefIterator &Other) const {
  assert(Tree == Other.Tree &&
         "Cannot compare two iterators of different trees.");
  return IdPointer != Other.IdPointer;
}

bool NodeRefIterator::operator==(const NodeRefIterator &Other) const {
  return !(*this != Other);
}

static bool isSpecializedNodeExcluded(const Decl *D) { return D->isImplicit(); }
static bool isSpecializedNodeExcluded(const Stmt *S) { return false; }
static bool isSpecializedNodeExcluded(CXXCtorInitializer *I) {
  return !I->isWritten();
}
static bool isSpecializedNodeExcluded(const TemplateArgumentLoc *S) {
  return false;
}
static bool isNodeExcluded(ASTUnit &AST, QualType QT) { return false; }

static bool isNodeExcluded(ASTUnit &AST, TemplateName *Template) {
  return false;
}

template <class T> static bool isNodeExcluded(ASTUnit &AST, T *N) {
  const SourceManager &SM = AST.getSourceManager();
  if (!N)
    return true;
  SourceLocation SLoc = N->getSourceRange().getBegin();
  if (SLoc.isValid()) {
    if (SM.isInSystemHeader(SLoc))
      return true;
    const Preprocessor &PP = AST.getPreprocessor();
    if (SLoc.isMacroID() && !PP.isAtStartOfMacroExpansion(SLoc))
      return true;
  }
  return isSpecializedNodeExcluded(N);
}

namespace {
// Sets Height, Parent and Children for each node.
struct PreorderVisitor
    : public LexicallyOrderedRecursiveASTVisitor<PreorderVisitor> {
  using BaseType = LexicallyOrderedRecursiveASTVisitor<PreorderVisitor>;

  int Id = 0, Depth = 0;
  NodeId Parent;
  SyntaxTree::Impl &Tree;

  PreorderVisitor(SyntaxTree::Impl &Tree)
      : BaseType(Tree.AST.getSourceManager()), Tree(Tree) {}

  template <class T> std::tuple<NodeId, NodeId> PreTraverse(const T &ASTNode) {
    NodeId MyId = Id;
    Tree.Nodes.emplace_back(Tree);
    Node &N = Tree.getMutableNode(MyId);
    N.Parent = Parent;
    N.Depth = Depth;
    N.ASTNode = DynTypedNode::create(ASTNode);
    assert(!N.ASTNode.getNodeKind().isNone() &&
           "Expected nodes to have a valid kind.");
    if (Parent.isValid()) {
      Node &P = Tree.getMutableNode(Parent);
      P.Children.push_back(MyId);
    }
    Parent = MyId;
    ++Id;
    ++Depth;
    return std::make_tuple(MyId, Tree.getNode(MyId).Parent);
  }
  void PostTraverse(std::tuple<NodeId, NodeId> State) {
    NodeId MyId, PreviousParent;
    std::tie(MyId, PreviousParent) = State;
    assert(MyId.isValid() && "Expecting to only traverse valid nodes.");
    Parent = PreviousParent;
    --Depth;
    Node &N = Tree.getMutableNode(MyId);
    N.RightMostDescendant = Id - 1;
    assert(N.RightMostDescendant >= Tree.getRootId() &&
           N.RightMostDescendant < Tree.getSize() &&
           "Rightmost descendant must be a valid tree node.");
    if (N.isLeaf())
      Tree.Leaves.push_back(MyId);
    N.Height = 1;
    for (NodeId Child : N.Children)
      N.Height = std::max(N.Height, 1 + Tree.getNode(Child).Height);
  }
  bool TraverseDecl(Decl *D) {
    if (isNodeExcluded(Tree.AST, D))
      return true;
    auto SavedState = PreTraverse(*D);
    BaseType::TraverseDecl(D);
    PostTraverse(SavedState);
    return true;
  }
  bool TraverseStmt(Stmt *S) {
    if (S)
      S = S->IgnoreImplicit();
    if (isNodeExcluded(Tree.AST, S))
      return true;
    auto SavedState = PreTraverse(*S);
    BaseType::TraverseStmt(S);
    PostTraverse(SavedState);
    return true;
  }
  bool TraverseTypeLoc(TypeLoc TL) {
    auto SavedState = PreTraverse(TL);
    BaseType::TraverseTypeLoc(TL);
    PostTraverse(SavedState);
    return true;
  }
  bool TraverseType(QualType QT) {
    if (isNodeExcluded(Tree.AST, QT))
      return true;
    auto SavedState = PreTraverse(QT);
    BaseType::TraverseType(QT);
    PostTraverse(SavedState);
    return true;
  }
  bool TraverseConstructorInitializer(CXXCtorInitializer *Init) {
    if (isNodeExcluded(Tree.AST, Init))
      return true;
    auto SavedState = PreTraverse(*Init);
    BaseType::TraverseConstructorInitializer(Init);
    PostTraverse(SavedState);
    return true;
  }
  bool TraverseTemplateArgumentLoc(const TemplateArgumentLoc &ArgLoc) {
    if (isNodeExcluded(Tree.AST, &ArgLoc))
      return true;
    Tree.TemplateArgumentLocations.emplace(Id, ArgLoc.getSourceRange());
    auto SavedState = PreTraverse(ArgLoc.getArgument());
    BaseType::TraverseTemplateArgumentLoc(ArgLoc);
    PostTraverse(SavedState);
    return true;
  }
  bool TraverseTemplateName(TemplateName Template) {
    if (isNodeExcluded(Tree.AST, &Template))
      return true;
    auto SavedState = PreTraverse(Template);
    BaseType::TraverseTemplateName(Template);
    PostTraverse(SavedState);
    return true;
  }
};
} // end anonymous namespace

SyntaxTree::Impl::Impl(SyntaxTree *Parent, ASTUnit &AST)
    : Parent(Parent), AST(AST), TypePP(AST.getLangOpts()), Leaves(*this),
      NodesBfs(*this), NodesPostorder(*this) {
  TypePP.AnonymousTagLocations = false;
}

SyntaxTree::Impl::Impl(SyntaxTree *Parent, Decl *N, ASTUnit &AST)
    : Impl(Parent, AST) {
  PreorderVisitor PreorderWalker(*this);
  PreorderWalker.TraverseDecl(N);
  initTree();
}

SyntaxTree::Impl::Impl(SyntaxTree *Parent, Stmt *N, ASTUnit &AST)
    : Impl(Parent, AST) {
  PreorderVisitor PreorderWalker(*this);
  PreorderWalker.TraverseStmt(N);
  initTree();
}

static void getSubtreePostorder(NodeList &Ids, NodeRef Root) {
  std::function<void(NodeRef)> Traverse = [&](NodeRef N) {
    for (NodeRef Child : N)
      Traverse(Child);
    Ids.push_back(N.getId());
  };
  Traverse(Root);
}

static void getSubtreeBfs(NodeList &Ids, NodeRef Root) {
  size_t Expanded = 0;
  Ids.push_back(Root.getId());
  while (Expanded < Ids.size())
    for (NodeRef Child : Ids[Expanded++])
      Ids.push_back(Child.getId());
}

void SyntaxTree::Impl::initTree() {
  setLeftMostDescendants();
  int PostorderId = 0;
  PreorderToPostorderId.resize(getSize());
  std::function<void(NodeRef)> PostorderTraverse = [&](NodeRef N) {
    for (NodeRef Child : N)
      PostorderTraverse(Child);
    PreorderToPostorderId[N.getId()] = PostorderId;
    ++PostorderId;
  };
  PostorderTraverse(getRoot());
  getSubtreeBfs(NodesBfs, getRoot());
  getSubtreePostorder(NodesPostorder, getRoot());
}

void SyntaxTree::Impl::setLeftMostDescendants() {
  for (NodeRef Leaf : Leaves) {
    getMutableNode(Leaf).LeftMostDescendant = Leaf.getId();
    const Node *Parent, *Cur = &Leaf;
    while ((Parent = Cur->getParent()) && &Parent->getChild(0) == Cur) {
      Cur = Parent;
      getMutableNode(*Cur).LeftMostDescendant = Leaf.getId();
    }
  }
}

static int getNumberOfDescendants(NodeRef N) {
  return N.RightMostDescendant - N.getId() + 1;
}

static bool isInSubtree(NodeRef N, NodeRef SubtreeRoot) {
  return N.getId() >= SubtreeRoot.getId() &&
         N.getId() <= SubtreeRoot.RightMostDescendant;
}

static HashType hashNode(NodeRef N) {
  llvm::MD5 Hash;
  SourceManager &SM = N.getTree().getSourceManager();
  const LangOptions &LangOpts = N.getTree().getLangOpts();
  Token Tok;
  for (auto TokenLocation : N.getOwnedTokens()) {
    bool Failure = Lexer::getRawToken(TokenLocation, Tok, SM, LangOpts,
                                      /*IgnoreWhiteSpace=*/true);
    assert(!Failure);
    auto Range = CharSourceRange::getCharRange(TokenLocation, Tok.getEndLoc());
    // This is here to make CompoundStmt nodes compare equal, to make the tests
    // pass. It should be changed to include changes to comments.
    if (!Tok.isOneOf(tok::comment, tok::semi))
      Hash.update(Lexer::getSourceText(Range, SM, LangOpts));
  }
  llvm::MD5::MD5Result HashResult;
  Hash.final(HashResult);
  return HashResult;
}

static bool areNodesDifferent(NodeRef N1, NodeRef N2) {
  return hashNode(N1) != hashNode(N2);
}
/// Identifies a node in a subtree by its postorder offset, starting at 1.
struct SNodeId {
  int Id = 0;

  explicit SNodeId(int Id) : Id(Id) {}
  explicit SNodeId() = default;

  operator int() const { return Id; }
  SNodeId &operator++() { return ++Id, *this; }
  SNodeId &operator--() { return --Id, *this; }
  SNodeId operator+(int Other) const { return SNodeId(Id + Other); }
};

class Subtree {
private:
  /// The parent tree.
  SyntaxTree::Impl &Tree;
  NodeRef Root;
  /// Maps subtree nodes to their leftmost descendants wihin the subtree.
  std::vector<SNodeId> LeftMostDescendants;

public:
  std::vector<SNodeId> KeyRoots;

  Subtree(NodeRef Root) : Tree(Root.Tree), Root(Root) {
    int NumLeaves = setLeftMostDescendants();
    computeKeyRoots(NumLeaves);
  }
  int getSize() const { return getNumberOfDescendants(Root); }
  NodeId getIdInRoot(SNodeId Id) const {
    return Tree.NodesPostorder[getPostorderIdInRoot(Id)].getId();
  }
  NodeRef getNode(SNodeId Id) const { return Tree.getNode(getIdInRoot(Id)); }
  SNodeId getLeftMostDescendant(SNodeId Id) const {
    assert(Id > 0 && Id <= getSize() && "Invalid subtree node index.");
    return LeftMostDescendants[Id - 1];
  }
  NodeId getPostorderIdInRoot(SNodeId Id = SNodeId(1)) const {
    assert(Id > 0 && Id <= getSize() && "Invalid subtree node index.");
    return Id - 1 + Tree.PreorderToPostorderId[Root.LeftMostDescendant];
  }

private:
  /// Returns the number of leafs in the subtree.
  int setLeftMostDescendants() {
    int NumLeaves = 0;
    LeftMostDescendants.resize(getSize());
    for (int I = 0; I < getSize(); ++I) {
      SNodeId SI(I + 1);
      NodeRef N = getNode(SI);
      NumLeaves += N.isLeaf();
      assert(I == Tree.PreorderToPostorderId[getIdInRoot(SI)] -
                      getPostorderIdInRoot() &&
             "Postorder traversal in subtree should correspond to traversal in "
             "the root tree by a constant offset.");
      LeftMostDescendants[I] =
          SNodeId(Tree.PreorderToPostorderId[N.LeftMostDescendant] -
                  getPostorderIdInRoot());
    }
    return NumLeaves;
  }
  void computeKeyRoots(int Leaves) {
    KeyRoots.resize(Leaves);
    std::unordered_set<int> Visited;
    int K = Leaves - 1;
    for (SNodeId I(getSize()); I > 0; --I) {
      SNodeId LeftDesc = getLeftMostDescendant(I);
      if (Visited.count(LeftDesc))
        continue;
      assert(K >= 0 && "K should be non-negative");
      KeyRoots[K] = I;
      Visited.insert(LeftDesc);
      --K;
    }
  }
};

/// Implementation of Zhang and Shasha's Algorithm for tree edit distance.
/// Computes an optimal mapping between two trees using only insertion,
/// deletion and update as edit actions (similar to the Levenshtein distance).
class ZhangShashaMatcher {
  const ASTDiff::Impl &DiffImpl;
  Subtree S1, S2;
  std::unique_ptr<std::unique_ptr<double[]>[]> TreeDist, ForestDist;

public:
  ZhangShashaMatcher(const ASTDiff::Impl &DiffImpl, NodeRef N1, NodeRef N2)
      : DiffImpl(DiffImpl), S1(N1), S2(N2) {
    TreeDist = llvm::make_unique<std::unique_ptr<double[]>[]>(
        size_t(S1.getSize()) + 1);
    ForestDist = llvm::make_unique<std::unique_ptr<double[]>[]>(
        size_t(S1.getSize()) + 1);
    for (int I = 0, E = S1.getSize() + 1; I < E; ++I) {
      TreeDist[I] = llvm::make_unique<double[]>(size_t(S2.getSize()) + 1);
      ForestDist[I] = llvm::make_unique<double[]>(size_t(S2.getSize()) + 1);
    }
  }

  std::vector<std::pair<NodeId, NodeId>> getMatchingNodes() {
    std::vector<std::pair<NodeId, NodeId>> Matches;
    std::vector<std::pair<SNodeId, SNodeId>> TreePairs;

    computeTreeDist();

    bool RootNodePair = true;

    TreePairs.emplace_back(SNodeId(S1.getSize()), SNodeId(S2.getSize()));

    while (!TreePairs.empty()) {
      SNodeId LastRow, LastCol, FirstRow, FirstCol, Row, Col;
      std::tie(LastRow, LastCol) = TreePairs.back();
      TreePairs.pop_back();

      if (!RootNodePair) {
        computeForestDist(LastRow, LastCol);
      }

      RootNodePair = false;

      FirstRow = S1.getLeftMostDescendant(LastRow);
      FirstCol = S2.getLeftMostDescendant(LastCol);

      Row = LastRow;
      Col = LastCol;

      while (Row > FirstRow || Col > FirstCol) {
        if (Row > FirstRow &&
            ForestDist[Row - 1][Col] + 1 == ForestDist[Row][Col]) {
          --Row;
        } else if (Col > FirstCol &&
                   ForestDist[Row][Col - 1] + 1 == ForestDist[Row][Col]) {
          --Col;
        } else {
          SNodeId LMD1 = S1.getLeftMostDescendant(Row);
          SNodeId LMD2 = S2.getLeftMostDescendant(Col);
          if (LMD1 == S1.getLeftMostDescendant(LastRow) &&
              LMD2 == S2.getLeftMostDescendant(LastCol)) {
            NodeRef N1 = S1.getNode(Row);
            NodeRef N2 = S2.getNode(Col);
            assert(DiffImpl.isMatchingPossible(N1, N2) &&
                   "These nodes must not be matched.");
            Matches.emplace_back(N1.getId(), N2.getId());
            --Row;
            --Col;
          } else {
            TreePairs.emplace_back(Row, Col);
            Row = LMD1;
            Col = LMD2;
          }
        }
      }
    }
    return Matches;
  }

private:
  /// We use a simple cost model for edit actions, which seems good enough.
  /// Simple cost model for edit actions. This seems to make the matching
  /// algorithm perform reasonably well.
  /// The values range between 0 and 1, or infinity if this edit action should
  /// always be avoided.
  static constexpr double DeletionCost = 1;
  static constexpr double InsertionCost = 1;

  double getUpdateCost(SNodeId Id1, SNodeId Id2) {
    NodeRef N1 = S1.getNode(Id1), N2 = S2.getNode(Id2);
    if (!DiffImpl.isMatchingPossible(N1, N2))
      return std::numeric_limits<double>::max();
    return areNodesDifferent(S1.getNode(Id1), S2.getNode(Id2));
  }

  void computeTreeDist() {
    for (SNodeId Id1 : S1.KeyRoots)
      for (SNodeId Id2 : S2.KeyRoots)
        computeForestDist(Id1, Id2);
  }

  void computeForestDist(SNodeId Id1, SNodeId Id2) {
    assert(Id1 > 0 && Id2 > 0 && "Expecting offsets greater than 0.");
    SNodeId LMD1 = S1.getLeftMostDescendant(Id1);
    SNodeId LMD2 = S2.getLeftMostDescendant(Id2);

    ForestDist[LMD1][LMD2] = 0;
    for (SNodeId D1 = LMD1 + 1; D1 <= Id1; ++D1) {
      ForestDist[D1][LMD2] = ForestDist[D1 - 1][LMD2] + DeletionCost;
      for (SNodeId D2 = LMD2 + 1; D2 <= Id2; ++D2) {
        ForestDist[LMD1][D2] = ForestDist[LMD1][D2 - 1] + InsertionCost;
        SNodeId DLMD1 = S1.getLeftMostDescendant(D1);
        SNodeId DLMD2 = S2.getLeftMostDescendant(D2);
        if (DLMD1 == LMD1 && DLMD2 == LMD2) {
          double UpdateCost = getUpdateCost(D1, D2);
          ForestDist[D1][D2] =
              std::min({ForestDist[D1 - 1][D2] + DeletionCost,
                        ForestDist[D1][D2 - 1] + InsertionCost,
                        ForestDist[D1 - 1][D2 - 1] + UpdateCost});
          TreeDist[D1][D2] = ForestDist[D1][D2];
        } else {
          ForestDist[D1][D2] =
              std::min({ForestDist[D1 - 1][D2] + DeletionCost,
                        ForestDist[D1][D2 - 1] + InsertionCost,
                        ForestDist[DLMD1][DLMD2] + TreeDist[D1][D2]});
        }
      }
    }
  }
};

NodeId Node::getId() const { return this - &Tree.getRoot(); }
SyntaxTree &Node::getTree() const { return *Tree.Parent; }
const Node *Node::getParent() const {
  if (Parent.isInvalid())
    return nullptr;
  return &Tree.getNode(Parent);
}

NodeRef Node::getChild(size_t Index) const {
  return Tree.getNode(Children[Index]);
}

ast_type_traits::ASTNodeKind Node::getType() const {
  return ASTNode.getNodeKind();
}

StringRef Node::getTypeLabel() const {
  if (isMacro())
    return "Macro";
  return getType().asStringRef();
}

bool Node::isMacro() const {
  return ASTNode.getSourceRange().getBegin().isMacroID();
}

llvm::Optional<std::string> Node::getQualifiedIdentifier() const {
  if (isMacro())
    return llvm::None;
  if (auto *ND = ASTNode.get<NamedDecl>()) {
    if (ND->getDeclName().isIdentifier())
      return ND->getQualifiedNameAsString();
    else
      return std::string();
  }
  return llvm::None;
}

llvm::Optional<StringRef> Node::getIdentifier() const {
  if (isMacro())
    return llvm::None;
  if (auto *ND = ASTNode.get<NamedDecl>()) {
    if (ND->getDeclName().isIdentifier())
      return ND->getName();
    else
      return StringRef();
  }
  return llvm::None;
}

static std::string getInitializerValue(const CXXCtorInitializer *Init, const PrintingPolicy &TypePP) {
  if (Init->isAnyMemberInitializer())
    return Init->getAnyMember()->getName();
  if (Init->isBaseInitializer())
    return QualType(Init->getBaseClass(), 0).getAsString(TypePP);
  if (Init->isDelegatingInitializer())
    return Init->getTypeSourceInfo()->getType().getAsString(TypePP);
  llvm_unreachable("Unknown initializer type");
}

// Returns the qualified name of ND. If it is subordinate to Context,
// then the prefix of the latter is removed from the returned value.
std::string Node::getRelativeName(const NamedDecl *ND, const DeclContext *Context) const {
  std::string Val = ND->getQualifiedNameAsString();
  std::string ContextPrefix; 
  if (!Context)
    return Val;
  if (auto *Namespace = dyn_cast<NamespaceDecl>(Context))
    ContextPrefix = Namespace->getQualifiedNameAsString();
  else if (auto *Record = dyn_cast<RecordDecl>(Context))
    ContextPrefix = Record->getQualifiedNameAsString();
  else if (Tree.AST.getLangOpts().CPlusPlus11)
    if (auto *Tag = dyn_cast<TagDecl>(Context))
      ContextPrefix = Tag->getQualifiedNameAsString();
  // Strip the qualifier, if Val refers to something in the current scope.
  // But leave one leading ':' in place, so that we know that this is a
  // relative path.
  if (!ContextPrefix.empty() && StringRef(Val).startswith(ContextPrefix))
    Val = Val.substr(ContextPrefix.size() + 1);
  return Val;
}

std::string Node::getRelativeName(const NamedDecl *ND) const {
  return getRelativeName(ND, ND->getDeclContext());
}

std::string Node::getFileName() const {

  const SourceManager &SM = Tree.AST.getSourceManager();
  CharSourceRange Range = getSourceRange();
  SourceLocation EndLoc = Range.getEnd(); 
  if (EndLoc.isValid()){
    FileID fileID = SM.getFileID(EndLoc);
    if (fileID.isValid()){
      const FileEntry *fileEntry = SM.getFileEntryForID(fileID);
      if (fileEntry->isValid())
        return fileEntry->getName();
    }
  }
  
  return "";

}

std::string Node::getValue() const {

  if (isMacro())
    return getMacroValue();
  if (auto *S = ASTNode.get<Stmt>())
    return getStmtValue(S);
  if (auto *D = ASTNode.get<Decl>())
    return getDeclValue(D);
  if (auto *Init = ASTNode.get<CXXCtorInitializer>())
    return getInitializerValue(Init, Tree.TypePP);

  return "";

  llvm_unreachable("Fatal: unhandled AST node: \n" );

}

std::string Node::getRefType() const {
  std::string refType;

  if (getTypeLabel() == "DeclRefExpr"){
    auto decRefNode = ASTNode.get<DeclRefExpr>();
    auto decNode = decRefNode->getDecl();
    if (auto *ref = dyn_cast<ParmVarDecl>(decNode))    
      refType =  "ParmVarDecl";
    if (auto *ref = dyn_cast<VarDecl>(decNode))    
      refType = "VarDecl";
    if (auto *ref = dyn_cast<FunctionDecl>(decNode))    
      refType = "FunctionDecl";
  }
  return refType;

}

std::string Node::getMacroValue() const {
  return Lexer::getSourceText(getSourceRange(), Tree.AST.getSourceManager(),
                                Tree.AST.getLangOpts());
  
}

std::string Node::getDeclValue(const Decl *D) const {
  std::string Value;
  if (auto *V = dyn_cast<ValueDecl>(D))
    return getRelativeName(V) + "(" + V->getType().getAsString(Tree.TypePP) + ")";
  if (auto *N = dyn_cast<NamedDecl>(D))
    Value += getRelativeName(N) + ";";
  if (auto *T = dyn_cast<TypedefNameDecl>(D))
    return Value + T->getUnderlyingType().getAsString(Tree.TypePP) + ";";
  if (auto *T = dyn_cast<TypeDecl>(D))
    if (T->getTypeForDecl())
      Value +=
          T->getTypeForDecl()->getCanonicalTypeInternal().getAsString(Tree.TypePP) +
          ";";
  if (auto *U = dyn_cast<UsingDirectiveDecl>(D))
    return U->getNominatedNamespace()->getName();
  if (auto *A = dyn_cast<AccessSpecDecl>(D)) {
    CharSourceRange Range(A->getSourceRange(), false);
    return Lexer::getSourceText(Range, Tree.AST.getSourceManager(),
                                Tree.AST.getLangOpts());
  }
  return Value;
}


const DeclContext *Node::getEnclosingDeclContext(ASTContext &AST, const Stmt *S) const {
  while (S) {
    const auto &Parents = AST.getParents(*S);
    if (Parents.empty())
      return nullptr;
    const auto &P = Parents[0];
    if (const auto *D = P.get<Decl>())
      return D->getDeclContext();
    S = P.get<Stmt>();
  }
  return nullptr;
}

std::string Node::getStmtValue(const Stmt *S) const {
  if (auto *U = dyn_cast<UnaryOperator>(S))
    return UnaryOperator::getOpcodeStr(U->getOpcode());
  if (auto *B = dyn_cast<BinaryOperator>(S))
    return B->getOpcodeStr();
  if (auto *M = dyn_cast<MemberExpr>(S))
    return getRelativeName(M->getMemberDecl());
  if (auto *I = dyn_cast<IntegerLiteral>(S)) {
    SmallString<256> Str;
    I->getValue().toString(Str, /*Radix=*/10, /*Signed=*/false);
    return Str.str();
  }
  if (auto *F = dyn_cast<FloatingLiteral>(S)) {
    SmallString<256> Str;
    F->getValue().toString(Str);
    return Str.str();
  }
  if (auto *D = dyn_cast<DeclRefExpr>(S))
    return getRelativeName(D->getDecl(), getEnclosingDeclContext(Tree.AST.getASTContext(), S));
  if (auto *String = dyn_cast<StringLiteral>(S))
    return String->getString();
  if (auto *B = dyn_cast<CXXBoolLiteralExpr>(S))
    return B->getValue() ? "true" : "false";
  return "";
}


NodeRefIterator Node::begin() const {
  return {&Tree, isLeaf() ? nullptr : &Children[0]};
}
NodeRefIterator Node::end() const {
  return {&Tree, isLeaf() ? nullptr : &Children[0] + Children.size()};
}

int Node::findPositionInParent() const {
  if (!getParent())
    return 0;
  const ArrayRef<NodeId> &Siblings = getParent()->Children;
  return std::find(Siblings.begin(), Siblings.end(), getId()) -
         Siblings.begin();
}

static SourceRange getSourceRangeImpl(NodeRef N) {
  const DynTypedNode &DTN = N.ASTNode;
  SyntaxTree::Impl &Tree = N.Tree;
  SourceManager &SM = Tree.AST.getSourceManager();
  const LangOptions &LangOpts = Tree.AST.getLangOpts();
  auto EndOfToken = [&](SourceLocation Loc) {
    return Lexer::getLocForEndOfToken(Loc, /*Offset=*/0, SM, LangOpts);
  };
  auto TokenToCharRange = [&](SourceRange Range) -> SourceRange {
    return {Range.getBegin(), EndOfToken(Range.getEnd())};
  };
  SourceRange Range = DTN.getSourceRange();
  // if (N.isMacro()) {
  //   SourceLocation BeginLoc = Range.getBegin();
  //   SourceLocation End = SM.getExpansionRange(BeginLoc).second;
  //   End = EndOfToken(End);
  //   return {SM.getExpansionLoc(BeginLoc), SM.getExpansionLoc(End)};
  // }
  if (auto *ThisExpr = DTN.get<CXXThisExpr>())
    if (ThisExpr->isImplicit())
      return {Range.getBegin(), Range.getBegin()};
  if (auto *CE = DTN.get<CXXConstructExpr>()) {
    if (!isa<CXXTemporaryObjectExpr>(CE))
      return CE->getParenOrBraceRange();
  } else if (DTN.get<ParmVarDecl>()) {
    return TokenToCharRange(Range);
  } else if (DTN.get<DeclStmt>() || DTN.get<FieldDecl>() ||
             DTN.get<VarDecl>() ||
             (DTN.get<CallExpr>() &&
              N.getParent()->ASTNode.get<CompoundStmt>()) ||
             (DTN.get<FunctionDecl>() &&
              !DTN.get<FunctionDecl>()->isThisDeclarationADefinition()) ||
             DTN.get<TypeDecl>() || DTN.get<UsingDirectiveDecl>() ||
             DTN.get<ClassTemplateDecl>()) {
    SourceLocation End = Range.getEnd();
    if (DTN.get<DeclStmt>())
      End = End.getLocWithOffset(-1);
    SourceLocation SemicolonLoc = Lexer::findLocationAfterToken(
        End, tok::semi, SM, LangOpts,
        /*SkipTrailingWhitespaceAndNewLine=*/false);
    Range.setEnd(SemicolonLoc);
    return Range;
  }
  return TokenToCharRange(Range);
}

CharSourceRange Node::getSourceRange() const {
  return CharSourceRange::getCharRange(getSourceRangeImpl(*this));
}

std::pair<unsigned, unsigned> Node::getSourceRangeOffsets() const {
  const SourceManager &SM = Tree.AST.getSourceManager();
  CharSourceRange Range = getSourceRange();
  unsigned Begin = SM.getFileOffset(Range.getBegin());
  unsigned End = SM.getFileOffset(Range.getEnd());
  return {Begin, End};
}

std::pair<unsigned, unsigned> Node::getSourceBeginLocation() const {
  const SourceManager &SM = Tree.AST.getSourceManager();
  CharSourceRange Range = getSourceRange();  
  SourceLocation BeginLoc = Range.getBegin();  
  PresumedLoc PLoc = SM.getPresumedLoc(BeginLoc); 
  if (PLoc.isInvalid())
    return {NULL, NULL};
  return {PLoc.getLine(), PLoc.getColumn()};
}

std::pair<unsigned, unsigned> Node::getSourceEndLocation() const {
  const SourceManager &SM = Tree.AST.getSourceManager();
  CharSourceRange Range = getSourceRange();
  SourceLocation EndLoc = Range.getEnd(); 
  PresumedLoc PLoc = SM.getPresumedLoc(EndLoc); 
  if (PLoc.isInvalid())
    return {NULL, NULL};
  return {PLoc.getLine(), PLoc.getColumn()};
}

static bool onlyWhitespace(StringRef Str) {
  return std::all_of(Str.begin(), Str.end(),
                     [](char C) { return std::isspace(C); });
}

SmallVector<CharSourceRange, 4> Node::getOwnedSourceRanges() const {
  SmallVector<CharSourceRange, 4> SourceRanges;
  SourceManager &SM = getTree().getSourceManager();
  const LangOptions &LangOpts = getTree().getLangOpts();
  CharSourceRange Range = getSourceRange();
  SourceLocation Offset = Range.getBegin();
  BeforeThanCompare<SourceLocation> Less(SM);
  auto AddSegment = [&](SourceLocation Until) {
    if (Offset.isValid() && Until.isValid() && Less(Offset, Until)) {
      CharSourceRange R = CharSourceRange::getCharRange({Offset, Until});
      StringRef Text = Lexer::getSourceText(R, SM, LangOpts);
      if (onlyWhitespace(Text))
        return;
      SourceRanges.emplace_back(CharSourceRange::getCharRange({Offset, Until}));
    }
  };
  int ChildIndex = 0;
  for (NodeRef Descendant : *this) {
    CharSourceRange DescendantRange = Descendant.getSourceRange();
    CharSourceRange LMDRange =
        getTree().getNode(Descendant.LeftMostDescendant).getSourceRange();
    CharSourceRange RMDRange =
        getTree().getNode(Descendant.RightMostDescendant).getSourceRange();
    auto MinValidBegin = [&Less](CharSourceRange &Range1,
                                 CharSourceRange &Range2) {
      SourceLocation Begin1 = Range1.getBegin(), Begin2 = Range2.getBegin();
      if (Begin1.isInvalid())
        return Begin2;
      if (Begin2.isInvalid())
        return Begin1;
      return std::min(Begin1, Begin2, Less);
    };
    auto MaxValidEnd = [&Less](CharSourceRange &Range1,
                               CharSourceRange &Range2) {
      SourceLocation End1 = Range1.getEnd(), End2 = Range2.getEnd();
      if (End1.isInvalid())
        return End2;
      if (End2.isInvalid())
        return End1;
      return std::max(End1, End2, Less);
    };
    auto Min = MinValidBegin(DescendantRange, LMDRange);
    auto Max = MaxValidEnd(DescendantRange, RMDRange);
    AddSegment(Min);
    if (Max.isValid())
      Offset = Max;
    ++ChildIndex;
  }
  AddSegment(Range.getEnd());
  return SourceRanges;
}

CharSourceRange Node::findRangeForDeletion() const {
  CharSourceRange Range = getSourceRange();
  if (!getParent())
    return Range;
  NodeRef Parent = *getParent();
  SyntaxTree &Tree = getTree();
  SourceManager &SM = Tree.getSourceManager();
  const LangOptions &LangOpts = Tree.getLangOpts();
  auto &DTN = ASTNode;
  auto &ParentDTN = Parent.ASTNode;
  size_t SiblingIndex = findPositionInParent();
  const auto &Siblings = Parent.Children;
  // Remove the comma if the location is within a comma-separated list of
  // at least size 2 (minus the callee for CallExpr).
  if ((ParentDTN.get<CallExpr>() && Siblings.size() > 2) ||
      (DTN.get<ParmVarDecl>() && Siblings.size() > 2)) {
    bool LastSibling = SiblingIndex == Siblings.size() - 1;
    SourceLocation CommaLoc;
    if (LastSibling) {
      CommaLoc = Parent.getChild(SiblingIndex - 1).getSourceRange().getEnd();
      Range.setBegin(CommaLoc);
    } else {
      Optional<Token> Comma =
          Lexer::findNextToken(Range.getEnd(), SM, LangOpts);
      if (Comma && Comma->is(tok::comma))
        Range.setEnd(Comma->getEndLoc());
    }
  }
  return Range;
}

void forEachTokenInRange(CharSourceRange Range, SyntaxTree &Tree,
                         std::function<void(Token &)> Body) {
  SourceLocation Begin = Range.getBegin(), End = Range.getEnd();
  SourceManager &SM = Tree.getSourceManager();
  BeforeThanCompare<SourceLocation> Less(SM);
  Token Tok;
  while (Begin.isValid() && Less(Begin, End) &&
         !Lexer::getRawToken(Begin, Tok, SM, Tree.getLangOpts(),
                             /*IgnoreWhiteSpace=*/true) &&
         Less(Tok.getLocation(), End)) {
    Body(Tok);
    Begin = Tok.getEndLoc();
  }
}

SmallVector<SourceLocation, 4> Node::getOwnedTokens() const {
  SmallVector<SourceLocation, 4> TokenLocations;
  BeforeThanCompare<SourceLocation> Less(getTree().getSourceManager());
  const auto &SourceRanges = getOwnedSourceRanges();
  for (auto &Range : SourceRanges) {
    forEachTokenInRange(Range, getTree(), [&TokenLocations](Token &Tok) {
      if (!isListSeparator(Tok))
        TokenLocations.push_back(Tok.getLocation());
    });
  }
  return TokenLocations;
}

namespace {
// Compares nodes by their depth.
struct HeightLess {
  SyntaxTree::Impl &Tree;
  HeightLess(SyntaxTree::Impl &Tree) : Tree(Tree) {}
  bool operator()(NodeId Id1, NodeId Id2) const {
    return Tree.getNode(Id1).Height < Tree.getNode(Id2).Height;
  }
};
} // end anonymous namespace

namespace {
// Priority queue for nodes, sorted descendingly by their height.
class PriorityList {
  SyntaxTree::Impl &Tree;
  HeightLess Cmp;
  std::vector<NodeId> Container;
  PriorityQueue<NodeId, std::vector<NodeId>, HeightLess> List;

public:
  PriorityList(SyntaxTree::Impl &Tree)
      : Tree(Tree), Cmp(Tree), List(Cmp, Container) {}

  void push(NodeId Id) { List.push(Id); }

  NodeList pop() {
    int Max = peekMax();
    NodeList Result(Tree);
    if (Max == 0)
      return Result;
    while (peekMax() == Max) {
      Result.push_back(List.top());
      List.pop();
    }
    // TODO this is here to get a stable output, not a good heuristic
    Result.sort();
    return Result;
  }
  int peekMax() const {
    if (List.empty())
      return 0;
    return Tree.getNode(List.top()).Height;
  }
  void open(NodeRef N) {
    for (NodeRef Child : N)
      push(Child.getId());
  }
};
} // end anonymous namespace

bool ASTDiff::Impl::identical(NodeRef N1, NodeRef N2) const {
  if (N1.getNumChildren() != N2.getNumChildren() ||
      !isMatchingPossible(N1, N2) || areNodesDifferent(N1, N2))
    return false;
  for (size_t Id = 0, E = N1.getNumChildren(); Id < E; ++Id)
    if (!identical(N1.getChild(Id), N2.getChild(Id)))
      return false;
  return true;
}

bool ASTDiff::Impl::isMatchingPossible(NodeRef N1, NodeRef N2) const {
  return Options.isMatchingAllowed(N1, N2);
}

bool ASTDiff::Impl::haveSameParents(NodeRef N1, NodeRef N2) const {
  const Node *P1 = N1.getParent();
  const Node *P2 = N2.getParent();
  return (!P1 && !P2) || (P1 && P2 && getDst(*P1) == P2);
}

void ASTDiff::Impl::addOptimalMapping(NodeRef N1, NodeRef N2) {
  if (std::max(getNumberOfDescendants(N1), getNumberOfDescendants(N2)) >
      Options.MaxSize)
    return;
  ZhangShashaMatcher Matcher(*this, N1, N2);
  std::vector<std::pair<NodeId, NodeId>> R = Matcher.getMatchingNodes();
  for (const auto Tuple : R) {
    NodeRef N1 = T1.getNode(Tuple.first);
    NodeRef N2 = T2.getNode(Tuple.second);
    if (!getDst(N1) && !getSrc(N2))
      link(N1, N2);
  }
}

double ASTDiff::Impl::getJaccardSimilarity(NodeRef N1, NodeRef N2) const {
  int CommonDescendants = 0;
  // Count the common descendants, excluding the subtree root.
  for (NodeId Src = N1.getId() + 1; Src <= N1.RightMostDescendant; ++Src) {
    const Node *Dst = getDst(T1.getNode(Src));
    if (Dst)
      CommonDescendants += isInSubtree(*Dst, N2);
  }
  // We need to subtract 1 to get the number of descendants excluding the
  // root.
  double Denominator = getNumberOfDescendants(N1) - 1 +
                       getNumberOfDescendants(N2) - 1 - CommonDescendants;
  // CommonDescendants is less than the size of one subtree.
  assert(Denominator >= 0 && "Expected non-negative denominator.");
  if (Denominator == 0)
    return 0;
  return CommonDescendants / Denominator;
}

double ASTDiff::Impl::getNodeSimilarity(NodeRef N1, NodeRef N2) const {
  auto Ident1 = N1.getIdentifier(), Ident2 = N2.getIdentifier();

  bool SameValue = !areNodesDifferent(N1, N2);
  auto SameIdent = Ident1 && Ident2 && *Ident1 == *Ident2;

  double NodeSimilarity = 0;
  NodeSimilarity += SameValue;
  NodeSimilarity += SameIdent;

  assert(haveSameParents(N1, N2));
  return NodeSimilarity * Options.MinSimilarity;
}

const Node *ASTDiff::Impl::findCandidate(NodeRef N1) const {
  const Node *Candidate = nullptr;
  double HighestSimilarity = 0.0;
  for (NodeRef N2 : T2) {
    if (!isMatchingPossible(N1, N2))
      continue;
    if (getSrc(N2))
      continue;
    double Similarity = getJaccardSimilarity(N1, N2);
    if (Similarity >= Options.MinSimilarity && Similarity > HighestSimilarity) {
      HighestSimilarity = Similarity;
      Candidate = &N2;
    }
  }
  return Candidate;
}

const Node *ASTDiff::Impl::findCandidateFromChildren(NodeRef N1,
                                                     NodeRef P2) const {
  const Node *Candidate = nullptr;
  double HighestSimilarity = 0.0;
  for (NodeRef N2 : P2) {
    if (!isMatchingPossible(N1, N2))
      continue;
    if (getSrc(N2))
      continue;
    double Similarity = getJaccardSimilarity(N1, N2);
    Similarity += getNodeSimilarity(N1, N2);
    if (Similarity >= Options.MinSimilarity && Similarity > HighestSimilarity) {
      HighestSimilarity = Similarity;
      Candidate = &N2;
    }
  }
  return Candidate;
}

void ASTDiff::Impl::matchBottomUp() {
  for (NodeRef N1 : T1.postorder()) {
    NodeId Id1 = N1.getId();
    if (Id1 == T1.getRootId() && !getDst(T1.getRoot()) &&
        !getSrc(T2.getRoot())) {
      if (isMatchingPossible(T1.getRoot(), T2.getRoot())) {
        link(T1.getRoot(), T2.getRoot());
        addOptimalMapping(T1.getRoot(), T2.getRoot());
      }
      break;
    }
    bool Matched = getDst(N1);
    bool MatchedChildren = false;
    for (NodeRef Child : N1) {
      if (getDst(Child)) {
        MatchedChildren = true;
        break;
      }
    }
    if (Matched || !MatchedChildren)
      continue;
    const Node *N2 = findCandidate(N1);
    if (N2) {
      link(N1, *N2);
      addOptimalMapping(N1, *N2);
    }
  }
}

void ASTDiff::Impl::matchChildren() {
  for (NodeRef N1 : T1) {
    if (getDst(N1))
      continue;
    if (!N1.getParent())
      continue;
    NodeRef P1 = *N1.getParent();
    if (!getDst(P1))
      continue;
    NodeRef P2 = *getDst(P1);
    const Node *N2 = findCandidateFromChildren(N1, P2);
    if (N2) {
      link(N1, *N2);
      addOptimalMapping(N1, *N2);
    }
  }
}

void ASTDiff::Impl::matchTopDown() {
  PriorityList L1(T1);
  PriorityList L2(T2);

  L1.push(T1.getRootId());
  L2.push(T2.getRootId());

  int Max1, Max2;
  while (std::min(Max1 = L1.peekMax(), Max2 = L2.peekMax()) >
         Options.MinHeight) {
    if (Max1 > Max2) {
      for (NodeRef N : L1.pop())
        L1.open(N);
      continue;
    }
    if (Max2 > Max1) {
      for (NodeRef N : L2.pop())
        L2.open(N);
      continue;
    }
    NodeList H1 = L1.pop();
    NodeList H2 = L2.pop();
    for (NodeRef N1 : H1) {
      for (NodeRef N2 : H2) {
        if (identical(N1, N2) && !getDst(N1) && !getSrc(N2)) {
          for (int I = 0, E = getNumberOfDescendants(N1); I < E; ++I) {
            link(T1.getNode(N1.getId() + I), T2.getNode(N2.getId() + I));
          }
        }
      }
    }
    for (NodeRef N1 : H1) {
      if (!getDst(N1))
        L1.open(N1);
    }
    for (NodeRef N2 : H2) {
      if (!getSrc(N2))
        L2.open(N2);
    }
  }
}

ASTDiff::Impl::Impl(SyntaxTree::Impl &T1, SyntaxTree::Impl &T2,
                    const ComparisonOptions &Options)
    : T1(T1), T2(T2), Options(Options) {
  int Size = T1.getSize() + T2.getSize();
  SrcToDst = llvm::make_unique<NodeId[]>(Size);
  DstToSrc = llvm::make_unique<NodeId[]>(Size);
  computeMapping();
  computeChangeKinds();
}

void ASTDiff::Impl::computeMapping() {
  matchTopDown();
  if (Options.StopAfterTopDown)
    return;
  matchBottomUp();
  if (Options.StopAfterBottomUp)
    return;
  matchChildren();
}

void ASTDiff::Impl::computeChangeKinds() {
  for (NodeRef N1 : T1) {
    if (!getDst(N1))
      ChangesT1.emplace(N1.getId(), NodeChange(Delete, -1));
  }
  for (NodeRef N2 : T2) {
    if (!getSrc(N2))
      ChangesT2.emplace(N2.getId(), NodeChange(Insert, -1));
  }
  for (NodeRef N1 : T1.NodesBfs) {
    if (!getDst(N1))
      continue;
    NodeRef N2 = *getDst(N1);
    if (!haveSameParents(N1, N2) ||
        findNewPosition(N1) != findNewPosition(N2)) {
      ChangesT1[N1.getId()].Shift -= 1;
      ChangesT2[N2.getId()].Shift -= 1;
    }
  }
  for (NodeRef N2 : T2.NodesBfs) {
    if (!getSrc(N2))
      continue;
    NodeRef N1 = *getSrc(N2);
    if (!haveSameParents(N1, N2) ||
        findNewPosition(N1) != findNewPosition(N2)) {
      ChangesT1[N1.getId()].Change = ChangesT2[N2.getId()].Change = Move;
    }
    if (areNodesDifferent(N1, N2)) {
      bool Moved = ChangesT1[N1.getId()].Change == Move;
      ChangesT1[N1.getId()].Change = ChangesT2[N2.getId()].Change =
          (Moved ? UpdateMove : Update);
    }
  }
}

const Node *ASTDiff::Impl::getMapped(NodeRef N) const {
  if (&N.Tree == &T1)
    return getDst(N);
  assert(&N.Tree == &T2 && "Invalid tree.");
  return getSrc(N);
}

void ASTDiff::Impl::link(NodeRef N1, NodeRef N2) {
  SrcToDst[N1.getId()] = N2.getId(), DstToSrc[N2.getId()] = N1.getId();
}

const Node *ASTDiff::Impl::getDst(NodeRef N1) const {
  assert(&N1.Tree == &T1 && "Invalid tree.");
  return SrcToDst[N1.getId()].isValid() ? &T2.getNode(SrcToDst[N1.getId()])
                                        : nullptr;
}
const Node *ASTDiff::Impl::getSrc(NodeRef N2) const {
  assert(&N2.Tree == &T2 && "Invalid tree.");
  return DstToSrc[N2.getId()].isValid() ? &T1.getNode(DstToSrc[N2.getId()])
                                        : nullptr;
}

int ASTDiff::Impl::findNewPosition(NodeRef N) const {
  const std::map<NodeId, NodeChange> *Changes;
  if (&N.Tree == &T1)
    Changes = &ChangesT1;
  else
    Changes = &ChangesT2;

  if (!N.getParent())
    return 0;
  int Position = N.findPositionInParent();
  for (NodeRef Sibling : *N.getParent()) {
    if (Changes->count(Sibling.getId()))
      Position += Changes->at(Sibling.getId()).Shift;
    if (&Sibling == &N)
      return Position;
  }
  llvm_unreachable("Node not found amongst parent's children.");
}

ChangeKind ASTDiff::Impl::getNodeChange(NodeRef N) const {
  const std::map<NodeId, NodeChange> *Changes;
  if (&N.Tree == &T1) {
    Changes = &ChangesT1;
  } else {
    assert(&N.Tree == &T2 && "Invalid tree.");
    Changes = &ChangesT2;
  }
  if (Changes->count(N.getId()))
    return Changes->at(N.getId()).Change;
  return NoChange;
}

ASTDiff::ASTDiff(SyntaxTree &T1, SyntaxTree &T2,
                 const ComparisonOptions &Options)
    : DiffImpl(llvm::make_unique<Impl>(*T1.TreeImpl, *T2.TreeImpl, Options)) {}

ASTDiff::~ASTDiff() = default;

const Node *ASTDiff::getMapped(NodeRef N) const {
  return DiffImpl->getMapped(N);
}

ChangeKind ASTDiff::getNodeChange(NodeRef N) const {
  return DiffImpl->getNodeChange(N);
}

static void dumpDstChange(raw_ostream &OS, const ASTDiff::Impl &Diff,
                          SyntaxTree::Impl &SrcTree, SyntaxTree::Impl &DstTree,
                          NodeRef Dst) {
  const Node *Src = Diff.getMapped(Dst);
  const Node *DstParent = Dst.getParent();
  ChangeKind Change = Diff.getNodeChange(Dst);
  printChangeKind(OS, Change);
  int offset;
  int numChildren;
  
  switch (Change) {
  case NoChange:
    break;
  case Delete:
    llvm_unreachable("The destination tree can't have deletions.");
  case Update:
    OS << " ";
    Src->dump(OS);
    OS << " to ";
    Dst.dump(OS);
    OS << "\n";
    break;
  case Insert:
    // offset = Dst.findPositionInParent();
        
    // // llvm::errs() << offset << "-" << numChildren << "\n";
    // OS << " ";
    // Dst.dump(OS);
    // OS << " into ";
    // if (!Dst.getParent())
    //   OS << "None";
    // else{
    //   if (Diff.getMapped(*DstParent) != NULL){
    //     Diff.getMapped(*DstParent)->dump(OS);
    //     OS << " at " << Src->findPositionInParent() << "\n";
    //     // numChildren = Diff.getMapped(*DstParent)->getNumChildren();
    //     // if ((offset + 1) != numChildren){
    //     //   OS << " before ";
    //     //   NodeRef nextChild = Dst.getParent()->getChild(offset + 1);
    //     //   if (Diff.getMapped(nextChild) != NULL){
    //     //     Diff.getMapped(nextChild)->dump(OS);
    //     //   } else {
    //     //     nextChild.dump(OS); 
    //     //   } 
    //     // }
    //     // if (offset  > 1){
    //     //   NodeRef prevChild = Dst.getParent()->getChild(offset - 1);
    //     //   OS << " after ";
    //     //   if (Diff.getMapped(prevChild) != NULL){
    //     //     Diff.getMapped(prevChild)->dump(OS);
    //     //   } else {
    //     //     prevChild.dump(OS); 
    //     //   } 
       
    //     // }

    //   }
    //   else 
    //     DstParent->dump(OS);
    //     OS << " at " << Dst.findPositionInParent() << "\n";
    // } 

    // OS << "\n";    
    // break;

  case Move:
  case UpdateMove:
    OS << " ";
    Dst.dump(OS);
    OS << " into ";
    if (!Dst.getParent())
      OS << "None";
    else
      Dst.getParent()->dump(OS);
    OS << " at " << Dst.findPositionInParent() << "\n";
    break;
  }
}

void ASTDiff::Impl::dumpChanges(raw_ostream &OS, bool DumpMatches) const {
  for (NodeRef N2 : T2) {
    const Node *N1 = getMapped(N2);
    if (DumpMatches && N1) {
      OS << "Match ";
      N1->dump(OS);
      OS << " to ";
      N2.dump(OS);
      OS << "\n";
    }
    dumpDstChange(OS, *this, T1, T2, N2);
  }
  for (NodeRef N1 : T1) {
    if (!getMapped(N1)) {
      OS << "Delete ";
      N1.dump(OS);
      OS << "\n";
    }
  }
}

void ASTDiff::dumpChanges(raw_ostream &OS, bool DumpMatches) const {
  DiffImpl->dumpChanges(OS, DumpMatches);
}

SyntaxTree::SyntaxTree(ASTUnit &AST)
    : TreeImpl(llvm::make_unique<SyntaxTree::Impl>(
          this, AST.getASTContext().getTranslationUnitDecl(), AST)) {}

SyntaxTree::~SyntaxTree() = default;

ASTUnit &SyntaxTree::getASTUnit() const { return TreeImpl->AST; }

SourceManager &SyntaxTree::getSourceManager() const {
  return TreeImpl->AST.getSourceManager();
}

const LangOptions &SyntaxTree::getLangOpts() const {
  return TreeImpl->AST.getLangOpts();
}

const ASTContext &SyntaxTree::getASTContext() const {
  return TreeImpl->AST.getASTContext();
}

NodeRef SyntaxTree::getNode(NodeId Id) const { return TreeImpl->getNode(Id); }

int SyntaxTree::getSize() const { return TreeImpl->getSize(); }
NodeRef SyntaxTree::getRoot() const { return TreeImpl->getRoot(); }
NodeId SyntaxTree::getRootId() const { return TreeImpl->getRootId(); }
SyntaxTree::PreorderIterator SyntaxTree::begin() const {
  return TreeImpl->begin();
}
SyntaxTree::PreorderIterator SyntaxTree::end() const { return TreeImpl->end(); }

SyntaxTree::PostorderIterator SyntaxTree::postorder_begin() const {
  return TreeImpl->postorder_begin();
}
SyntaxTree::PostorderIterator SyntaxTree::postorder_end() const {
  return TreeImpl->postorder_end();
}
llvm::iterator_range<SyntaxTree::PostorderIterator>
SyntaxTree::postorder() const {
  return TreeImpl->postorder();
}

} // end namespace diff
} // end namespace clang