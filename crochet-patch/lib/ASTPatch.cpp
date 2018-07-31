//===- ASTPatch.cpp - Structural patching based on ASTDiff ----*- C++ -*- -===//
//
//                     The LLVM Compiler Infrastructure
//
// This file is distributed under the University of Illinois Open Source
// License. See LICENSE.TXT for details.
//
//===----------------------------------------------------------------------===//

#include "crochet/ASTPatch.h"

#include "clang/AST/DeclTemplate.h"
#include "clang/AST/ExprCXX.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Tooling/Core/Replacement.h"
#include <fstream>
#include <sstream>
#include <string>
#include <map>

using namespace llvm;
using namespace clang;
using namespace tooling;

namespace clang {
    namespace diff {

        static Error error(patching_error code) {
            return llvm::make_error<PatchingError>(code);
        };

        static CharSourceRange makeEmptyCharRange(SourceLocation Point) {
            return CharSourceRange::getCharRange(Point, Point);
        }

// Returns a comparison function that considers invalid source locations
// to be less than anything.
        static std::function<bool(SourceLocation, SourceLocation)>
        makeTolerantLess(SourceManager &SM) {
            return [&SM](SourceLocation A, SourceLocation B) {
                if (A.isInvalid())
                    return true;
                if (B.isInvalid())
                    return false;
                BeforeThanCompare <SourceLocation> Less(SM);
                return Less(A, B);
            };
        }

        namespace {
// This wraps a node from Patcher::Target or Patcher::Dst.
            class PatchedTreeNode {
                NodeRef BaseNode;

            public:
                operator NodeRef() const { return BaseNode; }

                NodeRef originalNode() const { return *this; }

                CharSourceRange getSourceRange() const { return BaseNode.getSourceRange(); }

                NodeId getId() const { return BaseNode.getId(); }

                SyntaxTree &getTree() const { return BaseNode.getTree(); }

                StringRef getTypeLabel() const { return BaseNode.getTypeLabel(); }

                decltype(BaseNode.getOwnedSourceRanges()) getOwnedSourceRanges() {
                    return BaseNode.getOwnedSourceRanges();
                }

                // This flag indicates whether this node, or any of its descendants was
                // changed with regards to the original tree.
                bool Changed = false;
                // The pointers to the children, including nodes that have been inserted or
                // moved here.
                SmallVector<PatchedTreeNode *, 4> Children;
                // First location for each child.
                SmallVector<SourceLocation, 4> ChildrenLocations;
                // The offsets at which the children should be inserted into OwnText.
                SmallVector<unsigned, 4> ChildrenOffsets;

                // This contains the text of this node, but not the text of it's children.
                Optional <std::string> OwnText;

                PatchedTreeNode(NodeRef BaseNode) : BaseNode(BaseNode) {}

                PatchedTreeNode(const PatchedTreeNode &Other) = delete;

                PatchedTreeNode(PatchedTreeNode &&Other) = default;

                void addInsertion(PatchedTreeNode &PatchedNode, SourceLocation InsertionLoc) {
                    addChildAt(PatchedNode, InsertionLoc);
                }

                void addChild(PatchedTreeNode &PatchedNode) {
                    SourceLocation InsertionLoc = PatchedNode.getSourceRange().getBegin();
                    addChildAt(PatchedNode, InsertionLoc);
                }

            private:
                void addChildAt(PatchedTreeNode &PatchedNode, SourceLocation InsertionLoc) {
                    auto Less = makeTolerantLess(getTree().getSourceManager());
                    auto It = std::lower_bound(ChildrenLocations.begin(),
                                               ChildrenLocations.end(), InsertionLoc, Less);
                    auto Offset = It - ChildrenLocations.begin();
                    Children.insert(Children.begin() + Offset, &PatchedNode);
                    ChildrenLocations.insert(It, InsertionLoc);
                }
            };
        } // end anonymous namespace

        namespace {
            class Patcher {
                SyntaxTree &Src, &Dst, &Target;
                SourceManager &SM;
                const LangOptions &LangOpts;
                BeforeThanCompare <SourceLocation> Less;

                RefactoringTool &TargetTool;
                bool Debug;
                std::vector <PatchedTreeNode> PatchedTreeNodes;
                std::map<NodeId, PatchedTreeNode *> InsertedNodes;
                std::map<std::string, int> LocNodeMap; //mapping location to noderef id for program C
                // Maps NodeId in Dst to a flag that is true if this node is
                // part of an inserted subtree.
                std::vector<bool> AtomicInsertions;

            public:
                Rewriter Rewrite;
                ASTDiff Diff, TargetDiff;

                std::pair<int, bool>
                findPointOfInsertion(NodeRef N, PatchedTreeNode &TargetParent) const;

                std::string translateVariables(NodeRef node, std::string statement);
                CharSourceRange expandRange(CharSourceRange range, SyntaxTree &Tree);

                bool insertCode(NodeRef insertNode, NodeRef targetNode, int Offset, SyntaxTree &SourceTree);
                bool deleteCode(NodeRef deleteNode);

                Patcher(SyntaxTree &Src, SyntaxTree &Dst, SyntaxTree &Target,
                        const ComparisonOptions &Options, RefactoringTool &TargetTool,
                        bool Debug)
                        : Src(Src), Dst(Dst), Target(Target), SM(Target.getSourceManager()),
                          LangOpts(Target.getLangOpts()), Less(SM), Diff(Src, Dst, Options),
                          TargetDiff(Src, Target, Options), TargetTool(TargetTool), Debug(Debug) {

                    Rewrite.setSourceMgr(SM, LangOpts);
                    int count = 0;
                    for (diff::NodeRef node : Dst) {

                        if (node.getTypeLabel() == "VarDecl" || node.getTypeLabel() == "ParmVarDecl" ||
                            node.getTypeLabel() == "FieldDecl") {

                            if (auto vardec = node.ASTNode.get<VarDecl>()) {
                                count++;
                                SourceLocation loc = vardec->getLocation();
                                std::string locId = loc.printToString(Dst.getSourceManager());
                                int nodeid = node.getId().Id;
                                // llvm::outs() << nodeid << "\n";
                                LocNodeMap[locId] = nodeid;

                            } else if (auto pardec = node.ASTNode.get<ParmVarDecl>()) {
                                count++;
                                SourceLocation loc = pardec->getLocation();
                                std::string locId = loc.printToString(Dst.getSourceManager());
                                int nodeid = node.getId().Id;
                                // llvm::outs() << nodeid << "\n";
                                LocNodeMap[locId] = nodeid;

                            } else if (auto fielddec = node.ASTNode.get<FieldDecl>()) {
                                count++;
                                SourceLocation loc = fielddec->getLocation();
                                std::string locId = loc.printToString(Dst.getSourceManager());
                                int nodeid = node.getId().Id;
                                // llvm::outs() << nodeid << "\n";
                                LocNodeMap[locId] = nodeid;

                            }


                        }
                    }

                    // llvm::outs() << "added to map: " << count << "\n";


                }

                Error apply();

            private:
                void buildPatchedTree();

                void addInsertedAndMovedNodes();

                SourceLocation findLocationForInsertion(NodeRef &InsertedNode,
                                                        PatchedTreeNode &InsertionTarget);

                SourceLocation findLocationForMove(NodeRef DstNode, NodeRef TargetNode,
                                                   PatchedTreeNode &NewParent);

                void markChangedNodes();

                Error addReplacementsForChangedNodes();

                Error addReplacementsForTopLevelChanges();

                // Recursively builds the text that is represented by this subtree.
                std::string buildSourceText(PatchedTreeNode &PatchedNode);

                void setOwnedSourceText(PatchedTreeNode &PatchedNode);

                bool isInserted(const PatchedTreeNode &PatchedNode) const {
                    return isFromDst(PatchedNode);
                }

                ChangeKind getChange(NodeRef TargetNode) const {
                    if (!isFromTarget(TargetNode))
                        return NoChange;
                    const Node *SrcNode = TargetDiff.getMapped(TargetNode);
                    if (!SrcNode)
                        return NoChange;
                    return Diff.getNodeChange(*SrcNode);
                }

                bool isRemoved(NodeRef TargetNode) const {
                    return getChange(TargetNode) == Delete;
                }

                bool isMoved(NodeRef TargetNode) const {
                    return getChange(TargetNode) == Move || getChange(TargetNode) == UpdateMove;
                }

                bool isRemovedOrMoved(NodeRef TargetNode) const {
                    return isRemoved(TargetNode) || isMoved(TargetNode);
                }

                PatchedTreeNode &findParent(NodeRef N) {
                    if (isFromDst(N))
                        return findDstParent(N);
                    return findTargetParent(N);
                }

                PatchedTreeNode &findDstParent(NodeRef DstNode) {
                    const Node *SrcNode = Diff.getMapped(DstNode);
                    NodeRef DstParent = *DstNode.getParent();
                    if (SrcNode) {
                        assert(Diff.getNodeChange(*SrcNode) == Insert);
                        const Node *TargetParent = mapDstToTarget(DstParent);
                        assert(TargetParent);
                        return getTargetPatchedNode(*TargetParent);
                    }
                    return getPatchedNode(DstParent);
                }

                PatchedTreeNode &findTargetParent(NodeRef TargetNode) {
                    assert(isFromTarget(TargetNode));
                    const Node *SrcNode = TargetDiff.getMapped(TargetNode);
                    if (SrcNode) {
                        ChangeKind Change = Diff.getNodeChange(*SrcNode);
                        if (Change == Move || Change == UpdateMove) {
                            NodeRef DstNode = *Diff.getMapped(*SrcNode);
                            return getPatchedNode(*DstNode.getParent());
                        }
                    }
                    return getTargetPatchedNode(*TargetNode.getParent());
                }

                CharSourceRange getRangeForReplacing(NodeRef TargetNode) const {
                    if (isRemovedOrMoved(TargetNode))
                        return TargetNode.findRangeForDeletion();
                    return TargetNode.getSourceRange();
                }

                Error addReplacement(Replacement &&R) {
                    return TargetTool.getReplacements()[R.getFilePath()].add(R);
                }

                bool isFromTarget(NodeRef N) const { return &N.getTree() == &Target; }

                bool isFromDst(NodeRef N) const { return &N.getTree() == &Dst; }

                PatchedTreeNode &getTargetPatchedNode(NodeRef N) {
                    assert(isFromTarget(N));
                    return PatchedTreeNodes[N.getId()];
                }

                PatchedTreeNode &getPatchedNode(NodeRef N) {
                    if (isFromDst(N))
                        return *InsertedNodes.at(N.getId());
                    return PatchedTreeNodes[N.getId()];
                }

                const Node *mapDstToTarget(NodeRef DstNode) const {
                    const Node *SrcNode = Diff.getMapped(DstNode);
                    if (!SrcNode)
                        return nullptr;
                    return TargetDiff.getMapped(*SrcNode);
                }

                const Node *mapTargetToDst(NodeRef TargetNode) const {
                    const Node *SrcNode = TargetDiff.getMapped(TargetNode);
                    if (!SrcNode)
                        return nullptr;
                    return Diff.getMapped(*SrcNode);
                }
            };
        } // end anonymous namespace

        static void markBiggestSubtrees(std::vector<bool> &Marked, SyntaxTree &Tree,
                                        llvm::function_ref<bool(NodeRef)> Predicate) {
            Marked.resize(Tree.getSize());
            for (NodeRef N : Tree.postorder()) {
                bool AllChildrenMarked =
                        std::all_of(N.begin(), N.end(),
                                    [&Marked](NodeRef Child) { return Marked[Child.getId()]; });
                Marked[N.getId()] = Predicate(N) && AllChildrenMarked;
            }
        }

        Error Patcher::apply() {
            if (Debug)
                Diff.dumpChanges(llvm::errs(), /*DumpMatches=*/true);

            llvm::outs() << "marking biggest sub trees\n";
            markBiggestSubtrees(AtomicInsertions, Dst, [this](NodeRef DstNode) {
                return Diff.getNodeChange(DstNode) == Insert;
            });


            buildPatchedTree();

            addInsertedAndMovedNodes();

            markChangedNodes();


            if (auto Err = addReplacementsForChangedNodes()) {
                return Err;
            }


            if (!TargetTool.applyAllReplacements(Rewrite)) {
                llvm::errs() << "Failed to apply replacements\n";
                return error(patching_error::failed_to_apply_replacements);
            }


            if (Rewrite.overwriteChangedFiles()) {
                // Some file has not been saved successfully.
                llvm::errs() << "Some file has not been saved successfully\n";
                return error(patching_error::failed_to_overwrite_files);
            }

            llvm::outs() << "patch success\n";

            return Error::success();

        }

        static bool wantToInsertBefore(SourceLocation Insertion, SourceLocation Point,
                                       BeforeThanCompare <SourceLocation> &Less) {
            assert(Insertion.isValid());
            assert(Point.isValid());
            return Less(Insertion, Point);
        }

        void Patcher::buildPatchedTree() {
            // Firstly, add all nodes of the tree that will be patched to
            // PatchedTreeNodes. This way, their offset (getId()) is the same as in the
            // original tree.
            PatchedTreeNodes.reserve(Target.getSize());
            for (NodeRef TargetNode : Target)
                PatchedTreeNodes.emplace_back(TargetNode);
            // Then add all inserted nodes, from Dst.
            for (NodeId DstId = Dst.getRootId(), E = Dst.getSize(); DstId < E; ++DstId) {
                NodeRef DstNode = Dst.getNode(DstId);
                ChangeKind Change = Diff.getNodeChange(DstNode);
                if (Change == Insert) {
                    PatchedTreeNodes.emplace_back(DstNode);
                    InsertedNodes.emplace(DstNode.getId(), &PatchedTreeNodes.back());
                    // If the whole subtree is inserted, we can skip the children, as we
                    // will just copy the text of the entire subtree.
                    if (AtomicInsertions[DstId])
                        DstId = DstNode.RightMostDescendant;
                }
            }
            // Add existing children.
            for (auto &PatchedNode : PatchedTreeNodes) {
                if (isFromTarget(PatchedNode))
                    for (auto &Child : PatchedNode.originalNode())
                        if (!isRemovedOrMoved(Child))
                            PatchedNode.addChild(getPatchedNode(Child));
            }
        }

        void Patcher::addInsertedAndMovedNodes() {
            ChangeKind Change = NoChange;
            for (NodeId DstId = Dst.getRootId(), E = Dst.getSize(); DstId < E;
                 DstId = Change == Insert && AtomicInsertions[DstId]
                         ? Dst.getNode(DstId).RightMostDescendant + 1
                         : DstId + 1) {
                NodeRef DstNode = Dst.getNode(DstId);
                Change = Diff.getNodeChange(DstNode);
                if (!(Change == Move || Change == UpdateMove || Change == Insert))
                    continue;
                NodeRef DstParent = *DstNode.getParent();
                PatchedTreeNode *InsertionTarget, *NodeToInsert;
                SourceLocation InsertionLoc;
                if (Diff.getNodeChange(DstParent) == Insert) {
                    InsertionTarget = &getPatchedNode(DstParent);
                } else {
                    const Node *TargetParent = mapDstToTarget(DstParent);
                    if (!TargetParent)
                        continue;
                    InsertionTarget = &getTargetPatchedNode(*TargetParent);
                }
                if (Change == Insert) {
                    NodeToInsert = &getPatchedNode(DstNode);
                    InsertionLoc = findLocationForInsertion(DstNode, *InsertionTarget);
                } else {
                    assert(Change == Move || Change == UpdateMove);
                    const Node *TargetNode = mapDstToTarget(DstNode);
                    assert(TargetNode && "Node to update not found.");
                    NodeToInsert = &getTargetPatchedNode(*TargetNode);
                    InsertionLoc =
                            findLocationForMove(DstNode, *TargetNode, *InsertionTarget);
                }
                assert(InsertionLoc.isValid());
                InsertionTarget->addInsertion(*NodeToInsert, InsertionLoc);
            }
        }

        SourceLocation
        Patcher::findLocationForInsertion(NodeRef DstNode,
                                          PatchedTreeNode &InsertionTarget) {
            assert(isFromDst(DstNode));
            assert(isFromDst(InsertionTarget) || isFromTarget(InsertionTarget));
            int ChildIndex;
            bool RightOfChild;
            unsigned NumChildren = InsertionTarget.Children.size();
            std::tie(ChildIndex, RightOfChild) =
                    findPointOfInsertion(DstNode, InsertionTarget);
            if (NumChildren && ChildIndex != -1) {
                auto NeighborRange = InsertionTarget.Children[ChildIndex]->getSourceRange();
                SourceLocation InsertionLocation =
                        RightOfChild ? NeighborRange.getEnd() : NeighborRange.getBegin();
                if (InsertionLocation.isValid())
                    return InsertionLocation;
            }
            llvm_unreachable("Not implemented.");
        }

        SourceLocation Patcher::findLocationForMove(NodeRef DstNode, NodeRef TargetNode,
                                                    PatchedTreeNode &NewParent) {
            assert(isFromDst(DstNode));
            assert(isFromTarget(TargetNode));
            return DstNode.getSourceRange().getEnd();
        }

        void Patcher::markChangedNodes() {
            for (auto Pair : InsertedNodes) {
                NodeRef DstNode = Dst.getNode(Pair.first);
                getPatchedNode(DstNode).Changed = true;
            }
            // Mark nodes in original as changed.
            for (NodeRef TargetNode : Target.postorder()) {
                auto &PatchedNode = PatchedTreeNodes[TargetNode.getId()];
                const Node *SrcNode = TargetDiff.getMapped(TargetNode);
                if (!SrcNode)
                    continue;
                ChangeKind Change = Diff.getNodeChange(*SrcNode);
                auto &Children = PatchedNode.Children;
                bool AnyChildChanged =
                        std::any_of(Children.begin(), Children.end(),
                                    [](PatchedTreeNode *Child) { return Child->Changed; });
                bool AnyChildRemoved = std::any_of(
                        PatchedNode.originalNode().begin(), PatchedNode.originalNode().end(),
                        [this](NodeRef Child) { return isRemovedOrMoved(Child); });
                assert(!PatchedNode.Changed);
                PatchedNode.Changed =
                        AnyChildChanged || AnyChildRemoved || Change != NoChange;
            }
        }

        Error Patcher::addReplacementsForChangedNodes() {
            for (NodeId TargetId = Target.getRootId(), E = Target.getSize(); TargetId < E;
                 ++TargetId) {
                NodeRef TargetNode = Target.getNode(TargetId);
                auto &PatchedNode = getTargetPatchedNode(TargetNode);
                if (!PatchedNode.Changed)
                    continue;
                if (TargetId == Target.getRootId())
                    return addReplacementsForTopLevelChanges();
                CharSourceRange Range = getRangeForReplacing(TargetNode);
                std::string Text =
                        isRemovedOrMoved(PatchedNode) ? "" : buildSourceText(PatchedNode);
                if (auto Err = addReplacement({SM, Range, Text, LangOpts}))
                    return Err;
                TargetId = TargetNode.RightMostDescendant;
            }
            return Error::success();
        }

        Error Patcher::addReplacementsForTopLevelChanges() {
            auto &Root = getTargetPatchedNode(Target.getRoot());
            for (unsigned I = 0, E = Root.Children.size(); I < E; ++I) {
                PatchedTreeNode *Child = Root.Children[I];
                if (!Child->Changed)
                    continue;
                std::string ChildText = buildSourceText(*Child);
                CharSourceRange ChildRange;
                if (isInserted(*Child) || isMoved(*Child)) {
                    SourceLocation InsertionLoc;
                    unsigned NumChildren = Root.Children.size();
                    int ChildIndex;
                    bool RightOfChild;
                    std::tie(ChildIndex, RightOfChild) = findPointOfInsertion(*Child, Root);
                    if (NumChildren && ChildIndex != -1) {
                        auto NeighborRange = Root.Children[ChildIndex]->getSourceRange();
                        InsertionLoc =
                                RightOfChild ? NeighborRange.getEnd() : NeighborRange.getBegin();
                    } else {
                        InsertionLoc = SM.getLocForEndOfFile(SM.getMainFileID())
                                .getLocWithOffset(-int(strlen("\n")));
                    }
                    ChildRange = makeEmptyCharRange(InsertionLoc);
                } else {
                    ChildRange = Child->getSourceRange();
                }
                if (auto Err = addReplacement({SM, ChildRange, ChildText, LangOpts})) {
                    return Err;
                }
            }
            for (NodeRef Child : Root.originalNode()) {
                if (isRemovedOrMoved(Child)) {
                    auto ChildRange = Child.findRangeForDeletion();
                    if (auto Err = addReplacement({SM, ChildRange, "", LangOpts}))
                        return Err;
                }
            }
            return Error::success();
        }

        static StringRef trailingText(SourceLocation Loc, SyntaxTree &Tree) {
            Token NextToken;
            bool Failure = Lexer::getRawToken(Loc, NextToken, Tree.getSourceManager(),
                                              Tree.getLangOpts(),
                    /*IgnoreWhiteSpace=*/true);
            if (Failure)
                return StringRef();
            assert(!Failure);
            return Lexer::getSourceText(
                    CharSourceRange::getCharRange({Loc, NextToken.getLocation()}),
                    Tree.getSourceManager(), Tree.getLangOpts());
        }

        std::string Patcher::buildSourceText(PatchedTreeNode &PatchedNode) {
            auto &Children = PatchedNode.Children;
            auto &ChildrenOffsets = PatchedNode.ChildrenOffsets;
            auto &OwnText = PatchedNode.OwnText;
            auto Range = PatchedNode.getSourceRange();
            SyntaxTree &Tree = PatchedNode.getTree();
            SourceManager &MySM = Tree.getSourceManager();
            const LangOptions &MyLangOpts = Tree.getLangOpts();
            assert(!isRemoved(PatchedNode));
            if (!PatchedNode.Changed ||
                (isFromDst(PatchedNode) && AtomicInsertions[PatchedNode.getId()])) {
                std::string Text = Lexer::getSourceText(Range, MySM, MyLangOpts);
                // TODO why
                if (!isFromDst(PatchedNode))
                    Text += trailingText(Range.getEnd(), Tree);
                return Text;
            }
            setOwnedSourceText(PatchedNode);
            std::string Result;
            unsigned Offset = 0;
            assert(ChildrenOffsets.size() == Children.size());
            for (unsigned I = 0, E = Children.size(); I < E; ++I) {
                PatchedTreeNode *Child = Children[I];
                unsigned Start = ChildrenOffsets[I];
                Result += OwnText->substr(Offset, Start - Offset);
                Result += buildSourceText(*Child);
                Offset = Start;
            }
            assert(Offset <= OwnText->size());
            Result += OwnText->substr(Offset, OwnText->size() - Offset);
            return Result;
        }

        void Patcher::setOwnedSourceText(PatchedTreeNode &PatchedNode) {
            assert(isFromTarget(PatchedNode) || isFromDst(PatchedNode));
            SyntaxTree &Tree = PatchedNode.getTree();
            const Node *SrcNode = nullptr;
            bool IsUpdate = false;
            auto &OwnText = PatchedNode.OwnText;
            auto &Children = PatchedNode.Children;
            auto &ChildrenLocations = PatchedNode.ChildrenLocations;
            auto &ChildrenOffsets = PatchedNode.ChildrenOffsets;
            OwnText = "";
            unsigned NumChildren = Children.size();
            if (isFromTarget(PatchedNode)) {
                SrcNode = TargetDiff.getMapped(PatchedNode);
                ChangeKind Change = SrcNode ? Diff.getNodeChange(*SrcNode) : NoChange;
                IsUpdate = Change == Update || Change == UpdateMove;
            }
            unsigned ChildIndex = 0;
            auto MySourceRanges = PatchedNode.getOwnedSourceRanges();
            BeforeThanCompare <SourceLocation> MyLess(Tree.getSourceManager());
            for (auto &MySubRange : MySourceRanges) {
                SourceLocation ChildBegin;
                SourceLocation InsertionBegin;
                while (ChildIndex < NumChildren &&
                       ((ChildBegin = ChildrenLocations[ChildIndex]).isInvalid() ||
                        wantToInsertBefore(ChildBegin, MySubRange.getEnd(), MyLess))) {
                    ChildrenOffsets.push_back(OwnText->size());
                    ++ChildIndex;
                }
                if (IsUpdate) {
                    llvm_unreachable("Not implemented.");
                } else {
                    *OwnText += Lexer::getSourceText(MySubRange, Tree.getSourceManager(),
                                                     Tree.getLangOpts());
                }
            }
            while (ChildIndex++ < NumChildren)
                ChildrenOffsets.push_back(OwnText->size());
        }

        std::pair<int, bool>
        Patcher::findPointOfInsertion(NodeRef N, PatchedTreeNode &TargetParent) const {
            assert(isFromDst(N) || isFromTarget(N));
            assert(isFromTarget(TargetParent));
            auto MapFunction = [this, &N](PatchedTreeNode &Sibling) {
                if (isFromDst(N) == isFromDst(Sibling))
                    return &NodeRef(Sibling);
                if (isFromDst(N))
                    return mapTargetToDst(Sibling);
                else
                    return mapDstToTarget(Sibling);
            };
            unsigned NumChildren = TargetParent.Children.size();
            BeforeThanCompare <SourceLocation> Less(N.getTree().getSourceManager());
            auto NodeIndex = N.findPositionInParent();
            SourceLocation MyLoc = N.getSourceRange().getBegin();
            assert(MyLoc.isValid());
            for (unsigned I = 0; I < NumChildren; ++I) {
                const Node *Sibling = MapFunction(*TargetParent.Children[I]);
                if (!Sibling)
                    continue;
                SourceLocation SiblingLoc = Sibling->getSourceRange().getBegin();
                if (SiblingLoc.isInvalid())
                    continue;
                if (NodeIndex && Sibling == &N.getParent()->getChild(NodeIndex - 1)) {
                    return {I, /*RightOfSibling=*/true};
                }
                if (Less(MyLoc, SiblingLoc)) {
                    return {I, /*RightOfSibling=*/false};
                }
            }
            return {-1, true};
        }

        bool replaceSubString(std::string &str, const std::string &from, const std::string &to) {
            size_t start_pos = str.find(from);
            if (start_pos == std::string::npos)
                return false;
            str.replace(start_pos, from.length(), to);
            return true;
        }

        std::string Patcher::translateVariables(NodeRef node, std::string statement) {

            unsigned childNodesInUpdateRange = node.getNumChildren();
            // llvm::errs() << "child count " << childNodesInUpdateRange << "\n";


            if (node.getTypeLabel() == "MemberExpr") {

                // llvm::outs() << "translating member name \n";
                auto memNode = node.ASTNode.get<MemberExpr>();
                auto decNode = memNode->getMemberDecl();
                SourceLocation loc = decNode->getLocation();
                std::string locId = loc.printToString(Dst.getSourceManager());
                // llvm::errs() << locId << "\n";
                // llvm::outs() << node.getValue() << "\n";

                if (LocNodeMap.find(locId) == LocNodeMap.end()) {

                    llvm::errs() << "invalid key referenced: " << locId << "\n";

                } else {
                    int nodeid = LocNodeMap.at(locId);
                    NodeRef nodeInDst = Dst.getNode(NodeId(nodeid));

                    if (Diff.getMapped(nodeInDst) != NULL) {
                        NodeRef nodeInSrc = *Diff.getMapped(nodeInDst);
                        std::string variableNameInSource = *nodeInDst.getIdentifier();
                        // llvm::outs() << "before translation: " << variableNameInSource << "\n";

                        if (TargetDiff.getMapped(nodeInSrc) != NULL) {
                            NodeRef nodeInTarget = *TargetDiff.getMapped(nodeInSrc);
                            // llvm::outs() << "mapped node: " << nodeInTarget.getValue() << "\n";
                            std::string variableNameInTarget = *nodeInTarget.getIdentifier();
                            // llvm::outs() << "after translation: " << variableNameInTarget << "\n";
                            replaceSubString(statement, variableNameInSource, variableNameInTarget);
                            // llvm::outs() << "after replacement: " << statement << "\n";
                        } else {
                            llvm::errs() << "mapping not found for member definition";
                        }

                    }

                }

                return statement;


            } else if (node.getTypeLabel() == "VarDecl") {

                // llvm::outs() << "translating variable definition \n";
                auto decNode = node.ASTNode.get<VarDecl>();
                SourceLocation loc = decNode->getLocation();
                std::string locId = loc.printToString(Dst.getSourceManager());
                // llvm::errs() << locId << "\n";
                // llvm::outs() << node.getValue() << "\n";

                if (LocNodeMap.find(locId) == LocNodeMap.end()) {

                    llvm::errs() << "invalid key referenced: " << locId << "\n";

                } else {
                    // llvm::outs() << "found location\n" ;
                    int nodeid = LocNodeMap.at(locId);
                    NodeRef nodeInDst = Dst.getNode(NodeId(nodeid));
                    std::string variableNameInSource = *nodeInDst.getIdentifier();
                    // llvm::outs() << "before translation: " << variableNameInSource << "\n";

                    if (Diff.getMapped(nodeInDst) != NULL) {
                        NodeRef nodeInSrc = *Diff.getMapped(nodeInDst);

                        if (TargetDiff.getMapped(nodeInSrc) != NULL) {
                            NodeRef nodeInTarget = *TargetDiff.getMapped(nodeInSrc);
                            // llvm::outs() << "mapped node: " << nodeInTarget.getValue() << "\n";
                            std::string variableNameInTarget = *nodeInTarget.getIdentifier();
                            // llvm::outs() << "after translation: " << variableNameInTarget << "\n";
                            replaceSubString(statement, variableNameInSource, variableNameInTarget);

                        }

                    } //else {
                    //     std::string variableNameInTarget = variableNameInSource + "_crochet";
                    //     // llvm::outs() << "after translation: " << variableNameInTarget << "\n";
                    //     replaceSubString(statement, variableNameInSource, variableNameInTarget);
                    // }

                }

                return statement;


            } else if (node.getTypeLabel() == "FieldDecl") {

                // llvm::outs() << "translating member definition \n";
                auto decNode = node.ASTNode.get<FieldDecl>();
                SourceLocation loc = decNode->getLocation();
                std::string locId = loc.printToString(Dst.getSourceManager());
                // llvm::errs() << locId << "\n";
                // llvm::outs() << node.getValue() << "\n";

                if (LocNodeMap.find(locId) == LocNodeMap.end()) {

                    llvm::errs() << "invalid key referenced: " << locId << "\n";

                } else {
                    // llvm::outs() << "found location\n" ;
                    int nodeid = LocNodeMap.at(locId);
                    NodeRef nodeInDst = Dst.getNode(NodeId(nodeid));
                    std::string variableNameInSource = *nodeInDst.getIdentifier();
                    // llvm::outs() << "before translation: " << variableNameInSource << "\n";

                    if (Diff.getMapped(nodeInDst) != NULL) {
                        NodeRef nodeInSrc = *Diff.getMapped(nodeInDst);

                        if (TargetDiff.getMapped(nodeInSrc) != NULL) {
                            NodeRef nodeInTarget = *TargetDiff.getMapped(nodeInSrc);
                            // llvm::outs() << "mapped node: " << nodeInTarget.getValue() << "\n";
                            std::string variableNameInTarget = *nodeInTarget.getIdentifier();
                            // llvm::outs() << "after translation: " << variableNameInTarget << "\n";
                            replaceSubString(statement, variableNameInSource, variableNameInTarget);

                        }

                    } //else {
                    //     std::string variableNameInTarget = variableNameInSource + "_crochet";
                    //     // llvm::outs() << "after translation: " << variableNameInTarget << "\n";
                    //     replaceSubString(statement, variableNameInSource, variableNameInTarget);
                    // }

                }

                return statement;

            }


            for (unsigned childIndex = 0; childIndex < childNodesInUpdateRange; childIndex++) {
                // llvm::errs() << "child " << childIndex << "\n";
                NodeRef childNode = node.getChild(childIndex);
                // llvm::outs() << "child " << childIndex << " type " << childNode.getTypeLabel() << "\n";

                if (childNode.getTypeLabel() == "DeclRefExpr") {

                    // llvm::outs() << "translating reference \n";

                    auto decRefNode = childNode.ASTNode.get<DeclRefExpr>();
                    auto decNode = decRefNode->getDecl();
                    SourceLocation loc = decNode->getLocation();
                    std::string locId = loc.printToString(Dst.getSourceManager());

                    if (LocNodeMap.find(locId) == LocNodeMap.end()) {
                        llvm::errs() << "invalid key referenced: " << locId << "\n";

                    } else {
                        int nodeid = LocNodeMap.at(locId);
                        NodeRef nodeInDst = Dst.getNode(NodeId(nodeid));
                        std::string variableNameInSource = *nodeInDst.getIdentifier();
                        // llvm::outs() << "before translation: " << variableNameInSource << "\n";
                        if (Diff.getMapped(nodeInDst) != NULL) {
                            NodeRef nodeInSrc = *Diff.getMapped(nodeInDst);


                            if (TargetDiff.getMapped(nodeInSrc) != NULL) {
                                NodeRef nodeInTarget = *TargetDiff.getMapped(nodeInSrc);
                                std::string variableNameInTarget = *nodeInTarget.getIdentifier();
                                // llvm::outs() << "after translation: " << variableNameInTarget << "\n";
                                replaceSubString(statement, variableNameInSource, variableNameInTarget);

                            }

                        } //else {
                        //    std::string variableNameInTarget = variableNameInSource + "_crochet";
                        //    // llvm::outs() << "after translation: " << variableNameInTarget << "\n";
                        //    replaceSubString(statement, variableNameInSource, variableNameInTarget);
                        // }

                    }

                }

                if (childNode.getNumChildren() > 0) {
                    statement = translateVariables(childNode, statement);
                }

            }

            return statement;
        }

        CharSourceRange Patcher::expandRange(CharSourceRange range, SyntaxTree &Tree) {

            SourceLocation startLoc = range.getBegin();
            SourceLocation endLoc = range.getEnd();

            // llvm::outs() << endLoc.printToString(Target.getSourceManager()) << "\n";
            endLoc = Lexer::getLocForEndOfToken(endLoc, /*Offset=*/0, Tree.getSourceManager(), Tree.getLangOpts());
            // llvm::outs() << endLoc.printToString(Target.getSourceManager()) << "\n";

            // Break down the source location.
            std::pair<FileID, unsigned> endLocInfo = Tree.getSourceManager().getDecomposedLoc(endLoc);
            // Try to load the file buffer.
            bool invalidTemp = false;
            StringRef file = Tree.getSourceManager().getBufferData(endLocInfo.first, &invalidTemp);

            if (!invalidTemp) {
                const char *tokenBegin = file.data() + endLocInfo.second;
                // Lex from the start of the given location.
                Lexer lexer(Tree.getSourceManager().getLocForStartOfFile(endLocInfo.first), Tree.getLangOpts(), file.begin(), tokenBegin, file.end());
                Token tok;
                lexer.LexFromRawLexer(tok);
                // llvm::outs() << tok.getName() << "\n";
                if (tok.is(tok::semi) || tok.is(tok::comma) || tok.is(tok::raw_identifier)) {
                    // llvm::outs() << "ok\n";
                    range.setEnd(endLoc);
                }
            }
            return range;
        }

        bool Patcher::deleteCode(NodeRef deleteNode) {
            bool modified = false;
            CharSourceRange range = deleteNode.findRangeForDeletion();
            SourceLocation startLoc = range.getBegin();
            SourceLocation endLoc = range.getEnd();

            if (startLoc.isMacroID()) {
                // llvm::outs() << "Macro identified\n";
                // Get the start/end expansion locations
                CharSourceRange expansionRange = Rewrite.getSourceMgr().getImmediateExpansionRange(startLoc);
                // We're just interested in the start location
                startLoc = expansionRange.getBegin();
                range.setBegin(startLoc);
            }

            if (deleteNode.getTypeLabel() == "BinaryOperator" || deleteNode.getTypeLabel() == "DeclStmt" || deleteNode.getTypeLabel() == "Macro") {
                range = expandRange(range,Target);
            }

            Rewriter::RewriteOptions delRangeOpts;
            delRangeOpts.RemoveLineIfEmpty = true;
            Rewrite.RemoveText(range, delRangeOpts);
            modified = true;
            return modified;
        }

        bool Patcher::insertCode(NodeRef insertNode, NodeRef targetNode, int Offset, SyntaxTree &SourceTree) {

            bool modified = false;

            // llvm::outs() << "nodes matched\n";

            CharSourceRange range = targetNode.getSourceRange();
            CharSourceRange extractRange = insertNode.getSourceRange();
            SourceLocation insertLoc = range.getBegin();
            std::string insertStatement;


            if (insertLoc.isMacroID()) {

                llvm::outs() << "Macro identified\n";
                // Get the start/end expansion locations
                CharSourceRange expansionRange = Rewrite.getSourceMgr().getImmediateExpansionRange(
                        insertLoc);
                // We're just interested in the start location
                insertLoc = expansionRange.getBegin();
                range.setBegin(insertLoc);

            }

            extractRange = expandRange(extractRange, SourceTree);            
            insertStatement = Lexer::getSourceText(extractRange, SourceTree.getSourceManager(), SourceTree.getLangOpts());
            insertStatement = " " + insertStatement + " ";

            // llvm::outs() << insertStatement << "\n";
            insertStatement = translateVariables(insertNode, insertStatement);
            // llvm::outs() << insertStatement << "\n";



            if (!insertStatement.empty()) {

                unsigned int NumChildren = targetNode.getNumChildren();
                if (targetNode.getTypeLabel() == "CompoundStmt") {

                    insertStatement = "\n" + insertStatement + "\n";

                    if (Offset == 0) {
                        if (NumChildren > 0) {
                            Rewrite.InsertTextAfterToken(insertLoc, insertStatement);
                            modified = true;

                        } else {
                            Rewrite.InsertTextAfter(insertLoc, insertStatement);
                            modified = true;
                        }

                    } else {

                        NodeRef nearestChildNode = targetNode.getChild(Offset - 1);
                        insertLoc = nearestChildNode.getSourceRange().getEnd();

                        if (Rewrite.InsertTextAfterToken(insertLoc, insertStatement))
                            llvm::errs() << "error inserting\n";
                        modified = true;


                    }

                } else if (targetNode.getTypeLabel() == "IfStmt") {

                    if (Offset == 0) {
                        auto ifNode = targetNode.ASTNode.get<IfStmt>();
                        auto condNode = ifNode->getCond();
                        insertLoc = condNode->getExprLoc();
                        std::string locId = insertLoc.printToString(Target.getSourceManager());
                        // llvm::outs() << locId << "\n";

                        if (Rewrite.InsertTextBefore(insertLoc, insertStatement))
                            llvm::errs() << "error inserting\n";
                        modified = true;

                    } else {

                        NodeRef nearestChildNode = targetNode.getChild(Offset - 1);
                        insertLoc = nearestChildNode.getSourceRange().getEnd();

                        if (Rewrite.InsertTextAfterToken(insertLoc, insertStatement))
                            llvm::errs() << "error inserting\n";
                        modified = true;


                    }

                } else if (targetNode.getTypeLabel() == "BinaryOperator") {

                    insertStatement = " " + insertStatement + " ";
                    // llvm::outs() << insertLoc.printToString(Target.getSourceManager()) << "\n";
                    auto binaryNode = targetNode.ASTNode.get<BinaryOperator>();
                    insertLoc = binaryNode->getOperatorLoc();
                    std::string locId = insertLoc.printToString(Target.getSourceManager());
                    // llvm::outs() << locId << "\n";

                    if (Offset == 0) {
                        if (Rewrite.InsertTextBefore(insertLoc, insertStatement))
                            llvm::errs() << "error inserting\n";


                    } else {
                        if (Rewrite.InsertTextAfterToken(insertLoc, insertStatement))
                            llvm::errs() << "error inserting\n";
                    }

                    modified = true;

                } else {

                    if (Offset == 0) {
                        if (NumChildren > 0) {
                            // NodeRef firstChild = targetNode.getChild(Offset);
                            // startLoc = firstChild.getSourceRange().getBegin();
                            // crochetPatcher.Rewrite.InsertTextBefore(startLoc, insertStatement);

                            Rewrite.InsertTextAfterToken(insertLoc, insertStatement);
                            modified = true;


                        } else {

                            Rewrite.InsertTextAfter(insertLoc, insertStatement);
                            modified = true;
                            // Rewrite.InsertTextAfter(r.getBegin(), insert_value);
                            // PresumedLoc InsertLoc = SM.getPresumedLoc(r.getBegin());
                            // llvm::outs() << "InsertLoc: " << InsertLoc.getLine() << ":" << InsertLoc.getColumn() << "\n";
                        }

                    } else {

                        // llvm::outs() << Offset << "\n";
                        // llvm::outs() << NumChildren << "\n";

                        if (Offset <= NumChildren - 1) {
                            // llvm::outs() <<"if leg\n";
                            NodeRef nearestChildNode = targetNode.getChild(Offset);
                            // llvm::outs() <<"got child\n";
                            insertLoc = nearestChildNode.getSourceRange().getBegin();
                            // llvm::outs() <<"got loc\n";
                            // if (insertLoc.isValid())
                            //  llvm::outs() <<"valid\n";
                            if (Rewrite.InsertText(insertLoc, insertStatement))
                                llvm::errs() << "error inserting\n";
                            // llvm::outs() <<"inserted\n";
                            modified = true;

                        } else {
                            // llvm::outs() <<"else leg\n";
                            NodeRef nearestChildNode = targetNode.getChild(Offset - 1);
                            // llvm::outs() <<"got child\n";
                            insertLoc = nearestChildNode.getSourceRange().getEnd();
                            // llvm::outs() <<"got loc\n";
                            Rewrite.InsertTextAfterToken(insertLoc, insertStatement);
                            // llvm::outs() <<"inserted\n";
                            modified = true;
                        }


                    }

                }


            }

            return modified;
        }

        Error patch(RefactoringTool &TargetTool, SyntaxTree &Src, SyntaxTree &Dst, std::string ScriptFilePath,
                    const ComparisonOptions &Options, bool Debug) {

            std::vector <std::unique_ptr<ASTUnit>> TargetASTs;
            TargetTool.buildASTs(TargetASTs);

            if (TargetASTs.size() == 0)
                return error(patching_error::failed_to_build_AST);
            SyntaxTree Target(*TargetASTs[0]);

            Patcher crochetPatcher(Src, Dst, Target, Options, TargetTool, Debug);

            std::ifstream infile(ScriptFilePath);
            std::string line;
            bool modified = false;

            while (std::getline(infile, line)) {
                std::string operation = line.substr(0, line.find(" "));
                // llvm::outs() << operation << "\n";

                if (operation == "Insert") {

                    // llvm::outs() << "insert op\n";
                    std::string offset = line.substr(line.find(" at ") + 4);
                    int Offset = stoi(offset);
                    line = line.substr(0, line.find(" at "));
                    std::string nextChild, nextChildType, nextChildId;
                    std::string prevChild, prevChildType, prevChildId;


                    std::string nodeB = line.substr(line.find(" ") + 1, line.find(")") - line.find(" "));
                    std::string nodeTypeB = nodeB.substr(0, nodeB.find("("));
                    std::string nodeIdB = nodeB.substr(nodeB.find("(") + 1, nodeB.find(")") - nodeB.find("(") - 1);

                    std::string nodeC = line.substr(line.find(" into ") + 6);
                    std::string nodeTypeC = nodeC.substr(0, nodeC.find("("));
                    std::string nodeIdC = nodeC.substr(nodeC.find("(") + 1, nodeC.find(")") - nodeC.find("(") - 1);

                    // llvm::outs() << nodeC << "\n";
                    // llvm::outs() << nodeIdC << "\n";
                    // llvm::outs() << nodeTypeC << "\n";

                    // llvm::outs() << nodeB << "\n";
                    // llvm::outs() << nodeIdB << "\n";
                    // llvm::outs() << nodeTypeB << "\n";

                    NodeRef insertNode = Dst.getNode(NodeId(stoi(nodeIdB)));
                    NodeRef targetNode = Target.getNode(NodeId(stoi(nodeIdC)));


                    // NodeRef targetParentNode = targetNode.getParent();
                    // llvm::outs() << insertNode.getTypeLabel() << "\n";
                    // llvm::outs() << targetNode.getTypeLabel() << "\n";


                    if ((targetNode.getTypeLabel() == nodeTypeC) && (insertNode.getTypeLabel() == nodeTypeB)) {                        
                        modified = crochetPatcher.insertCode(insertNode, targetNode, Offset, Dst);

                    } else {
                        llvm::errs() << "Error: wrong node type for given Id\n";
                        return error(patching_error::failed_to_apply_replacements);

                    }

                } else if (operation == "Move") {

                    // llvm::outs() << "move op\n";
                    std::string offset = line.substr(line.find(" at ") + 4);
                    int Offset = stoi(offset);
                    line = line.substr(0, line.find(" at "));
                    std::string nodeB = line.substr(line.find(" ") + 1, line.find(")") - line.find(" "));
                    std::string nodeTypeB = nodeB.substr(0, nodeB.find("("));
                    std::string nodeIdB = nodeB.substr(nodeB.find("(") + 1, nodeB.find(")") - nodeB.find("(") - 1);

                    std::string nodeC = line.substr(line.find(" into ") + 6);
                    std::string nodeTypeC = nodeC.substr(0, nodeC.find("("));
                    std::string nodeIdC = nodeC.substr(nodeC.find("(") + 1, nodeC.find(")") - nodeC.find("(") - 1);

                    NodeRef movingNode = Target.getNode(NodeId(stoi(nodeIdB)));
                    NodeRef targetNode = Target.getNode(NodeId(stoi(nodeIdC)));
                    // NodeRef targetParentNode = targetNode.getParent();


                    // llvm::outs() << nodeC << "\n";
                    // llvm::outs() << nodeIdC << "\n";
                    // llvm::outs() << nodeTypeC << "\n";

                    // llvm::outs() << nodeB << "\n";
                    // llvm::outs() << nodeIdB << "\n";
                    // llvm::outs() << nodeTypeB << "\n";

                    // llvm::outs() << movingNode.getTypeLabel() << "\n";
                    // llvm::outs() << targetNode.getTypeLabel() << "\n";

                    if ((targetNode.getTypeLabel() == nodeTypeC) && (movingNode.getTypeLabel() == nodeTypeB)) {

                        // llvm::outs() << "nodes matched\n";

                        CharSourceRange deleteRange = movingNode.findRangeForDeletion();

                        if (crochetPatcher.deleteCode(movingNode)) {                            
                            modified = crochetPatcher.insertCode(movingNode, targetNode, Offset, Target);
                        } else {
                            llvm::errs() << "Error: couldn't remove code for move\n";
                            return error(patching_error::failed_to_apply_replacements);

                        }


                    } else {
                        llvm::errs() << "Error: wrong node type for given Id\n";
                        return error(patching_error::failed_to_apply_replacements);

                    }

                } else if (operation == "Update") {

                    // llvm::outs() << "update op\n";

                    std::string nodeC = line.substr(line.find(" ") + 1, line.find(")") - line.find(" "));
                    std::string nodeTypeC = nodeC.substr(0, nodeC.find("("));
                    std::string nodeIdC = nodeC.substr(nodeC.find("(") + 1, nodeC.find(")") - nodeC.find("(") - 1);

                    std::string nodeB = line.substr(line.find(" to ") + 4);
                    std::string nodeTypeB = nodeB.substr(0, nodeB.find("("));
                    std::string nodeIdB = nodeB.substr(nodeB.find("(") + 1, nodeB.find(")") - nodeB.find("(") - 1);

                    NodeRef updateNode = Dst.getNode(NodeId(stoi(nodeIdB)));
                    NodeRef targetNode = Target.getNode(NodeId(stoi(nodeIdC)));


                    // llvm::outs() << nodeC << "\n";
                    // llvm::outs() << nodeIdC << "\n";
                    // llvm::outs() << nodeTypeC << "\n";

                    // llvm::outs() << nodeB << "\n";
                    // llvm::outs() << nodeIdB << "\n";
                    // llvm::outs() << nodeTypeB << "\n";

                    // llvm::outs() << updateNode.getTypeLabel() << "\n";
                    // llvm::outs() << targetNode.getTypeLabel() << "\n";

                    if ((targetNode.getTypeLabel() == nodeTypeC) && (updateNode.getTypeLabel() == nodeTypeB)) {

                        // llvm::outs() << "nodes matched\n";
                        CharSourceRange range;
                        if (targetNode.getTypeLabel() == "BinaryOperator") {

                            SourceRange r = targetNode.ASTNode.getSourceRange();
                            range.setBegin(r.getBegin());
                            range.setEnd(r.getEnd());

                        } else {
                            range = targetNode.getSourceRange();
                        }

                        SourceLocation startLoc = range.getBegin();
                        SourceLocation endLoc = range.getEnd();

                        if (startLoc.isMacroID()) {
                            // llvm::outs() << "Macro identified\n";
                            // Get the start/end expansion locations
                            CharSourceRange expansionRange = crochetPatcher.Rewrite.getSourceMgr().getImmediateExpansionRange(
                                    startLoc);
                            // We're just interested in the start location
                            startLoc = expansionRange.getBegin();
                            range.setBegin(startLoc);
                        }

                        std::string updateValue = updateNode.getValue();
                        std::string oldValue = targetNode.getValue();


                        if (targetNode.getTypeLabel() == "MemberExpr") {

                            updateValue = updateValue.substr(1);
                            oldValue = oldValue.substr(1);

                        }


                        // llvm::outs() << updateValue << "\n";
                        updateValue = crochetPatcher.translateVariables(updateNode, updateValue);

                        // llvm::outs() << updateValue << "\n";
                        // llvm::outs() << oldValue << "\n";

                        if (!updateValue.empty()) {
                            std::string statement = Lexer::getSourceText(range, Target.getSourceManager(),
                                                                         Target.getLangOpts());

                            // llvm::outs() << statement << "\n";
                            replaceSubString(statement, oldValue, updateValue);
                            // llvm::outs() << statement << "\n";
                            if (crochetPatcher.Rewrite.RemoveText(range))
                                return error(patching_error::failed_to_apply_replacements);

                            modified = true;

                            // llvm::outs() << "statement removed" << "\n";
                            if (crochetPatcher.Rewrite.InsertText(range.getBegin(), statement))
                                return error(patching_error::failed_to_apply_replacements);
                            // llvm::outs() << "statement updated" << "\n";
                        }

                    } else {
                        llvm::errs() << "Error: wrong node type for given Id\n";
                        return error(patching_error::failed_to_apply_replacements);

                    }


                } else if (operation == "Delete") {

                    // llvm::outs() << "delete op\n";

                    std::string nodeType = line.substr(line.find(" ") + 1, line.find("(") - operation.length() - 1);
                    std::string nodeId = line.substr(line.find("(") + 1, line.find(")") - line.find("(") - 1);

                    NodeRef deleteNode = Target.getNode(NodeId(stoi(nodeId)));

                    // llvm::outs() << deleteNode.getTypeLabel() << "\n";
                    // llvm::outs() << "type: " << nodeType << "\n";
                    // llvm::outs() << "id: " << nodeId << "\n";

                    if (deleteNode.getTypeLabel() == nodeType) {
                        modified = crochetPatcher.deleteCode(deleteNode);

                    } else {
                        llvm::errs() << "Error: wrong node type for given Id\n";
                        return error(patching_error::failed_to_apply_replacements);

                    }


                } else if (operation == "UpdateMove") {

                    // llvm::outs() << "move op\n";

                } else {
                    llvm::errs() << "unknown op\n";
                    return error(patching_error::failed_to_apply_replacements);
                }


            }

            const RewriteBuffer *RewriteBuf = crochetPatcher.Rewrite.getRewriteBufferFor(
                    Target.getSourceManager().getMainFileID());
            // llvm::outs()  << "/* Start Crochet Output */\n";
            if (modified)
                llvm::outs() << std::string(RewriteBuf->begin(), RewriteBuf->end());
            // llvm::outs()  << "/* End Crochet Output */\n";

            // return Patcher(Src, Dst, Target, Options, TargetTool, Debug).apply();
            return Error::success();
        }

        std::string PatchingError::message() const {
            switch (Err) {
                case patching_error::failed_to_build_AST:
                    return "Failed to build AST.\n";
                case patching_error::failed_to_apply_replacements:
                    return "Failed to apply replacements.\n";
                case patching_error::failed_to_overwrite_files:
                    return "Failed to overwrite some file(s).\n";
            };
        }

        char PatchingError::ID = 1;

    } // end namespace diff
} // end namespace clang