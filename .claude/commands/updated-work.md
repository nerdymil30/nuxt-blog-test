# Work Plan Execution Command

## Introduction

This command helps you analyze a work document (plan, Markdown file, specification, or any structured document), create a comprehensive todo list using the TodoWrite tool, and then systematically execute each task until the entire plan is completed. It combines deep analysis with practical execution to transform plans into reality.

## Prerequisites

- A work document to analyze (plan file, specification, or any structured document)
- Clear understanding of project context and goals
- Access to necessary tools and permissions for implementation
- Ability to test and validate completed work
- Git repository with main branch

## Main Tasks

### 1. Setup Development Environment

- Ensure main branch is up to date
- Create feature branch with descriptive name
- Setup worktree for isolated development
- Configure development environment

### 2. Analyze Input Document

<input_document> #$ARGUMENTS </input_document>

## Execution Workflow

### Phase 1: Environment Setup

1. **Update Main Branch**

   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create Feature Branch and Worktree**

   - Determine appropriate branch name from document
   - Get the root directory of the Git repository:

   ```bash
   git_root=$(git rev-parse --show-toplevel)
   ```

   - Create worktrees directory if it doesn't exist:

   ```bash
   mkdir -p "$git_root/.worktrees"
   ```

   - Add .worktrees to .gitignore if not already there:

   ```bash
   if ! grep -q "^\.worktrees$" "$git_root/.gitignore"; then
     echo ".worktrees" >> "$git_root/.gitignore"
   fi
   ```

   - Create the new worktree with feature branch:

   ```bash
   git worktree add -b feature-branch-name "$git_root/.worktrees/feature-branch-name" main
   ```

   - Change to the new worktree directory:

   ```bash
   cd "$git_root/.worktrees/feature-branch-name"
   ```

3. **Verify Environment**
   - Confirm in correct worktree directory
   - Install dependencies if needed
   - Run initial tests to ensure clean state

### Phase 2: Document Analysis and Task Framework

1. **Read Input Document**

   - Use Read tool to examine the work document
   - Identify all deliverables and requirements
   - Note any constraints or dependencies
   - Extract success criteria

2. **Draft Parent Tasks (Generate Tasks · Phase 1)**
   - Convert the requirements into ~5 high-level parent tasks.
   - Present the parent task list to the user in Markdown and pause: "I’ve generated the high-level tasks. Ready for sub-tasks? Reply ‘Go’ to continue."

3. **Await Confirmation Before Detailing (Generate Tasks · Phase 2)**
   - After the user says "Go," expand each parent into actionable sub-tasks that a junior developer can follow, including validation steps and edge-case coverage.
   - Identify candidate files (code + tests) that will be touched and capture them for the eventual `Relevant Files` section.

4. **Publish Task List Artifact**
   - Save or update `/tasks/tasks-[source-file].md` with the parent tasks, sub-tasks, relevant files, and notes.

### Phase 3: Systematic Execution

1. **Task Execution Loop**

   ```
   while (tasks remain):
     - Identify the next sub-task based on priority and dependencies
     - Ask the user for approval before starting the sub-task
     - Execute the sub-task end-to-end
     - Run targeted validation (tests, lint, checks) for that sub-task
     - Mark the sub-task `[x]` in the task list
     - If all subtasks for a parent are `[x]`:
         · Run the full test suite
         · Stage clean changes and remove temporary artifacts
         · Commit using a conventional single-line command referencing the task
     - Update progress notes and surface blockers immediately
   ```

2. **Execution Guardrails**
   - Work strictly one sub-task at a time and wait for explicit "yes/y" before the next.
   - Pause after each completed sub-task to confirm results with the user before proceeding.

3. **Maintain the Task List**
   - Keep statuses accurate, add newly discovered tasks, and ensure `Relevant Files` stays aligned with actual edits throughout execution.

### Phase 4: Completion and Submission

1. **Final Validation**

   - Verify all tasks completed
   - Run comprehensive test suite
   - Execute final lint and typecheck
   - Check all deliverables present
   - Ensure documentation updated

2. **Prepare for Submission**

   - Stage and commit all changes
   - Write commit messages
   - Push feature branch to remote
   - Create detailed pull request

3. **Create Pull Request**
   ```bash
   git push -u origin feature-branch-name
   gh pr create --title "Feature: [Description]" --body "[Detailed description]"
   ```
