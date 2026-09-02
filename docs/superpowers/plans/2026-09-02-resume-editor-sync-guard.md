# 简历编辑同步与离开保护实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Web 简历编辑器明确区分本机保存与云端同步，并在存在未同步修改时保护用户免于误退出。

**Architecture:** 在现有 `resume-editor-orchestration` 中维护相对最近远程保存的 `isDirty` 状态；编辑器消费该状态展示同步文案、内联离开确认和按需 `beforeunload` 保护。现有本机检查点、远程保存、校验和 App 路由保持不变。

**Tech Stack:** Vue 3 `<script setup>`, TypeScript, Vitest, existing localStorage checkpoint and async save helpers.

## Global Constraints

- 保留现有 800ms 本机检查点、防抖、远程手动保存和草稿数据结构。
- 不新增后端接口、数据库字段或依赖。
- 无未同步修改时返回直接触发既有 `cancel`；有未同步修改时必须先显示内联确认条。
- 恢复比服务端更新的本机检查点时，`isDirty` 必须为 `true`。
- 继续使用既有 `aria-live="polite"`、`text-action`、`primary-button` 和 `danger-action` 语义，窄屏不得遮挡文案。

---

### Task 1: Expose remote-sync dirty state

**Files:**
- Modify: `web-frontend/src/lib/resume-editor-orchestration.ts`
- Test: `web-frontend/src/tests/resume-editor-orchestration.spec.ts`

**Interfaces:**
- Consumes: existing checkpoint callbacks, `hydrate`, `save`, `draftRevision` behavior.
- Produces: returned `isDirty: Ref<boolean>` alongside existing `draft`, `localSaveState`, `saving`, `hydrate`, and `save` values.

- [ ] **Step 1: Write failing tests**

Add tests that assert:

```ts
await controller.hydrate(validDraft())
expect(controller.isDirty.value).toBe(false)
controller.draft.value!.resume.basic.city = "深圳"
await nextTick()
expect(controller.isDirty.value).toBe(true)
```

Also cover a newer restored checkpoint starting dirty, successful remote save clearing dirty when no edits occur during the request, preserving dirty when an edit occurs during the request, and retaining dirty after a remote error.

- [ ] **Step 2: Run the focused tests and verify the expected failure**

Run `npm.cmd run test -- --run src/tests/resume-editor-orchestration.spec.ts` from `web-frontend`. The new assertions must fail because `isDirty` is not yet exposed.

- [ ] **Step 3: Implement the minimal state machine**

Add `const isDirty = ref(false)`. Set it to whether `restoreCheckpoint(serverDraft)` returned a checkpoint during hydrate. In the deep draft watcher, set it to `true` for post-hydration edits. Capture `savedRevision` before remote save; only set `isDirty = false` after a successful save when `draftRevision === savedRevision`. Keep it true for in-flight edits, validation failures, remote errors, and local checkpoint errors. Return `isDirty` from the orchestration object.

- [ ] **Step 4: Run the focused tests and then the editor workflow tests**

Run `npm.cmd run test -- --run src/tests/resume-editor-orchestration.spec.ts src/tests/draft-checkpoint.spec.ts src/tests/interaction.spec.ts`. Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/lib/resume-editor-orchestration.ts web-frontend/src/tests/resume-editor-orchestration.spec.ts
git commit -m "feat(web): expose resume editor sync state"
```

### Task 2: Add editor feedback and leave protection

**Files:**
- Modify: `web-frontend/src/views/ResumeEditorView.vue`
- Test: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- Consumes: Task 1 `isDirty` ref, existing `localSaveState`, `saving`, `clearDraftCheckpoint`, and `cancel` emit.
- Produces: inline discard confirmation, accurate save-status copy, and conditional browser unload protection without changing App wiring.

- [ ] **Step 1: Write failing interaction contracts**

Extend the editor contracts to require `isDirty`, distinct local/cloud status branches, a confirmation state with “继续编辑” and “放弃并返回”, a successful `clearDraftCheckpoint` before `emit("cancel")`, and `beforeunload` registration/removal tied to dirty state. The test must fail against the current editor because none of these contracts are present.

- [ ] **Step 2: Run the focused interaction test and verify RED**

Run `npm.cmd run test -- --run src/tests/interaction.spec.ts`. Confirm failures are the missing editor contracts, not a test import or path error.

- [ ] **Step 3: Implement the minimal editor interaction**

Consume `isDirty` from orchestration. Change the status expression to show “正在保存到本机”, “已保存到本机，尚未同步”, “已同步到云端”, or the existing local-save error. Replace direct cancel with a handler that emits immediately when clean and otherwise opens an inline confirmation bar. The discard branch must clear the current checkpoint and emit `cancel` only when clearing succeeds; the retry-safe error remains in the editor. Register a `beforeunload` handler only while dirty and remove it when clean or unmounted. Keep loading/saving guards, keyboard shortcuts, validation, and current button classes intact.

- [ ] **Step 4: Run focused tests and build**

Run `npm.cmd run test -- --run src/tests/interaction.spec.ts src/tests/resume-editor-orchestration.spec.ts` and `npm.cmd run build` from `web-frontend`. Expected: all pass and Vite build succeeds.

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/views/ResumeEditorView.vue web-frontend/src/tests/interaction.spec.ts
git commit -m "feat(web): protect unsynced resume edits"
```

### Task 3: Whole-branch verification

**Files:**
- Inspect only: current branch changes and existing Web test/build configuration.

**Interfaces:**
- Consumes: Task 1 and Task 2 commits.
- Produces: verification evidence for full Web tests, production build, diff hygiene, and the Impeccable mechanical detector.

- [ ] **Step 1: Run the full Web test suite**

Run `npm.cmd run test -- --run` from `web-frontend`; all existing and new tests must pass.

- [ ] **Step 2: Run production build and diff checks**

Run `npm.cmd run build` from `web-frontend` and `git diff --check <merge-base>..HEAD` from the repository root. Both must exit successfully.

- [ ] **Step 3: Run the required UI mechanical detector**

Run `node "C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs" --json web-frontend/src/views/ResumeEditorView.vue web-frontend/src/App.vue`. Inspect any findings and fix only concrete regressions within scope.

- [ ] **Step 4: Record verification and complete the branch review**

Use the existing SDD ledger/review process, then remove only this plan’s ignored SDD workspace after the final review is clean.
