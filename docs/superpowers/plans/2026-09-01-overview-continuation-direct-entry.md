# Overview Continuation Direct Entry Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

Goal: Let overview continuation actions open a known resume draft directly and provide accessible action feedback while preserving existing navigation.

Architecture: Reuse the existing OverviewState.continuations records and the existing open-draft event path already handled by App.vue. OverviewView owns a small routing handler that sends resume items with ids to the editor and all other items to their current view target; no backend or persistence changes are needed.

Tech Stack: Vue 3.5, TypeScript, Vue Test Utils/Vitest, existing lucide-vue-next icons, existing CSS tokens.

## Global Constraints

- Modify only web-frontend/src/views/OverviewView.vue, web-frontend/src/App.vue, web-frontend/src/tests/dashboard.spec.ts, and web-frontend/src/tests/interaction.spec.ts.
- Keep existing backend APIs, response shapes, database persistence, dependencies, and resume editor implementation unchanged.
- Preserve 44px touch targets, current desktop/mobile layout, existing loading/error/empty/focus behavior, and Chinese user-facing copy.
- A resume continuation without an id must navigate to the resume list and must not emit an invalid open-draft event.
- Run the complete Web test suite, production build, and git diff --check before acceptance.

---

### Task 1: Route Overview Continuation Actions

Files:
- Modify: web-frontend/src/views/OverviewView.vue
- Test: web-frontend/src/tests/dashboard.spec.ts
- Test: web-frontend/src/tests/interaction.spec.ts

Interfaces:
- Consumes: OverviewState.continuations: ContinuationItem[], where each item has kind, optional id, title, and target.
- Produces: local openContinuation(item: ContinuationItem): void behavior that emits either open-draft with a draft id or navigate with the existing target, and updates focusStatus before emitting.

- [ ] Step 1: Write failing dashboard routing contract tests

Add source-contract assertions in web-frontend/src/tests/interaction.spec.ts next to the existing overview interaction assertions:

    it("routes continuation resume items to the existing draft editor event", () => {
      const overview = readFileSync(new URL("../views/OverviewView.vue", import.meta.url), "utf8")

      expect(overview).toContain("function openContinuation(item: ContinuationItem)")
      expect(overview).toContain('if (item.kind === "resume" && item.id)')
      expect(overview).toContain('emit("open-draft", item.id)')
      expect(overview).toContain('emit("navigate", item.target)')
      expect(overview).toContain("focusStatus.value =")
    })

    it("keeps continuation buttons accessible and distinguishes resume editing", () => {
      const overview = readFileSync(new URL("../views/OverviewView.vue", import.meta.url), "utf8")

      expect(overview).toContain('item.kind === "resume" ? "继续编辑" : "继续"')
      expect(overview).toContain(":aria-label=")
      expect(overview).toContain("openContinuation(item)")
    })

Add a data-level assertion in web-frontend/src/tests/dashboard.spec.ts to ensure draft continuation ids remain available:

    it("keeps draft ids on continuation items for direct editor entry", () => {
      const state = buildOverviewState({
        applications: [],
        drafts: [{ id: "draft-42", job_title: "Product Designer" }],
        tasks: [{ id: "task-1", title: "Prepare portfolio", status: "pending" }],
      })

      expect(state.continuations.some((item) => item.kind === "resume" && item.id === "draft-42" && item.target === "resume")).toBe(true)
    })

- [ ] Step 2: Run focused tests and verify the new contract fails

Run:

    cd web-frontend
    npm.cmd run test -- --run src/tests/interaction.spec.ts src/tests/dashboard.spec.ts

Expected: the new openContinuation and accessible-label assertions fail because the view currently emits only navigate from continuation buttons.

- [ ] Step 3: Implement the smallest Overview routing change

In OverviewView.vue:

1. Extend the defineEmits type with "open-draft": [draftId: string] while retaining the existing navigate event.
2. Add this handler beside runFocus:

    function openContinuation(item: ContinuationItem): void {
      focusStatus.value = "已选择：" + item.title
      if (item.kind === "resume" && item.id) {
        emit("open-draft", item.id)
        return
      }
      emit("navigate", item.target)
    }

3. Replace the continuation button click binding with @click="openContinuation(item)".
4. Render "继续编辑" only for resume items and "继续" otherwise.
5. Add an aria-label containing the action and item title to each continuation button.
6. Leave starter actions on their existing navigate path because they have no draft id.

- [ ] Step 4: Run focused tests and verify they pass

Run the same command from Step 2. Expected: all focused dashboard and interaction tests pass.

- [ ] Step 5: Commit the Overview change

    git add web-frontend/src/views/OverviewView.vue web-frontend/src/tests/dashboard.spec.ts web-frontend/src/tests/interaction.spec.ts
    git commit -m "feat(web): route overview continuations directly"

### Task 2: Forward Draft Opening Through App Shell

Files:
- Modify: web-frontend/src/App.vue
- Test: web-frontend/src/tests/interaction.spec.ts

Interfaces:
- Consumes: child component open-draft event carrying draftId: string.
- Produces: the existing editingDraftId state update, which mounts ResumeEditorView through the current v-if="editingDraftId" branch.

- [ ] Step 1: Write the failing App event contract test

Add an assertion beside existing App orchestration assertions in web-frontend/src/tests/interaction.spec.ts:

    it("forwards overview draft openings to the existing editor state", () => {
      const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")

      expect(app).toContain('@open-draft="editingDraftId = $event"')
      expect(app).toContain('v-if="editingDraftId"')
      expect(app).toContain(':draft-id="editingDraftId"')
    })

- [ ] Step 2: Run the focused App contract test and verify it fails

Run:

    cd web-frontend
    npm.cmd run test -- --run src/tests/interaction.spec.ts

Expected: the assertion for @open-draft fails because the dynamic component currently listens only for navigate.

- [ ] Step 3: Add the existing event forwarding in App.vue

Update the dynamic component invocation in App.vue so it retains the current navigation handler and adds:

    @open-draft="editingDraftId = $event"

Do not add another editor state variable or change the existing editor cancel/save listeners.

- [ ] Step 4: Run focused tests and verify they pass

Run the command from Step 2. Expected: all interaction.spec.ts tests pass.

- [ ] Step 5: Commit the App shell change

    git add web-frontend/src/App.vue web-frontend/src/tests/interaction.spec.ts
    git commit -m "feat(web): open overview drafts in editor"

### Task 3: Integration Verification And Release Gate

Files:
- Test: web-frontend/src/tests/dashboard.spec.ts
- Test: web-frontend/src/tests/interaction.spec.ts
- No production changes unless a test exposes a requirement explicitly covered by the spec.

Interfaces:
- Consumes: Task 1 continuation routing and Task 2 App event forwarding.
- Produces: verified direct draft entry, fallback navigation, live feedback, and regression-free Web build.

- [ ] Step 1: Run the complete Web test suite

    cd web-frontend
    npm.cmd run test -- --run

Expected: all test files pass, including dashboard continuation and App shell contracts.

- [ ] Step 2: Run the production build

    cd web-frontend
    npm.cmd run build

Expected: Vite completes without Vue template/compiler errors.

- [ ] Step 3: Check diff and changed-file scope

    git diff --check
    git status --short
    git log --oneline -8

Expected: no whitespace errors; only explicitly committed Web files are part of this iteration; pre-existing unrelated dirty files remain untouched.

- [ ] Step 4: Verify acceptance scenarios

Confirm from code and tests that:

1. A continuation resume with id emits open-draft and App assigns that id to editingDraftId.
2. Task/application continuations emit their existing navigate targets.
3. A resume continuation without id falls back to navigate("resume").
4. Continuation clicks update the existing aria-live="polite" status and do not make a new request.
5. Empty, loading, error, focus rotation, and responsive markup remain unchanged.

- [ ] Step 5: Commit only an explicitly required acceptance correction

If and only if Step 4 finds a concrete requirement gap, add a focused test or correction with:

    git add web-frontend/src
    git commit -m "test(web): close overview continuation coverage gap"

Otherwise, do not create an empty verification commit.
